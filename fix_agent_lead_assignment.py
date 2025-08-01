#!/usr/bin/env python3
"""
🔧 AGENT LEAD ASSIGNMENT FIX
This script assigns leads to existing agents who don't have any leads assigned.
"""

import requests
import json

def main():
    """Fix lead assignment for existing agents"""
    
    base_url = 'https://api.vantagepointcrm.com'
    
    print("🔧 AGENT LEAD ASSIGNMENT FIX")
    print("=" * 50)
    
    # Login as admin
    print("1️⃣ Logging in as admin...")
    login_response = requests.post(f"{base_url}/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        return False
    
    admin_token = login_response.json()['access_token']
    print("✅ Admin login successful")
    
    # Get hopper stats
    print("2️⃣ Checking hopper statistics...")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    hopper_response = requests.get(f"{base_url}/api/v1/hopper/stats", headers=headers)
    
    if hopper_response.status_code == 200:
        hopper_data = hopper_response.json()
        stats = hopper_data['hopper_stats']
        print(f"📊 Total leads: {stats['total_leads']}")
        print(f"📊 Available in hopper: {stats['hopper_available']}")
        print(f"📊 Assigned active: {stats['assigned_active']}")
        print(f"📊 Max per agent: {stats['max_leads_per_agent']}")
    else:
        print(f"⚠️ Could not get hopper stats: {hopper_response.status_code}")
    
    # Check agent1's current leads
    print("3️⃣ Checking agent1's current leads...")
    agent1_login = requests.post(f"{base_url}/api/v1/auth/login", json={
        "username": "agent1",
        "password": "admin123"
    })
    
    if agent1_login.status_code == 200:
        agent1_token = agent1_login.json()['access_token']
        agent1_headers = {"Authorization": f"Bearer {agent1_token}"}
        
        agent1_leads = requests.get(f"{base_url}/api/v1/leads", headers=agent1_headers)
        if agent1_leads.status_code == 200:
            agent1_data = agent1_leads.json()
            current_leads = agent1_data['total_leads']
            print(f"📋 Agent1 currently has: {current_leads} leads")
            
            if current_leads == 0:
                print("🔧 Agent1 needs leads! Triggering assignment...")
                
                # Strategy: Create a temporary user which will trigger the hopper system
                # This will cause the hopper to redistribute leads and potentially assign some to agent1
                
                # First, let's try to create a dummy lead to trigger the system
                print("4️⃣ Creating trigger lead to activate hopper system...")
                
                trigger_lead = {
                    "practice_name": "TRIGGER - Lead Assignment Fix",
                    "owner_name": "System Trigger",
                    "practice_phone": "555-0000",
                    "email": "trigger@system.com",
                    "address": "123 System St",
                    "city": "System City",
                    "state": "SY",
                    "zip_code": "00000",
                    "specialty": "System",
                    "score": 1,
                    "priority": "low",
                    "status": "new"
                }
                
                create_response = requests.post(
                    f"{base_url}/api/v1/leads", 
                    headers=headers, 
                    json=trigger_lead
                )
                
                if create_response.status_code == 201:
                    print("✅ Trigger lead created")
                    
                    # Now check agent1's leads again
                    print("5️⃣ Rechecking agent1's leads...")
                    agent1_leads_after = requests.get(f"{base_url}/api/v1/leads", headers=agent1_headers)
                    if agent1_leads_after.status_code == 200:
                        new_data = agent1_leads_after.json()
                        new_count = new_data['total_leads']
                        print(f"📋 Agent1 now has: {new_count} leads")
                        
                        if new_count > current_leads:
                            print(f"🎉 SUCCESS! Agent1 gained {new_count - current_leads} leads")
                            return True
                        else:
                            print("⚠️ No leads were assigned. The hopper system may need manual intervention.")
                            
                            print("\n💡 SUGGESTED SOLUTIONS:")
                            print("1. Check if there are unassigned leads in the system")
                            print("2. Manually recycle expired leads using the admin panel")
                            print("3. Create more leads to populate the hopper")
                            
                            return False
                else:
                    print(f"❌ Failed to create trigger lead: {create_response.status_code}")
                    return False
            else:
                print(f"✅ Agent1 already has {current_leads} leads assigned")
                return True
        else:
            print(f"❌ Could not check agent1's leads: {agent1_leads.status_code}")
            return False
    else:
        print(f"❌ Agent1 login failed: {agent1_login.status_code}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎊 LEAD ASSIGNMENT FIX COMPLETED SUCCESSFULLY!")
    else:
        print("\n🔧 Manual intervention may be required. Check the admin panel for lead distribution.")