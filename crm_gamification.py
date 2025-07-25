#!/usr/bin/env python3
"""
Cura Genesis CRM - Gamification System
Points, badges, achievements, and leaderboards to motivate sales team
"""

from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel
import json
import logging
from enum import Enum
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# ===================================================================
# ENUMS
# ===================================================================

class BadgeType(Enum):
    ACTIVITY = "activity"          # Based on number of activities
    ACHIEVEMENT = "achievement"    # Based on specific achievements
    MILESTONE = "milestone"        # Based on reaching milestones
    STREAK = "streak"             # Based on consecutive actions
    SPECIAL = "special"           # Special recognition badges

class PointCategory(Enum):
    CONTACT = "contact"           # Contact-related points
    QUALIFICATION = "qualification"  # Lead qualification points
    CONVERSION = "conversion"     # Deal closing points
    ACTIVITY = "activity"         # General activity points
    BONUS = "bonus"              # Special bonus points

# ===================================================================
# DATABASE MODELS
# ===================================================================

class UserPoints(Base):
    __tablename__ = "user_points"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    points = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False)  # PointCategory
    action = Column(String(100), nullable=False)
    description = Column(Text)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    activity_id = Column(Integer, ForeignKey("activities.id"))
    multiplier = Column(Float, default=1.0)  # Point multipliers for special events
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    lead = relationship("Lead")
    activity = relationship("Activity")

class Badge(Base):
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    icon = Column(String(100))  # Icon name or emoji
    badge_type = Column(String(50), nullable=False)  # BadgeType
    points_required = Column(Integer, default=0)
    conditions = Column(JSON)  # Flexible conditions as JSON
    is_active = Column(Boolean, default=True)
    rarity = Column(String(20), default="common")  # common, rare, epic, legendary
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_badges = relationship("UserBadge", back_populates="badge")

class UserBadge(Base):
    __tablename__ = "user_badges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    lead_id = Column(Integer, ForeignKey("leads.id"))  # Lead that triggered the badge
    progress_data = Column(JSON)  # Store progress towards badge
    
    # Relationships
    user = relationship("User")
    badge = relationship("Badge", back_populates="user_badges")
    lead = relationship("Lead")

