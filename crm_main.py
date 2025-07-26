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
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

# FastAPI and web framework imports
from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Database and ORM imports
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session, relationship
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

# Import shared models to avoid circular imports
from crm_shared_models import UserRole, LeadStatus, LeadPriority, ActivityType

# Import your existing lead scoring systems
sys.path.append('.')
try:
    from medicare_allograft_lead_extractor import MedicareAllografLeadExtractor
    from rural_verified_scoring import RuralVerifiedScoring
    from overlooked_opportunity_scorer import OverlookedOpportunityScorer
    from recalibrated_scoring import RecalibratedScoring
    # Import lead distribution services with late import to avoid circular dependency 
    # from crm_lead_distribution import LeadDistributionService, run_lead_recycling_check, run_lead_redistribution
    from crm_monitoring import (
        initialize_monitoring, MonitoringMiddleware, metrics_collector, 
        apm_monitor, monitoring_dashboard, PROMETHEUS_AVAILABLE
    )
except ImportError:
    logging.warning("Some lead scoring modules not found - running in basic mode")

# ================================
# Configuration and Settings
# ================================

class Settings(BaseSettings):
    database_url: str = "postgresql://crmuser:CuraGenesis2024!SecurePassword@cura-genesis-crm-db.c6ds4c4qok1n.us-east-1.rds.amazonaws.com:5432/cura_genesis_crm"
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

    model_config = {"env_file": ".env", "extra": "ignore"}

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

class Base(DeclarativeBase):
    pass

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

# Import shared enums to avoid circular dependencies
from crm_shared_models import UserRole, LeadStatus, ActivityType, LeadPriority, ActivityOutcome

# User Model - Replace points/level with performance metrics
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]), default=UserRole.AGENT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True))
    
    # Team hierarchy
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Replace points/level with performance metrics
    conversion_rate = Column(Float, default=0.0)  # Percentage of leads converted
    activity_score = Column(Integer, default=0)   # Raw activity count
    deals_closed = Column(Integer, default=0)     # Total deals closed
    current_percentile = Column(Float, default=0.0)  # Performance percentile (0-100)
    current_rank = Column(Integer, default=0)     # Current rank among peers
    performance_score = Column(Float, default=0.0)  # Computed score for ranking
    
    # Keep badges for achievements
    badges = Column(JSON)
    
    # Relationships
    leads = relationship("Lead", back_populates="assigned_user")
    activities = relationship("Activity", back_populates="user")
    
    # Team hierarchy relationships
    manager = relationship("User", remote_side=[id], backref="team_members")

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
    status = Column(SQLEnum(LeadStatus, name="lead_status", values_callable=lambda x: [e.value for e in x]), default=LeadStatus.NEW)
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
    assigned_user = relationship("User", back_populates="leads")
    activities = relationship("Activity", back_populates="lead")

class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(SQLEnum(ActivityType, name="activity_type", values_callable=lambda x: [e.value for e in x]), nullable=False)
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

# Achievement system replaced with simple badges stored in User.badges JSON field

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

class AgentLeadTypePerformance(Base):
    """Track agent performance by lead type for smart assignment"""
    __tablename__ = "agent_lead_type_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Lead Type Categorization
    specialty_category = Column(String, nullable=True)  # e.g., "Cardiology", "Nephrology"
    priority_level = Column(String, nullable=True)      # A+, A, B+, B, C
    state_region = Column(String, nullable=True)        # State for geographic patterns
    practice_size = Column(String, nullable=True)       # Small (1-2), Medium (3-10), Large (10+)
    score_range = Column(String, nullable=True)         # High (80+), Medium (60-79), Low (<60)
    lead_source = Column(String, nullable=True)         # Medicare, Rural, Overlooked, etc.
    
    # Performance Metrics
    total_assigned = Column(Integer, default=0)         # Total leads of this type assigned
    total_contacted = Column(Integer, default=0)        # Total contacted
    total_closed_won = Column(Integer, default=0)       # Total successfully closed
    total_closed_lost = Column(Integer, default=0)      # Total lost
    total_recycled = Column(Integer, default=0)         # Total recycled back to pool
    
    # Calculated Performance Scores
    contact_rate = Column(Float, default=0.0)           # contacted / assigned
    conversion_rate = Column(Float, default=0.0)        # closed_won / contacted
    close_rate = Column(Float, default=0.0)            # closed_won / assigned
    avg_days_to_close = Column(Float, default=0.0)     # Average time to close
    
    # Timestamps
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    agent = relationship("User")

class LeadTypeAnalytics(Base):
    """Aggregate analytics by lead type across all agents"""
    __tablename__ = "lead_type_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Lead Type Categorization (same as above)
    specialty_category = Column(String, nullable=True)
    priority_level = Column(String, nullable=True)
    state_region = Column(String, nullable=True)
    practice_size = Column(String, nullable=True)
    score_range = Column(String, nullable=True)
    lead_source = Column(String, nullable=True)
    
    # Aggregate Metrics
    total_leads = Column(Integer, default=0)
    total_contacted = Column(Integer, default=0)
    total_closed_won = Column(Integer, default=0)
    total_closed_lost = Column(Integer, default=0)
    
    # Performance Metrics
    overall_contact_rate = Column(Float, default=0.0)
    overall_conversion_rate = Column(Float, default=0.0)
    overall_close_rate = Column(Float, default=0.0)
    avg_deal_value = Column(Float, default=0.0)
    
    # Top Performers for this lead type
    best_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    best_agent_conversion_rate = Column(Float, default=0.0)
    
    # Update tracking
    last_calculated = Column(DateTime, default=func.now())
    
    # Relationships
    best_agent = relationship("User")

# ================================
# Pydantic Models (API Schemas)
# ================================

class LeadCreate(BaseModel):
    """Schema for creating new leads via API"""
    npi: Optional[str] = None
    ein: Optional[str] = None
    practice_name: str
    owner_name: Optional[str] = None
    practice_phone: Optional[str] = None
    owner_phone: Optional[str] = None
    specialties: Optional[str] = None
    category: Optional[str] = None
    providers: int = 1
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None
    entity_type: Optional[str] = None
    is_sole_proprietor: Optional[str] = None
    
    # Optional scoring (will be calculated if not provided)
    score: Optional[int] = None
    priority: Optional[str] = None
    medicare_allograft_score: Optional[int] = 0
    overlooked_opportunity_score: Optional[int] = 0
    rural_verified_score: Optional[int] = 0
    scoring_breakdown: Optional[Dict[str, Any]] = None
    
    # Lead source tracking
    source: str = "api_manual_entry"
    estimated_deal_value: Optional[float] = None

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

# UserResponse Model - Update to show percentiles/ranks
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    manager_id: Optional[int]
    conversion_rate: float
    activity_score: int
    deals_closed: int
    current_percentile: float
    current_rank: int
    badges: Optional[List[str]]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class LeadResponse(BaseModel):
    id: int
    
    # Original NPPES Data
    npi: Optional[str]
    ein: Optional[str]
    practice_name: Optional[str]
    owner_name: Optional[str]
    practice_phone: Optional[str]
    owner_phone: Optional[str]
    specialties: Optional[str]
    providers: Optional[int]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    address: Optional[str]
    entity_type: Optional[str]
    is_sole_proprietor: Optional[str]
    
    # Scoring System
    score: int
    priority: Optional[str]
    category: Optional[str]
    medicare_allograft_score: Optional[int]
    overlooked_opportunity_score: Optional[int]
    rural_verified_score: Optional[int]
    scoring_breakdown: Optional[Dict[str, Any]]
    
    # CRM Enhancement Fields
    status: LeadStatus
    source: Optional[str]
    assigned_user_id: Optional[int]
    assigned_at: Optional[datetime]
    
    # Lead Recycling System
    last_contact_date: Optional[datetime]
    next_follow_up: Optional[datetime]
    contact_attempts: int
    recycling_eligible_at: Optional[datetime]
    times_recycled: Optional[int]
    previous_agents: Optional[List[int]]
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class LeadUpdate(BaseModel):
    """Schema for updating existing leads via API - allows agents to edit core lead information"""
    
    # Core Lead Information that agents can edit
    practice_name: Optional[str] = None
    owner_name: Optional[str] = None
    practice_phone: Optional[str] = None
    owner_phone: Optional[str] = None
    
    # Address Information
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None
    
    # Business Details
    ein: Optional[str] = None
    npi: Optional[str] = None
    entity_type: Optional[str] = None
    specialties: Optional[str] = None
    
    # Additional editable fields
    providers: Optional[int] = None
    is_sole_proprietor: Optional[str] = None
    category: Optional[str] = None
    
    class Config:
        # Only include non-None values in the update
        exclude_unset = True

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

