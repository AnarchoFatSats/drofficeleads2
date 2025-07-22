#!/usr/bin/env python3
"""
Cura Genesis CRM - Complete FastAPI Application
Full-featured CRM with authentication, gamification, lead tracking, and analytics
"""

import os
import sys
import json
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

# FastAPI and web framework imports
from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse

# Database and ORM imports
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func

# Authentication and security
from passlib.context import CryptContext
from jose import JWTError, jwt

# Validation and serialization
from pydantic import BaseModel, EmailStr, validator
from pydantic_settings import BaseSettings

# Background tasks and caching
import redis
from celery import Celery

# Utilities
import structlog
from enum import Enum
import asyncio
import logging

# Import your existing lead scoring systems
sys.path.append('.')
try:
    from medicare_allograft_lead_extractor import MedicareAllografLeadExtractor
    from rural_verified_scoring import RuralVerifiedScoring
    from overlooked_opportunity_scorer import OverlookedOpportunityScorer
    from recalibrated_scoring import RecalibratedScoring
except ImportError:
    logging.warning("Some lead scoring modules not found - running in basic mode")

# ================================
# Configuration and Settings
# ================================

class Settings(BaseSettings):
    database_url: str = "postgresql://alexsiegel@localhost:5432/cura_genesis_crm"
    secret_key: str = "cura-genesis-crm-super-secret-key-change-in-production-2025"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    refresh_token_expire_days: int = 7
    redis_url: str = "redis://localhost:6379/0"
    enable_gamification: bool = True
    recycling_enabled: bool = True
    recycling_days_default: int = 7
    min_contact_attempts: int = 3
    app_name: str = "Cura Genesis CRM"
    debug: bool = True

    class Config:
        env_file = ".env"

settings = Settings()

# ================================
# Logging Configuration
# ================================

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = structlog.get_logger()

# ================================
# Database Configuration
# ================================

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Database dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================================
# Redis Configuration
# ================================

try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    redis_client.ping()
    logger.info("✅ Redis connected successfully")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}")
    redis_client = None

# ================================
# Database Models
# ================================

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    DEMO_SCHEDULED = "demo_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    RECYCLED = "recycled"

class ActivityType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    DEMO = "demo"
    FOLLOW_UP = "follow_up"
    NOTE = "note"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.AGENT)
    is_active = Column(Boolean, default=True)
    phone = Column(String, nullable=True)
    territory = Column(String, nullable=True)
    hire_date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Gamification fields
    total_points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    badges = Column(JSON, default=list)
    
    # Relationships
    assigned_leads = relationship("Lead", back_populates="assigned_user")
    activities = relationship("Activity", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Original NPPES Data (preserved)
    npi = Column(String, unique=True, index=True)
    ein = Column(String, nullable=True)
    practice_name = Column(String, nullable=True)
    owner_name = Column(String, nullable=True)
    practice_phone = Column(String, nullable=True)
    owner_phone = Column(String, nullable=True)
    specialties = Column(String, nullable=True)
    providers = Column(Integer, default=1)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    entity_type = Column(String, nullable=True)
    is_sole_proprietor = Column(String, nullable=True)
    
    # Scoring System (preserved)
    score = Column(Integer, default=0)
    priority = Column(String, nullable=True)  # A+, A, B+, B, C
    category = Column(String, nullable=True)
    medicare_allograft_score = Column(Integer, default=0)
    overlooked_opportunity_score = Column(Integer, default=0)
    rural_verified_score = Column(Integer, default=0)
    scoring_breakdown = Column(JSON, nullable=True)
    
    # CRM Enhancement Fields
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW)
    source = Column(String, default="nppes_extraction")
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    
    # Lead Recycling System
    last_contact_date = Column(DateTime, nullable=True)
    next_follow_up = Column(DateTime, nullable=True)
    contact_attempts = Column(Integer, default=0)
    recycling_eligible_at = Column(DateTime, nullable=True)
    times_recycled = Column(Integer, default=0)
    previous_agents = Column(JSON, default=list)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    assigned_user = relationship("User", back_populates="assigned_leads")
    activities = relationship("Activity", back_populates="lead")