class LeaderboardEntry(Base):
    __tablename__ = "leaderboard_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly
    
    # Point metrics
    total_points = Column(Integer, default=0)
    contact_points = Column(Integer, default=0)
    qualification_points = Column(Integer, default=0)
    conversion_points = Column(Integer, default=0)
    
    # Activity metrics
    calls_made = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    meetings_scheduled = Column(Integer, default=0)
    leads_contacted = Column(Integer, default=0)
    leads_qualified = Column(Integer, default=0)
    deals_closed = Column(Integer, default=0)
    revenue_generated = Column(Float, default=0)
    
    # Performance metrics
    avg_response_time_hours = Column(Float)
    conversion_rate = Column(Float)
    lead_score_avg = Column(Float)
    
    # Rankings
    points_rank = Column(Integer)
    activity_rank = Column(Integer)
    conversion_rank = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(100))
    category = Column(String(50), nullable=False)
    target_value = Column(Integer, nullable=False)
    period = Column(String(20))  # daily, weekly, monthly, all_time
    points_reward = Column(Integer, default=0)
    badge_reward_id = Column(Integer, ForeignKey("badges.id"))
    conditions = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    current_value = Column(Integer, default=0)
    target_value = Column(Integer, nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    achievement = relationship("Achievement")

# ===================================================================
# PYDANTIC MODELS
# ===================================================================

class PointsCreate(BaseModel):
    user_id: int
    points: int
    category: str
    action: str
    description: Optional[str] = None
    lead_id: Optional[int] = None
    activity_id: Optional[int] = None
    multiplier: float = 1.0

class BadgeCreate(BaseModel):
    name: str
    description: str
    icon: str
    badge_type: str
    points_required: int = 0
    conditions: Dict[str, Any] = {}
    rarity: str = "common"

class LeaderboardResponse(BaseModel):
    user_id: int
    user_name: str
    total_points: int
    rank: int
    avatar: Optional[str] = None
    territory: Optional[str] = None
    deals_closed: int = 0
    revenue_generated: float = 0
    
class UserStatsResponse(BaseModel):
    user_id: int
    total_points: int
    daily_points: int
    weekly_points: int
    monthly_points: int
    badges_earned: int
    current_streak: int
    best_streak: int
    achievements_completed: int
    rank_daily: Optional[int] = None
    rank_weekly: Optional[int] = None
    rank_monthly: Optional[int] = None

class BadgeResponse(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    rarity: str
    earned_at: Optional[datetime] = None
    progress_percentage: Optional[float] = None

# ===================================================================
# GAMIFICATION SERVICE
# ===================================================================

class GamificationService:
    def __init__(self):
        # Point values for different actions
        self.point_values = {
            # Contact Points
            "first_contact": 10,
            "call_connected": 15,
            "call_voicemail": 5,
            "email_sent": 3,
            "email_opened": 5,
            "email_replied": 10,
            "meeting_scheduled": 25,
            
            # Qualification Points
            "lead_qualified": 30,
            "demo_scheduled": 50,
            "proposal_sent": 75,
            "needs_identified": 20,
            "budget_confirmed": 25,
            "decision_maker_contact": 15,
            
            # Conversion Points
            "deal_closed": 200,
            "upsell_closed": 100,
            "referral_generated": 50,
            "contract_signed": 150,
            
            # Activity Points
            "daily_login": 5,
            "profile_completed": 10,
            "training_completed": 20,
            "crm_updated": 2,
            "note_added": 3,
            
            # Bonus Points
            "speed_contact": 25,      # Contact within 1 hour
            "weekend_activity": 10,   # Activity on weekend
            "early_bird": 15,         # Activity before 8 AM
            "night_owl": 10,          # Activity after 8 PM
            "perfect_week": 100,      # 5 days of activity
        }
        
        # Badge conditions
        self.badge_conditions = {
            "first_blood": {"deals_closed": 1},
            "speed_demon": {"avg_response_time_hours": 1},
            "closer": {"deals_closed": 3, "period": "month"},
            "lead_hunter": {"calls_made": 50, "period": "week"},
            "territory_king": {"rank": 1, "scope": "territory", "period": "month"},
            "consistent_performer": {"days_active": 20, "period": "month"},
            "email_champion": {"emails_sent": 100, "period": "month"},
            "meeting_master": {"meetings_scheduled": 10, "period": "month"},
            "revenue_rockstar": {"revenue_generated": 50000, "period": "quarter"},
            "perfect_month": {"days_active": 30, "perfect_score": True},
        }

    async def award_points(self, db: Session, user_id: int, action: str, 
                          lead_id: Optional[int] = None, activity_id: Optional[int] = None,
                          multiplier: float = 1.0, custom_points: Optional[int] = None) -> int:
        """Award points to user for an action"""
        try:
            points = custom_points or self.point_values.get(action, 0)
            if points <= 0:
                return 0
            
            # Apply multiplier
            final_points = int(points * multiplier)
            
            # Determine category
            category = self._get_point_category(action)
            
            # Create point record
            point_record = UserPoints(
                user_id=user_id,
                points=final_points,
                category=category.value,
                action=action,
                description=self._get_action_description(action),
                lead_id=lead_id,
                activity_id=activity_id,
                multiplier=multiplier
            )
            
            db.add(point_record)
            db.commit()
            
            # Check for badge achievements
            await self._check_badge_achievements(db, user_id, action)
            
            # Update leaderboards
            await self._update_leaderboards(db, user_id)
            
            logger.info(f"Awarded {final_points} points to user {user_id} for {action}")
            return final_points
            
        except Exception as e:
            logger.error(f"Error awarding points: {e}")
            db.rollback()
            return 0

    async def get_user_stats(self, db: Session, user_id: int) -> UserStatsResponse:
        """Get comprehensive user statistics"""
        try:
            # Calculate total points
            total_points_query = db.query(UserPoints).filter(UserPoints.user_id == user_id)
            total_points = sum(p.points for p in total_points_query.all())
            
            # Calculate period-specific points
            now = datetime.utcnow()
            today = now.date()
            week_start = today - timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            
            daily_points = sum(p.points for p in total_points_query.filter(
                UserPoints.created_at >= datetime.combine(today, datetime.min.time())
            ).all())
            
            weekly_points = sum(p.points for p in total_points_query.filter(
                UserPoints.created_at >= datetime.combine(week_start, datetime.min.time())
            ).all())
            
            monthly_points = sum(p.points for p in total_points_query.filter(
                UserPoints.created_at >= datetime.combine(month_start, datetime.min.time())
            ).all())
            
            # Count badges
            badges_count = db.query(UserBadge).filter(UserBadge.user_id == user_id).count()
            
            # Calculate streaks (simplified - consecutive days with activity)
            current_streak = await self._calculate_current_streak(db, user_id)
            best_streak = await self._calculate_best_streak(db, user_id)
            
            # Count achievements
            achievements_count = db.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.completed == True
            ).count()
            
            # Get rankings
            rankings = await self._get_user_rankings(db, user_id)
            
            return UserStatsResponse(
                user_id=user_id,
                total_points=total_points,
                daily_points=daily_points,
                weekly_points=weekly_points,
                monthly_points=monthly_points,
                badges_earned=badges_count,
                current_streak=current_streak,
                best_streak=best_streak,
                achievements_completed=achievements_count,
                rank_daily=rankings.get("daily"),
                rank_weekly=rankings.get("weekly"),
                rank_monthly=rankings.get("monthly")
            )
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return UserStatsResponse(user_id=user_id, total_points=0, daily_points=0, 
                                   weekly_points=0, monthly_points=0, badges_earned=0,
                                   current_streak=0, best_streak=0, achievements_completed=0)

    async def get_leaderboard(self, db: Session, period: str = "daily", 
                            territory_id: Optional[int] = None, limit: int = 50) -> List[LeaderboardResponse]:
        """Get leaderboard for specified period"""
        try:
            # Calculate date range
            now = datetime.utcnow()
            if period == "daily":
                start_date = datetime.combine(now.date(), datetime.min.time())
            elif period == "weekly":
                start_date = datetime.combine(now.date() - timedelta(days=now.weekday()), datetime.min.time())
            elif period == "monthly":
                start_date = datetime.combine(now.date().replace(day=1), datetime.min.time())
            else:
                start_date = datetime(2020, 1, 1)  # All time
            
            # Query leaderboard entries
            query = db.query(LeaderboardEntry).filter(
                LeaderboardEntry.date >= start_date,
                LeaderboardEntry.period_type == period
            )
            
            if territory_id:
                # Filter by territory (would need to join with users table)
                pass
            
            entries = query.order_by(LeaderboardEntry.total_points.desc()).limit(limit).all()
            
            leaderboard = []
            for rank, entry in enumerate(entries, 1):
                user = db.query(User).filter(User.id == entry.user_id).first()
                if user:
                    leaderboard.append(LeaderboardResponse(
                        user_id=entry.user_id,
                        user_name=user.full_name,
                        total_points=entry.total_points,
                        rank=rank,
                        deals_closed=entry.deals_closed,
                        revenue_generated=entry.revenue_generated
                    ))
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []

    async def get_user_badges(self, db: Session, user_id: int) -> List[BadgeResponse]:
        """Get all badges for a user"""
        try:
            user_badges = db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
            badges = []
            
            for user_badge in user_badges:
                badge = user_badge.badge
                badges.append(BadgeResponse(
                    id=badge.id,
                    name=badge.name,
                    description=badge.description,
                    icon=badge.icon,
                    rarity=badge.rarity,
                    earned_at=user_badge.earned_at
                ))
            
            return badges
            
        except Exception as e:
            logger.error(f"Error getting user badges: {e}")
            return []

    async def create_badge(self, db: Session, badge_data: BadgeCreate) -> Badge:
        """Create a new badge"""
        try:
            badge = Badge(
                name=badge_data.name,
                description=badge_data.description,
                icon=badge_data.icon,
                badge_type=badge_data.badge_type,
                points_required=badge_data.points_required,
                conditions=badge_data.conditions,
                rarity=badge_data.rarity
            )
            
            db.add(badge)
            db.commit()
            db.refresh(badge)
            
            logger.info(f"Created badge: {badge.name}")
            return badge
            
        except Exception as e:
            logger.error(f"Error creating badge: {e}")
            db.rollback()
            raise

    async def _check_badge_achievements(self, db: Session, user_id: int, action: str):
        """Check if user earned any badges"""
        try:
            # Get all active badges
            badges = db.query(Badge).filter(Badge.is_active == True).all()
            
            for badge in badges:
                # Check if user already has this badge
                existing = db.query(UserBadge).filter(
                    UserBadge.user_id == user_id,
                    UserBadge.badge_id == badge.id
                ).first()
                
                if existing:
                    continue
                
                # Check badge conditions
                if await self._check_badge_conditions(db, user_id, badge, action):
                    # Award badge
                    user_badge = UserBadge(
                        user_id=user_id,
                        badge_id=badge.id
                    )
                    
                    db.add(user_badge)
                    db.commit()
                    
                    logger.info(f"User {user_id} earned badge: {badge.name}")
                    
                    # Award bonus points for badge
                    if badge.points_required > 0:
                        await self.award_points(db, user_id, "badge_earned", 
                                              custom_points=badge.points_required)
                    
        except Exception as e:
            logger.error(f"Error checking badge achievements: {e}")

    async def _check_badge_conditions(self, db: Session, user_id: int, badge: Badge, action: str) -> bool:
        """Check if badge conditions are met"""
        try:
            conditions = badge.conditions
            if not conditions:
                return False
            
            # Different condition types
            if "deals_closed" in conditions:
                deals_count = self._get_user_metric(db, user_id, "deals_closed", 
                                                  conditions.get("period"))
                if deals_count < conditions["deals_closed"]:
                    return False
            
            if "calls_made" in conditions:
                calls_count = self._get_user_metric(db, user_id, "calls_made", 
                                                  conditions.get("period"))
                if calls_count < conditions["calls_made"]:
                    return False
            
            if "avg_response_time_hours" in conditions:
                response_time = self._get_user_avg_response_time(db, user_id)
                if response_time > conditions["avg_response_time_hours"]:
                    return False
            
            # Add more condition checks as needed
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking badge conditions: {e}")
            return False

    def _get_point_category(self, action: str) -> PointCategory:
        """Determine point category based on action"""
        if action in ["first_contact", "call_connected", "call_voicemail", "email_sent", "email_opened", "meeting_scheduled"]:
            return PointCategory.CONTACT
        elif action in ["lead_qualified", "demo_scheduled", "proposal_sent", "needs_identified", "budget_confirmed"]:
            return PointCategory.QUALIFICATION
        elif action in ["deal_closed", "upsell_closed", "referral_generated", "contract_signed"]:
            return PointCategory.CONVERSION
        elif action in ["daily_login", "profile_completed", "training_completed", "crm_updated", "note_added"]:
            return PointCategory.ACTIVITY
        else:
            return PointCategory.BONUS

    def _get_action_description(self, action: str) -> str:
        """Get human-readable description for action"""
        descriptions = {
            "first_contact": "Made first contact with lead",
            "call_connected": "Successfully connected on call",
            "call_voicemail": "Left voicemail message",
            "email_sent": "Sent email to lead",
            "email_opened": "Lead opened email",
            "email_replied": "Lead replied to email",
            "meeting_scheduled": "Scheduled meeting with lead",
            "lead_qualified": "Qualified a lead",
            "demo_scheduled": "Scheduled product demo",
            "proposal_sent": "Sent proposal to lead",
            "deal_closed": "Closed a deal",
            "speed_contact": "Contacted lead within 1 hour",
            "weekend_activity": "Weekend activity bonus",
            "early_bird": "Early morning activity bonus",
            "night_owl": "Late night activity bonus",
            "perfect_week": "Perfect week achievement",
        }
        return descriptions.get(action, f"Action: {action}")

    def _get_user_metric(self, db: Session, user_id: int, metric: str, period: Optional[str] = None) -> int:
        """Get user metric for specified period"""
        # This would query the appropriate tables based on the metric
        # Implementation depends on your specific data structure
        return 0

    def _get_user_avg_response_time(self, db: Session, user_id: int) -> float:
        """Calculate user's average response time"""
        # This would calculate based on lead assignment and first contact times
        return 24.0  # Placeholder

    async def _calculate_current_streak(self, db: Session, user_id: int) -> int:
        """Calculate current activity streak"""
        # Implementation to count consecutive days with activity
        return 5  # Placeholder

    async def _calculate_best_streak(self, db: Session, user_id: int) -> int:
        """Calculate best activity streak"""
        # Implementation to find the longest streak
        return 10  # Placeholder

    async def _get_user_rankings(self, db: Session, user_id: int) -> Dict[str, int]:
        """Get user's current rankings"""
        # Implementation to calculate rankings for different periods
        return {"daily": 5, "weekly": 3, "monthly": 8}  # Placeholder

    async def _update_leaderboards(self, db: Session, user_id: int):
        """Update leaderboard entries for user"""
        try:
            today = date.today()
            
            # Update daily leaderboard entry
            daily_entry = db.query(LeaderboardEntry).filter(
                LeaderboardEntry.user_id == user_id,
                LeaderboardEntry.date == datetime.combine(today, datetime.min.time()),
                LeaderboardEntry.period_type == "daily"
            ).first()
            
            if not daily_entry:
                daily_entry = LeaderboardEntry(
                    user_id=user_id,
                    date=datetime.combine(today, datetime.min.time()),
                    period_type="daily"
                )
                db.add(daily_entry)
            
            # Recalculate metrics
            daily_points = db.query(UserPoints).filter(
                UserPoints.user_id == user_id,
                UserPoints.created_at >= datetime.combine(today, datetime.min.time())
            ).all()
            
            daily_entry.total_points = sum(p.points for p in daily_points)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating leaderboards: {e}")
            db.rollback()

# ===================================================================
# ACHIEVEMENT CHALLENGES
# ===================================================================

class ChallengeManager:
    """Manages time-limited challenges and competitions"""
    
    def __init__(self):
        self.active_challenges = {}
    
    async def create_weekly_challenge(self, db: Session, challenge_data: Dict[str, Any]):
        """Create a weekly challenge"""
        # Implementation for weekly challenges
        pass
    
    async def create_team_competition(self, db: Session, teams: List[int], duration_days: int):
        """Create team-based competition"""
        # Implementation for team competitions
        pass
    
    async def check_challenge_progress(self, db: Session, user_id: int, challenge_id: int):
        """Check user's progress on a challenge"""
        # Implementation for challenge progress tracking
        pass

# Export main components
__all__ = [
    "GamificationService",
    "ChallengeManager", 
    "UserPoints",
    "Badge",
    "UserBadge",
    "LeaderboardEntry",
    "PointsCreate",
    "BadgeCreate",
    "LeaderboardResponse",
    "UserStatsResponse",
    "BadgeResponse"
] 