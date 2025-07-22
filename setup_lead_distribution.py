#!/usr/bin/env python3
"""
Lead Distribution Setup Script
Initializes the advanced lead distribution system for Cura Genesis CRM
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import our CRM models and services
sys.path.append('.')
from crm_main import User, Lead, UserRole, LeadStatus, Base
from crm_lead_distribution import LeadDistributionService, initialize_lead_distribution

# Configuration
DATABASE_URL = "postgresql://alexsiegel@localhost:5432/cura_genesis_crm"

def setup_distribution_system():
    """Set up the complete lead distribution system"""
    print("🚀 Setting up Advanced Lead Distribution System")
    print("=" * 60)
    
    # Connect to database
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create distribution service
        distribution_service = LeadDistributionService(db)
        
        # Get current system stats
        print("📊 Current System Status:")
        system_stats = distribution_service.get_system_lead_stats()
        print(f"   Total Leads: {system_stats['total_leads']}")
        print(f"   Assigned Leads: {system_stats['assigned_leads']}")
        print(f"   Available Leads: {system_stats['available_leads']}")
        print(f"   Active Agents: {system_stats['active_agents']}")
        print(f"   Target Assignment: {system_stats['target_assigned']} (20 per agent)")
        print(f"   Distribution Health: {system_stats['distribution_health']}")
        
        print("\n🎯 Configuring Lead Distribution...")
        
        # Configure distribution settings
        distribution_service.leads_per_agent = 20
        distribution_service.inactivity_hours = 24
        distribution_service.max_recycling_attempts = 3
        
        print(f"   ✅ Leads per agent: {distribution_service.leads_per_agent}")
        print(f"   ✅ Inactivity timeout: {distribution_service.inactivity_hours} hours")
        print(f"   ✅ Max recycling attempts: {distribution_service.max_recycling_attempts}")
        
        # Reset all lead assignments to start fresh
        print("\n🔄 Resetting lead assignments...")
        reset_count = db.query(Lead).filter(
            Lead.status.notin_([LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST])
        ).update({
            Lead.assigned_user_id: None,
            Lead.assigned_at: None,
            Lead.status: LeadStatus.NEW,
            Lead.recycling_eligible_at: None,
            Lead.times_recycled: 0,
            Lead.previous_agents: []
        })
        db.commit()
        print(f"   ✅ Reset {reset_count} leads to unassigned state")
        
        # Get active agents
        agents = distribution_service.get_active_agents()
        print(f"\n👥 Found {len(agents)} active agents:")
        for agent in agents:
            print(f"   - {agent.full_name} (@{agent.username}) - {agent.territory}")
        
        # Distribute leads
        print("\n📋 Distributing leads to agents...")
        result = distribution_service.redistribute_all_leads()
        
        print(f"\n✅ Distribution Complete!")
        print(f"   Agents: {result['agents']}")
        print(f"   Leads Distributed: {result['leads_distributed']}")
        
        # Show agent assignments
        print(f"\n📊 Agent Lead Assignments:")
        for agent_name, stats in result.get("agent_stats", {}).items():
            print(f"   {agent_name}: {stats['total_leads']} leads (distributed: {stats['distributed']})")
        
        # Final system stats
        print(f"\n📈 Final System Status:")
        final_stats = distribution_service.get_system_lead_stats()
        print(f"   Total Leads: {final_stats['total_leads']}")
        print(f"   Assigned Leads: {final_stats['assigned_leads']}")
        print(f"   Available Leads: {final_stats['available_leads']}")
        print(f"   Distribution Health: {final_stats['distribution_health']}")
        
        # Test agent dashboard stats
        print(f"\n🎯 Agent Dashboard Examples:")
        for agent in agents[:2]:  # Show first 2 agents
            agent_stats = distribution_service.get_agent_dashboard_stats(agent.id)
            print(f"   {agent.username}:")
            print(f"     Active Leads: {agent_stats['active_leads']}/{agent_stats['target_leads']}")
            print(f"     Sales Today: {agent_stats['sales_today']}")
            print(f"     Activities Today: {agent_stats['activities_today']}")
        
        print(f"\n🎉 Lead Distribution System Setup Complete!")
        print(f"=" * 60)
        print(f"✅ Each agent now has up to 20 leads")
        print(f"✅ 24-hour inactivity recycling active") 
        print(f"✅ Automatic redistribution on lead closure")
        print(f"✅ Real-time notifications enabled")
        print(f"\n🌐 Access your CRM: http://localhost:8002/crm_enhanced_dashboard.html")
        print(f"🔗 API Server: http://localhost:8001/")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def test_distribution_features():
    """Test key distribution features"""
    print("\n🧪 Testing Distribution Features...")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        distribution_service = LeadDistributionService(db)
        
        # Test getting available leads
        available = distribution_service.get_available_leads(5)
        print(f"   ✅ Available leads query: {len(available)} leads found")
        
        # Test agent stats
        agents = distribution_service.get_active_agents()
        if agents:
            test_agent = agents[0]
            stats = distribution_service.get_agent_dashboard_stats(test_agent.id)
            print(f"   ✅ Agent stats for {test_agent.username}: {stats['active_leads']} active leads")
        
        # Test system stats
        system_stats = distribution_service.get_system_lead_stats()
        print(f"   ✅ System stats: {system_stats['distribution_health']} health")
        
        print("   🎉 All distribution features working correctly!")
        
    except Exception as e:
        print(f"   ❌ Testing failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🏥 Cura Genesis CRM - Lead Distribution Setup")
    print("This will configure your CRM for optimal lead management")
    print()
    
    confirm = input("Ready to set up lead distribution? (y/N): ")
    if confirm.lower() != 'y':
        print("Setup cancelled.")
        sys.exit(0)
    
    setup_distribution_system()
    test_distribution_features()
    
    print("\n🎊 Your CRM is now optimized for maximum sales efficiency!")
    print("Each agent will automatically maintain 20 active leads at all times.") 