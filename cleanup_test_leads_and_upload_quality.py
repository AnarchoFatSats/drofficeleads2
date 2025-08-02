#!/usr/bin/env python3
"""
🧹 CLEANUP TEST LEADS & UPLOAD HIGH-QUALITY PRACTICES
Remove generic "Medical Practice X" leads and replace with real practices
"""

import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

def cleanup_and_upgrade_leads():
    """Remove test leads and upload high-quality real practices"""
    
    print("🧹 CLEANUP TEST LEADS & UPGRADE TO QUALITY PRACTICES")
    print("=" * 60)
    
    base_url = "https://api.vantagepointcrm.com"
    http = urllib3.PoolManager()
    
    # Get admin token
    print("🔐 Getting admin authentication...")
    login_response = http.request(
        'POST',
        f'{base_url}/api/v1/auth/login',
        body=json.dumps({"username": "admin", "password": "admin123"}),
        headers={'Content-Type': 'application/json'}
    )
    
    if login_response.status != 200:
        print(f"❌ Login failed: {login_response.status}")
        return
    
    login_data = json.loads(login_response.data.decode('utf-8'))
    token = login_data.get('access_token')
    print("✅ Admin authenticated")
    
    # Get current leads
    print("\n📋 Getting current leads...")
    leads_response = http.request(
        'GET',
        f'{base_url}/api/v1/leads',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    )
    
    if leads_response.status != 200:
        print(f"❌ Failed to get leads: {leads_response.status}")
        return
    
    leads_data = json.loads(leads_response.data.decode('utf-8'))
    leads = leads_data.get('leads', [])
    
    print(f"📊 Total leads in system: {len(leads)}")
    
    # Identify test leads to remove
    test_leads = [l for l in leads if 
                  l['practice_name'].startswith('Medical Practice') or
                  l['practice_name'] == 'Unknown Practice' or
                  'TEST' in l['practice_name'].upper()]
    
    real_leads = [l for l in leads if l not in test_leads]
    
    print(f"❌ Test/Generic leads to remove: {len(test_leads)}")
    print(f"✅ Real practice leads to keep: {len(real_leads)}")
    
    # Delete test leads
    print(f"\n🗑️ Removing {len(test_leads)} test leads...")
    deleted_count = 0
    for lead in test_leads[:50]:  # Remove first 50 test leads
        lead_id = lead['id']
        
        delete_response = http.request(
            'DELETE',
            f'{base_url}/api/v1/leads/{lead_id}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if delete_response.status == 200:
            print(f"   ✅ Deleted: {lead['practice_name']} (ID: {lead_id})")
            deleted_count += 1
        else:
            print(f"   ❌ Failed to delete: {lead['practice_name']} (Status: {delete_response.status})")
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"✅ Deleted {deleted_count} test leads")
    print(f"✅ System now has higher quality lead data")
    
    # Load high-quality local leads for upload
    print(f"\n📋 LOADING HIGH-QUALITY LOCAL LEADS...")
    
    try:
        with open('hot_leads.json', 'r') as f:
            hot_leads = json.load(f)
        
        # Filter for highest quality practices only
        quality_leads = []
        unique_names = set()
        
        for lead in hot_leads:
            practice_name = lead.get('practice_name', '')
            
            # Skip if generic name or already seen
            if (practice_name.startswith('Medical Practice') or 
                practice_name in unique_names or
                practice_name == 'Unknown Practice' or
                '<UNAVAIL>' in practice_name):
                continue
                
            # Only include high-quality named practices
            if len(practice_name) > 10 and not practice_name.isdigit():
                unique_names.add(practice_name)
                quality_leads.append(lead)
                
                if len(quality_leads) >= 50:  # Upload top 50 quality leads
                    break
        
        print(f"🏆 Found {len(quality_leads)} high-quality unique practices to upload")
        
        # Show sample of what we're uploading
        print(f"\n📋 SAMPLE QUALITY PRACTICES TO UPLOAD:")
        for i, lead in enumerate(quality_leads[:10], 1):
            name = lead.get('practice_name', 'Unknown')
            specialty = lead.get('specialty', lead.get('specialties', 'Unknown'))
            print(f"   {i}. {name} - {specialty}")
        
        # Upload quality leads in batches
        print(f"\n🚀 UPLOADING {len(quality_leads)} QUALITY PRACTICES...")
        
        batch_size = 10
        uploaded_count = 0
        
        for i in range(0, len(quality_leads), batch_size):
            batch = quality_leads[i:i+batch_size]
            
            # Convert to CRM format
            crm_batch = []
            for lead in batch:
                crm_lead = {
                    "practice_name": lead.get('practice_name', 'Unknown Practice'),
                    "owner_name": lead.get('owner_name', ''),
                    "practice_phone": lead.get('practice_phone', lead.get('phone', '')),
                    "email": lead.get('email', ''),
                    "city": lead.get('city', ''),
                    "state": lead.get('state', ''),
                    "zip_code": lead.get('zip_code', ''),
                    "specialties": lead.get('specialty', lead.get('specialties', '')),
                    "score": lead.get('score', 100),
                    "priority": "high",
                    "status": "new",
                    "npi": lead.get('npi', ''),
                    "address": lead.get('address', '')
                }
                crm_batch.append(crm_lead)
            
            # Upload batch
            upload_response = http.request(
                'POST',
                f'{base_url}/api/v1/leads/bulk',
                body=json.dumps({"leads": crm_batch}),
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if upload_response.status == 200:
                batch_num = (i // batch_size) + 1
                print(f"   ✅ Batch {batch_num}: {len(batch)} quality practices uploaded")
                uploaded_count += len(batch)
            else:
                print(f"   ❌ Batch {batch_num}: Upload failed ({upload_response.status})")
        
        print(f"\n🎉 QUALITY UPGRADE COMPLETE:")
        print(f"✅ Removed {deleted_count} test leads")
        print(f"✅ Added {uploaded_count} high-quality real practices")
        print(f"📈 System now has better lead quality!")
        
    except Exception as e:
        print(f"❌ Error loading local leads: {e}")

if __name__ == "__main__":
    cleanup_and_upgrade_leads()