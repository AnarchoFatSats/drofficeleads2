#!/usr/bin/env python3
"""
Enhanced CRM Features - Industry Best Practices
Adds missing features for world-class CRM functionality
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel
from datetime import datetime, date
from crm_main import Base

# ================================
# Enhanced Database Models
# ================================

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class EmailTemplateType(str, Enum):
    INITIAL_OUTREACH = "initial_outreach"
    FOLLOW_UP = "follow_up"
    MEETING_REQUEST = "meeting_request"
    PROPOSAL = "proposal"
    THANK_YOU = "thank_you"
    NURTURE = "nurture"
    REMINDER = "reminder"

class DealStage(str, Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class CallType(str, Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"

class CallOutcome(str, Enum):
    CONNECTED = "connected"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    BUSY = "busy"
    DISCONNECTED = "disconnected"
    SCHEDULED_CALLBACK = "scheduled_callback"

# ================================
# Enhanced Task Management System
# ================================

class Task(Base):
    __tablename__ = "crm_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    deal_id = Column(Integer, ForeignKey("crm_deals.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    completed_at = Column(DateTime, nullable=True)
    estimated_hours = Column(Numeric(4, 2), default=1.0)
    actual_hours = Column(Numeric(4, 2), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])

# ================================
# Email Management System
# ================================

class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    template_type = Column(SQLEnum(EmailTemplateType), nullable=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Numeric(5, 2), default=0.0)  # Response rate percentage
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    creator = relationship("User")

class EmailHistory(Base):
    __tablename__ = "email_history"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    sent_by = Column(Integer, ForeignKey("users.id"))
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    recipient_email = Column(String(255), nullable=False)
    sent_at = Column(DateTime, default=func.now())
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    bounce_reason = Column(String(255), nullable=True)
    
    sender = relationship("User")

# ================================
# Deal/Opportunity Management
# ================================

class Deal(Base):
    __tablename__ = "crm_deals"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    value = Column(Numeric(12, 2))  # Deal value in dollars
    stage = Column(SQLEnum(DealStage), default=DealStage.PROSPECTING)
    probability = Column(Integer, default=0)  # 0-100% chance of closing
    expected_close_date = Column(Date)
    actual_close_date = Column(Date, nullable=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    product_interest = Column(String(255))  # Which Cura Genesis product
    competitor = Column(String(255), nullable=True)
    lost_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])

# ================================
# Advanced Call Management
# ================================

class CallLog(Base):
    __tablename__ = "call_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    phone_number = Column(String(20))
    duration_minutes = Column(Integer, default=0)
    call_type = Column(SQLEnum(CallType))
    outcome = Column(SQLEnum(CallOutcome))
    notes = Column(Text)
    follow_up_date = Column(DateTime, nullable=True)
    recording_url = Column(String(500), nullable=True)
    call_quality_score = Column(Integer, nullable=True)  # 1-10 rating
    next_action = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User")

# ================================
# Lead Scoring & Pipeline Management
# ================================

class LeadScore(Base):
    __tablename__ = "lead_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True)
    demographic_score = Column(Integer, default=0)  # Based on title, company size, etc.
    behavioral_score = Column(Integer, default=0)   # Based on email opens, website visits
    engagement_score = Column(Integer, default=0)   # Based on calls, meetings, responses
    fit_score = Column(Integer, default=0)          # How well they match ICP
    total_score = Column(Integer, default=0)        # Combined score
    last_calculated = Column(DateTime, default=func.now())
    scoring_factors = Column(Text)  # JSON string of scoring breakdown

# ================================
# Pydantic Models for API
# ================================

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: Optional[int] = None
    lead_id: Optional[int] = None
    deal_id: Optional[int] = None
    estimated_hours: Optional[float] = 1.0

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    actual_hours: Optional[float] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    priority: TaskPriority
    status: TaskStatus
    assigned_to: Optional[int]
    lead_id: Optional[int]
    deal_id: Optional[int]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    body: str
    template_type: EmailTemplateType

class EmailTemplateResponse(BaseModel):
    id: int
    name: str
    subject: str
    body: str
    template_type: EmailTemplateType
    is_active: bool
    usage_count: int
    success_rate: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class DealCreate(BaseModel):
    title: str
    description: Optional[str] = None
    value: Optional[float] = None
    stage: DealStage = DealStage.PROSPECTING
    probability: int = 0
    expected_close_date: Optional[date] = None
    lead_id: int
    product_interest: Optional[str] = None

class DealUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[DealStage] = None
    probability: Optional[int] = None
    expected_close_date: Optional[date] = None
    product_interest: Optional[str] = None
    competitor: Optional[str] = None
    lost_reason: Optional[str] = None

class DealResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    value: Optional[float]
    stage: DealStage
    probability: int
    expected_close_date: Optional[date]
    actual_close_date: Optional[date]
    lead_id: int
    assigned_to: Optional[int]
    product_interest: Optional[str]
    competitor: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CallLogCreate(BaseModel):
    lead_id: int
    phone_number: str
    duration_minutes: int = 0
    call_type: CallType
    outcome: CallOutcome
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    call_quality_score: Optional[int] = None
    next_action: Optional[str] = None

class CallLogResponse(BaseModel):
    id: int
    lead_id: int
    user_id: int
    phone_number: str
    duration_minutes: int
    call_type: CallType
    outcome: CallOutcome
    notes: Optional[str]
    follow_up_date: Optional[datetime]
    call_quality_score: Optional[int]
    next_action: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PipelineStageStats(BaseModel):
    stage: str
    count: int
    total_value: float
    avg_probability: float
    avg_days_in_stage: int

class PipelineAnalytics(BaseModel):
    total_deals: int
    total_pipeline_value: float
    weighted_pipeline_value: float
    avg_deal_size: float
    conversion_rate_by_stage: Dict[str, float]
    stage_stats: List[PipelineStageStats]

class ConversionMetrics(BaseModel):
    agent_id: int
    agent_name: str
    leads_assigned: int
    leads_contacted: int
    leads_qualified: int
    deals_created: int
    deals_won: int
    total_deal_value: float
    conversion_rate: float
    avg_time_to_first_contact: float  # hours
    avg_time_to_close: float  # days

class TopPerformerStats(BaseModel):
    rank: int
    agent_id: int
    agent_name: str
    username: str
    conversion_rate: float
    total_sales: int
    total_deal_value: float
    avg_deal_size: float
    calls_made: int
    emails_sent: int
    points: int
    level: int

# ================================
# Enhanced CRM Services
# ================================

class PipelineService:
    """Advanced pipeline management and analytics"""
    
    @staticmethod
    def calculate_pipeline_velocity(db, user_id: Optional[int] = None):
        """Calculate how fast deals move through pipeline stages"""
        # Implementation for pipeline velocity calculation
        pass
    
    @staticmethod
    def get_conversion_funnel(db, date_from: date, date_to: date):
        """Get conversion rates between each stage"""
        # Implementation for conversion funnel analysis
        pass
    
    @staticmethod
    def forecast_revenue(db, months_ahead: int = 3):
        """Forecast revenue based on pipeline and historical data"""
        # Implementation for revenue forecasting
        pass

class LeadScoringService:
    """Advanced lead scoring based on multiple factors"""
    
    SCORING_WEIGHTS = {
        'job_title': {
            'ceo': 25, 'president': 25, 'owner': 25,
            'director': 20, 'manager': 15, 'coordinator': 10,
            'assistant': 5, 'other': 8
        },
        'company_size': {
            'enterprise': 25, 'large': 20, 'medium': 15,
            'small': 10, 'startup': 8
        },
        'industry_fit': {
            'perfect_match': 30, 'good_match': 20,
            'fair_match': 10, 'poor_match': 2
        },
        'engagement_level': {
            'high': 20, 'medium': 10, 'low': 5, 'none': 0
        }
    }
    
    @staticmethod
    def calculate_lead_score(lead_data: dict) -> dict:
        """Calculate comprehensive lead score"""
        demographic_score = LeadScoringService._calculate_demographic_score(lead_data)
        behavioral_score = LeadScoringService._calculate_behavioral_score(lead_data)
        engagement_score = LeadScoringService._calculate_engagement_score(lead_data)
        fit_score = LeadScoringService._calculate_fit_score(lead_data)
        
        total_score = demographic_score + behavioral_score + engagement_score + fit_score
        
        return {
            'demographic_score': demographic_score,
            'behavioral_score': behavioral_score,
            'engagement_score': engagement_score,
            'fit_score': fit_score,
            'total_score': min(total_score, 100),  # Cap at 100
            'scoring_factors': {
                'demographic': demographic_score,
                'behavioral': behavioral_score,
                'engagement': engagement_score,
                'fit': fit_score
            }
        }
    
    @staticmethod
    def _calculate_demographic_score(lead_data: dict) -> int:
        """Score based on job title, company size, etc."""
        score = 0
        
        # Job title scoring
        job_title = lead_data.get('job_title', '').lower()
        for key, value in LeadScoringService.SCORING_WEIGHTS['job_title'].items():
            if key in job_title:
                score += value
                break
        
        return min(score, 30)  # Cap demographic score
    
    @staticmethod
    def _calculate_behavioral_score(lead_data: dict) -> int:
        """Score based on website visits, email opens, etc."""
        # Placeholder for behavioral scoring
        return lead_data.get('behavioral_score', 0)
    
    @staticmethod
    def _calculate_engagement_score(lead_data: dict) -> int:
        """Score based on calls answered, emails replied, etc."""
        # Placeholder for engagement scoring
        return lead_data.get('engagement_score', 0)
    
    @staticmethod
    def _calculate_fit_score(lead_data: dict) -> int:
        """Score based on how well they match ideal customer profile"""
        # Use existing scoring system from medicare_allograft_lead_extractor
        return lead_data.get('score', 0) // 4  # Convert to 0-25 scale

class AutomationService:
    """Automated workflows and follow-ups"""
    
    @staticmethod
    def create_follow_up_tasks(db, lead_id: int, user_id: int):
        """Automatically create follow-up tasks based on lead stage"""
        # Implementation for automatic task creation
        pass
    
    @staticmethod
    def send_automated_emails(db, template_type: EmailTemplateType, lead_ids: List[int]):
        """Send automated email sequences"""
        # Implementation for email automation
        pass
    
    @staticmethod
    def update_lead_scores(db):
        """Batch update all lead scores"""
        # Implementation for batch score updates
        pass 