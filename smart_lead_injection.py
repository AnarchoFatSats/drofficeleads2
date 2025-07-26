#!/usr/bin/env python3
"""
Smart Lead Injection System
Scores new incoming leads against existing database and injects qualified prospects
"""

import sys
import json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Import our CRM models
sys.path.append('.')
from crm_main import User, Lead, LeadStatus, Base
from crm_lead_distribution import LeadDistributionService

# Configuration
DATABASE_URL = "postgresql://alexsiegel@localhost:5432/cura_genesis_crm"

class SmartLeadInjection:
    """Intelligent lead scoring and injection system"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()
        self.distribution_service = LeadDistributionService(self.db)
        
        # Scoring thresholds based on your existing database
        self.score_thresholds = {
            'A+': 90,  # Must be 90+ to qualify (like your Podiatrist + Wound Care)
            'A': 75,   # High value prospects
            'B': 60,   # Good prospects
            'C': 40    # Standard prospects
        }
        
        # Specialty scoring weights (based on your Medicare Allograft system)
        self.specialty_scores = {
            'Podiatrist': 50,
            'Wound Care': 40, 
            'Mohs Surgery': 35,
            'Dermatology': 30,
            'Family Medicine': 25,
            'Internal Medicine': 20,
            'General Practice': 15
        }
        
        # Rural ZIP bonus (your rural targeting system)
        self.rural_bonus = 20
        
        # Multi-specialty bonus
        self.multi_specialty_bonus = 15
    
    def calculate_lead_score(self, new_lead_data):
        """Calculate score for new lead using your proven methodology"""
        score = 0
        priority = "C Priority"
        
        # Specialty scoring
        specialties = new_lead_data.get('specialties', '').split(',')
        specialty_scores = []
        
        for specialty in specialties:
            specialty = specialty.strip()
            if specialty in self.specialty_scores:
                specialty_scores.append(self.specialty_scores[specialty])
        
        if specialty_scores:
            score += max(specialty_scores)  # Base score from primary specialty
            
            # Multi-specialty bonus
            if len(specialty_scores) > 1:
                score += self.multi_specialty_bonus
            
            # A+ Priority: Podiatrist + Wound Care combination
            if 'Podiatrist' in specialties and any('Wound' in s for s in specialties):
                score += 30  # Special A+ bonus
                priority = "A+ Priority"
        
        # Rural location bonus
        if new_lead_data.get('is_rural', False):
            score += self.rural_bonus
        
        # Independent practice bonus (vs hospital-affiliated)
        if new_lead_data.get('is_independent', True):
            score += 10
        
        # Small practice bonus (1-5 providers)
        providers = new_lead_data.get('providers', 1)
        if 1 <= providers <= 5:
            score += 10
        
        # Determine priority based on final score
        if score >= self.score_thresholds['A+']:
            priority = "A+ Priority"
        elif score >= self.score_thresholds['A']:
            priority = "A Priority"
        elif score >= self.score_thresholds['B']:
            priority = "B Priority"
        
        return score, priority
    
    def should_inject_lead(self, score, priority):
        """Determine if lead qualifies for injection based on existing database standards"""
        # Only inject leads that meet your quality standards
        return score >= self.score_thresholds['B']  # 60+ score threshold
    
    def inject_qualified_lead(self, new_lead_data, score, priority):
        """Inject a qualified lead into the CRM system"""
        try:
            # Check for duplicates
            existing = self.db.query(Lead).filter(
                Lead.practice_phone == new_lead_data.get('practice_phone')
            ).first()
            
            if existing:
                print(f"⚠️ Duplicate lead found: {new_lead_data.get('practice_name')}")
                return False
            
            # Create new lead
            new_lead = Lead(
                practice_name=new_lead_data.get('practice_name'),
                owner_name=new_lead_data.get('owner_name'),
                practice_phone=new_lead_data.get('practice_phone'),
                owner_phone=new_lead_data.get('owner_phone'),
                specialties=new_lead_data.get('specialties'),
                city=new_lead_data.get('city'),
                state=new_lead_data.get('state'),
                zip_code=new_lead_data.get('zip_code'),
                address=new_lead_data.get('address'),
                providers=new_lead_data.get('providers', 1),
                
                # Scoring data
                score=score,
                priority=priority[0],  # A+, A, B, C
                category=new_lead_data.get('primary_specialty'),
                
                # CRM fields
                status=LeadStatus.NEW,
                source="smart_injection",
                contact_attempts=0,
                times_recycled=0,
                created_at=datetime.utcnow()
            )
            
            self.db.add(new_lead)
            self.db.commit()
            
            # Auto-assign to agent if high priority
            if priority in ["A+ Priority", "A Priority"]:
                self.distribution_service.assign_lead_to_best_agent(new_lead.id)
            
            print(f"✅ Injected: {new_lead.practice_name} - {priority} (Score: {score})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to inject lead: {e}")
            self.db.rollback()
            return False
    
    def process_new_leads_file(self, file_path):
        """Process a file of new leads and inject qualified ones"""
        print(f"🔍 Processing new leads from: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                new_leads = json.load(f)
        except:
            print(f"❌ Could not load file: {file_path}")
            return
        
        injected_count = 0
        total_processed = 0
        
        for lead_data in new_leads:
            total_processed += 1
            
            # Score the new lead
            score, priority = self.calculate_lead_score(lead_data)
            
            # Check if it qualifies for injection
            if self.should_inject_lead(score, priority):
                if self.inject_qualified_lead(lead_data, score, priority):
                    injected_count += 1
            else:
                print(f"⏭️ Skipped: {lead_data.get('practice_name')} - Score too low ({score})")
        
        print(f"\n📊 INJECTION SUMMARY:")
        print(f"   Processed: {total_processed} new leads")
        print(f"   Injected: {injected_count} qualified leads")
        print(f"   Success Rate: {injected_count/total_processed*100:.1f}%")
        
        # Trigger lead distribution for new leads
        if injected_count > 0:
            self.distribution_service.redistribute_leads()
            print(f"🔄 Lead distribution updated - new leads assigned to agents")

def main():
    print("🎯 Smart Lead Injection System")
    print("=" * 50)
    
    injector = SmartLeadInjection()
    
    # Example: Process new leads from NPPES quarterly update
    # injector.process_new_leads_file('new_nppes_leads.json')
    
    # Show current system stats
    print("\n📊 Current Lead Distribution:")
    stats = injector.distribution_service.get_system_lead_stats()
    print(f"   Total Leads: {stats['total_leads']}")
    print(f"   Available for Assignment: {stats['available_leads']}")
    print(f"   Active Agents: {stats['active_agents']}")
    print(f"   Distribution Health: {stats['distribution_health']}")

if __name__ == "__main__":
    main() 