# LeaderboardEntry Model - Update for percentile/rank system
class LeaderboardEntry(BaseModel):
    user_id: int
    username: str
    full_name: Optional[str]
    conversion_rate: float
    activity_score: int
    deals_closed: int
    current_percentile: float
    rank: int

class AnalyticsResponse(BaseModel):
    total_leads: int
    leads_by_status: Dict[str, int]
    conversion_rate: float
    avg_deal_size: float
    top_performers: List[LeaderboardEntry]
    recent_activities: List[ActivityResponse]

class LeadTypePerformanceResponse(BaseModel):
    """Agent performance for a specific lead type"""
    agent_id: int
    agent_name: str
    specialty_category: Optional[str]
    priority_level: Optional[str]
    state_region: Optional[str]
    practice_size: Optional[str]
    score_range: Optional[str]
    lead_source: Optional[str]
    total_assigned: int
    total_contacted: int
    total_closed_won: int
    contact_rate: float
    conversion_rate: float
    close_rate: float
    avg_days_to_close: float

class LeadTypeAnalyticsResponse(BaseModel):
    """Analytics for a specific lead type across all agents"""
    specialty_category: Optional[str]
    priority_level: Optional[str]
    state_region: Optional[str]
    practice_size: Optional[str]
    score_range: Optional[str]
    lead_source: Optional[str]
    total_leads: int
    total_contacted: int
    total_closed_won: int
    overall_contact_rate: float
    overall_conversion_rate: float
    overall_close_rate: float
    best_agent_name: Optional[str]
    best_agent_conversion_rate: float
    top_agents: List[LeadTypePerformanceResponse]

class SmartAssignmentResponse(BaseModel):
    """Response for smart lead assignment recommendations"""
    lead_id: int
    recommended_agent_id: int
    recommended_agent_name: str
    confidence_score: float
    reason: str
    lead_type_match: Dict[str, str]

# Team Management Models
class CreateUserRequest(BaseModel):
    """Request model for creating new users"""
    username: str
    email: str
    full_name: str
    password: str
    role: UserRole
    manager_id: Optional[int] = None

class TeamMemberResponse(BaseModel):
    """Response model for team member with basic info"""
    id: int
    username: str
    full_name: Optional[str]
    email: str
    role: UserRole
    is_active: bool
    current_percentile: float
    current_rank: int
    deals_closed: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TeamOverviewResponse(BaseModel):
    """Response model for team overview"""
    manager: UserResponse
    team_members: List[TeamMemberResponse]
    team_stats: Dict[str, Any]

class ManagerStatsResponse(BaseModel):
    """Response model for manager statistics"""
    manager_id: int
    manager_name: str
    team_size: int
    team_conversion_rate: float
    team_deals_closed: int
    avg_team_percentile: float
    top_performer: Optional[TeamMemberResponse]

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
# Lead Type Analytics Service
# ================================

class LeadTypeAnalyticsService:
    @staticmethod
    def categorize_lead(lead: Lead) -> Dict[str, str]:
        """Categorize a lead for analytics tracking"""
        # Extract primary specialty
        specialty_category = "General"
        if lead.specialties:
            specialties_lower = lead.specialties.lower()
            if "cardio" in specialties_lower or "heart" in specialties_lower:
                specialty_category = "Cardiology"
            elif "nephro" in specialties_lower or "kidney" in specialties_lower or "renal" in specialties_lower:
                specialty_category = "Nephrology"
            elif "onco" in specialties_lower or "cancer" in specialties_lower:
                specialty_category = "Oncology"
            elif "endo" in specialties_lower or "diabetes" in specialties_lower:
                specialty_category = "Endocrinology"
            elif "neuro" in specialties_lower:
                specialty_category = "Neurology"
            elif "gastro" in specialties_lower:
                specialty_category = "Gastroenterology"
            elif "pulmo" in specialties_lower or "lung" in specialties_lower:
                specialty_category = "Pulmonology"
        
        # Practice size category
        practice_size = "Small"
        if lead.providers:
            if lead.providers >= 10:
                practice_size = "Large"
            elif lead.providers >= 3:
                practice_size = "Medium"
        
        # Score range
        score_range = "Low"
        if lead.score >= 80:
            score_range = "High"
        elif lead.score >= 60:
            score_range = "Medium"
        
        # Lead source based on scoring breakdown
        lead_source = "General"
        if lead.medicare_allograft_score and lead.medicare_allograft_score > 0:
            lead_source = "Medicare"
        elif lead.rural_verified_score and lead.rural_verified_score > 0:
            lead_source = "Rural"
        elif lead.overlooked_opportunity_score and lead.overlooked_opportunity_score > 0:
            lead_source = "Overlooked"
        
        return {
            "specialty_category": specialty_category,
            "priority_level": lead.priority or "C",
            "state_region": lead.state or "Unknown",
            "practice_size": practice_size,
            "score_range": score_range,
            "lead_source": lead_source
        }
    
    @staticmethod
    def update_agent_performance(db: Session, agent_id: int, lead: Lead, outcome: str):
        """Update agent performance tracking for lead type"""
        lead_type = LeadTypeAnalyticsService.categorize_lead(lead)
        
        # Find or create performance record for this agent and lead type combination
        performance = db.query(AgentLeadTypePerformance).filter(
            AgentLeadTypePerformance.agent_id == agent_id,
            AgentLeadTypePerformance.specialty_category == lead_type["specialty_category"],
            AgentLeadTypePerformance.priority_level == lead_type["priority_level"],
            AgentLeadTypePerformance.state_region == lead_type["state_region"],
            AgentLeadTypePerformance.practice_size == lead_type["practice_size"],
            AgentLeadTypePerformance.score_range == lead_type["score_range"],
            AgentLeadTypePerformance.lead_source == lead_type["lead_source"]
        ).first()
        
        if not performance:
            performance = AgentLeadTypePerformance(
                agent_id=agent_id,
                **lead_type
            )
            db.add(performance)
        
        # Update metrics based on outcome
        if outcome == "assigned":
            performance.total_assigned += 1
        elif outcome == "contacted":
            performance.total_contacted += 1
        elif outcome == "closed_won":
            performance.total_closed_won += 1
        elif outcome == "closed_lost":
            performance.total_closed_lost += 1
        elif outcome == "recycled":
            performance.total_recycled += 1
        
        # Recalculate rates
        if performance.total_assigned > 0:
            performance.contact_rate = performance.total_contacted / performance.total_assigned
            performance.close_rate = performance.total_closed_won / performance.total_assigned
        
        if performance.total_contacted > 0:
            performance.conversion_rate = performance.total_closed_won / performance.total_contacted
        
        # Calculate average days to close (simplified - would need to track actual dates)
        if performance.total_closed_won > 0:
            performance.avg_days_to_close = 14.0  # Placeholder - would calculate from actual data
        
        db.commit()
        
        # Update aggregate analytics
        LeadTypeAnalyticsService.update_aggregate_analytics(db, lead_type)
    
    @staticmethod
    def update_aggregate_analytics(db: Session, lead_type: Dict[str, str]):
        """Update aggregate analytics for a lead type"""
        analytics = db.query(LeadTypeAnalytics).filter(
            LeadTypeAnalytics.specialty_category == lead_type["specialty_category"],
            LeadTypeAnalytics.priority_level == lead_type["priority_level"],
            LeadTypeAnalytics.state_region == lead_type["state_region"],
            LeadTypeAnalytics.practice_size == lead_type["practice_size"],
            LeadTypeAnalytics.score_range == lead_type["score_range"],
            LeadTypeAnalytics.lead_source == lead_type["lead_source"]
        ).first()
        
        if not analytics:
            analytics = LeadTypeAnalytics(**lead_type)
            db.add(analytics)
        
        # Recalculate from all agent performances for this lead type
        performances = db.query(AgentLeadTypePerformance).filter(
            AgentLeadTypePerformance.specialty_category == lead_type["specialty_category"],
            AgentLeadTypePerformance.priority_level == lead_type["priority_level"],
            AgentLeadTypePerformance.state_region == lead_type["state_region"],
            AgentLeadTypePerformance.practice_size == lead_type["practice_size"],
            AgentLeadTypePerformance.score_range == lead_type["score_range"],
            AgentLeadTypePerformance.lead_source == lead_type["lead_source"]
        ).all()
        
        if performances:
            analytics.total_leads = sum(p.total_assigned for p in performances)
            analytics.total_contacted = sum(p.total_contacted for p in performances)
            analytics.total_closed_won = sum(p.total_closed_won for p in performances)
            analytics.total_closed_lost = sum(p.total_closed_lost for p in performances)
            
            if analytics.total_leads > 0:
                analytics.overall_contact_rate = analytics.total_contacted / analytics.total_leads
                analytics.overall_close_rate = analytics.total_closed_won / analytics.total_leads
            
            if analytics.total_contacted > 0:
                analytics.overall_conversion_rate = analytics.total_closed_won / analytics.total_contacted
            
            # Find best performing agent for this lead type
            best_performance = max(performances, key=lambda p: p.conversion_rate, default=None)
            if best_performance:
                analytics.best_agent_id = best_performance.agent_id
                analytics.best_agent_conversion_rate = best_performance.conversion_rate
        
        analytics.last_calculated = datetime.utcnow()
        db.commit()
    
    @staticmethod
    def get_smart_assignment_recommendation(db: Session, lead: Lead) -> Optional[Dict[str, Any]]:
        """Get smart assignment recommendation for a lead"""
        lead_type = LeadTypeAnalyticsService.categorize_lead(lead)
        
        # Find agents with performance data for this lead type
        performances = db.query(AgentLeadTypePerformance).filter(
            AgentLeadTypePerformance.specialty_category == lead_type["specialty_category"],
            AgentLeadTypePerformance.priority_level == lead_type["priority_level"],
            AgentLeadTypePerformance.total_assigned >= 3  # Minimum assignments for reliable data
        ).join(User).filter(User.is_active == True).all()
        
        if not performances:
            # Fallback to broader specialty matching
            performances = db.query(AgentLeadTypePerformance).filter(
                AgentLeadTypePerformance.specialty_category == lead_type["specialty_category"],
                AgentLeadTypePerformance.total_assigned >= 2
            ).join(User).filter(User.is_active == True).all()
        
        if not performances:
            return None
        
        # Score each agent based on weighted performance metrics
        agent_scores = []
        for perf in performances:
            # Weighted scoring: conversion rate (50%) + contact rate (30%) + close rate (20%)
            score = (
                perf.conversion_rate * 0.5 +
                perf.contact_rate * 0.3 +
                perf.close_rate * 0.2
            )
            
            # Boost score for recent good performance
            if perf.total_assigned >= 5 and perf.conversion_rate > 0.2:
                score += 0.1
            
            agent_scores.append({
                "agent_id": perf.agent_id,
                "agent": perf.agent,
                "score": score,
                "performance": perf,
                "match_type": "specialty"
            })
        
        # Sort by score and return top recommendation
        agent_scores.sort(key=lambda x: x["score"], reverse=True)
        
        if agent_scores:
            best_match = agent_scores[0]
            confidence = min(best_match["score"] * 100, 95)  # Cap at 95%
            
            return {
                "agent_id": best_match["agent_id"],
                "agent_name": best_match["agent"].full_name,
                "confidence_score": confidence,
                "reason": f"Best {lead_type['specialty_category']} performance: {best_match['performance'].conversion_rate:.1%} conversion rate",
                "lead_type_match": lead_type
            }
        
        return None