class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(SQLEnum(ActivityType), nullable=False)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    outcome = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    lead = relationship("Lead", back_populates="activities")
    user = relationship("User", back_populates="activities")

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    badge_icon = Column(String, nullable=True)
    points_required = Column(Integer, default=0)
    criteria = Column(JSON, nullable=True)  # Flexible criteria storage
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime, default=func.now())
    points_earned = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    notification_type = Column(String, default="info")  # info, success, warning, error
    is_read = Column(Boolean, default=False)
    data = Column(JSON, nullable=True)  # Additional data payload
    created_at = Column(DateTime, default=func.now())

# ================================
# Pydantic Models (API Schemas)
# ================================

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    role: UserRole = UserRole.AGENT
    phone: Optional[str] = None
    territory: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    total_points: int
    level: int
    badges: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class LeadResponse(BaseModel):
    id: int
    npi: Optional[str]
    practice_name: Optional[str]
    owner_name: Optional[str]
    practice_phone: Optional[str]
    owner_phone: Optional[str]
    specialties: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    score: int
    priority: Optional[str]
    status: LeadStatus
    assigned_user_id: Optional[int]
    contact_attempts: int
    created_at: datetime

    class Config:
        from_attributes = True

class ActivityCreate(BaseModel):
    lead_id: int
    activity_type: ActivityType
    subject: str
    description: Optional[str] = None
    outcome: Optional[str] = None
    duration_minutes: Optional[int] = None
    scheduled_at: Optional[datetime] = None

class ActivityResponse(BaseModel):
    id: int
    lead_id: int
    user_id: int
    activity_type: ActivityType
    subject: str
    description: Optional[str]
    outcome: Optional[str]
    duration_minutes: Optional[int]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    user_id: int
    username: str
    full_name: str
    total_points: int
    level: int
    rank: int

class AnalyticsResponse(BaseModel):
    total_leads: int
    leads_by_status: Dict[str, int]
    conversion_rate: float
    avg_deal_size: float
    top_performers: List[LeaderboardEntry]
    recent_activities: List[ActivityResponse]

