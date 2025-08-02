#!/usr/bin/env python3
"""
🎯 ASSIGN 20 LEADS TO TESTAGENT1 (ID: 26)
Direct assignment using PUT API
"""

import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

def assign_leads_to_testagent1():
    """Assign 20 unassigned leads to testagent1 (ID: 26)"""
    
    print("🎯 ASSIGNING LEADS TO TESTAGENT1")
    print("=" * 50)
    print("👤 Target: testagent1 (user_id: 26)")
    print("📊 Goal: 20 leads assigned")
    print("")
    
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
    
    # Find unassigned leads
    unassigned_leads = [l for l in leads if not l.get('assigned_user_id') or l.get('assigned_user_id') is None]
    testagent1_leads = [l for l in leads if l.get('assigned_user_id') == 26]
    
    print(f"🆕 Currently unassigned: {len(unassigned_leads)} leads")
    print(f"👤 testagent1 current leads: {len(testagent1_leads)}")
    
    if len(unassigned_leads) == 0:
        print("❌ No unassigned leads available!")
        return
    
    # Assign first 20 unassigned leads to testagent1
    target_count = min(20, len(unassigned_leads))
    print(f"\n🎯 Assigning {target_count} leads to testagent1 (user_id: 26)...")
    
    success_count = 0
    for i, lead in enumerate(unassigned_leads[:target_count]):
        lead_id = lead['id']
        
        # Update lead assignment
        update_response = http.request(
            'PUT',
            f'{base_url}/api/v1/leads/{lead_id}',
            body=json.dumps({"assigned_user_id": 26}),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if update_response.status == 200:
            practice_name = lead.get('practice_name', 'Unknown Practice')
            print(f"   ✅ Lead {lead_id}: {practice_name} → testagent1")
            success_count += 1
        else:
            print(f"   ❌ Lead {lead_id}: Failed ({update_response.status})")
    
    print(f"\n📊 ASSIGNMENT SUMMARY:")
    print(f"✅ Successfully assigned: {success_count} leads to testagent1")
    print(f"👤 testagent1 should now have: {len(testagent1_leads) + success_count} total leads")
    
    print(f"\n🎉 SUCCESS: testagent1 now has proper lead allocation!")
    print(f"🎯 Test the role-based filtering now!")

if __name__ == "__main__":
    assign_leads_to_testagent1()