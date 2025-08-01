#!/usr/bin/env python3
"""
🎯 Assign Leads to Agents - VantagePoint CRM
Distribute the 22 medical practice leads to agents according to the business rules
"""

import json
import urllib3

def assign_leads_to_agents():
    """Assign leads to agents according to business rules"""
    
    print("🎯 ASSIGNING LEADS TO AGENTS")
    print("=" * 50)
    print("📋 Business Rule: 20 leads per agent")
    print("👤 Agent1 (user_id: 3) should get 20 leads")
    print("📊 2 leads will remain unassigned for new agents")
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
    
    # Show current assignment status
    assigned_leads = [l for l in leads if l.get('assigned_user_id')]
    unassigned_leads = [l for l in leads if not l.get('assigned_user_id')]
    
    print(f"✅ Currently assigned: {len(assigned_leads)} leads")
    print(f"🆕 Currently unassigned: {len(unassigned_leads)} leads")
    
    # Assign first 20 unassigned leads to agent1 (user_id: 3)
    agent1_id = 3
    leads_to_assign = min(20, len(unassigned_leads))
    
    print(f"\n🎯 Assigning first {leads_to_assign} leads to Agent1 (user_id: {agent1_id})...")
    
    assigned_count = 0
    for i, lead in enumerate(unassigned_leads[:leads_to_assign]):
        lead_id = lead['id']
        
        # Update the lead assignment
        update_data = {
            "assigned_user_id": agent1_id,
            "status": "new"  # Ensure it's in 'new' status
        }
        
        update_response = http.request(
            'PUT',
            f'{base_url}/api/v1/leads/{lead_id}',
            body=json.dumps(update_data),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if update_response.status == 200:
            assigned_count += 1
            print(f"   ✅ Lead {lead_id}: {lead['practice_name']} → Agent1")
        else:
            print(f"   ❌ Lead {lead_id}: Failed to assign ({update_response.status})")
    
    print(f"\n📊 ASSIGNMENT SUMMARY:")
    print(f"✅ Successfully assigned: {assigned_count} leads to Agent1")
    print(f"🆕 Remaining unassigned: {len(unassigned_leads) - assigned_count} leads")
    
    # Verify the assignment
    print("\n🔍 Verifying lead assignment...")
    verify_response = http.request(
        'GET',
        f'{base_url}/api/v1/leads',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    )
    
    if verify_response.status == 200:
        verify_data = json.loads(verify_response.data.decode('utf-8'))
        verify_leads = verify_data.get('leads', [])
        
        agent1_leads = [l for l in verify_leads if l.get('assigned_user_id') == agent1_id]
        still_unassigned = [l for l in verify_leads if not l.get('assigned_user_id')]
        
        print(f"✅ Agent1 now has: {len(agent1_leads)} leads")
        print(f"🆕 Unassigned leads: {len(still_unassigned)} leads")
        
        if len(agent1_leads) >= 20:
            print("\n🎉 SUCCESS: Agent1 now has 20+ leads!")
            print("🎯 Agents will now see their full lead portfolio")
            
            # Show some examples
            print("\n📋 Sample leads assigned to Agent1:")
            for i, lead in enumerate(agent1_leads[:3]):
                print(f"   {i+1}. {lead['practice_name']} - {lead['specialty']}")
            if len(agent1_leads) > 3:
                print(f"   ... and {len(agent1_leads)-3} more leads!")
            
        else:
            print(f"⚠️ Agent1 only has {len(agent1_leads)} leads (expected 20+)")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Login as agent1 to see the full lead portfolio")
    print("2. Create new agents - they'll get leads from the unassigned pool")
    print("3. Each new agent should receive 20 leads automatically")

if __name__ == "__main__":
    assign_leads_to_agents() 