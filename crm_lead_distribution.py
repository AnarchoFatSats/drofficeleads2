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
        # Import here to avoid circular dependency
        from sqlalchemy import text
        
        # Use raw SQL query to avoid model import
        result = self.db.execute(text("""
            SELECT id, username, full_name, email, role, is_active 
            FROM users 
            WHERE role = 'agent' AND is_active = true
        """))
        
        # Create simple agent objects
        class Agent:
            def __init__(self, id, username, full_name, email, role, is_active):
                self.id = id
                self.username = username
                self.full_name = full_name
                self.email = email
                self.role = role
                self.is_active = is_active
        
        return [Agent(row.id, row.username, row.full_name, row.email, row.role, row.is_active) 
                for row in result]
    
    def get_agent_lead_count(self, agent_id: int) -> int:
        """Get current number of active leads for an agent"""
        from sqlalchemy import text
        
        result = self.db.execute(text("""
            SELECT COUNT(*) as count 
            FROM leads 
            WHERE assigned_user_id = :agent_id 
            AND status NOT IN ('closed_won', 'closed_lost', 'recycled')
        """), {"agent_id": agent_id})
        
        return result.scalar()
    
    def get_available_leads(self, limit: int = None):
        """Get leads available for assignment"""
        from sqlalchemy import text
        
        limit_clause = f"LIMIT {limit}" if limit else ""
        
        result = self.db.execute(text(f"""
            SELECT id, practice_name, score, created_at, assigned_user_id, status, times_recycled
            FROM leads 
            WHERE (assigned_user_id IS NULL OR status = 'recycled')
            AND status NOT IN ('closed_won', 'closed_lost')
            AND times_recycled < :max_recycling
            ORDER BY score DESC, created_at ASC
            {limit_clause}
        """), {"max_recycling": self.max_recycling_attempts})
        
        # Create simple lead objects
        class Lead:
            def __init__(self, id, practice_name, score, created_at, assigned_user_id, status, times_recycled):
                self.id = id
                self.practice_name = practice_name
                self.score = score
                self.created_at = created_at
                self.assigned_user_id = assigned_user_id
                self.status = status
                self.times_recycled = times_recycled
                self.previous_agents = []  # Default empty list
        
        return [Lead(row.id, row.practice_name, row.score, row.created_at, 
                    row.assigned_user_id, row.status, row.times_recycled) 
                for row in result]
    
    def assign_lead_to_agent(self, lead, agent) -> bool:
        """Assign a single lead to an agent"""
        try:
            from sqlalchemy import text
            
            # Update lead assignment using raw SQL
            self.db.execute(text("""
                UPDATE leads SET 
                    assigned_user_id = :agent_id,
                    assigned_at = :assigned_at,
                    status = 'new',
                    recycling_eligible_at = NULL,
                    updated_at = :updated_at,
                    times_recycled = CASE 
                        WHEN status = 'recycled' THEN times_recycled + 1 
                        ELSE times_recycled 
                    END
                WHERE id = :lead_id
            """), {
                "agent_id": agent.id,
                "assigned_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "lead_id": lead.id
            })
            
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
        from sqlalchemy import text
        
        # Update lead status using raw SQL
        result = self.db.execute(text("""
            UPDATE leads SET 
                status = :new_status,
                updated_at = :updated_at
            WHERE id = :lead_id
            RETURNING status
        """), {
            "new_status": new_status.value,
            "updated_at": datetime.utcnow(),
            "lead_id": lead_id
        })
        
        if not result.rowcount:
            return False
        
        # If lead is closed (sale made or do not call), remove from agent's active pool
        if new_status in [LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST]:
            logger.info(f"✅ Lead {lead_id} closed as {new_status.value} by agent {agent_id}")
            
            # Get the agent info and redistribute leads to maintain 20
            agent_result = self.db.execute(text("""
                SELECT id, username, full_name FROM users WHERE id = :agent_id
            """), {"agent_id": agent_id})
            
            agent_row = agent_result.first()
            if agent_row:
                self.db.commit()  # Commit the status change first
                
                # Create simple agent object
                class Agent:
                    def __init__(self, id, username, full_name):
                        self.id = id
                        self.username = username
                        self.full_name = full_name
                
                agent = Agent(agent_row.id, agent_row.username, agent_row.full_name)
                new_leads = self.distribute_leads_to_agent(agent)
                logger.info(f"🔄 Assigned {new_leads} new leads to {agent.username} to maintain {self.leads_per_agent}")
        
        self.db.commit()
        return True
    
    def check_inactive_leads(self) -> int:
        """Find and recycle leads that haven't been touched in 24 hours"""
        from sqlalchemy import text
        cutoff_time = datetime.utcnow() - timedelta(hours=self.inactivity_hours)
        
        # Find and recycle inactive leads using raw SQL
        result = self.db.execute(text("""
            UPDATE leads SET 
                assigned_user_id = NULL,
                assigned_at = NULL,
                status = 'recycled',
                times_recycled = times_recycled + 1,
                updated_at = :updated_at
            WHERE id IN (
                SELECT l.id FROM leads l
                WHERE l.assigned_user_id IS NOT NULL
                AND l.status NOT IN ('closed_won', 'closed_lost', 'recycled')
                AND (l.last_contact_date IS NULL OR l.last_contact_date < :cutoff_time)
                AND l.assigned_at < :cutoff_time
                AND NOT EXISTS (
                    SELECT 1 FROM activities a 
                    WHERE a.lead_id = l.id 
                    AND a.created_at > :cutoff_time
                )
            )
            RETURNING id
        """), {
            "cutoff_time": cutoff_time,
            "updated_at": datetime.utcnow()
        })
        
        recycled_lead_ids = [row.id for row in result]
        recycled_count = len(recycled_lead_ids)
        
        if recycled_count > 0:
            self.db.commit()
            # Redistribute recycled leads
            self.redistribute_all_leads()
            logger.info(f"♻️ Recycled {recycled_count} inactive leads and redistributed")
        
        return recycled_count
    
    def get_agent_dashboard_stats(self, agent_id: int) -> Dict:
        """Get dashboard statistics for a specific agent"""
        from sqlalchemy import text
        
        # Active leads count
        active_leads = self.get_agent_lead_count(agent_id)
        
        # Leads closed today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stats_result = self.db.execute(text("""
            SELECT 
                COUNT(CASE WHEN status IN ('closed_won', 'closed_lost') AND updated_at >= :today_start THEN 1 END) as closed_today,
                COUNT(CASE WHEN status = 'closed_won' AND updated_at >= :today_start THEN 1 END) as sales_today
            FROM leads 
            WHERE assigned_user_id = :agent_id
        """), {"agent_id": agent_id, "today_start": today_start})
        
        stats_row = stats_result.first()
        
        # Activities today
        activities_result = self.db.execute(text("""
            SELECT COUNT(*) as activities_today 
            FROM activities 
            WHERE user_id = :agent_id AND created_at >= :today_start
        """), {"agent_id": agent_id, "today_start": today_start})
        
        activities_row = activities_result.first()
        
        return {
            "active_leads": active_leads,
            "target_leads": self.leads_per_agent,
            "leads_needed": max(0, self.leads_per_agent - active_leads),
            "closed_today": stats_row.closed_today if stats_row else 0,
            "sales_today": stats_row.sales_today if stats_row else 0,
            "activities_today": activities_row.activities_today if activities_row else 0
        }
    
    def force_redistribute_agent(self, agent_id: int) -> Dict:
        """Force redistribution for a specific agent"""
        from sqlalchemy import text
        
        agent_result = self.db.execute(text("""
            SELECT id, username, full_name FROM users WHERE id = :agent_id
        """), {"agent_id": agent_id})
        
        agent_row = agent_result.first()
        if not agent_row:
            return {"error": "Agent not found"}
        
        # Create simple agent object
        class Agent:
            def __init__(self, id, username, full_name):
                self.id = id
                self.username = username
                self.full_name = full_name
        
        agent = Agent(agent_row.id, agent_row.username, agent_row.full_name)
        distributed = self.distribute_leads_to_agent(agent)
        stats = self.get_agent_dashboard_stats(agent_id)
        
        return {
            "agent": agent.username,
            "leads_distributed": distributed,
            "stats": stats
        }
    
    def get_system_lead_stats(self) -> Dict:
        """Get overall system lead statistics"""
        from sqlalchemy import text
        
        # Get lead statistics using raw SQL
        lead_stats_result = self.db.execute(text("""
            SELECT 
                COUNT(*) as total_leads,
                COUNT(CASE WHEN assigned_user_id IS NOT NULL AND status NOT IN ('closed_won', 'closed_lost') THEN 1 END) as assigned_leads,
                COUNT(CASE WHEN status = 'closed_won' THEN 1 END) as closed_won,
                COUNT(CASE WHEN status = 'closed_lost' THEN 1 END) as closed_lost
            FROM leads
        """))
        
        stats_row = lead_stats_result.first()
        
        available_leads = len(self.get_available_leads())
        active_agents = len(self.get_active_agents())
        
        return {
            "total_leads": stats_row.total_leads if stats_row else 0,
            "assigned_leads": stats_row.assigned_leads if stats_row else 0,
            "available_leads": available_leads,
            "closed_won": stats_row.closed_won if stats_row else 0,
            "closed_lost": stats_row.closed_lost if stats_row else 0,
            "active_agents": active_agents,
            "target_assigned": active_agents * self.leads_per_agent,
            "distribution_health": "Good" if (stats_row.assigned_leads if stats_row else 0) >= (active_agents * self.leads_per_agent * 0.8) else "Needs Attention"
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
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Use environment variable or default
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://alexsiegel@localhost:5432/cura_genesis_crm')
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        result = initialize_lead_distribution(db)
        print("Distribution result:", result)
    finally:
        db.close() 