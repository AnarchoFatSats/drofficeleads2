#!/usr/bin/env python3
"""
Enhanced Lead Migration for Cura Genesis CRM
Imports existing hot_leads.json into PostgreSQL database
Creates sample users for immediate testing
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Import our CRM models
sys.path.append('.')
from crm_main import User, Lead, UserRole, LeadStatus, Base

# Configuration
DATABASE_URL = "postgresql://alexsiegel@localhost:5432/cura_genesis_crm"
LEADS_FILE = "web/data/hot_leads.json"

class EnhancedLeadMigrator:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def clean_phone(self, phone):
        """Clean phone number format"""
        if not phone or phone == "":
            return None
        # Remove non-digit characters
        cleaned = re.sub(r'[^\d]', '', str(phone))
        if len(cleaned) == 10:
            return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
        elif len(cleaned) == 11 and cleaned[0] == '1':
            return f"({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:]}"
        return str(phone)  # Return original if can't format
    
    def create_default_users(self):
        """Create default admin and sample agent users"""
        print("🔐 Creating default users...")
        
        # Check if admin already exists
        admin_exists = self.db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin_exists:
            print(f"   ✅ Admin user already exists: {admin_exists.username}")
        else:
            # Create admin
            admin = User(
                email="admin@curagenesis.com",
                username="admin",
                full_name="CRM Administrator",
                hashed_password=self.pwd_context.hash("admin123"),
                role=UserRole.ADMIN,
                phone="(555) 123-4567",
                territory="All",
                badges=["Founder", "Administrator"],
                total_points=1000,
                level=2
            )
            self.db.add(admin)
            print("   👑 Created admin user: admin / admin123")
        
        # Create sample agents
        sample_agents = [
            ("agent1@curagenesis.com", "agent1", "Sarah Johnson", "West Coast"),
            ("agent2@curagenesis.com", "agent2", "Mike Chen", "East Coast"),
            ("agent3@curagenesis.com", "agent3", "Emily Rodriguez", "Midwest"),
            ("agent4@curagenesis.com", "agent4", "David Thompson", "South"),
            ("agent5@curagenesis.com", "agent5", "Lisa Kim", "Northeast")
        ]
        
        for email, username, full_name, territory in sample_agents:
            existing = self.db.query(User).filter(User.username == username).first()
            if not existing:
                agent = User(
                    email=email,
                    username=username,
                    full_name=full_name,
                    hashed_password=self.pwd_context.hash("admin123"),  # Same password for testing
                    role=UserRole.AGENT,
                    phone=f"(555) {username[-1]}00-000{username[-1]}",
                    territory=territory,
                    badges=["New Agent"],
                    total_points=250,
                    level=1
                )
                self.db.add(agent)
                print(f"   👤 Created agent: {username} / admin123 ({territory})")
        
        # Create a manager
        manager_exists = self.db.query(User).filter(User.username == "manager").first()
        if not manager_exists:
            manager = User(
                email="manager@curagenesis.com",
                username="manager",
                full_name="Sales Manager",
                hashed_password=self.pwd_context.hash("admin123"),
                role=UserRole.MANAGER,
                phone="(555) 999-0001",
                territory="All",
                badges=["Manager", "Team Leader"],
                total_points=750,
                level=2
            )
            self.db.add(manager)
            print("   👔 Created manager: manager / admin123")
        
        self.db.commit()
        print("   ✅ User creation completed!")
    
    def migrate_leads(self):
        """Import leads from hot_leads.json"""
        print("📋 Starting lead migration...")
        
        # Load existing leads
        leads_file = Path(LEADS_FILE)
        if not leads_file.exists():
            print(f"   ❌ Lead file not found: {LEADS_FILE}")
            return
        
        with open(leads_file, 'r') as f:
            lead_data = json.load(f)
        
        print(f"   📊 Found {len(lead_data)} leads to migrate")
        
        # Get agents for assignment
        agents = self.db.query(User).filter(User.role == UserRole.AGENT).all()
        agent_count = len(agents)
        
        migrated_count = 0
        updated_count = 0
        
        for i, lead_json in enumerate(lead_data):
            try:
                # Check if lead already exists (by NPI)
                existing_lead = None
                if lead_json.get('npi'):
                    existing_lead = self.db.query(Lead).filter(Lead.npi == lead_json.get('npi')).first()
                
                if existing_lead:
                    # Update existing lead
                    self.update_lead_from_json(existing_lead, lead_json)
                    updated_count += 1
                else:
                    # Create new lead
                    lead = self.create_lead_from_json(lead_json, i, agents, agent_count)
                    self.db.add(lead)
                    migrated_count += 1
                
                # Commit every 100 leads
                if (i + 1) % 100 == 0:
                    self.db.commit()
                    print(f"   📈 Processed {i + 1}/{len(lead_data)} leads...")
                    
            except Exception as e:
                print(f"   ⚠️ Error processing lead {i}: {e}")
                continue
        
        # Final commit
        self.db.commit()
        print(f"   ✅ Migration completed!")
        print(f"   📊 New leads: {migrated_count}")
        print(f"   🔄 Updated leads: {updated_count}")
        
    def create_lead_from_json(self, lead_json, index, agents, agent_count):
        """Create a new Lead object from JSON data"""
        
        # Map priority
        priority_map = {
            "A+ Priority": "A+",
            "A Priority": "A", 
            "B+ Priority": "B+",
            "B Priority": "B",
            "C Priority": "C"
        }
        
        # Map status based on score
        score = lead_json.get('score', 0)
        if score >= 90:
            status = LeadStatus.NEW
        elif score >= 70:
            status = LeadStatus.NEW
        else:
            status = LeadStatus.NEW
        
        # Clean ZIP code
        zip_code = str(lead_json.get('zip', '')).split('.')[0] if lead_json.get('zip') else None
        
        lead = Lead(
            # Original NPPES Data (preserved)
            npi=lead_json.get('npi'),
            ein=lead_json.get('ein'),
            practice_name=lead_json.get('practice_name'),
            owner_name=lead_json.get('owner_name'),
            practice_phone=self.clean_phone(lead_json.get('practice_phone')),
            owner_phone=self.clean_phone(lead_json.get('owner_phone')),
            specialties=lead_json.get('specialties') or lead_json.get('category'),
            providers=lead_json.get('providers', 1),
            city=lead_json.get('city'),
            state=lead_json.get('state'),
            zip_code=zip_code,
            address=lead_json.get('address'),
            entity_type=lead_json.get('entity_type'),
            is_sole_proprietor=lead_json.get('is_sole_proprietor'),
            
            # Scoring System (preserved)
            score=score,
            priority=priority_map.get(lead_json.get('priority'), 'C'),
            category=lead_json.get('category'),
            medicare_allograft_score=lead_json.get('medicare_allograft_score', 0),
            overlooked_opportunity_score=lead_json.get('overlooked_opportunity_score', 0),
            rural_verified_score=lead_json.get('rural_verified_score', 0),
            scoring_breakdown=lead_json.get('scoring_breakdown'),
            
            # CRM Enhancement Fields
            status=status,
            source="nppes_extraction",
            assigned_user_id=None,  # Will assign high-priority leads below
            
            # Lead Recycling System
            contact_attempts=0,
            times_recycled=0,
            previous_agents=[]
        )
        
        # Assign high-priority leads to agents (A+ and A priority)
        if lead.priority in ['A+', 'A'] and agents:
            agent = agents[index % agent_count]
            lead.assigned_user_id = agent.id
            lead.assigned_at = datetime.utcnow()
            lead.status = LeadStatus.CONTACTED
        
        return lead
    
    def update_lead_from_json(self, lead, lead_json):
        """Update existing lead with new data"""
        # Update key fields while preserving CRM data
        lead.score = lead_json.get('score', lead.score)
        lead.practice_phone = self.clean_phone(lead_json.get('practice_phone')) or lead.practice_phone
        lead.owner_phone = self.clean_phone(lead_json.get('owner_phone')) or lead.owner_phone
        
        # Update scoring if provided
        if lead_json.get('medicare_allograft_score'):
            lead.medicare_allograft_score = lead_json.get('medicare_allograft_score')
        if lead_json.get('overlooked_opportunity_score'):
            lead.overlooked_opportunity_score = lead_json.get('overlooked_opportunity_score')
        if lead_json.get('rural_verified_score'):
            lead.rural_verified_score = lead_json.get('rural_verified_score')
    
    def create_sample_data(self):
        """Create sample activities and achievements for demo"""
        print("🎮 Creating sample gamification data...")
        
        # Award some points to demo users
        agents = self.db.query(User).filter(User.role == UserRole.AGENT).all()
        for i, agent in enumerate(agents):
            # Give different point levels for demo
            bonus_points = [100, 250, 150, 300, 200][i % 5]
            agent.total_points += bonus_points
            
            # Add some sample badges
            if bonus_points > 200:
                if not agent.badges:
                    agent.badges = []
                agent.badges.extend(["High Performer", "Call Champion"])
        
        self.db.commit()
        print("   ✅ Sample data created!")
    
    def run_migration(self):
        """Run complete migration process"""
        print("🚀 Starting Cura Genesis CRM Migration")
        print("=" * 50)
        
        # Create tables
        print("🏗️ Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        print("   ✅ Database schema ready!")
        
        # Create users
        self.create_default_users()
        
        # Migrate leads
        self.migrate_leads()
        
        # Create sample data
        self.create_sample_data()
        
        # Summary
        total_users = self.db.query(User).count()
        total_leads = self.db.query(Lead).count()
        assigned_leads = self.db.query(Lead).filter(Lead.assigned_user_id.isnot(None)).count()
        
        print("\n🎉 Migration Complete!")
        print("=" * 50)
        print(f"👥 Total Users: {total_users}")
        print(f"📋 Total Leads: {total_leads}")
        print(f"🎯 Assigned Leads: {assigned_leads}")
        print("\n🔑 Login Credentials:")
        print("   👑 Admin: admin / admin123")
        print("   👔 Manager: manager / admin123") 
        print("   👤 Agents: agent1-agent5 / admin123")
        print("\n🌐 CRM Dashboard: http://localhost:8002/crm_dashboard.html")
        print("🔗 API Base: http://localhost:8001/")
        
        self.db.close()

def main():
    """Main migration function"""
    migrator = EnhancedLeadMigrator()
    
    try:
        migrator.run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if migrator.db:
            migrator.db.close()

if __name__ == "__main__":
    main() 