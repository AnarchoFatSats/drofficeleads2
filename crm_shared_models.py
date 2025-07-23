#!/usr/bin/env python3
"""
Shared Models and Enums for Cura Genesis CRM
Common enums and base models to prevent circular imports
"""

from enum import Enum

# ================================
# User Enums
# ================================

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# ================================
# Lead Enums
# ================================

class LeadStatus(str, Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    DEMO_SCHEDULED = "demo_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    RECYCLED = "recycled"

class LeadPriority(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C = "C"

class LeadSource(str, Enum):
    NPPES_EXTRACTION = "nppes_extraction"
    MANUAL_ENTRY = "manual_entry"
    REFERRAL = "referral"
    MARKETING = "marketing"
    RECYCLED = "recycled"

# ================================
# Activity Enums
# ================================

class ActivityType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"
    TASK = "task"
    DEMO = "demo"
    PROPOSAL = "proposal"
    FOLLOW_UP = "follow_up"

class ActivityOutcome(str, Enum):
    CONNECTED = "connected"
    VOICEMAIL = "voicemail"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# ================================
# Gamification Enums
# ================================

class PointCategory(str, Enum):
    CONTACT = "contact"
    QUALIFICATION = "qualification"
    CONVERSION = "conversion"
    MILESTONE = "milestone"
    BONUS = "bonus"

class BadgeType(str, Enum):
    ACTIVITY = "activity"
    ACHIEVEMENT = "achievement"
    MILESTONE = "milestone"
    STREAK = "streak"
    SPECIAL = "special"

# ================================
# Notification Enums
# ================================

class NotificationType(str, Enum):
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

class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed" 