# ================================
# Gamification Service
# ================================

class GamificationService:
    ACTIVITY_WEIGHTS = {
        ActivityType.CALL: 2,
        ActivityType.EMAIL: 1,
        ActivityType.MEETING: 5,
        ActivityType.DEMO: 8,
        ActivityType.FOLLOW_UP: 2,
        ActivityType.NOTE: 1,
        "lead_qualified": 10,
        "demo_completed": 15,
        "deal_closed": 25,
        "first_contact": 3,
    }
    
    @staticmethod
    def update_performance_metrics(db: Session, user_id: int, activity_type: str, quantity: int = 1):
        """Update user's performance metrics instead of points"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        
        # Update activity score
        activity_score = GamificationService.ACTIVITY_WEIGHTS.get(activity_type, 0) * quantity
        user.activity_score += activity_score
        
        # Update deals closed for closing activities
        if activity_type == "deal_closed":
            user.deals_closed += quantity
        
        # Calculate conversion rate
        total_assigned = db.query(Lead).filter(Lead.assigned_user_id == user_id).count()
        closed_won = db.query(Lead).filter(
            Lead.assigned_user_id == user_id, 
            Lead.status == LeadStatus.CLOSED_WON
        ).count()
        
        user.conversion_rate = (closed_won / total_assigned * 100) if total_assigned > 0 else 0.0
        
        db.commit()
        
        # Recalculate percentiles and ranks for all users
        GamificationService.recalculate_rankings(db)
        
        return activity_score
    
    @staticmethod
    def recalculate_rankings(db: Session):
        """Recalculate percentiles and ranks for all active users"""
        users = db.query(User).filter(User.is_active == True).all()
        
        if len(users) <= 1:
            for user in users:
                user.current_percentile = 100.0
                user.current_rank = 1
            db.commit()
            return
        
        # Calculate composite performance score
        for user in users:
            # Weighted score: 40% conversion rate + 30% deals closed + 30% activity score
            user.performance_score = (
                user.conversion_rate * 0.4 +
                user.deals_closed * 3.0 +  # Scale deals closed
                user.activity_score * 0.3
            )
        
        # Sort by performance score
        users.sort(key=lambda u: u.performance_score, reverse=True)
        
        # Assign ranks and percentiles
        total_users = len(users)
        for rank, user in enumerate(users, 1):
            user.current_rank = rank
            # Percentile: percentage of users this user performs better than
            user.current_percentile = ((total_users - rank) / (total_users - 1) * 100) if total_users > 1 else 100.0
            
            # Award achievement badges based on percentile
            if user.badges is None:
                user.badges = []
            
            # Award percentile badges
            if user.current_percentile >= 95 and "Top 5%" not in user.badges:
                user.badges.append("Top 5%")
            elif user.current_percentile >= 90 and "Top 10%" not in user.badges:
                user.badges.append("Top 10%")
            elif user.current_percentile >= 75 and "Top 25%" not in user.badges:
                user.badges.append("Top 25%")
        
        db.commit()
    
    @staticmethod
    def get_leaderboard(db: Session, limit: int = 10) -> List[LeaderboardEntry]:
        # Ensure rankings are up to date
        GamificationService.recalculate_rankings(db)
        
        users = db.query(User).filter(User.is_active == True).order_by(User.current_rank.asc()).limit(limit).all()
        
        leaderboard = []
        for user in users:
            leaderboard.append(LeaderboardEntry(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                conversion_rate=user.conversion_rate,
                activity_score=user.activity_score,
                deals_closed=user.deals_closed,
                current_percentile=user.current_percentile,
                rank=user.current_rank
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
# Lifespan Context Manager
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
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
        
        # Initialize lead distribution system
        try:
            from crm_lead_distribution import initialize_lead_distribution
            initialize_lead_distribution(db)
            logger.info("🎯 Lead distribution system initialized")
        except Exception as e:
            logger.warning(f"⚠️ Lead distribution initialization failed: {e}")
        
        db.close()
    except Exception as e:
        logger.warning(f"⚠️ Startup initialization failed: {e}")
    
    # Initialize monitoring system
    try:
        initialize_monitoring(settings.database_url, redis_client)
        logger.info("🔍 Monitoring system initialized")
    except Exception as e:
        logger.warning(f"⚠️ Monitoring initialization failed: {e}")
    
    # Start background tasks
    asyncio.create_task(background_task_runner())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Cura Genesis CRM")

# ================================
# FastAPI Application
# ================================

app = FastAPI(
    title=settings.app_name,
    description="Advanced CRM system with lead scoring, gamification, and analytics",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None  # Disable redoc in production
)

# ================================
# Security Middleware
# ================================

from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Security headers middleware
class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message["headers"])
                
                # Security headers
                headers[b"x-content-type-options"] = b"nosniff"
                headers[b"x-frame-options"] = b"DENY"
                headers[b"x-xss-protection"] = b"1; mode=block"
                headers[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                headers[b"content-security-policy"] = b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
                headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                headers[b"permissions-policy"] = b"camera=(), microphone=(), geolocation=()"
                
                message["headers"] = list(headers.items())
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add trusted host middleware for production
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app", "*.herokuapp.com", "*"] if settings.debug else ["localhost", "127.0.0.1"]
)

# Add session middleware for CSRF protection
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.secret_key,
    max_age=86400,  # 24 hours
    same_site="strict",
    https_only=False  # Set to True in production with HTTPS
)

# ================================
# Rate Limiting Middleware
# ================================

from collections import defaultdict, deque

class RateLimitMiddleware:
    def __init__(self, app, calls: int = 100, period: int = 60):
        self.app = app
        self.calls = calls
        self.period = period
        self.clients = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get client IP
        client_ip = None
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"x-forwarded-for":
                client_ip = header_value.decode().split(",")[0].strip()
                break
            elif header_name == b"x-real-ip":
                client_ip = header_value.decode()
                break
        
        if not client_ip:
            client_ip = scope.get("client", ["unknown"])[0]

        # Check rate limit
        now = time.time()
        client_requests = self.clients[client_ip]
        
        # Remove old requests
        while client_requests and client_requests[0] < now - self.period:
            client_requests.popleft()
        
        # Check if rate limit exceeded
        if len(client_requests) >= self.calls:
            # Rate limited
            response = {
                "type": "http.response.start",
                "status": 429,
                "headers": [[b"content-type", b"application/json"]],
            }
            await send(response)
            
            body = '{"error": "Rate limit exceeded", "retry_after": 60}'
            await send({
                "type": "http.response.body",
                "body": body.encode(),
            })
            return
        
        # Add current request
        client_requests.append(now)
        
        await self.app(scope, receive, send)

# ================================
# Error Handling & Logging Middleware
# ================================

import traceback

class ErrorHandlingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Add request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message["headers"])
                headers[b"x-request-id"] = request_id.encode()
                message["headers"] = list(headers.items())
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            logger.error(f"Unhandled error in request {request_id}: {e}", exc_info=True)
            
            # Send error response
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"x-request-id", request_id.encode()]
                ],
            })
            
            error_response = {
                "error": "Internal server error",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await send({
                "type": "http.response.body",
                "body": json.dumps(error_response).encode(),
            })

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                method = scope["method"]
                path = scope["path"]
                client_ip = scope.get("client", ["unknown"])[0]
                
                duration = time.time() - start_time
                
                # Log request details
                logger.info(
                    f"{method} {path} - {status_code} - {duration:.3f}s - {client_ip}",
                    extra={
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "duration": duration,
                        "client_ip": client_ip
                    }
                )
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

# Add monitoring middleware (should be first to track all requests)
try:
    app.add_middleware(MonitoringMiddleware)
    logger.info("📊 Monitoring middleware enabled")
except Exception as e:
    logger.warning(f"⚠️ Monitoring middleware failed: {e}")

# Add error handling and logging middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)

# Add rate limiting (100 requests per minute per IP)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# CORS middleware with production-ready settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8001", "https://localhost:8001"] if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-CSRF-Token"],
    expose_headers=["X-Total-Count"]
)

# Static file serving for CRM dashboard
@app.get("/crm_enhanced_dashboard_v2.html")
async def serve_main_dashboard():
    """Serve the main CRM dashboard"""
    return FileResponse("crm_enhanced_dashboard_v2.html", media_type="text/html")

@app.get("/manifest.json")
async def serve_manifest():
    """Serve the web app manifest"""
    return FileResponse("manifest.json", media_type="application/json")

@app.get("/crm_enhanced_dashboard.html") 
async def serve_alt_dashboard():
    """Serve the alternative CRM dashboard"""
    return FileResponse("crm_enhanced_dashboard.html", media_type="text/html")

@app.get("/crm_dashboard.html")
async def serve_basic_dashboard():
    """Serve the basic CRM dashboard"""
    return FileResponse("crm_dashboard.html", media_type="text/html")

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
        user=UserResponse.model_validate(user)
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
    show_all: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get leads with smart distribution-aware filtering"""
    query = db.query(Lead)
    
    # For agents, show only their ACTIVE assigned leads (not closed ones)
    if current_user.role == UserRole.AGENT:
        query = query.filter(
            Lead.assigned_user_id == current_user.id,
            Lead.status.notin_([LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST, LeadStatus.RECYCLED])
        )
    elif current_user.role in [UserRole.ADMIN, UserRole.MANAGER]:
        # Admins and managers can see all leads if show_all=True
        if not show_all:
            # By default, show active leads
            query = query.filter(
                Lead.status.notin_([LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST, LeadStatus.RECYCLED])
            )
    
    # Filter by status if provided
    if status:
        query = query.filter(Lead.status == status)
    
    # Order by priority and score for agents
    if current_user.role == UserRole.AGENT:
        query = query.order_by(Lead.score.desc(), Lead.assigned_at.desc())
    else:
        query = query.order_by(Lead.created_at.desc())
    
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

