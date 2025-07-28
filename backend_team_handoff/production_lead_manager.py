#!/usr/bin/env python3
"""
Production Lead Manager
Manages smart lead rotation between local database and production cloud system
Only keeps working set of leads in expensive production database
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

class ProductionLeadManager:
    """Manages lead rotation between local and production systems"""
    
    def __init__(self):
        # Local database (full lead repository)
        self.local_db_url = "postgresql://alexsiegel@localhost:5432/cura_genesis_crm"
        
        # Production database (working set only)
        # This would be your AWS RDS instance
        self.production_db_url = "postgresql://username:password@prod-rds-endpoint:5432/cura_genesis_crm_prod"
        
        # Working set limits (cost-effective)
        self.lead_limits = {
            'hot_leads': 500,     # A+ Priority (90-100 score)
            'warm_leads': 1500,   # A Priority (75-89 score)  
            'pipeline_leads': 3000 # B Priority (60-74 score)
        }
        
        # Refresh thresholds
        self.refresh_thresholds = {
            'hot_leads': 100,     # Refresh when < 100 hot leads remain
            'warm_leads': 500,    # Refresh when < 500 warm leads remain
            'pipeline_leads': 1000 # Refresh when < 1000 pipeline leads remain
        }
    
    def get_local_session(self):
        """Connect to local full database"""
        engine = create_engine(self.local_db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
    
    def get_production_session(self):
        """Connect to production working database"""
        engine = create_engine(self.production_db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
    
    def analyze_local_inventory(self):
        """Analyze what leads are available locally"""
        local_db = self.get_local_session()
        
        try:
            # Count available leads by priority
            inventory = {
                'A+_available': local_db.query(Lead).filter(
                    Lead.score >= 90,
                    Lead.status == LeadStatus.NEW
                ).count(),
                'A_available': local_db.query(Lead).filter(
                    Lead.score >= 75,
                    Lead.score < 90,
                    Lead.status == LeadStatus.NEW
                ).count(),
                'B_available': local_db.query(Lead).filter(
                    Lead.score >= 60,
                    Lead.score < 75,
                    Lead.status == LeadStatus.NEW
                ).count(),
                'total_available': local_db.query(Lead).filter(
                    Lead.status == LeadStatus.NEW
                ).count()
            }
            
            print("📊 LOCAL LEAD INVENTORY:")
            print(f"   A+ Priority (90-100): {inventory['A+_available']:,} leads")
            print(f"   A Priority (75-89):   {inventory['A_available']:,} leads")
            print(f"   B Priority (60-74):   {inventory['B_available']:,} leads")
            print(f"   Total Available:      {inventory['total_available']:,} leads")
            
            return inventory
            
        finally:
            local_db.close()
    
    def analyze_production_usage(self):
        """Analyze current production lead usage"""
        # For now, simulate production analysis
        # In real deployment, this would connect to AWS RDS
        
        usage = {
            'hot_leads_remaining': 75,      # < 100 threshold
            'warm_leads_remaining': 450,    # < 500 threshold  
            'pipeline_leads_remaining': 2800, # Above 1000 threshold
            'agents_active': 5,
            'leads_per_agent': 20,
            'utilization': 85  # % of leads being actively worked
        }
        
        print("\n📈 PRODUCTION USAGE ANALYSIS:")
        print(f"   Hot Leads Remaining:      {usage['hot_leads_remaining']} (Need Refresh: {usage['hot_leads_remaining'] < self.refresh_thresholds['hot_leads']})")
        print(f"   Warm Leads Remaining:     {usage['warm_leads_remaining']} (Need Refresh: {usage['warm_leads_remaining'] < self.refresh_thresholds['warm_leads']})")
        print(f"   Pipeline Leads Remaining: {usage['pipeline_leads_remaining']} (Need Refresh: {usage['pipeline_leads_remaining'] < self.refresh_thresholds['pipeline_leads']})")
        print(f"   Active Agents:            {usage['agents_active']}")
        print(f"   Lead Utilization:         {usage['utilization']}%")
        
        return usage
    
    def prepare_lead_batch(self, priority_tier, batch_size):
        """Prepare a batch of leads for production upload"""
        local_db = self.get_local_session()
        
        try:
            # Define score ranges for each tier
            score_ranges = {
                'hot': (90, 100),
                'warm': (75, 89),
                'pipeline': (60, 74)
            }
            
            min_score, max_score = score_ranges[priority_tier]
            
            # Get top leads in score range
            leads = local_db.query(Lead).filter(
                Lead.score >= min_score,
                Lead.score <= max_score,
                Lead.status == LeadStatus.NEW
            ).order_by(Lead.score.desc()).limit(batch_size).all()
            
            lead_batch = []
            for lead in leads:
                lead_data = {
                    'practice_name': lead.practice_name,
                    'owner_name': lead.owner_name,
                    'practice_phone': lead.practice_phone,
                    'owner_phone': lead.owner_phone,
                    'specialties': lead.specialties,
                    'city': lead.city,
                    'state': lead.state,
                    'zip_code': lead.zip_code,
                    'score': lead.score,
                    'priority': lead.priority,
                    'category': lead.category,
                    'source': 'production_batch',
                    'batch_date': datetime.utcnow().isoformat()
                }
                lead_batch.append(lead_data)
            
            print(f"✅ Prepared {len(lead_batch)} {priority_tier} leads (Score: {min_score}-{max_score})")
            return lead_batch
            
        finally:
            local_db.close()
    
    def upload_to_production(self, lead_batch, tier_name):
        """Upload lead batch to production database"""
        # For now, save to JSON for AWS deployment
        output_file = f"production_leads_{tier_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(lead_batch, f, indent=2)
        
        print(f"💾 Saved {len(lead_batch)} leads to {output_file}")
        print(f"   Ready for production deployment to AWS RDS")
        
        # In production, this would:
        # 1. Connect to AWS RDS
        # 2. Insert leads into production database
        # 3. Trigger lead distribution to agents
        # 4. Mark local leads as "deployed"
        
        return output_file
    
    def refresh_production_leads(self):
        """Main orchestration: Refresh production leads based on usage"""
        print("🔄 PRODUCTION LEAD REFRESH SYSTEM")
        print("=" * 60)
        
        # Analyze current state
        inventory = self.analyze_local_inventory()
        usage = self.analyze_production_usage()
        
        # Determine what needs refreshing
        refresh_needed = []
        
        if usage['hot_leads_remaining'] < self.refresh_thresholds['hot_leads']:
            refresh_needed.append(('hot', self.lead_limits['hot_leads']))
        
        if usage['warm_leads_remaining'] < self.refresh_thresholds['warm_leads']:
            refresh_needed.append(('warm', self.lead_limits['warm_leads']))
        
        if usage['pipeline_leads_remaining'] < self.refresh_thresholds['pipeline_leads']:
            refresh_needed.append(('pipeline', self.lead_limits['pipeline_leads']))
        
        if not refresh_needed:
            print("\n✅ No refresh needed - all tiers above threshold")
            return
        
        print(f"\n🔄 REFRESH NEEDED: {len(refresh_needed)} tiers")
        
        # Prepare and upload batches
        uploaded_files = []
        for tier, batch_size in refresh_needed:
            print(f"\n📦 Preparing {tier} leads batch...")
            lead_batch = self.prepare_lead_batch(tier, batch_size)
            
            if lead_batch:
                output_file = self.upload_to_production(lead_batch, tier)
                uploaded_files.append(output_file)
        
        print(f"\n🎉 REFRESH COMPLETE!")
        print(f"   Files ready for AWS deployment: {len(uploaded_files)}")
        for file in uploaded_files:
            print(f"   - {file}")
        
        return uploaded_files

def main():
    manager = ProductionLeadManager()
    
    print("🏭 PRODUCTION LEAD MANAGEMENT SYSTEM")
    print("=" * 50)
    print("Manages smart lead rotation to keep production costs low")
    print("while maintaining high-quality lead pipeline\n")
    
    # Run refresh analysis
    uploaded_files = manager.refresh_production_leads()
    
    print("\n💡 NEXT STEPS:")
    print("1. Deploy uploaded JSON files to AWS RDS")
    print("2. Update Lambda backend to use RDS instead of hardcoded leads")
    print("3. Set up automated refresh trigger (weekly/as needed)")
    print("4. Monitor lead utilization and adjust thresholds")

if __name__ == "__main__":
    main() 