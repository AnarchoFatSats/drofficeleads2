#!/usr/bin/env python3
"""
Cura Genesis CRM - Real-time System
WebSocket notifications, lead recycling, and background tasks
"""

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel
import json
import asyncio
import logging
from collections import defaultdict
from enum import Enum
import redis
from celery import Celery
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# ===================================================================
# ENUMS
# ===================================================================

class NotificationType(Enum):
    NEW_LEAD = "new_lead"
    LEAD_ASSIGNED = "lead_assigned"
    LEAD_UPDATED = "lead_updated"
    LEAD_RECYCLED = "lead_recycled"
    TASK_DUE = "task_due"
    TASK_OVERDUE = "task_overdue"
    ACHIEVEMENT = "achievement"
    BADGE_EARNED = "badge_earned"
    POINTS_AWARDED = "points_awarded"
    LEADERBOARD_UPDATE = "leaderboard_update"
    SYSTEM_ALERT = "system_alert"
    MEETING_REMINDER = "meeting_reminder"
    FOLLOW_UP_REMINDER = "follow_up_reminder"

class NotificationStatus(Enum):
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# ===================================================================
# DATABASE MODELS
# ===================================================================

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # NotificationType
    status = Column(String(20), nullable=False, default="unread")  # NotificationStatus
    priority = Column(String(20), nullable=False, default="medium")  # NotificationPriority
    
    title = Column(String(200), nullable=False)
    message = Column(Text)
    action_url = Column(String(500))
    action_text = Column(String(100))
    
    # Related entities
    lead_id = Column(Integer, ForeignKey("leads.id"))
    activity_id = Column(Integer, ForeignKey("activities.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"))
    
    # Metadata
    notification_metadata = Column(JSON)  # Additional data for notification
    expires_at = Column(DateTime)  # Auto-expire notifications
    
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)
    dismissed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    lead = relationship("Lead")
    activity = relationship("Activity")
    task = relationship("Task")

class LeadRecyclingLog(Base):
    __tablename__ = "lead_recycling_log"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    previous_user_id = Column(Integer, ForeignKey("users.id"))
    new_user_id = Column(Integer, ForeignKey("users.id"))
    
    reason = Column(String(100), nullable=False)  # no_contact, time_expired, manual, etc.
    days_assigned = Column(Integer)
    contact_attempts = Column(Integer)
    last_activity_date = Column(DateTime)
    
    recycled_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    lead = relationship("Lead")
    previous_user = relationship("User", foreign_keys=[previous_user_id])
    new_user = relationship("User", foreign_keys=[new_user_id])

class SystemAlert(Base):
    __tablename__ = "system_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # info, warning, error, critical
    title = Column(String(200), nullable=False)
    message = Column(Text)
    
    target_users = Column(JSON)  # List of user IDs or roles to notify
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey("users.id"))

# ===================================================================
# PYDANTIC MODELS
# ===================================================================

class NotificationCreate(BaseModel):
    user_id: int
    type: str
    title: str
    message: Optional[str] = None
    priority: str = "medium"
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    lead_id: Optional[int] = None
    activity_id: Optional[int] = None
    task_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None

class NotificationResponse(BaseModel):
    id: int
    type: str
    status: str
    priority: str
    title: str
    message: Optional[str]
    action_url: Optional[str]
    action_text: Optional[str]
    created_at: datetime
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()

class LeadRecyclingRule(BaseModel):
    priority_levels: List[str]
    days_without_contact: int
    min_contact_attempts: int
    territory_specific: bool = False
    is_active: bool = True

