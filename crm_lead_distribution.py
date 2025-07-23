#!/usr/bin/env python3
"""
Advanced Lead Distribution System for Cura Genesis CRM
Manages automatic lead assignment with 20 leads per agent
"""

import sys
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging

# Import shared models to avoid circular imports
sys.path.append('.')
from crm_shared_models import UserRole, LeadStatus, ActivityType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LeadDistributionService:
    """Advanced lead distribution and management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.leads_per_agent = 20
        self.inactivity_hours = 24
        self.max_recycling_attempts = 3
    
    def get_active_agents(self):
        """Get all active agents who should receive leads"""
        # Late import to avoid circular dependency
        from crm_main import User
        return self.db.query(User).filter(
            User.role == UserRole.AGENT,
            User.is_active == True
        ).all()
    
    def get_agent_lead_count(self, agent_id: int) -> int:
        """Get current number of active leads for an agent"""
        from crm_main import Lead
        return self.db.query(Lead).filter(
            Lead.assigned_user_id == agent_id,
            Lead.status.notin_([
                LeadStatus.CLOSED_WON,
                LeadStatus.CLOSED_LOST,
                LeadStatus.RECYCLED
            ])
        ).count()
    
    def get_available_leads(self, limit: int = None):
        """Get leads available for assignment"""
        from crm_main import Lead
        query = self.db.query(Lead).filter(
            or_(
                Lead.assigned_user_id.is_(None),
                Lead.status == LeadStatus.RECYCLED
            ),
            Lead.status.notin_([
                LeadStatus.CLOSED_WON,
                LeadStatus.CLOSED_LOST
            ]),
            Lead.times_recycled < self.max_recycling_attempts
        ).order_by(
            Lead.score.desc(),  # Highest score first
            Lead.created_at.asc()  # Oldest first for fairness
        )
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def assign_lead_to_agent(self, lead, agent) -> bool:
        """Assign a single lead to an agent"""
        try:
            # Track previous assignments for recycling
            if lead.assigned_user_id and lead.assigned_user_id != agent.id:
                if lead.previous_agents is None:
                    lead.previous_agents = []
                if lead.assigned_user_id not in lead.previous_agents:
                    lead.previous_agents.append(lead.assigned_user_id)
            
            # Assign lead
            lead.assigned_user_id = agent.id
            lead.assigned_at = datetime.utcnow()
            lead.status = LeadStatus.NEW
            lead.recycling_eligible_at = None
            
            # If this is a recycled lead, increment counter
            if lead.status == LeadStatus.RECYCLED:
                lead.times_recycled += 1
            
            self.db.commit()
            
            logger.info(f"📋 Assigned lead {lead.id} ({lead.practice_name}) to agent {agent.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning lead {lead.id} to agent {agent.id}: {e}")
            self.db.rollback()
            return False
    
    def distribute_leads_to_agent(self, agent, target_count: int = None) -> int:
        """Distribute leads to bring agent up to target count"""
        if target_count is None:
            target_count = self.leads_per_agent
        
        current_count = self.get_agent_lead_count(agent.id)
        needed = target_count - current_count
        
        if needed <= 0:
            return 0
        
        available_leads = self.get_available_leads(needed)
        assigned_count = 0
        
        for lead in available_leads:
            if self.assign_lead_to_agent(lead, agent):
                assigned_count += 1
            
            if assigned_count >= needed:
                break
        
        logger.info(f"🎯 Agent {agent.username}: {current_count} → {current_count + assigned_count} leads")
        return assigned_count
    
    def redistribute_all_leads(self) -> Dict[str, int]:
        """Redistribute leads to all active agents"""
        active_agents = self.get_active_agents()
        
        if not active_agents:
            logger.warning("No active agents found for lead distribution")
            return {"agents": 0, "leads_distributed": 0}
        
        total_distributed = 0
        agent_stats = {}
        
        for agent in active_agents:
            distributed = self.distribute_leads_to_agent(agent)
            total_distributed += distributed
            agent_stats[agent.username] = {
                "distributed": distributed,
                "total_leads": self.get_agent_lead_count(agent.id)
            }
        
        logger.info(f"📊 Redistributed {total_distributed} leads to {len(active_agents)} agents")
        
        return {
            "agents": len(active_agents),
            "leads_distributed": total_distributed,
            "agent_stats": agent_stats
        }
    
    def handle_lead_disposition(self, lead_id: int, new_status: LeadStatus, agent_id: int) -> bool:
        """Handle lead status change and trigger redistribution if needed"""
        from crm_main import Lead, User
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return False
        
        old_status = lead.status
        lead.status = new_status
        lead.updated_at = datetime.utcnow()
        
        # If lead is closed (sale made or do not call), remove from agent's active pool
        if new_status in [LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST]:
            logger.info(f"✅ Lead {lead_id} closed as {new_status.value} by agent {agent_id}")
            
            # Get the agent and redistribute leads to maintain 20
            agent = self.db.query(User).filter(User.id == agent_id).first()
            if agent:
                self.db.commit()  # Commit the status change first
                new_leads = self.distribute_leads_to_agent(agent)
                logger.info(f"🔄 Assigned {new_leads} new leads to {agent.username} to maintain {self.leads_per_agent}")
        
        self.db.commit()
        return True
    
    def check_inactive_leads(self) -> int:
        """Find and recycle leads that haven't been touched in 24 hours"""
        from crm_main import Lead, Activity
        cutoff_time = datetime.utcnow() - timedelta(hours=self.inactivity_hours)
        
        # Find leads that haven't had activity in 24 hours
        inactive_leads = self.db.query(Lead).filter(
            Lead.assigned_user_id.isnot(None),
            Lead.status.notin_([
                LeadStatus.CLOSED_WON,
                LeadStatus.CLOSED_LOST,
                LeadStatus.RECYCLED
            ]),
            or_(
                Lead.last_contact_date.is_(None),
                Lead.last_contact_date < cutoff_time
            ),
            Lead.assigned_at < cutoff_time
        ).all()
        
        recycled_count = 0
        
        for lead in inactive_leads:
            # Check if there's any recent activity
            recent_activity = self.db.query(Activity).filter(
                Activity.lead_id == lead.id,
                Activity.created_at > cutoff_time
            ).first()
            
            if not recent_activity:
                # Recycle the lead
                if lead.previous_agents is None:
                    lead.previous_agents = []
                
                if lead.assigned_user_id not in lead.previous_agents:
                    lead.previous_agents.append(lead.assigned_user_id)
                
                old_agent_id = lead.assigned_user_id
                lead.assigned_user_id = None
                lead.assigned_at = None
                lead.status = LeadStatus.RECYCLED
                lead.times_recycled += 1
                
                recycled_count += 1
                logger.info(f"♻️ Recycled inactive lead {lead.id} from agent {old_agent_id}")
        
        if recycled_count > 0:
            self.db.commit()
            # Redistribute recycled leads
            self.redistribute_all_leads()
            logger.info(f"♻️ Recycled {recycled_count} inactive leads and redistributed")
        
        return recycled_count
    
    def get_agent_dashboard_stats(self, agent_id: int) -> Dict:
        """Get dashboard statistics for a specific agent"""
        from crm_main import Lead, Activity
        # Active leads count
        active_leads = self.get_agent_lead_count(agent_id)
        
        # Leads closed today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        closed_today = self.db.query(Lead).filter(
            Lead.assigned_user_id == agent_id,
            Lead.status.in_([LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST]),
            Lead.updated_at >= today_start
        ).count()
        
        # Sales made today
        sales_today = self.db.query(Lead).filter(
            Lead.assigned_user_id == agent_id,
            Lead.status == LeadStatus.CLOSED_WON,
            Lead.updated_at >= today_start
        ).count()
        
        # Activities today
        activities_today = self.db.query(Activity).filter(
            Activity.user_id == agent_id,
            Activity.created_at >= today_start
        ).count()
        
        return {
            "active_leads": active_leads,
            "target_leads": self.leads_per_agent,
            "leads_needed": max(0, self.leads_per_agent - active_leads),
            "closed_today": closed_today,
            "sales_today": sales_today,
            "activities_today": activities_today
        }
    
    def force_redistribute_agent(self, agent_id: int) -> Dict:
        """Force redistribution for a specific agent"""
        from crm_main import User
        agent = self.db.query(User).filter(User.id == agent_id).first()
        if not agent:
            return {"error": "Agent not found"}
        
        distributed = self.distribute_leads_to_agent(agent)
        stats = self.get_agent_dashboard_stats(agent_id)
        
        return {
            "agent": agent.username,
            "leads_distributed": distributed,
            "stats": stats
        }
    
    def get_system_lead_stats(self) -> Dict:
        """Get overall system lead statistics"""
        from crm_main import Lead
        total_leads = self.db.query(Lead).count()
        
        assigned_leads = self.db.query(Lead).filter(
            Lead.assigned_user_id.isnot(None),
            Lead.status.notin_([LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST])
        ).count()
        
        available_leads = len(self.get_available_leads())
        
        closed_won = self.db.query(Lead).filter(
            Lead.status == LeadStatus.CLOSED_WON
        ).count()
        
        closed_lost = self.db.query(Lead).filter(
            Lead.status == LeadStatus.CLOSED_LOST
        ).count()
        
        active_agents = len(self.get_active_agents())
        
        return {
            "total_leads": total_leads,
            "assigned_leads": assigned_leads,
            "available_leads": available_leads,
            "closed_won": closed_won,
            "closed_lost": closed_lost,
            "active_agents": active_agents,
            "target_assigned": active_agents * self.leads_per_agent,
            "distribution_health": "Good" if assigned_leads >= (active_agents * self.leads_per_agent * 0.8) else "Needs Attention"
        }


# Background task functions for automation
def run_lead_recycling_check(db: Session):
    """Background task to check for inactive leads"""
    distribution_service = LeadDistributionService(db)
    recycled = distribution_service.check_inactive_leads()
    return recycled

def run_lead_redistribution(db: Session):
    """Background task to ensure all agents have enough leads"""
    distribution_service = LeadDistributionService(db)
    result = distribution_service.redistribute_all_leads()
    return result

def initialize_lead_distribution(db: Session):
    """Initialize the lead distribution system"""
    distribution_service = LeadDistributionService(db)
    
    # Get system stats
    stats = distribution_service.get_system_lead_stats()
    logger.info(f"📊 System Stats: {stats}")
    
    # Redistribute all leads
    result = distribution_service.redistribute_all_leads()
    logger.info(f"🚀 Initial distribution complete: {result}")
    
    return result

if __name__ == "__main__":
    # Test the distribution service
    from crm_main import SessionLocal
    
    db = SessionLocal()
    try:
        result = initialize_lead_distribution(db)
        print("Distribution result:", result)
    finally:
        db.close() 