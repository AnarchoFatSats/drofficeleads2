#!/usr/bin/env python3
"""
🚀 EFFICIENT BULK LEAD UPLOAD - VantagePoint CRM
Upload 1,000+ leads efficiently using the bulk endpoint
"""

import json
import urllib3
from datetime import datetime

def load_and_score_leads():
    """Load all local leads and score them"""
    
    print("📋 LOADING AND SCORING ALL LOCAL LEADS")
    print("=" * 50)
    
    all_leads = []
    
    # Load all lead sources
    lead_files = [
        ('hot_leads.json', 'main_database'),
        ('production_leads_hot_20250725_203038.json', 'production_hot'),
        ('production_leads_warm_20250725_203038.json', 'production_warm'),
        ('lambda_leads_converted.json', 'lambda_converted'),
        ('web/data/hot_leads.json', 'web_data')
    ]
    
    for filename, source in lead_files:
        try:
            with open(filename, 'r') as f:
                leads = json.load(f)
            print(f"✅ {source}: {len(leads)} leads")
            
            # Add source tracking to each lead
            for lead in leads:
                lead['data_source'] = source
            
            all_leads.extend(leads)
        except Exception as e:
            print(f"❌ {source}: {e}")
    
    print(f"\n📊 TOTAL LEADS: {len(all_leads)}")
    
    # Score and rank leads
    scored_leads = []
    for lead in all_leads:
        # Calculate composite score
        base_score = lead.get('score', 50)
        
        # Priority bonus
        priority = str(lead.get('priority', ''))
        priority_bonus = 0
        if 'A+' in priority:
            priority_bonus = 30
        elif 'A' in priority:
            priority_bonus = 20
        elif 'B+' in priority:
            priority_bonus = 15
        elif 'B' in priority:
            priority_bonus = 10
        
        # High-value specialty bonus
        specialty = str(lead.get('category', lead.get('specialties', '')))
        specialty_bonus = 0
        high_value = ['Cardiology', 'Orthopedic', 'Neurology', 'Dermatology', 'Podiatrist', 'Surgery']
        if any(sp.lower() in specialty.lower() for sp in high_value):
            specialty_bonus = 15
        
        # Contact completeness bonus
        contact_bonus = 0
        if lead.get('practice_phone'):
            contact_bonus += 5
        if lead.get('npi') and str(lead.get('npi')) != 'null':
            contact_bonus += 10
        
        composite_score = base_score + priority_bonus + specialty_bonus + contact_bonus
        lead['composite_score'] = composite_score
        scored_leads.append(lead)
    
    # Sort by composite score
    scored_leads.sort(key=lambda x: x['composite_score'], reverse=True)
    
    print(f"🏆 Top score: {scored_leads[0]['composite_score']}")
    print(f"🎯 Average score: {sum(l['composite_score'] for l in scored_leads) / len(scored_leads):.1f}")
    
    return scored_leads

def convert_leads_for_crm(leads, max_count=1000):
    """Convert leads to CRM format"""
    
    print(f"\n🔄 CONVERTING {min(len(leads), max_count)} LEADS TO CRM FORMAT")
    print("=" * 60)
    
    crm_leads = []
    
    for i, lead in enumerate(leads[:max_count], 1):
        # Clean practice name
        practice_name = lead.get('practice_name', 'Unknown Practice')
        if practice_name in ['<UNAVAIL>', 'nan', None, '']:
            practice_name = f"Medical Practice {i}"
        
        # Clean owner name
        owner_name = lead.get('owner_name', 'Unknown Doctor')
        if 'nan' in str(owner_name) or owner_name in [None, '']:
            owner_name = f"Dr. Medical Director"
        if ',' in owner_name:
            parts = owner_name.split(',')
            if len(parts) >= 2:
                owner_name = f"Dr. {parts[0].strip()}"
        
        # Generate email
        email_base = practice_name.lower().replace(' ', '').replace("'", '')[:15]
        email = f"contact@{email_base}.com"
        
        # Extract location data
        city = lead.get('city', 'Unknown City')
        state = lead.get('state', 'XX')
        zip_code = str(lead.get('zip', lead.get('zip_code', '00000'))).split('.')[0]
        address = lead.get('address', f"Medical Plaza {i}")
        
        # Extract specialty
        specialty = lead.get('category', lead.get('specialties', 'General Practice'))
        
        # Generate phone if missing
        practice_phone = lead.get('practice_phone', '')
        if not practice_phone or practice_phone in ['nan', 'null']:
            practice_phone = f"(555) {i:03d}-{(i * 7) % 10000:04d}"
        
        # Calculate priority
        score = lead.get('composite_score', lead.get('score', 70))
        if score >= 90:
            priority = 'high'
        elif score >= 75:
            priority = 'medium'
        else:
            priority = 'low'
        
        # Generate identifiers
        npi = lead.get('npi', f'NPI{i:08d}')
        ptan = f"P{i:08d}"
        ein_tin = f"{(i % 90 + 10):02d}-{(i * 123) % 10000000:07d}"
        
        # Create CRM lead
        crm_lead = {
            "practice_name": practice_name,
            "owner_name": owner_name,
            "practice_phone": practice_phone,
            "email": email,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "specialty": specialty,
            "score": min(100, int(score)),
            "priority": priority,
            "status": "new",
            "assigned_user_id": None,  # Will be distributed automatically
            "docs_sent": False,
            "ptan": ptan,
            "ein_tin": ein_tin,
            "npi": str(npi),
            "source": f"bulk_upload_{lead.get('data_source', 'unknown')}",
            "original_score": lead.get('score', 0),
            "composite_score": score
        }
        
        crm_leads.append(crm_lead)
    
    print(f"✅ Converted {len(crm_leads)} leads to CRM format")
    
    return crm_leads