# ================================
# Authentication Service
# ================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    @staticmethod
    def create_refresh_token(data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    @staticmethod
    def verify_token(token: str):
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            return username
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

# ================================
# Gamification Service
# ================================

class GamificationService:
    POINT_VALUES = {
        ActivityType.CALL: 10,
        ActivityType.EMAIL: 5,
        ActivityType.MEETING: 25,
        ActivityType.DEMO: 50,
        ActivityType.FOLLOW_UP: 8,
        ActivityType.NOTE: 2,
        "lead_qualified": 30,
        "demo_completed": 75,
        "deal_closed": 200,
        "first_contact": 15,
    }
    
    @staticmethod
    def award_points(db: Session, user_id: int, activity_type: str, quantity: int = 1):
        points = GamificationService.POINT_VALUES.get(activity_type, 0) * quantity
        
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.total_points += points
            
            # Level up logic (every 1000 points = new level)
            new_level = (user.total_points // 1000) + 1
            if new_level > user.level:
                user.level = new_level
                # Award level-up badge
                if user.badges is None:
                    user.badges = []
                user.badges.append(f"Level {new_level} Achiever")
            
            db.commit()
            return points
        return 0
    
    @staticmethod
    def get_leaderboard(db: Session, limit: int = 10) -> List[LeaderboardEntry]:
        users = db.query(User).filter(User.is_active == True).order_by(User.total_points.desc()).limit(limit).all()
        
        leaderboard = []
        for rank, user in enumerate(users, 1):
            leaderboard.append(LeaderboardEntry(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                total_points=user.total_points,
                level=user.level,
                rank=rank
            ))
        
        return leaderboard

# ================================
# Lead Recycling Service
# ================================

class LeadRecyclingService:
    @staticmethod
    def mark_for_recycling(db: Session, lead_id: int):
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead and lead.assigned_user_id:
            # Mark as eligible for recycling after configured days
            recycling_date = datetime.utcnow() + timedelta(days=settings.recycling_days_default)
            lead.recycling_eligible_at = recycling_date
            db.commit()
    
    @staticmethod
    def process_recycling(db: Session):
        """Background task to recycle leads"""
        now = datetime.utcnow()
        eligible_leads = db.query(Lead).filter(
            Lead.recycling_eligible_at <= now,
            Lead.status.notin_([LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST])
        ).all()
        
        recycled_count = 0
        for lead in eligible_leads:
            if lead.assigned_user_id:
                # Track previous agent
                if lead.previous_agents is None:
                    lead.previous_agents = []
                lead.previous_agents.append(lead.assigned_user_id)
                
                # Unassign and mark as recycled
                lead.assigned_user_id = None
                lead.assigned_at = None
                lead.status = LeadStatus.RECYCLED
                lead.times_recycled += 1
                lead.recycling_eligible_at = None
                
                recycled_count += 1
        
        db.commit()
        logger.info(f"♻️ Recycled {recycled_count} leads")
        return recycled_count

# ================================
# WebSocket Connection Manager
# ================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_id] = websocket
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.user_connections:
            await self.user_connections[user_id].send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# ================================
# Dependencies
# ================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    username = AuthService.verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# ================================
# Initialize Lead Scoring Systems
# ================================

try:
    medicare_extractor = MedicareAllografLeadExtractor()
    rural_scorer = RuralVerifiedScoring()
    opportunity_scorer = OverlookedOpportunityScorer()
    recalibrated_scorer = RecalibratedScoring()
    logger.info("Lead scoring systems initialized successfully")
except Exception as e:
    logger.warning(f"Lead scoring initialization warning: {e}")
    medicare_extractor = None
    rural_scorer = None
    opportunity_scorer = None
    recalibrated_scorer = None

# ================================
# FastAPI Application
# ================================

app = FastAPI(
    title=settings.app_name,
    description="Advanced CRM system with lead scoring, gamification, and analytics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# API Routes - Authentication
# ================================

@app.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create new user
    hashed_password = AuthService.get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        phone=user_data.phone,
        territory=user_data.territory,
        badges=[]
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"👤 New user registered: {user.username} ({user.role})")
    return user

@app.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user or not AuthService.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive")
    
    # Create tokens
    access_token = AuthService.create_access_token(data={"sub": user.username})
    refresh_token = AuthService.create_refresh_token(data={"sub": user.username})
    
    logger.info(f"🔑 User logged in: {user.username}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.from_orm(user)
    )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user

# ================================
# API Routes - Lead Management
# ================================

@app.get("/api/v1/leads", response_model=List[LeadResponse])
async def get_leads(
    skip: int = 0,
    limit: int = 100,
    status: Optional[LeadStatus] = None,
    assigned_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get leads with filtering options"""
    query = db.query(Lead)
    
    # Filter by status if provided
    if status:
        query = query.filter(Lead.status == status)
    
    # Filter by assignment if requested
    if assigned_only:
        query = query.filter(Lead.assigned_user_id == current_user.id)
    
    # For agents, only show their assigned leads unless they're admin/manager
    if current_user.role == UserRole.AGENT:
        query = query.filter(Lead.assigned_user_id == current_user.id)
    
    leads = query.offset(skip).limit(limit).all()
    return leads

@app.get("/api/v1/leads/legacy", response_model=Dict[str, Any])
async def get_legacy_leads():
    """Get leads from the original JSON file (for backward compatibility)"""
    try:
        leads_file = Path('web/data/hot_leads.json')
        if leads_file.exists():
            with open(leads_file, 'r') as f:
                leads = json.load(f)
            return {
                'leads': leads[:10], 
                'total': len(leads), 
                'message': 'Legacy leads loaded successfully'
            }
        else:
            return {'leads': [], 'total': 0, 'message': 'No legacy leads file found'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error loading legacy leads: {str(e)}')

@app.post("/api/v1/leads/{lead_id}/assign")
async def assign_lead(
    lead_id: int,
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign a lead to an agent"""
    # Only admins and managers can assign leads
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    agent = db.query(User).filter(User.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    lead.assigned_user_id = agent_id
    lead.assigned_at = datetime.utcnow()
    if lead.status == LeadStatus.NEW:
        lead.status = LeadStatus.CONTACTED
    
    db.commit()
    
    # Send notification to agent
    await manager.send_personal_message(
        json.dumps({
            "type": "lead_assigned",
            "message": f"New lead assigned: {lead.practice_name}",
            "lead_id": lead_id
        }),
        agent_id
    )
    
    logger.info(f"📋 Lead {lead_id} assigned to {agent.username}")
    return {"message": "Lead assigned successfully"}

@app.patch("/api/v1/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: int,
    status: LeadStatus,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update lead status"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check permissions
    if current_user.role == UserRole.AGENT and lead.assigned_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only update your assigned leads")
    
    old_status = lead.status
    lead.status = status
    lead.updated_at = datetime.utcnow()
    
    # Award points for status changes
    if status == LeadStatus.QUALIFIED and old_status != LeadStatus.QUALIFIED:
        GamificationService.award_points(db, current_user.id, "lead_qualified")
    elif status == LeadStatus.CLOSED_WON:
        GamificationService.award_points(db, current_user.id, "deal_closed")
    
    db.commit()
    
    logger.info(f"📊 Lead {lead_id} status updated: {old_status} → {status}")
    return {"message": "Lead status updated successfully"}

# ================================
# API Routes - Activities
# ================================

@app.post("/api/v1/activities", response_model=ActivityResponse)
async def create_activity(
    activity: ActivityCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new activity"""
    # Verify lead exists and user has access
    lead = db.query(Lead).filter(Lead.id == activity.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if current_user.role == UserRole.AGENT and lead.assigned_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only add activities to your assigned leads")
    
    # Create activity
    db_activity = Activity(
        lead_id=activity.lead_id,
        user_id=current_user.id,
        activity_type=activity.activity_type,
        subject=activity.subject,
        description=activity.description,
        outcome=activity.outcome,
        duration_minutes=activity.duration_minutes,
        scheduled_at=activity.scheduled_at,
        completed_at=datetime.utcnow() if not activity.scheduled_at else None
    )
    
    db.add(db_activity)
    
    # Update lead contact tracking
    lead.last_contact_date = datetime.utcnow()
    lead.contact_attempts += 1
    
    # Award gamification points
    GamificationService.award_points(db, current_user.id, activity.activity_type)
    
    # Special points for first contact
    if lead.contact_attempts == 1:
        GamificationService.award_points(db, current_user.id, "first_contact")
    
    db.commit()
    db.refresh(db_activity)
    
    logger.info(f"📝 Activity created: {activity.activity_type} for lead {activity.lead_id}")
    return db_activity

@app.get("/api/v1/activities", response_model=List[ActivityResponse])
async def get_activities(
    lead_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get activities with optional lead filtering"""
    query = db.query(Activity)
    
    if lead_id:
        query = query.filter(Activity.lead_id == lead_id)
    
    # For agents, only show activities for their assigned leads
    if current_user.role == UserRole.AGENT:
        assigned_lead_ids = db.query(Lead.id).filter(Lead.assigned_user_id == current_user.id).subquery()
        query = query.filter(Activity.lead_id.in_(assigned_lead_ids))
    
    activities = query.order_by(Activity.created_at.desc()).offset(skip).limit(limit).all()
    return activities

# ================================
# API Routes - Gamification
# ================================

@app.get("/api/v1/gamification/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the points leaderboard"""
    return GamificationService.get_leaderboard(db, limit)

@app.get("/api/v1/gamification/my-stats")
async def get_my_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's gamification stats"""
    # Get user's rank
    all_users = db.query(User).filter(User.is_active == True).order_by(User.total_points.desc()).all()
    rank = next((i + 1 for i, user in enumerate(all_users) if user.id == current_user.id), 0)
    
    # Get recent activities count
    recent_activities = db.query(Activity).filter(
        Activity.user_id == current_user.id,
        Activity.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    return {
        "total_points": current_user.total_points,
        "level": current_user.level,
        "rank": rank,
        "badges": current_user.badges or [],
        "recent_activities": recent_activities
    }

# ================================
# API Routes - Analytics
# ================================

@app.get("/api/v1/analytics/dashboard", response_model=AnalyticsResponse)
async def get_analytics_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics dashboard"""
    
    # Total leads
    total_leads = db.query(Lead).count()
    
    # Leads by status
    status_counts = {}
    for status in LeadStatus:
        count = db.query(Lead).filter(Lead.status == status).count()
        status_counts[status.value] = count
    
    # Conversion rate (closed won / total leads with contact attempts)
    contacted_leads = db.query(Lead).filter(Lead.contact_attempts > 0).count()
    won_leads = db.query(Lead).filter(Lead.status == LeadStatus.CLOSED_WON).count()
    conversion_rate = (won_leads / contacted_leads * 100) if contacted_leads > 0 else 0
    
    # Top performers
    top_performers = GamificationService.get_leaderboard(db, 5)
    
    # Recent activities
    recent_activities = db.query(Activity).order_by(Activity.created_at.desc()).limit(10).all()
    
    return AnalyticsResponse(
        total_leads=total_leads,
        leads_by_status=status_counts,
        conversion_rate=round(conversion_rate, 2),
        avg_deal_size=0.0,  # Placeholder - would need deal value tracking
        top_performers=top_performers,
        recent_activities=recent_activities
    )

# ================================
# WebSocket Endpoint
# ================================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now - can add real-time features here
            await manager.send_personal_message(f"Echo: {data}", user_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# ================================
# Background Tasks
# ================================

@app.post("/admin/recycle-leads")
async def trigger_lead_recycling(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Manually trigger lead recycling (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    recycled_count = LeadRecyclingService.process_recycling(db)
    return {"message": f"Recycled {recycled_count} leads"}

# ================================
# Health and Status
# ================================

@app.get("/")
async def root():
    return {
        "message": "Cura Genesis CRM API",
        "status": "running",
        "version": "1.0.0",
        "features": [
            "Authentication & Authorization",
            "Lead Management & Scoring",
            "Activity Tracking",
            "Gamification System",
            "Real-time Notifications",
            "Analytics Dashboard",
            "Lead Recycling"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",
        "redis": "connected" if redis_client else "disconnected",
        "lead_scoring": "active" if medicare_extractor else "disabled"
    }
    
    try:
        # Test database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except:
        health_status["database"] = "error"
        health_status["status"] = "unhealthy"
    
    return health_status

# ================================
# Startup Events
# ================================

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting Cura Genesis CRM", version="1.0.0")
    
    # Create tables if they don't exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Create default admin user if none exists
    try:
        db = SessionLocal()
        admin_exists = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin_exists:
            admin_user = User(
                email="admin@curagenesis.com",
                username="admin",
                full_name="CRM Administrator",
                hashed_password=AuthService.get_password_hash("admin123"),
                role=UserRole.ADMIN,
                badges=["Founder", "Administrator"]
            )
            db.add(admin_user)
            db.commit()
            logger.info("👑 Default admin user created: admin / admin123")
        db.close()
    except Exception as e:
        logger.warning(f"⚠️ Admin user creation failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Cura Genesis CRM")

# ================================
# Run the application
# ================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001, 
        log_level="info" if not settings.debug else "debug"
    ) 