@app.post("/api/v1/leads", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new lead via API"""
    # Check if lead with this NPI already exists
    if lead_data.npi:
        existing_lead = db.query(Lead).filter(Lead.npi == lead_data.npi).first()
        if existing_lead:
            raise HTTPException(
                status_code=400, 
                detail=f"Lead with NPI {lead_data.npi} already exists (ID: {existing_lead.id})"
            )
    
    # Ensure required fields are present
    if not lead_data.practice_name:
        raise HTTPException(status_code=400, detail="Practice name is required")
    
    # Calculate basic scoring if not provided
    if lead_data.score is None:
        # Simple scoring algorithm based on available data
        base_score = 50  # Base score
        if lead_data.specialties and "cardio" in lead_data.specialties.lower():
            base_score += 20
        if lead_data.specialties and "nephro" in lead_data.specialties.lower():
            base_score += 25
        if lead_data.providers and lead_data.providers > 1:
            base_score += 10
        lead_data.score = min(base_score, 100)
    
    # Set priority based on score
    if lead_data.priority is None:
        if lead_data.score >= 90:
            lead_data.priority = "A+"
        elif lead_data.score >= 80:
            lead_data.priority = "A"
        elif lead_data.score >= 70:
            lead_data.priority = "B+"
        elif lead_data.score >= 60:
            lead_data.priority = "B"
        else:
            lead_data.priority = "C"
    
    # Create new lead
    new_lead = Lead(
        npi=lead_data.npi,
        ein=lead_data.ein,
        practice_name=lead_data.practice_name,
        owner_name=lead_data.owner_name,
        practice_phone=lead_data.practice_phone,
        owner_phone=lead_data.owner_phone,
        specialties=lead_data.specialties,
        category=lead_data.category,
        providers=lead_data.providers,
        city=lead_data.city,
        state=lead_data.state,
        zip_code=lead_data.zip_code,
        address=lead_data.address,
        entity_type=lead_data.entity_type,
        is_sole_proprietor=lead_data.is_sole_proprietor,
        score=lead_data.score,
        priority=lead_data.priority,
        medicare_allograft_score=lead_data.medicare_allograft_score,
        overlooked_opportunity_score=lead_data.overlooked_opportunity_score,
        rural_verified_score=lead_data.rural_verified_score,
        scoring_breakdown=lead_data.scoring_breakdown,
        status=LeadStatus.NEW,
        source=lead_data.source
    )
    
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    
    # Log the creation
    logger.info(f"📋 New lead created via API: {new_lead.practice_name} (Score: {new_lead.score}, Priority: {new_lead.priority})")
    
    # Auto-assign to lead distribution if enabled
    try:
        from crm_lead_distribution import LeadDistributionService
        distribution_service = LeadDistributionService(db)
        available_leads = distribution_service.get_available_leads(1)
        if new_lead in available_leads:
            distribution_service.redistribute_all_leads()
            logger.info(f"📊 New lead {new_lead.id} added to distribution pool")
    except Exception as e:
        logger.warning(f"⚠️ Auto-distribution failed for new lead: {e}")
    
    return new_lead

@app.put("/api/v1/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update lead information - agents can edit their assigned leads, admins/managers can edit any lead"""
    
    # Get the lead
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check permissions - agents can only edit their assigned leads
    if current_user.role == UserRole.AGENT and lead.assigned_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only update your assigned leads")
    
    # Get the update data as dict, excluding unset values
    update_data = lead_update.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    
    # Log the update for audit trail
    updated_fields = list(update_data.keys())
    logger.info(f"📝 Lead {lead_id} update by {current_user.username}: fields {updated_fields}")
    
    # Update the lead fields
    for field, value in update_data.items():
        if hasattr(lead, field):
            # Clean phone numbers if they're being updated
            if field in ['practice_phone', 'owner_phone'] and value:
                # Basic phone cleaning - remove non-digits and format
                import re
                digits = re.sub(r'\D', '', str(value))
                if len(digits) == 10:
                    value = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
                elif len(digits) == 11 and digits[0] == '1':
                    value = f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
                else:
                    value = digits if digits else None
            
            setattr(lead, field, value)
    
    # Update the updated_at timestamp
    lead.updated_at = datetime.utcnow()
    
    # Commit the changes
    try:
        db.commit()
        db.refresh(lead)
        logger.info(f"✅ Lead {lead_id} updated successfully by {current_user.username}")
        return lead
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to update lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update lead")

@app.post("/api/v1/leads/bulk", response_model=Dict[str, Any])
async def bulk_create_leads(
    leads_data: List[LeadCreate],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk import leads via API (Admin/Manager only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Admin or Manager access required")
    
    if len(leads_data) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 leads per bulk import")
    
    created_leads = []
    failed_leads = []
    duplicate_npis = []
    
    for i, lead_data in enumerate(leads_data):
        try:
            # Check for duplicates
            if lead_data.npi:
                existing_lead = db.query(Lead).filter(Lead.npi == lead_data.npi).first()
                if existing_lead:
                    duplicate_npis.append({
                        "index": i,
                        "npi": lead_data.npi,
                        "practice_name": lead_data.practice_name,
                        "existing_id": existing_lead.id
                    })
                    continue
            
            # Validate required fields
            if not lead_data.practice_name:
                failed_leads.append({
                    "index": i,
                    "error": "Practice name is required",
                    "data": lead_data.practice_name
                })
                continue
            
            # Calculate scoring if not provided
            if lead_data.score is None:
                base_score = 50
                if lead_data.specialties and "cardio" in lead_data.specialties.lower():
                    base_score += 20
                if lead_data.specialties and "nephro" in lead_data.specialties.lower():
                    base_score += 25
                if lead_data.providers and lead_data.providers > 1:
                    base_score += 10
                lead_data.score = min(base_score, 100)
            
            # Set priority based on score
            if lead_data.priority is None:
                if lead_data.score >= 90:
                    lead_data.priority = "A+"
                elif lead_data.score >= 80:
                    lead_data.priority = "A"
                elif lead_data.score >= 70:
                    lead_data.priority = "B+"
                elif lead_data.score >= 60:
                    lead_data.priority = "B"
                else:
                    lead_data.priority = "C"
            
            # Create lead
            new_lead = Lead(
                npi=lead_data.npi,
                ein=lead_data.ein,
                practice_name=lead_data.practice_name,
                owner_name=lead_data.owner_name,
                practice_phone=lead_data.practice_phone,
                owner_phone=lead_data.owner_phone,
                specialties=lead_data.specialties,
                category=lead_data.category,
                providers=lead_data.providers,
                city=lead_data.city,
                state=lead_data.state,
                zip_code=lead_data.zip_code,
                address=lead_data.address,
                entity_type=lead_data.entity_type,
                is_sole_proprietor=lead_data.is_sole_proprietor,
                score=lead_data.score,
                priority=lead_data.priority,
                medicare_allograft_score=lead_data.medicare_allograft_score,
                overlooked_opportunity_score=lead_data.overlooked_opportunity_score,
                rural_verified_score=lead_data.rural_verified_score,
                scoring_breakdown=lead_data.scoring_breakdown,
                status=LeadStatus.NEW,
                source=lead_data.source
            )
            
            db.add(new_lead)
            created_leads.append({
                "index": i,
                "practice_name": lead_data.practice_name,
                "score": lead_data.score,
                "priority": lead_data.priority
            })
            
        except Exception as e:
            failed_leads.append({
                "index": i,
                "error": str(e),
                "practice_name": getattr(lead_data, 'practice_name', 'Unknown')
            })
    
    # Commit all successful leads
    try:
        db.commit()
        logger.info(f"📊 Bulk import: {len(created_leads)} leads created, {len(failed_leads)} failed, {len(duplicate_npis)} duplicates")
        
        # Trigger redistribution if new leads were added
        if created_leads:
            try:
                distribution_service = LeadDistributionService(db)
                distribution_service.redistribute_all_leads()
                logger.info(f"📋 Redistributed leads after bulk import")
            except Exception as e:
                logger.warning(f"⚠️ Auto-redistribution failed after bulk import: {e}")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk import failed: {str(e)}")
    
    return {
        "summary": {
            "total_submitted": len(leads_data),
            "created": len(created_leads),
            "failed": len(failed_leads),
            "duplicates": len(duplicate_npis)
        },
        "created_leads": created_leads,
        "failed_leads": failed_leads,
        "duplicate_npis": duplicate_npis
    }

# ================================
# API Routes - Lead Distribution System
# ================================

@app.get("/api/v1/distribution/stats")
async def get_distribution_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get lead distribution system statistics"""
    distribution_service = LeadDistributionService(db)
    
    if current_user.role == UserRole.AGENT:
        # Agents get their personal stats
        agent_stats = distribution_service.get_agent_dashboard_stats(current_user.id)
        return {
            "type": "agent_stats",
            "stats": agent_stats
        }
    else:
        # Managers and admins get system stats
        system_stats = distribution_service.get_system_lead_stats()
        return {
            "type": "system_stats",
            "stats": system_stats
        }

@app.post("/api/v1/distribution/redistribute")
async def force_redistribution(
    agent_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Force lead redistribution (admin/manager only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    distribution_service = LeadDistributionService(db)
    
    if agent_id:
        # Redistribute for specific agent
        result = distribution_service.force_redistribute_agent(agent_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        # Notify the agent
        await manager.send_personal_message(
            json.dumps({
                "type": "leads_redistributed",
                "message": f"📋 {result['leads_distributed']} new leads assigned to you!",
                "stats": result["stats"]
            }),
            agent_id
        )
        
        return result
    else:
        # Redistribute for all agents
        result = distribution_service.redistribute_all_leads()
        
        # Notify all agents who got new leads
        for agent_name, stats in result.get("agent_stats", {}).items():
            if stats["distributed"] > 0:
                agent = db.query(User).filter(User.username == agent_name).first()
                if agent:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "leads_redistributed",
                            "message": f"📋 {stats['distributed']} new leads assigned to you!",
                            "total_leads": stats["total_leads"]
                        }),
                        agent.id
                    )
        
        return result

@app.post("/api/v1/distribution/recycle-check")
async def trigger_recycle_check(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Manually trigger 24-hour inactivity check (admin/manager only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    recycled_count = run_lead_recycling_check(db)
    
    return {
        "message": f"Recycling check complete",
        "leads_recycled": recycled_count,
        "redistributed": recycled_count > 0
    }

@app.get("/api/v1/distribution/agent-performance")
async def get_agent_performance(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get agent performance metrics"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        # Agents can only see their own stats
        distribution_service = LeadDistributionService(db)
        return distribution_service.get_agent_dashboard_stats(current_user.id)
    
    # Managers and admins see all agent performance
    agents = db.query(User).filter(User.role == UserRole.AGENT, User.is_active == True).all()
    distribution_service = LeadDistributionService(db)
    
    performance_data = []
    for agent in agents:
        stats = distribution_service.get_agent_dashboard_stats(agent.id)
        stats.update({
            "agent_id": agent.id,
            "agent_name": agent.full_name,
            "username": agent.username,
            "conversion_rate": agent.conversion_rate,
            "current_percentile": agent.current_percentile,
            "current_rank": agent.current_rank,
            "activity_score": agent.activity_score,
            "deals_closed": agent.deals_closed
        })
        performance_data.append(stats)
    
    # Sort by sales made today, then by conversion rate, then by rank (lower is better)
    performance_data.sort(key=lambda x: (x["sales_today"], x["conversion_rate"], -x["current_rank"]), reverse=True)
    
    return {
        "agents": performance_data,
        "summary": {
            "total_agents": len(performance_data),
            "total_active_leads": sum(agent["active_leads"] for agent in performance_data),
            "total_sales_today": sum(agent["sales_today"] for agent in performance_data),
            "total_activities_today": sum(agent["activities_today"] for agent in performance_data)
        }
    }

@app.patch("/api/v1/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: int,
    status: LeadStatus,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update lead status with automatic redistribution"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check permissions
    if current_user.role == UserRole.AGENT and lead.assigned_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only update your assigned leads")
    
    old_status = lead.status
    
    # Use the distribution service to handle the status change
    distribution_service = LeadDistributionService(db)
    success = distribution_service.handle_lead_disposition(lead_id, status, current_user.id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update lead status")
    
    # Update performance metrics for status changes
    if status == LeadStatus.QUALIFIED and old_status != LeadStatus.QUALIFIED:
        GamificationService.update_performance_metrics(db, current_user.id, "lead_qualified")
    elif status == LeadStatus.CLOSED_WON:
        GamificationService.update_performance_metrics(db, current_user.id, "deal_closed")
        # Track lead type performance
        LeadTypeAnalyticsService.update_agent_performance(db, current_user.id, lead, "closed_won")
        await manager.send_personal_message(
            json.dumps({
                "type": "sale_made",
                "message": f"🎉 Sale made! New leads assigned automatically.",
                "lead_id": lead_id
            }),
            current_user.id
        )
    elif status == LeadStatus.CLOSED_LOST:
        # Track lead type performance
        LeadTypeAnalyticsService.update_agent_performance(db, current_user.id, lead, "closed_lost")
        await manager.send_personal_message(
            json.dumps({
                "type": "lead_closed",
                "message": f"📋 Lead closed. New leads assigned automatically.",
                "lead_id": lead_id
            }),
            current_user.id
        )
    
    logger.info(f"📊 Lead {lead_id} status updated: {old_status} → {status}")
    
    # Get updated agent stats for response
    if current_user.role == UserRole.AGENT:
        agent_stats = distribution_service.get_agent_dashboard_stats(current_user.id)
        return {
            "message": "Lead status updated successfully",
            "agent_stats": agent_stats,
            "auto_assigned": status in [LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST]
        }
    
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
    
    # Update lead contact tracking for distribution system
    lead.last_contact_date = datetime.utcnow()
    lead.contact_attempts += 1
    
    # Reset recycling timer since there was activity
    lead.recycling_eligible_at = None
    
    # Update performance metrics
    GamificationService.update_performance_metrics(db, current_user.id, activity.activity_type)
    
    # Track lead type performance for first contact
    if lead.contact_attempts == 1:
        GamificationService.update_performance_metrics(db, current_user.id, "first_contact")
        LeadTypeAnalyticsService.update_agent_performance(db, current_user.id, lead, "contacted")
    
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
    """Get current user's performance stats"""
    # Ensure rankings are up to date
    GamificationService.recalculate_rankings(db)
    
    # Get recent activities count
    recent_activities = db.query(Activity).filter(
        Activity.user_id == current_user.id,
        Activity.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    return {
        "conversion_rate": current_user.conversion_rate,
        "activity_score": current_user.activity_score,
        "deals_closed": current_user.deals_closed,
        "current_percentile": current_user.current_percentile,
        "current_rank": current_user.current_rank,
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

@app.get("/api/v1/analytics/lead-types", response_model=List[LeadTypeAnalyticsResponse])
async def get_lead_type_analytics(
    specialty: Optional[str] = None,
    priority: Optional[str] = None,
    state: Optional[str] = None,
    min_leads: int = 5,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analytics breakdown by lead type"""
    query = db.query(LeadTypeAnalytics).filter(LeadTypeAnalytics.total_leads >= min_leads)
    
    if specialty:
        query = query.filter(LeadTypeAnalytics.specialty_category == specialty)
    if priority:
        query = query.filter(LeadTypeAnalytics.priority_level == priority)
    if state:
        query = query.filter(LeadTypeAnalytics.state_region == state)
    
    analytics = query.order_by(LeadTypeAnalytics.overall_conversion_rate.desc()).all()
    
    result = []
    for analytic in analytics:
        # Get top agents for this lead type
        top_agents = db.query(AgentLeadTypePerformance).filter(
            AgentLeadTypePerformance.specialty_category == analytic.specialty_category,
            AgentLeadTypePerformance.priority_level == analytic.priority_level,
            AgentLeadTypePerformance.state_region == analytic.state_region,
            AgentLeadTypePerformance.practice_size == analytic.practice_size,
            AgentLeadTypePerformance.score_range == analytic.score_range,
            AgentLeadTypePerformance.lead_source == analytic.lead_source,
            AgentLeadTypePerformance.total_assigned >= 3
        ).join(User).order_by(AgentLeadTypePerformance.conversion_rate.desc()).limit(3).all()
        
        top_agent_responses = []
        for perf in top_agents:
            top_agent_responses.append(LeadTypePerformanceResponse(
                agent_id=perf.agent_id,
                agent_name=perf.agent.full_name,
                specialty_category=perf.specialty_category,
                priority_level=perf.priority_level,
                state_region=perf.state_region,
                practice_size=perf.practice_size,
                score_range=perf.score_range,
                lead_source=perf.lead_source,
                total_assigned=perf.total_assigned,
                total_contacted=perf.total_contacted,
                total_closed_won=perf.total_closed_won,
                contact_rate=perf.contact_rate,
                conversion_rate=perf.conversion_rate,
                close_rate=perf.close_rate,
                avg_days_to_close=perf.avg_days_to_close
            ))
        
        result.append(LeadTypeAnalyticsResponse(
            specialty_category=analytic.specialty_category,
            priority_level=analytic.priority_level,
            state_region=analytic.state_region,
            practice_size=analytic.practice_size,
            score_range=analytic.score_range,
            lead_source=analytic.lead_source,
            total_leads=analytic.total_leads,
            total_contacted=analytic.total_contacted,
            total_closed_won=analytic.total_closed_won,
            overall_contact_rate=analytic.overall_contact_rate,
            overall_conversion_rate=analytic.overall_conversion_rate,
            overall_close_rate=analytic.overall_close_rate,
            best_agent_name=analytic.best_agent.full_name if analytic.best_agent else None,
            best_agent_conversion_rate=analytic.best_agent_conversion_rate,
            top_agents=top_agent_responses
        ))
    
    return result

@app.get("/api/v1/analytics/agent-performance/{agent_id}", response_model=List[LeadTypePerformanceResponse])
async def get_agent_lead_type_performance(
    agent_id: int,
    min_assigned: int = 2,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get agent's performance breakdown by lead type"""
    # Check permissions
    if current_user.role == UserRole.AGENT and current_user.id != agent_id:
        raise HTTPException(status_code=403, detail="Can only view your own detailed performance")
    
    performances = db.query(AgentLeadTypePerformance).filter(
        AgentLeadTypePerformance.agent_id == agent_id,
        AgentLeadTypePerformance.total_assigned >= min_assigned
    ).join(User).order_by(AgentLeadTypePerformance.conversion_rate.desc()).all()
    
    result = []
    for perf in performances:
        result.append(LeadTypePerformanceResponse(
            agent_id=perf.agent_id,
            agent_name=perf.agent.full_name,
            specialty_category=perf.specialty_category,
            priority_level=perf.priority_level,
            state_region=perf.state_region,
            practice_size=perf.practice_size,
            score_range=perf.score_range,
            lead_source=perf.lead_source,
            total_assigned=perf.total_assigned,
            total_contacted=perf.total_contacted,
            total_closed_won=perf.total_closed_won,
            contact_rate=perf.contact_rate,
            conversion_rate=perf.conversion_rate,
            close_rate=perf.close_rate,
            avg_days_to_close=perf.avg_days_to_close
        ))
    
    return result

@app.get("/api/v1/analytics/smart-assignment/{lead_id}", response_model=SmartAssignmentResponse)
async def get_smart_assignment_recommendation(
    lead_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get smart assignment recommendation for a lead"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Admin or Manager access required")
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead.assigned_user_id:
        raise HTTPException(status_code=400, detail="Lead is already assigned")
    
    recommendation = LeadTypeAnalyticsService.get_smart_assignment_recommendation(db, lead)
    
    if not recommendation:
        raise HTTPException(status_code=404, detail="No performance data available for smart assignment")
    
    return SmartAssignmentResponse(
        lead_id=lead_id,
        recommended_agent_id=recommendation["agent_id"],
        recommended_agent_name=recommendation["agent_name"],
        confidence_score=recommendation["confidence_score"],
        reason=recommendation["reason"],
        lead_type_match=recommendation["lead_type_match"]
    )

@app.post("/api/v1/analytics/recalculate-lead-types")
async def recalculate_lead_type_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Recalculate all lead type analytics (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Clear existing analytics
    db.query(AgentLeadTypePerformance).delete()
    db.query(LeadTypeAnalytics).delete()
    
    # Recalculate from all leads
    leads = db.query(Lead).all()
    
    processed_count = 0
    for lead in leads:
        if lead.assigned_user_id:
            # Track assignment
            LeadTypeAnalyticsService.update_agent_performance(db, lead.assigned_user_id, lead, "assigned")
            
            # Track contact if there were contact attempts
            if lead.contact_attempts > 0:
                LeadTypeAnalyticsService.update_agent_performance(db, lead.assigned_user_id, lead, "contacted")
            
            # Track outcome
            if lead.status == LeadStatus.CLOSED_WON:
                LeadTypeAnalyticsService.update_agent_performance(db, lead.assigned_user_id, lead, "closed_won")
            elif lead.status == LeadStatus.CLOSED_LOST:
                LeadTypeAnalyticsService.update_agent_performance(db, lead.assigned_user_id, lead, "closed_lost")
            elif lead.status == LeadStatus.RECYCLED:
                LeadTypeAnalyticsService.update_agent_performance(db, lead.assigned_user_id, lead, "recycled")
            
            processed_count += 1
    
    logger.info(f"📊 Recalculated lead type analytics for {processed_count} assigned leads")
    
    return {
        "message": "Lead type analytics recalculated successfully",
        "processed_leads": processed_count,
        "total_leads": len(leads)
    }

# ================================
# Team Management Endpoints
# ================================

@app.post("/api/v1/team/create-user", response_model=UserResponse)
async def create_team_member(
    user_data: CreateUserRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new team member (Manager can create agents, Admin can create anyone)"""
    
    # Permission checks
    if current_user.role == UserRole.AGENT:
        raise HTTPException(status_code=403, detail="Agents cannot create users")
    elif current_user.role == UserRole.MANAGER:
        # Managers can only create agents under themselves
        if user_data.role != UserRole.AGENT:
            raise HTTPException(status_code=403, detail="Managers can only create agents")
        user_data.manager_id = current_user.id
    elif current_user.role == UserRole.ADMIN:
        # Admins can create anyone, but if creating an agent and manager_id not set, ask for it
        if user_data.role == UserRole.AGENT and user_data.manager_id is None:
            raise HTTPException(status_code=400, detail="Please specify a manager for this agent")
    
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Validate manager exists if specified
    if user_data.manager_id:
        manager = db.query(User).filter(User.id == user_data.manager_id).first()
        if not manager:
            raise HTTPException(status_code=400, detail="Specified manager does not exist")
        if manager.role != UserRole.MANAGER:
            raise HTTPException(status_code=400, detail="Specified user is not a manager")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        manager_id=user_data.manager_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"👥 User created: {new_user.username} ({new_user.role}) by {current_user.username}")
    
    return new_user

@app.get("/api/v1/team/my-team", response_model=TeamOverviewResponse)
async def get_my_team(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get team overview for current manager"""
    
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only managers can view team overview")
    
    # Get team members
    team_members = db.query(User).filter(
        User.manager_id == current_user.id,
        User.is_active == True
    ).all()
    
    # Calculate team stats
    if team_members:
        total_deals = sum(member.deals_closed for member in team_members)
        avg_percentile = sum(member.current_percentile for member in team_members) / len(team_members)
        avg_conversion = sum(member.conversion_rate for member in team_members) / len(team_members)
        top_performer = max(team_members, key=lambda x: x.current_percentile, default=None)
    else:
        total_deals = 0
        avg_percentile = 0
        avg_conversion = 0
        top_performer = None
    
    team_stats = {
        "team_size": len(team_members),
        "total_deals_closed": total_deals,
        "average_percentile": round(avg_percentile, 1),
        "average_conversion_rate": round(avg_conversion, 2),
        "active_agents": len([m for m in team_members if m.is_active])
    }
    
    return TeamOverviewResponse(
        manager=current_user,
        team_members=team_members,
        team_stats=team_stats
    )

@app.get("/api/v1/team/all-managers", response_model=List[ManagerStatsResponse])
async def get_all_managers(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all managers with their team statistics (Admin only)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all managers
    managers = db.query(User).filter(
        User.role == UserRole.MANAGER,
        User.is_active == True
    ).all()
    
    manager_stats = []
    for manager in managers:
        # Get team members
        team_members = db.query(User).filter(
            User.manager_id == manager.id,
            User.is_active == True
        ).all()
        
        if team_members:
            team_conversion_rate = sum(member.conversion_rate for member in team_members) / len(team_members)
            team_deals_closed = sum(member.deals_closed for member in team_members)
            avg_team_percentile = sum(member.current_percentile for member in team_members) / len(team_members)
            top_performer = max(team_members, key=lambda x: x.current_percentile, default=None)
        else:
            team_conversion_rate = 0
            team_deals_closed = 0
            avg_team_percentile = 0
            top_performer = None
        
        manager_stats.append(ManagerStatsResponse(
            manager_id=manager.id,
            manager_name=manager.full_name or manager.username,
            team_size=len(team_members),
            team_conversion_rate=round(team_conversion_rate, 2),
            team_deals_closed=team_deals_closed,
            avg_team_percentile=round(avg_team_percentile, 1),
            top_performer=top_performer
        ))
    
    return manager_stats

@app.get("/api/v1/team/unassigned-agents", response_model=List[TeamMemberResponse])
async def get_unassigned_agents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all agents without a manager (Admin only)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    unassigned_agents = db.query(User).filter(
        User.role == UserRole.AGENT,
        User.manager_id.is_(None),
        User.is_active == True
    ).all()
    
    return unassigned_agents

@app.put("/api/v1/team/assign-agent/{agent_id}")
async def assign_agent_to_manager(
    agent_id: int,
    manager_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign an agent to a manager (Admin only)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get agent
    agent = db.query(User).filter(User.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.role != UserRole.AGENT:
        raise HTTPException(status_code=400, detail="User is not an agent")
    
    # Get manager
    manager = db.query(User).filter(User.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    if manager.role != UserRole.MANAGER:
        raise HTTPException(status_code=400, detail="User is not a manager")
    
    # Assign agent to manager
    agent.manager_id = manager_id
    db.commit()
    
    logger.info(f"👥 Agent {agent.username} assigned to manager {manager.username} by {current_user.username}")
    
    return {"message": f"Agent {agent.username} assigned to manager {manager.username}"}

@app.delete("/api/v1/team/remove-agent/{agent_id}")
async def remove_agent_from_team(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove an agent from a team (Manager can remove from their team, Admin can remove anyone)"""
    
    # Get agent
    agent = db.query(User).filter(User.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.role != UserRole.AGENT:
        raise HTTPException(status_code=400, detail="User is not an agent")
    
    # Permission check
    if current_user.role == UserRole.MANAGER:
        if agent.manager_id != current_user.id:
            raise HTTPException(status_code=403, detail="Can only remove agents from your own team")
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Remove from team
    old_manager_id = agent.manager_id
    agent.manager_id = None
    db.commit()
    
    logger.info(f"👥 Agent {agent.username} removed from team by {current_user.username}")
    
    return {"message": f"Agent {agent.username} removed from team"}

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
    """Comprehensive health check for production monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
    
    try:
        # Test database connection and get counts
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        
        lead_count = db.query(Lead).count()
        user_count = db.query(User).count()
        active_agents = db.query(User).filter(User.role == UserRole.AGENT, User.is_active == True).count()
        
        health_status["database"] = "connected"
        health_status["database_stats"] = {
            "total_leads": lead_count,
            "total_users": user_count,
            "active_agents": active_agents
        }
        
        db.close()
    except Exception as e:
        health_status["database"] = "error"
        health_status["database_error"] = str(e)
        health_status["status"] = "unhealthy"
    
    # Test Redis connection
    try:
        if redis_client:
            redis_client.ping()
            health_status["redis"] = "connected"
        else:
            health_status["redis"] = "disabled"
    except Exception as e:
        health_status["redis"] = "error"
        health_status["redis_error"] = str(e)
    
    # Check lead scoring systems
    health_status["lead_scoring"] = "active" if medicare_extractor else "disabled"
    
    # Check lead distribution system
    try:
        db = SessionLocal()
        distribution_service = LeadDistributionService(db)
        system_stats = distribution_service.get_system_lead_stats()
        health_status["lead_distribution"] = "active"
        health_status["distribution_stats"] = system_stats
        db.close()
    except Exception as e:
        health_status["lead_distribution"] = "error"
        health_status["distribution_error"] = str(e)
    
    # Feature flags
    health_status["features"] = {
        "lead_creation_api": True,
        "bulk_import": True,
        "role_based_access": True,
        "gamification": True,
        "auto_recycling": True,
        "real_time_updates": True
    }
    
    return health_status

# ================================
# Monitoring & Observability Endpoints  
# ================================

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    if not PROMETHEUS_AVAILABLE or not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collection not available")
    
    from fastapi.responses import Response
    metrics_data = metrics_collector.get_metrics()
    return Response(content=metrics_data, media_type="text/plain")

@app.get("/api/v1/monitoring/health")
async def comprehensive_health_check():
    """Comprehensive health check with detailed system status"""
    if not monitoring_dashboard:
        raise HTTPException(status_code=503, detail="Monitoring not initialized")
    
    try:
        health_data = await monitoring_dashboard.health_checker.comprehensive_health_check()
        return health_data
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/v1/monitoring/performance")
async def get_performance_metrics(hours: int = 1):
    """Get application performance metrics"""
    if not apm_monitor:
        raise HTTPException(status_code=503, detail="APM not initialized")
    
    try:
        performance_data = apm_monitor.get_performance_summary(hours=hours)
        return performance_data
    except Exception as e:
        logger.error(f"Performance metrics failed: {e}")
        return {"error": str(e)}

@app.get("/api/v1/monitoring/database")
async def get_database_metrics():
    """Get database performance and connection metrics"""
    if not monitoring_dashboard:
        raise HTTPException(status_code=503, detail="Monitoring not initialized")
    
    try:
        db_data = {
            "connections": monitoring_dashboard.db_monitor.get_connection_stats(),
            "tables": monitoring_dashboard.db_monitor.get_table_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
        return db_data
    except Exception as e:
        logger.error(f"Database metrics failed: {e}")
        return {"error": str(e)}

@app.get("/api/v1/monitoring/dashboard")
async def get_monitoring_dashboard():
    """Get comprehensive monitoring dashboard data"""
    if not monitoring_dashboard:
        raise HTTPException(status_code=503, detail="Monitoring not initialized")
    
    try:
        dashboard_data = await monitoring_dashboard.get_dashboard_data()
        return dashboard_data
    except Exception as e:
        logger.error(f"Dashboard data failed: {e}")
        return {"error": str(e)}

@app.get("/api/v1/monitoring/alerts")
async def get_recent_alerts(hours: int = 24):
    """Get recent system alerts"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available for alerts")
    
    try:
        cutoff_time = int(time.time()) - (hours * 3600)
        alert_keys = []
        
        # Get all alert keys within time range
        for key in redis_client.scan_iter(match="alerts:*"):
            timestamp = int(key.decode().split(":")[-1])
            if timestamp >= cutoff_time:
                alert_keys.append(key)
        
        alerts = []
        for key in alert_keys:
            try:
                alert_data = json.loads(redis_client.get(key))
                alerts.append(alert_data)
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Sort by timestamp (most recent first)
        alerts.sort(key=lambda x: x.get('metric', {}).get('timestamp', ''), reverse=True)
        
        return {
            "alerts": alerts,
            "total_count": len(alerts),
            "hours_examined": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Alerts retrieval failed: {e}")
        return {"error": str(e)}

@app.post("/api/v1/monitoring/test-alert")
async def trigger_test_alert():
    """Trigger a test alert for monitoring system validation"""
    if not apm_monitor:
        raise HTTPException(status_code=503, detail="APM not initialized")
    
    try:
        from crm_monitoring import PerformanceMetric
        
        # Create a test alert
        test_metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            endpoint="/test-alert",
            method="POST",
            duration=6.0,  # Triggers slow response alert
            status_code=200,
            user_id=None,
            error_message=None,
            memory_usage=500 * 1024 * 1024,  # 500MB
            cpu_usage=50.0
        )
        
        apm_monitor.record_request(test_metric)
        
        return {
            "message": "Test alert triggered successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Test alert failed: {e}")
        return {"error": str(e)}

# ================================
# Background Tasks
# ================================

async def background_task_runner():
    """Run periodic background tasks"""
    logger.info("🔄 Starting background task runner")
    
    while True:
        try:
            # Sleep for 30 minutes between checks
            await asyncio.sleep(30 * 60)
            
            db = SessionLocal()
            try:
                # Check for inactive leads every 30 minutes
                recycled_count = run_lead_recycling_check(db)
                if recycled_count > 0:
                    logger.info(f"♻️ Background task recycled {recycled_count} leads")
                
                # Ensure all agents have adequate leads
                distribution_result = run_lead_redistribution(db)
                if distribution_result.get("leads_distributed", 0) > 0:
                    logger.info(f"📋 Background task distributed {distribution_result['leads_distributed']} leads")
                
            except Exception as e:
                logger.error(f"❌ Background task error: {e}")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Background task runner error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

# ================================
# Old event handlers replaced with lifespan
# ================================

# ================================
# Run the application
# ================================

if __name__ == "__main__":
    import uvicorn
    import socket
    
    def find_available_port(start_port=8001, max_port=8010):
        """Find an available port starting from start_port"""
        for port in range(start_port, max_port + 1):
            try:
                # Try to bind to the port
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("0.0.0.0", port))
                    logger.info(f"✅ Port {port} is available")
                    return port
            except OSError:
                logger.warning(f"⚠️ Port {port} is already in use")
                continue
        
        # If no port found in range, let system assign one
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", 0))
            port = s.getsockname()[1]
            logger.info(f"✅ Using system-assigned port {port}")
            return port
    
    # Find available port
    available_port = find_available_port()
    
    logger.info(f"🚀 Starting Cura Genesis CRM on http://0.0.0.0:{available_port}")
    logger.info(f"📊 Dashboard: http://localhost:{available_port}/crm_enhanced_dashboard_v2.html")
    logger.info(f"📋 API Docs: http://localhost:{available_port}/docs")
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=available_port, 
            log_level="info" if not settings.debug else "debug"
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1) 