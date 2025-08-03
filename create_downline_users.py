#!/usr/bin/env python3
"""
VantagePoint CRM - Downline User Creation Tool
==============================================
Create new agent accounts for your downline team

USAGE:
    python3 create_downline_users.py

This tool will:
1. Login as admin
2. Allow you to create multiple downline agents
3. Set custom usernames and passwords
4. Automatically assign leads (optional)
"""

import requests
import json

def create_downline_user():
    """Interactive tool to create downline users"""
    
    base_url = 'https://api.vantagepointcrm.com'
    
    print("🚀 VantagePoint CRM - Downline User Creation")
    print("=" * 50)
    
    # Login as admin
    print("🔐 Logging in as admin...")
    try:
        login_response = requests.post(f'{base_url}/api/v1/auth/login',
                                     json={'username': 'admin', 'password': 'admin123'},
                                     timeout=15)
        
        if login_response.status_code != 200:
            print(f"❌ Admin login failed: {login_response.text}")
            return
        
        token = login_response.json()['access_token']
        print("✅ Admin authenticated successfully")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Create users interactively
    while True:
        print("\n" + "="*50)
        print("👤 CREATE NEW DOWNLINE AGENT")
        print("="*50)
        
        # Get user input
        username = input("Enter username (or 'quit' to exit): ").strip()
        if username.lower() in ['quit', 'exit', 'q']:
            break
        
        password = input("Enter password (default: admin123): ").strip()
        if not password:
            password = 'admin123'
        
        full_name = input("Enter full name: ").strip()
        if not full_name:
            full_name = username.title()
        
        # Create user
        user_data = {
            'username': username,
            'password': password,
            'role': 'agent',
            'full_name': full_name
        }
        
        print(f"\n🔄 Creating user '{username}'...")
        
        try:
            create_response = requests.post(f'{base_url}/api/v1/users',
                                          json=user_data,
                                          headers={'Authorization': f'Bearer {token}'},
                                          timeout=15)
            
            if create_response.status_code == 201:
                response_data = create_response.json()
                user_info = response_data['user']
                
                print("✅ USER CREATED SUCCESSFULLY!")
                print(f"   👤 Username: {user_info['username']}")
                print(f"   🆔 User ID: {user_info['id']}")
                print(f"   🎯 Role: {user_info['role']}")
                print(f"   📧 Email: {user_info['email']}")
                print(f"   🔐 Password: {password}")
                
                # Test login
                print(f"\n🧪 Testing login for {username}...")
                test_login = requests.post(f'{base_url}/api/v1/auth/login',
                                         json={'username': username, 'password': password},
                                         timeout=15)
                
                if test_login.status_code == 200:
                    print("✅ Login test successful!")
                else:
                    print(f"❌ Login test failed: {test_login.text[:100]}")
                
            elif create_response.status_code == 400:
                error_data = create_response.json()
                if "already exists" in error_data.get('detail', ''):
                    print(f"❌ Username '{username}' already exists. Try a different username.")
                else:
                    print(f"❌ Creation failed: {error_data.get('detail', 'Unknown error')}")
            else:
                print(f"❌ Creation failed ({create_response.status_code}): {create_response.text[:150]}")
                
        except Exception as e:
            print(f"❌ Error creating user: {e}")
        
        # Ask if they want to create another
        continue_choice = input("\nCreate another user? (y/n): ").strip().lower()
        if continue_choice not in ['y', 'yes']:
            break
    
    print("\n🎉 Downline user creation session complete!")
    print("💡 Your new agents can now login to the VantagePoint CRM")
    print("🔗 Login URL: https://vantagepointcrm.com/index.html")

if __name__ == "__main__":
    create_downline_user()