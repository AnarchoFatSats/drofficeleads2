#!/usr/bin/env python3
"""
Enhanced Smart Lead Injection System - 3K Lead Upload
Phased upload of 3,000 leads with intelligent scoring and distribution
"""

import sys
import json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import time

# Import our CRM models
sys.path.append('.')
from crm_main import User, Lead, LeadStatus, Base
from crm_lead_distribution import LeadDistributionService

# Production database configuration
DATABASE_URL = "postgresql://crmuser:CuraGenesis2024%21SecurePassword@cura-genesis-crm-db.c6ds4c4qok1n.us-east-1.rds.amazonaws.com:5432/cura_genesis_crm"

class SmartLeadInjection3K:
    """Enhanced lead injection system for 3K lead upload"""
    
    def __init__(self):
        print("🔗 Connecting to production database...")
        self.engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()
        
        # Test connection
        try:
            result = self.db.execute(text("SELECT COUNT(*) FROM leads"))
            current_leads = result.scalar()
            print(f"✅ Connected! Current leads in database: {current_leads}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
        
        self.distribution_service = LeadDistributionService(self.db)
        
        # Phase configuration for current upload (adjusted for available 100 leads)
        self.phases = {
            'phase_1': {
                'name': 'A+ Priority Leads',
                'score_min': 90,
                'score_max': 100,
                'target_count': 26,  # All available A+ leads
                'description': 'Premium Medicare Allograft targets'
            },
            'phase_2': {
                'name': 'A Priority Leads', 
                'score_min': 75,
                'score_max': 89,
                'target_count': 44,  # All available A leads
                'description': 'High-value prospects'
            },
            'phase_3': {
                'name': 'B Priority Leads',
                'score_min': 60,
                'score_max': 74,
                'target_count': 30,  # All available B leads
                'description': 'Quality prospects'
            }
        }
        
        # Batch processing configuration
        self.batch_size = 100  # Process leads in batches for better performance
        
    def load_source_leads(self, file_path='web/data/hot_leads.json'):
        """Load and analyze source lead data"""
        print(f"📁 Loading source leads from: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                leads = json.load(f)
            
            print(f"✅ Loaded {len(leads)} source leads")
            
            # Analyze score distribution
            scores = [lead.get('score', 0) for lead in leads]
            print(f"\n📊 Score Distribution Analysis:")
            print(f"   A+ (90-100): {len([s for s in scores if s >= 90])}")
            print(f"   A (75-89):   {len([s for s in scores if 75 <= s < 90])}")
            print(f"   B (60-74):   {len([s for s in scores if 60 <= s < 75])}")
            print(f"   C (40-59):   {len([s for s in scores if 40 <= s < 60])}")
            print(f"   Low (<40):   {len([s for s in scores if s < 40])}")
            
            return leads
            
        except Exception as e:
            print(f"❌ Failed to load source leads: {e}")
            return []
    
    def filter_leads_by_phase(self, leads, phase_key):
        """Filter leads for specific upload phase"""
        phase = self.phases[phase_key]
        
        filtered_leads = []
        for lead in leads:
            score = lead.get('score', 0)
            if phase['score_min'] <= score <= phase['score_max']:
                filtered_leads.append(lead)
        
        # Sort by score (highest first) and limit to target count
        filtered_leads.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return filtered_leads[:phase['target_count']]
    
    def check_duplicate_lead(self, lead_data):
        """Check if lead already exists in database"""
        # Check by practice phone (primary identifier)
        if lead_data.get('practice_phone'):
            existing = self.db.query(Lead).filter(
                Lead.practice_phone == lead_data['practice_phone']
            ).first()
            if existing:
                return True
        
        # Check by NPI if available
        if lead_data.get('npi'):
            existing = self.db.query(Lead).filter(
                Lead.npi == lead_data['npi']
            ).first()
            if existing:
                return True
                
        return False
    
    def transform_lead_data(self, source_lead):
        """Transform source lead data to CRM format"""
        # Determine priority letter from score
        score = source_lead.get('score', 0)
        if score >= 90:
            priority = 'A+'
        elif score >= 75:
            priority = 'A'
        elif score >= 60:
            priority = 'B'
        else:
            priority = 'C'
        
        # Fix boolean conversion for is_sole_proprietor
        sole_prop_value = source_lead.get('is_sole_proprietor', False)
        if isinstance(sole_prop_value, str):
            if sole_prop_value.lower() in ['true', '1', 'yes', 'y']:
                is_sole_proprietor = True
            elif sole_prop_value.lower() in ['false', '0', 'no', 'n']:
                is_sole_proprietor = False
            else:
                is_sole_proprietor = False  # Default for 'nan' or other values
        else:
            is_sole_proprietor = bool(sole_prop_value)
        
        return {
            'practice_name': source_lead.get('practice_name', 'Unknown Practice'),
            'owner_name': source_lead.get('owner_name', ''),
            'practice_phone': source_lead.get('practice_phone', ''),
            'owner_phone': source_lead.get('owner_phone', ''),
            'specialties': source_lead.get('specialties', ''),
            'city': source_lead.get('city', ''),
            'state': source_lead.get('state', ''),
            'zip_code': str(source_lead.get('zip', '')),
            'address': source_lead.get('address', ''),
            'providers': source_lead.get('providers', 1),
            'npi': str(source_lead.get('npi', '')) if source_lead.get('npi') else '',
            'ein': str(source_lead.get('ein', '')) if source_lead.get('ein') else '',
            'entity_type': source_lead.get('entity_type', 'Organization'),
            'is_sole_proprietor': is_sole_proprietor,
            
            # Scoring and priority
            'score': score,
            'priority': priority,
            'category': source_lead.get('category', 'Medicare Prospect'),
            
            # CRM metadata
            'status': LeadStatus.NEW,
            'source': 'nppes_extraction',  # Valid enum value
            'contact_attempts': 0,
            'times_recycled': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
            # Let SQLAlchemy handle default for previous_agents array
        }
    
    def inject_lead_batch(self, leads_batch):
        """Inject a batch of leads with error handling"""
        success_count = 0
        duplicate_count = 0
        error_count = 0
        
        for lead_data in leads_batch:
            try:
                # Check for duplicates
                if self.check_duplicate_lead(lead_data):
                    duplicate_count += 1
                    continue
                
                # Transform and create lead
                lead_info = self.transform_lead_data(lead_data)
                
                new_lead = Lead(**lead_info)
                self.db.add(new_lead)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"⚠️ Error processing lead {lead_data.get('practice_name', 'Unknown')}: {e}")
        
        # Commit batch
        try:
            self.db.commit()
            print(f"   ✅ Batch committed: {success_count} leads added")
        except Exception as e:
            self.db.rollback()
            error_count = len(leads_batch)
            success_count = 0
            print(f"   ❌ Batch commit failed: {e}")
        
        return success_count, duplicate_count, error_count
    
    def execute_phase_upload(self, phase_key, source_leads):
        """Execute upload for specific phase"""
        phase = self.phases[phase_key]
        
        print(f"\n🚀 STARTING {phase['name'].upper()}")
        print("=" * 60)
        print(f"Target: {phase['target_count']} leads (Score {phase['score_min']}-{phase['score_max']})")
        print(f"Description: {phase['description']}")
        
        # Filter leads for this phase
        phase_leads = self.filter_leads_by_phase(source_leads, phase_key)
        
        if not phase_leads:
            print(f"❌ No leads found for {phase['name']}")
            return
        
        print(f"📋 Found {len(phase_leads)} qualifying leads for upload")
        
        # Process in batches
        total_success = 0
        total_duplicates = 0
        total_errors = 0
        
        for i in range(0, len(phase_leads), self.batch_size):
            batch = phase_leads[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(phase_leads) + self.batch_size - 1) // self.batch_size
            
            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} leads)...")
            
            success, duplicates, errors = self.inject_lead_batch(batch)
            total_success += success
            total_duplicates += duplicates
            total_errors += errors
            
            # Brief pause between batches to avoid overwhelming the database
            time.sleep(0.5)
        
        # Phase summary
        print(f"\n✅ {phase['name']} COMPLETE!")
        print(f"   Successfully uploaded: {total_success} leads")
        print(f"   Duplicates skipped: {total_duplicates}")
        print(f"   Errors: {total_errors}")
        print(f"   Success rate: {total_success/(len(phase_leads))*100:.1f}%")
        
        return total_success, total_duplicates, total_errors
    
    def execute_full_3k_upload(self):
        """Execute the complete 3K lead upload process"""
        print("🎯 SMART LEAD INJECTION - 3K UPLOAD")
        print("=" * 60)
        print("Executing phased upload of 3,000 high-quality Medicare prospects")
        
        # Load source data
        source_leads = self.load_source_leads()
        if not source_leads:
            print("❌ No source leads available")
            return
        
        # Get baseline stats
        result = self.db.execute(text("SELECT COUNT(*) FROM leads"))
        initial_count = result.scalar()
        
        print(f"\n📊 BASELINE: {initial_count} leads currently in CRM")
        
        # Execute each phase
        phase_results = {}
        
        for phase_key in ['phase_1', 'phase_2', 'phase_3']:
            success, duplicates, errors = self.execute_phase_upload(phase_key, source_leads)
            phase_results[phase_key] = {
                'success': success,
                'duplicates': duplicates,
                'errors': errors
            }
            
            # Pause between phases
            if phase_key != 'phase_3':
                print(f"\n⏳ Pausing 3 seconds before next phase...")
                time.sleep(3)
        
        # Final summary
        total_uploaded = sum(r['success'] for r in phase_results.values())
        total_duplicates = sum(r['duplicates'] for r in phase_results.values())
        total_errors = sum(r['errors'] for r in phase_results.values())
        
        result = self.db.execute(text("SELECT COUNT(*) FROM leads"))
        final_count = result.scalar()
        
        print(f"\n🎉 3K UPLOAD COMPLETE!")
        print("=" * 60)
        print(f"📊 FINAL RESULTS:")
        print(f"   Initial leads: {initial_count}")
        print(f"   Final leads: {final_count}")
        print(f"   Net increase: {final_count - initial_count}")
        print(f"   Successfully uploaded: {total_uploaded}")
        print(f"   Duplicates skipped: {total_duplicates}")
        print(f"   Total errors: {total_errors}")
        
        print(f"\n🎯 PHASE BREAKDOWN:")
        for phase_key, results in phase_results.items():
            phase = self.phases[phase_key]
            print(f"   {phase['name']}: {results['success']} leads uploaded")
        
        # Trigger lead distribution update
        print(f"\n🔄 Updating lead distribution...")
        try:
            # Use the correct method name
            self.distribution_service.run_lead_recycling_check()
            print("✅ Lead distribution updated successfully")
        except Exception as e:
            print(f"⚠️ Lead distribution update failed: {e}")
        
        print(f"\n🚀 Your sales team now has {final_count} hot leads ready for dialing!")

def main():
    """Main execution function"""
    print("🏥 Cura Genesis CRM - Smart Lead Injection 3K")
    print("=" * 60)
    
    try:
        injector = SmartLeadInjection3K()
        injector.execute_full_3k_upload()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Upload interrupted by user")
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 