# ===================================================================
# WEBSOCKET CONNECTION MANAGER
# ===================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = defaultdict(list)
        self.user_sessions: Dict[int, Dict[str, Any]] = defaultdict(dict)
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a user's WebSocket"""
        await websocket.accept()
        self.active_connections[user_id].append(websocket)
        
        # Update user session info
        self.user_sessions[user_id].update({
            "connected_at": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "is_online": True
        })
        
        logger.info(f"WebSocket connected: user {user_id}")
        
        # Send welcome message with pending notifications
        await self.send_personal_message({
            "type": "connection_established",
            "data": {
                "message": "Connected to Cura Genesis CRM",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }, user_id)

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect a user's WebSocket"""
        if websocket in self.active_connections[user_id]:
            self.active_connections[user_id].remove(websocket)
        
        # Update session info
        if not self.active_connections[user_id]:  # No more connections
            self.user_sessions[user_id].update({
                "disconnected_at": datetime.utcnow(),
                "is_online": False
            })
        
        logger.info(f"WebSocket disconnected: user {user_id}")

    async def send_personal_message(self, message: Dict[str, Any], user_id: int):
        """Send message to specific user"""
        connections = self.active_connections.get(user_id, [])
        disconnected = []
        
        for connection in connections:
            try:
                await connection.send_json(message)
                # Update last seen
                self.user_sessions[user_id]["last_seen"] = datetime.utcnow()
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            if conn in self.active_connections[user_id]:
                self.active_connections[user_id].remove(conn)

    async def send_to_territory(self, message: Dict[str, Any], territory_id: int):
        """Send message to all users in a territory"""
        # Would need to query users by territory and send to each
        # Implementation depends on user-territory relationship
        pass

    async def send_to_role(self, message: Dict[str, Any], role: str):
        """Send message to all users with specific role"""
        # Would need to query users by role and send to each
        # Implementation depends on user role structure
        pass

    async def broadcast(self, message: Dict[str, Any]):
        """Send message to all connected users"""
        all_connections = []
        for user_connections in self.active_connections.values():
            all_connections.extend(user_connections)
        
        disconnected = []
        for connection in all_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            for user_id, connections in self.active_connections.items():
                if conn in connections:
                    connections.remove(conn)

    def get_online_users(self) -> List[int]:
        """Get list of currently online user IDs"""
        return [user_id for user_id, connections in self.active_connections.items() if connections]

    def is_user_online(self, user_id: int) -> bool:
        """Check if user is currently online"""
        return len(self.active_connections.get(user_id, [])) > 0

# ===================================================================
# NOTIFICATION SERVICE
# ===================================================================

class NotificationService:
    def __init__(self, connection_manager: ConnectionManager, redis_client=None):
        self.connection_manager = connection_manager
        self.redis_client = redis_client
        
    async def create_notification(self, db: Session, notification_data: NotificationCreate) -> Notification:
        """Create and send notification"""
        try:
            # Create notification in database
            notification = Notification(
                user_id=notification_data.user_id,
                type=notification_data.type,
                title=notification_data.title,
                message=notification_data.message,
                priority=notification_data.priority,
                action_url=notification_data.action_url,
                action_text=notification_data.action_text,
                lead_id=notification_data.lead_id,
                activity_id=notification_data.activity_id,
                task_id=notification_data.task_id,
                                 notification_metadata=notification_data.metadata,
                expires_at=notification_data.expires_at
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send real-time notification if user is online
            await self._send_realtime_notification(notification)
            
            # Store in Redis for quick access
            if self.redis_client:
                await self._cache_notification(notification)
            
            logger.info(f"Notification created: {notification.title} for user {notification.user_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            db.rollback()
            raise

    async def _send_realtime_notification(self, notification: Notification):
        """Send real-time notification via WebSocket"""
        message = {
            "type": "notification",
            "data": {
                "id": notification.id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "priority": notification.priority,
                "action_url": notification.action_url,
                "action_text": notification.action_text,
                "created_at": notification.created_at.isoformat(),
                                 "metadata": notification.notification_metadata
            }
        }
        
        await self.connection_manager.send_personal_message(message, notification.user_id)

    async def _cache_notification(self, notification: Notification):
        """Cache notification in Redis"""
        try:
            key = f"notifications:{notification.user_id}"
            notification_data = {
                "id": notification.id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "priority": notification.priority,
                "created_at": notification.created_at.isoformat()
            }
            
            self.redis_client.lpush(key, json.dumps(notification_data))
            self.redis_client.ltrim(key, 0, 99)  # Keep last 100 notifications
            self.redis_client.expire(key, 86400)  # Expire after 24 hours
            
        except Exception as e:
            logger.warning(f"Failed to cache notification: {e}")

    async def mark_notification_read(self, db: Session, notification_id: int, user_id: int):
        """Mark notification as read"""
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            
            if notification:
                notification.status = NotificationStatus.READ.value
                notification.read_at = datetime.utcnow()
                db.commit()
                
                # Send real-time update
                await self.connection_manager.send_personal_message({
                    "type": "notification_read",
                    "data": {"notification_id": notification_id}
                }, user_id)
                
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            db.rollback()

    async def get_user_notifications(self, db: Session, user_id: int, 
                                   unread_only: bool = False, limit: int = 50) -> List[NotificationResponse]:
        """Get notifications for user"""
        try:
            query = db.query(Notification).filter(Notification.user_id == user_id)
            
            if unread_only:
                query = query.filter(Notification.status == NotificationStatus.UNREAD.value)
            
            notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
            
            return [NotificationResponse.model_validate(n) for n in notifications]
            
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []

# ===================================================================
# LEAD RECYCLING SERVICE
# ===================================================================

class LeadRecyclingService:
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
        # Default recycling rules
        self.default_rules = {
            "A+": {"days": 7, "min_contacts": 3},
            "A": {"days": 7, "min_contacts": 3},
            "B+": {"days": 10, "min_contacts": 2},
            "B": {"days": 14, "min_contacts": 2},
            "C": {"days": 21, "min_contacts": 1}
        }

    async def check_leads_for_recycling(self, db: Session):
        """Check all leads for recycling eligibility"""
        try:
            now = datetime.utcnow()
            recycled_count = 0
            
            # Get leads eligible for recycling
            eligible_leads = db.query(Lead).filter(
                Lead.status.in_(["assigned", "contacted"]),
                Lead.recycling_eligible_at <= now,
                Lead.assigned_to.isnot(None)
            ).all()
            
            logger.info(f"Checking {len(eligible_leads)} leads for recycling")
            
            for lead in eligible_leads:
                if await self._should_recycle_lead(db, lead):
                    await self._recycle_lead(db, lead)
                    recycled_count += 1
            
            if recycled_count > 0:
                logger.info(f"Recycled {recycled_count} leads")
                
        except Exception as e:
            logger.error(f"Error checking leads for recycling: {e}")

    async def _should_recycle_lead(self, db: Session, lead) -> bool:
        """Determine if lead should be recycled"""
        try:
            # Get recycling rules for lead priority
            rules = self.default_rules.get(lead.priority, self.default_rules["C"])
            
            # Check days assigned
            days_assigned = (datetime.utcnow() - lead.assigned_at).days
            if days_assigned < rules["days"]:
                return False
            
            # Check contact attempts
            contact_attempts = db.query(Activity).filter(
                Activity.lead_id == lead.id,
                Activity.type.in_(["call", "email", "meeting"])
            ).count()
            
            if contact_attempts >= rules["min_contacts"]:
                return False
            
            # Check last activity
            last_activity = db.query(Activity).filter(
                Activity.lead_id == lead.id
            ).order_by(Activity.created_at.desc()).first()
            
            if last_activity:
                days_since_activity = (datetime.utcnow() - last_activity.created_at).days
                if days_since_activity < rules["days"]:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if lead should be recycled: {e}")
            return False

    async def _recycle_lead(self, db: Session, lead):
        """Recycle a lead"""
        try:
            previous_user_id = lead.assigned_to
            
            # Log the recycling
            recycling_log = LeadRecyclingLog(
                lead_id=lead.id,
                previous_user_id=previous_user_id,
                reason="time_expired",
                days_assigned=(datetime.utcnow() - lead.assigned_at).days,
                contact_attempts=db.query(Activity).filter(
                    Activity.lead_id == lead.id,
                    Activity.type.in_(["call", "email"])
                ).count()
            )
            
            # Update lead
            lead.assigned_to = None
            lead.assigned_at = None
            lead.status = "recycled"
            lead.recycling_eligible_at = None
            lead.times_recycled = (lead.times_recycled or 0) + 1
            
            # Add previous agent to the list
            if lead.previous_agents:
                lead.previous_agents.append(previous_user_id)
            else:
                lead.previous_agents = [previous_user_id]
            
            db.add(recycling_log)
            db.commit()
            
            # Send notifications
            await self._send_recycling_notifications(db, lead, previous_user_id)
            
            logger.info(f"Lead {lead.id} recycled from user {previous_user_id}")
            
        except Exception as e:
            logger.error(f"Error recycling lead: {e}")
            db.rollback()

    async def _send_recycling_notifications(self, db: Session, lead, previous_user_id: int):
        """Send notifications about lead recycling"""
        try:
            # Notify previous agent
            await self.notification_service.create_notification(db, NotificationCreate(
                user_id=previous_user_id,
                type=NotificationType.LEAD_RECYCLED.value,
                title=f"Lead Recycled: {lead.practice_name}",
                message=f"Lead has been recycled due to inactivity. It's now available for reassignment.",
                priority=NotificationPriority.MEDIUM.value,
                lead_id=lead.id,
                action_url=f"/leads/{lead.id}",
                action_text="View Lead"
            ))
            
            # Notify managers about recycled high-priority lead
            if lead.priority in ["A+", "A"]:
                # Would send to managers - implementation depends on user management
                pass
                
        except Exception as e:
            logger.error(f"Error sending recycling notifications: {e}")

    async def manual_recycle_lead(self, db: Session, lead_id: int, user_id: int, reason: str = "manual"):
        """Manually recycle a lead"""
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError("Lead not found")
            
            if lead.assigned_to:
                # Log manual recycling
                recycling_log = LeadRecyclingLog(
                    lead_id=lead.id,
                    previous_user_id=lead.assigned_to,
                    reason=reason,
                    days_assigned=(datetime.utcnow() - lead.assigned_at).days if lead.assigned_at else 0,
                    notes=f"Manually recycled by user {user_id}"
                )
                
                previous_user_id = lead.assigned_to
                
                # Update lead
                lead.assigned_to = None
                lead.assigned_at = None
                lead.status = "recycled"
                lead.recycling_eligible_at = None
                lead.times_recycled = (lead.times_recycled or 0) + 1
                
                db.add(recycling_log)
                db.commit()
                
                # Send notifications
                await self._send_recycling_notifications(db, lead, previous_user_id)
                
                logger.info(f"Lead {lead_id} manually recycled by user {user_id}")
                
        except Exception as e:
            logger.error(f"Error manually recycling lead: {e}")
            db.rollback()
            raise

# ===================================================================
# BACKGROUND TASKS (using Celery)
# ===================================================================

# Celery app configuration
celery_app = Celery(
    "cura_genesis_crm",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/2"
)

@celery_app.task
def check_lead_recycling_task():
    """Background task to check lead recycling"""
    try:
        # This would need to be connected to your database session
        # Implementation depends on your database setup
        logger.info("Checking lead recycling (background task)")
        
    except Exception as e:
        logger.error(f"Error in lead recycling task: {e}")

@celery_app.task
def send_task_reminders():
    """Send reminders for due/overdue tasks"""
    try:
        # Implementation for task reminders
        logger.info("Sending task reminders")
        
    except Exception as e:
        logger.error(f"Error sending task reminders: {e}")

@celery_app.task
def update_leaderboards():
    """Update daily leaderboards"""
    try:
        # Implementation for leaderboard updates
        logger.info("Updating leaderboards")
        
    except Exception as e:
        logger.error(f"Error updating leaderboards: {e}")

@celery_app.task
def cleanup_expired_notifications():
    """Clean up expired notifications"""
    try:
        # Implementation for notification cleanup
        logger.info("Cleaning up expired notifications")
        
    except Exception as e:
        logger.error(f"Error cleaning up notifications: {e}")

# ===================================================================
# REAL-TIME EVENT HANDLERS
# ===================================================================

class EventHandler:
    def __init__(self, notification_service: NotificationService, 
                 gamification_service, connection_manager: ConnectionManager):
        self.notification_service = notification_service
        self.gamification_service = gamification_service
        self.connection_manager = connection_manager

    async def handle_new_lead(self, db: Session, lead):
        """Handle new lead creation"""
        try:
            # Notify relevant users about new high-priority lead
            if lead.priority in ["A+", "A"]:
                # Notify managers or specific agents
                await self.notification_service.create_notification(db, NotificationCreate(
                    user_id=1,  # Would be dynamic based on territory/rules
                    type=NotificationType.NEW_LEAD.value,
                    title=f"New {lead.priority} Lead: {lead.practice_name}",
                    message=f"High-priority lead ready for assignment",
                    priority=NotificationPriority.HIGH.value,
                    lead_id=lead.id,
                    action_url=f"/leads/{lead.id}",
                    action_text="Assign Lead"
                ))
            
            # Broadcast to online managers
            await self.connection_manager.send_to_role({
                "type": "new_lead_alert",
                "data": {
                    "lead_id": lead.id,
                    "priority": lead.priority,
                    "practice_name": lead.practice_name,
                    "score": lead.score
                }
            }, "manager")
            
        except Exception as e:
            logger.error(f"Error handling new lead event: {e}")

    async def handle_lead_assignment(self, db: Session, lead, agent_id: int):
        """Handle lead assignment to agent"""
        try:
            # Notify agent about new assignment
            await self.notification_service.create_notification(db, NotificationCreate(
                user_id=agent_id,
                type=NotificationType.LEAD_ASSIGNED.value,
                title=f"New Lead Assigned: {lead.practice_name}",
                message=f"You have been assigned a {lead.priority} priority lead",
                priority=NotificationPriority.HIGH.value if lead.priority in ["A+", "A"] else NotificationPriority.MEDIUM.value,
                lead_id=lead.id,
                action_url=f"/leads/{lead.id}",
                action_text="View Lead"
            ))
            
            # Award points for lead assignment
            await self.gamification_service.award_points(
                db, agent_id, "lead_assigned", lead_id=lead.id
            )
            
        except Exception as e:
            logger.error(f"Error handling lead assignment: {e}")

    async def handle_activity_created(self, db: Session, activity, user_id: int):
        """Handle new activity creation"""
        try:
            # Award points based on activity type
            action_map = {
                "call": "call_connected" if activity.outcome == "connected" else "call_voicemail",
                "email": "email_sent",
                "meeting": "meeting_scheduled"
            }
            
            action = action_map.get(activity.type, "activity_completed")
            points = await self.gamification_service.award_points(
                db, user_id, action, lead_id=activity.lead_id, activity_id=activity.id
            )
            
            # Send real-time update about points
            if points > 0:
                await self.connection_manager.send_personal_message({
                    "type": "points_awarded",
                    "data": {
                        "points": points,
                        "action": action,
                        "total_points": "calculated_total"  # Would calculate actual total
                    }
                }, user_id)
            
        except Exception as e:
            logger.error(f"Error handling activity created: {e}")

# ===================================================================
# SCHEDULER
# ===================================================================

class TaskScheduler:
    def __init__(self):
        self.running = False
        
    async def start(self):
        """Start the scheduler"""
        self.running = True
        await asyncio.gather(
            self._schedule_lead_recycling(),
            self._schedule_task_reminders(),
            self._schedule_leaderboard_updates(),
            self._schedule_notification_cleanup()
        )
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
    
    async def _schedule_lead_recycling(self):
        """Schedule lead recycling checks"""
        while self.running:
            try:
                # Run every hour
                await asyncio.sleep(3600)
                celery_app.send_task("check_lead_recycling_task")
            except Exception as e:
                logger.error(f"Error in lead recycling scheduler: {e}")
    
    async def _schedule_task_reminders(self):
        """Schedule task reminder checks"""
        while self.running:
            try:
                # Run every 30 minutes
                await asyncio.sleep(1800)
                celery_app.send_task("send_task_reminders")
            except Exception as e:
                logger.error(f"Error in task reminder scheduler: {e}")
    
    async def _schedule_leaderboard_updates(self):
        """Schedule leaderboard updates"""
        while self.running:
            try:
                # Run every hour
                await asyncio.sleep(3600)
                celery_app.send_task("update_leaderboards")
            except Exception as e:
                logger.error(f"Error in leaderboard scheduler: {e}")
    
    async def _schedule_notification_cleanup(self):
        """Schedule notification cleanup"""
        while self.running:
            try:
                # Run daily
                await asyncio.sleep(86400)
                celery_app.send_task("cleanup_expired_notifications")
            except Exception as e:
                logger.error(f"Error in notification cleanup scheduler: {e}")

# Export main components
__all__ = [
    "ConnectionManager",
    "NotificationService", 
    "LeadRecyclingService",
    "EventHandler",
    "TaskScheduler",
    "NotificationCreate",
    "NotificationResponse",
    "WebSocketMessage",
    "celery_app"
] 