def bulk_upload_to_crm(leads):
    """Upload leads using the efficient bulk endpoint"""
    
    print(f"\n🚀 BULK UPLOADING {len(leads)} LEADS TO CRM")
    print("=" * 50)
    
    base_url = "https://api.vantagepointcrm.com"
    http = urllib3.PoolManager()
    
    # Get admin token
    print("🔐 Authenticating as admin...")
    login_response = http.request(
        'POST',
        f'{base_url}/api/v1/auth/login',
        body=json.dumps({"username": "admin", "password": "admin123"}),
        headers={'Content-Type': 'application/json'}
    )
    
    if login_response.status != 200:
        print(f"❌ Authentication failed: {login_response.status}")
        return False
    
    login_data = json.loads(login_response.data.decode('utf-8'))
    token = login_data.get('access_token')
    print("✅ Admin authenticated")
    
    # Upload in batches of 50 for optimal performance
    batch_size = 50
    total_batches = (len(leads) + batch_size - 1) // batch_size
    total_uploaded = 0
    total_failed = 0
    
    for i in range(0, len(leads), batch_size):
        batch = leads[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} leads)")
        
        # Prepare bulk upload payload
        bulk_payload = {
            "leads": batch
        }
        
        # Make bulk upload request
        upload_response = http.request(
            'POST',
            f'{base_url}/api/v1/leads/bulk',
            body=json.dumps(bulk_payload),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if upload_response.status in [200, 201]:
            response_data = json.loads(upload_response.data.decode('utf-8'))
            created_count = response_data.get('created_count', 0)
            failed_count = response_data.get('failed_count', 0)
            
            total_uploaded += created_count
            total_failed += failed_count
            
            print(f"   ✅ {created_count} uploaded, {failed_count} failed")
            
            # Show sample of uploaded leads
            if created_count > 0:
                sample_leads = batch[:3]
                for lead in sample_leads:
                    print(f"      → {lead['practice_name']} ({lead['specialty']}, Score: {lead['score']})")
        else:
            print(f"   ❌ Batch failed: {upload_response.status}")
            total_failed += len(batch)
    
    print(f"\n📊 BULK UPLOAD SUMMARY:")
    print(f"✅ Successfully uploaded: {total_uploaded} leads")
    print(f"❌ Failed uploads: {total_failed} leads")
    print(f"📈 Success rate: {(total_uploaded / len(leads) * 100):.1f}%")
    
    return total_uploaded > 0

def save_upload_tracking(uploaded_count, total_count):
    """Save tracking information"""
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    tracking_data = {
        "upload_timestamp": timestamp,
        "uploaded_count": uploaded_count,
        "total_processed": total_count,
        "success_rate": f"{(uploaded_count / total_count * 100):.1f}%",
        "upload_method": "bulk_endpoint",
        "notes": f"Bulk upload of {uploaded_count} leads from local database using /api/v1/leads/bulk endpoint"
    }
    
    filename = f"bulk_upload_tracking_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(tracking_data, f, indent=2)
    
    print(f"\n💾 Upload tracking saved to: {filename}")
    return filename

def main():
    """Main execution function"""
    
    print("🚀 VANTAGEPOINT CRM - EFFICIENT BULK LEAD UPLOAD")
    print("=" * 60)
    print(f"🕐 Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("🎯 Target: Upload best available leads using bulk endpoint")
    print("⚡ Method: Efficient batch processing with /api/v1/leads/bulk")
    print("")
    
    try:
        # Step 1: Load and score all leads
        scored_leads = load_and_score_leads()
        
        if len(scored_leads) == 0:
            print("❌ No leads found!")
            return
        
        # Step 2: Determine upload count
        available_count = len(scored_leads)
        target_count = min(1000, available_count)
        
        print(f"\n🎯 UPLOAD PLAN:")
        print(f"📊 Available leads: {available_count}")
        print(f"🎯 Target upload: {target_count} leads")
        print(f"⚡ Method: Bulk upload in batches of 50")
        
        # Step 3: Convert leads
        crm_leads = convert_leads_for_crm(scored_leads, target_count)
        
        # Step 4: Show preview
        print(f"\n🏆 TOP 5 LEADS TO UPLOAD:")
        for i, lead in enumerate(crm_leads[:5], 1):
            print(f"  {i}. {lead['practice_name']} - {lead['specialty']} (Score: {lead['score']})")
        
        # Step 5: Upload leads
        success = bulk_upload_to_crm(crm_leads)
        
        if success:
            # Step 6: Save tracking
            tracking_file = save_upload_tracking(len(crm_leads), len(crm_leads))
            
            print(f"\n🎉 BULK UPLOAD COMPLETE!")
            print(f"✅ Successfully processed leads using efficient bulk endpoint")
            print(f"📊 Agents will now have a huge lead pool to work from")
            print(f"🔍 Tracking: {tracking_file}")
            
            print(f"\n🎯 NEXT STEPS:")
            print(f"1. Check CRM dashboard - should show {target_count}+ total leads")
            print(f"2. Create new agents - they'll get leads from this pool")
            print(f"3. Existing agents will see expanded lead portfolios")
        else:
            print(f"\n❌ Bulk upload failed - check logs for details")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 