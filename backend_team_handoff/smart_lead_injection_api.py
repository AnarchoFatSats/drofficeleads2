#!/usr/bin/env python3
"""
API-Based Smart Lead Injection System - 3K Lead Upload
Uses the CRM's bulk import API instead of direct database access
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path

class APISmartLeadInjection:
    """API-based lead injection system for reliable uploads"""
    
    def __init__(self, base_url="https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod"):
        self.base_url = base_url
        self.auth_token = None
        self.headers = {"Content-Type": "application/json"}
        
        # Phase configuration 
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
        self.batch_size = 50  # API can handle larger batches efficiently
    
    def authenticate(self, username="admin", password="admin123"):
        """Authenticate with the CRM API"""
        print("🔐 Authenticating with CRM API...")
        
        auth_data = {"username": username, "password": password}
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json=auth_data,
            headers=self.headers
        )
        
        if response.status_code == 200:
            self.auth_token = response.json()["access_token"]
            self.headers["Authorization"] = f"Bearer {self.auth_token}"
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
    
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
    
    def transform_lead_for_api(self, source_lead):
        """Transform source lead data to API format"""
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
        
        return {
            'practice_name': source_lead.get('practice_name', 'Unknown Practice'),
            'owner_name': source_lead.get('owner_name', ''),
            'practice_phone': source_lead.get('practice_phone', ''),
            'owner_phone': source_lead.get('owner_phone', ''),
            'specialties': source_lead.get('specialties', ''),
            'city': source_lead.get('city', ''),
            'state': source_lead.get('state', ''),
            'zip_code': str(source_lead.get('zip', '')) if source_lead.get('zip') else '',
            'address': source_lead.get('address', ''),
            'providers': source_lead.get('providers', 1),
            'npi': str(source_lead.get('npi', '')) if source_lead.get('npi') else '',
            'ein': str(source_lead.get('ein', '')) if source_lead.get('ein') else '',
            'entity_type': source_lead.get('entity_type', 'Organization'),
            'score': score,
            'priority': priority,
            'category': source_lead.get('category', 'Medicare Prospect')
        }
    
    def upload_lead_batch(self, leads_batch):
        """Upload batch of leads to Lambda backend using POST endpoint to create new leads"""
        created = 0
        duplicates = 0
        errors = 0
        
        for lead in leads_batch:
            try:
                # Use POST to create new leads in Lambda backend
                response = requests.post(
                    f"{self.base_url}/api/v1/leads",
                    json={
                        "practice_name": lead.get("practice_name", ""),
                        "owner_name": lead.get("owner_name", ""),
                        "practice_phone": lead.get("practice_phone", ""),
                        "owner_phone": lead.get("owner_phone", ""),
                        "email": lead.get("email", ""),
                        "address": lead.get("address", ""),
                        "city": lead.get("city", ""),
                        "state": lead.get("state", ""),
                        "zip_code": lead.get("zip_code", ""),
                        "npi": lead.get("npi", ""),
                        "specialty": lead.get("specialty", ""),
                        "score": lead.get("score", 0),
                        "priority": lead.get("priority", "C"),
                        "status": "NEW",
                        "assigned_user_id": 3,  # Assign to agent1 by default
                        "est_revenue": lead.get("est_revenue", 0),
                        "tags": lead.get("tags", [])
                    },
                    headers=self.headers
                )
                
                if response.status_code == 201:
                    created += 1
                    print(f"✅ Created lead: {lead.get('practice_name', 'Unknown')}")
                elif response.status_code == 409:
                    duplicates += 1
                    print(f"⚠️ Duplicate: {lead.get('practice_name', 'Unknown')}")
                else:
                    errors += 1
                    print(f"❌ Error creating {lead.get('practice_name', 'Unknown')}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                errors += 1
                print(f"❌ Exception creating {lead.get('practice_name', 'Unknown')}: {e}")
        
        return {
            "created": created,
            "duplicates": duplicates,
            "errors": errors
        }
    
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
            return 0, 0, 0
        
        print(f"📋 Found {len(phase_leads)} qualifying leads for upload")
        
        # Transform leads for API
        api_leads = [self.transform_lead_for_api(lead) for lead in phase_leads]
        
        # Process in batches
        total_success = 0
        total_duplicates = 0
        total_errors = 0
        
        for i in range(0, len(api_leads), self.batch_size):
            batch = api_leads[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(api_leads) + self.batch_size - 1) // self.batch_size
            
            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} leads)...")
            
            batch_result = self.upload_lead_batch(batch)
            total_success += batch_result["created"]
            total_duplicates += batch_result["duplicates"]
            total_errors += batch_result["errors"]
            
            print(f"   ✅ Batch result: {batch_result['created']} created, {batch_result['duplicates']} duplicates, {batch_result['errors']} errors")
            
            # Brief pause between batches
            time.sleep(1)
        
        # Phase summary
        print(f"\n✅ {phase['name']} COMPLETE!")
        print(f"   Successfully uploaded: {total_success} leads")
        print(f"   Duplicates skipped: {total_duplicates}")
        print(f"   Errors: {total_errors}")
        print(f"   Success rate: {total_success/(len(phase_leads))*100:.1f}%")
        
        return total_success, total_duplicates, total_errors
    
    def get_current_lead_count(self):
        """Get current lead count from API"""
        try:
            response = requests.get(f"{self.base_url}/health", headers=self.headers)
            if response.status_code == 200:
                health_data = response.json()
                return health_data.get('database_stats', {}).get('total_leads', 0)
        except:
            pass
        return 0
    
    def execute_full_upload(self):
        """Execute the complete lead upload process"""
        print("🎯 API-BASED SMART LEAD INJECTION")
        print("=" * 60)
        print("Executing phased upload of high-quality Medicare prospects")
        
        # Authenticate
        if not self.authenticate():
            print("❌ Failed to authenticate")
            return
        
        # Load source data
        source_leads = self.load_source_leads()
        if not source_leads:
            print("❌ No source leads available")
            return
        
        # Get baseline stats
        initial_count = self.get_current_lead_count()
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
        
        final_count = self.get_current_lead_count()
        
        print(f"\n🎉 UPLOAD COMPLETE!")
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
        
        print(f"\n🚀 Your sales team now has {final_count} hot leads ready for dialing!")

def main():
    """Main execution function"""
    print("🏥 Cura Genesis CRM - API-Based Lead Injection")
    print("=" * 60)
    
    try:
        injector = APISmartLeadInjection()
        injector.execute_full_upload()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Upload interrupted by user")
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 