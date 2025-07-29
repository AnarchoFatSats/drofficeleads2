#!/usr/bin/env python3
"""
🔍 Basic System Check for VantagePoint CRM
"""

import json
import urllib3

def check_basic_system():
    """Check basic system functionality"""
    
    print("🔍 BASIC VANTAGEPOINT CRM SYSTEM CHECK")
    print("=" * 50)
    
    try:
        http = urllib3.PoolManager()
        
        # Test login with known accounts
        accounts_to_test = [
            ("admin", "admin123", "👑 Admin"),
            ("manager1", "admin123", "👨‍💼 Manager"),
            ("agent1", "admin123", "👤 Agent")
        ]
        
        working_accounts = []
        
        for username, password, role_name in accounts_to_test:
            print(f"Testing {role_name}: {username}")
            
            login_data = {
                "username": username,
                "password": password
            }
            
            login_response = http.request(
                'POST',
                'https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod/api/v1/auth/login',
                body=json.dumps(login_data),
                headers={'Content-Type': 'application/json'}
            )
            
            if login_response.status == 200:
                login_result = json.loads(login_response.data.decode('utf-8'))
                user_info = login_result.get('user', {})
                print(f"   ✅ {role_name} login successful")
                print(f"   📧 Email: {user_info.get('email', 'N/A')}")
                print(f"   👤 Full Name: {user_info.get('full_name', 'N/A')}")
                working_accounts.append((username, user_info))
            else:
                print(f"   ❌ {role_name} login failed: {login_response.status}")
            print()
        
        print("-" * 50)
        print(f"📊 WORKING ACCOUNTS: {len(working_accounts)} out of 3 default accounts")
        
        if len(working_accounts) == 3:
            print("✅ All default accounts are working")
        else:
            print("⚠️ Some default accounts may have issues")
        
        # Try to check if additional users might exist by testing some common usernames
        print("\n🔍 Checking for additional users...")
        common_usernames = ["agent2", "agent3", "manager2", "test", "demo", "user1", "sales1"]
        found_additional = []
        
        for test_username in common_usernames:
            login_data = {
                "username": test_username,
                "password": "admin123"  # Default password
            }
            
            login_response = http.request(
                'POST',
                'https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod/api/v1/auth/login',
                body=json.dumps(login_data),
                headers={'Content-Type': 'application/json'}
            )
            
            if login_response.status == 200:
                login_result = json.loads(login_response.data.decode('utf-8'))
                user_info = login_result.get('user', {})
                found_additional.append(test_username)
                print(f"   ✅ Found additional user: {test_username}")
                print(f"      Role: {user_info.get('role', 'N/A')}")
                print(f"      Email: {user_info.get('email', 'N/A')}")
        
        if found_additional:
            print(f"\n🎉 Found {len(found_additional)} additional users: {', '.join(found_additional)}")
            print("   These were created through the admin panel and are still active!")
        else:
            print("\n❌ No additional users found with common usernames and default password")
            print("   Either:")
            print("   • No additional users were created")
            print("   • They were created with custom passwords")
            print("   • They were lost due to Lambda restart")
        
        print("\n⚠️ IMPORTANT NOTES:")
        print("   • Users created through UI are stored in Lambda memory only")
        print("   • Lambda restarts periodically, losing in-memory data")
        print("   • Only hardcoded users in lambda_function.py persist")
        print("   • To make users permanent, they need to be added to the code")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_basic_system() 