#!/usr/bin/env python3
"""
👥 Check Current Users in VantagePoint CRM
Tests the live system to see what users currently exist
"""

import json
import urllib3
import time

def check_current_users():
    """Check what users currently exist in the system"""
    
    print("👥 CHECKING CURRENT USERS IN VANTAGEPOINT CRM")
    print("=" * 60)
    
    try:
        http = urllib3.PoolManager()
        
        # 1. Login as admin to get token
        print("🔐 Logging in as admin...")
        
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = http.request(
            'POST',
            'https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod/api/v1/auth/login',
            body=json.dumps(login_data),
            headers={'Content-Type': 'application/json'}
        )
        
        if login_response.status != 200:
            print(f"❌ Login failed: {login_response.status}")
            return
        
        login_result = json.loads(login_response.data.decode('utf-8'))
        token = login_result.get('access_token')
        
        if not token:
            print("❌ No token received from login")
            return
        
        print("✅ Login successful")
        
        # 2. Check organizational structure to see all users
        print("🏢 Fetching organizational structure...")
        
        org_response = http.request(
            'GET',
            'https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod/api/v1/organization',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if org_response.status != 200:
            print(f"❌ Organization fetch failed: {org_response.status}")
            return
        
        org_data = json.loads(org_response.data.decode('utf-8'))
        
        # 3. Display current users
        print("\n📊 CURRENT SYSTEM USERS:")
        print("-" * 40)
        
        total_users = 0
        
        # Show admins (we know admin exists but let's confirm)
        print(f"👑 ADMINS: {org_data.get('total_admins', 0)}")
        total_users += org_data.get('total_admins', 0)
        
        # Show managers
        managers = org_data.get('managers', [])
        print(f"👨‍💼 MANAGERS: {len(managers)}")
        total_users += len(managers)
        
        for manager in managers:
            print(f"   • {manager['full_name']} ({manager['username']})")
            print(f"     📧 {manager['email']}")
            print(f"     👥 {manager['agent_count']} agents")
            print(f"     📊 {manager['team_leads']} leads | {manager['team_sales']} sales | {manager['team_conversion_rate']}% conversion")
            print()
        
        # Show agents (including unassigned)
        total_agents = org_data.get('total_agents', 0)
        print(f"👤 AGENTS: {total_agents}")
        total_users += total_agents
        
        # Agents under managers
        for manager in managers:
            if manager.get('agents'):
                print(f"   Under {manager['full_name']}:")
                for agent in manager['agents']:
                    print(f"     • {agent['full_name']} ({agent['username']})")
                    print(f"       📧 {agent['email']}")
                    print(f"       📊 {agent['lead_count']} leads | {agent['sales_count']} sales")
                    status_icon = "🟢" if agent['is_active'] else "🔴"
                    print(f"       {status_icon} {'Active' if agent['is_active'] else 'Inactive'}")
                    print()
        
        # Unassigned agents
        unassigned = org_data.get('unassigned_agents', [])
        if unassigned:
            print("   ⚠️ UNASSIGNED AGENTS:")
            for agent in unassigned:
                print(f"     • {agent['full_name']} ({agent['username']})")
                print(f"       📧 {agent['email']}")
                print(f"       📊 {agent['lead_count']} leads | {agent['sales_count']} sales")
                status_icon = "🟢" if agent['is_active'] else "🔴"
                print(f"       {status_icon} {'Active' if agent['is_active'] else 'Inactive'}")
                print()
        
        print("-" * 40)
        print(f"📈 TOTAL USERS IN SYSTEM: {total_users}")
        
        # 4. Analysis
        print("\n🔍 ANALYSIS:")
        
        # Check if we have more than the 3 default users
        if total_users > 3:
            print(f"✅ Found {total_users - 3} additional users beyond the default 3")
            print("   These were created through the admin panel")
        else:
            print("ℹ️ Only the default 3 users found (admin, manager1, agent1)")
            print("   Either no additional users were created, or they were lost due to Lambda restart")
        
        # Warn about statelessness
        print("\n⚠️ IMPORTANT LIMITATION:")
        print("   • Lambda functions are STATELESS")
        print("   • Users created through UI are stored in MEMORY only")
        print("   • When Lambda restarts, additional users are LOST")
        print("   • Only hardcoded users (admin, manager1, agent1) persist")
        
        print("\n💡 RECOMMENDATIONS:")
        print("   1. For production: Implement persistent database (RDS, DynamoDB)")
        print("   2. For testing: Recreate users after Lambda restarts")
        print("   3. Current system: Only hardcoded users are permanent")

    except Exception as e:
        print(f"❌ Error checking users: {e}")

if __name__ == "__main__":
    check_current_users() 