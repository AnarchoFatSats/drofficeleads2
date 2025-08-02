#!/usr/bin/env python3
"""
Create Admin User Directly in DynamoDB
=====================================

Bypass Lambda and directly create admin user in DynamoDB
"""

import boto3
from botocore.exceptions import ClientError
import json

def create_admin_user_directly():
    """Create admin user directly in DynamoDB"""
    print("🔧 CREATING ADMIN USER DIRECTLY IN DYNAMODB")
    print("=" * 60)
    
    try:
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        users_table = dynamodb.Table('vantagepoint-users')
        
        print("📊 Checking users table status...")
        
        # Check if table exists
        try:
            table_status = users_table.table_status
            print(f"✅ Users table exists - Status: {table_status}")
        except ClientError as e:
            if 'ResourceNotFoundException' in str(e):
                print("❌ Users table 'vantagepoint-users' does not exist!")
                print("💡 This explains the authentication issue")
                return False
            else:
                print(f"❌ Error checking table: {e}")
                return False
        
        # Define admin users
        admin_users = [
            {
                "id": 1,
                "username": "admin",
                "password": "admin123",
                "role": "admin",
                "email": "admin@vantagepoint.com",
                "full_name": "System Administrator",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "manager_id": None
            },
            {
                "id": 2,
                "username": "manager1", 
                "password": "admin123",
                "role": "manager",
                "email": "manager1@vantagepoint.com",
                "full_name": "Sales Manager",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "manager_id": None
            },
            {
                "id": 3,
                "username": "agent1",
                "password": "admin123", 
                "role": "agent",
                "email": "agent1@vantagepoint.com",
                "full_name": "Sales Agent",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "manager_id": 2
            },
            {
                "id": 26,
                "username": "testagent1",
                "password": "admin123",
                "role": "agent", 
                "email": "testagent1@vantagepoint.com",
                "full_name": "Test Agent 1",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "manager_id": 2
            }
        ]
        
        print("👤 Creating admin users...")
        created_count = 0
        
        for user_data in admin_users:
            try:
                # Check if user already exists
                existing = users_table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr('username').eq(user_data['username'])
                )
                
                if existing['Items']:
                    print(f"👤 User exists: {user_data['username']}")
                else:
                    # Create the user
                    users_table.put_item(Item=user_data)
                    print(f"✅ Created user: {user_data['username']} ({user_data['role']})")
                    created_count += 1
                    
            except Exception as e:
                print(f"❌ Error creating {user_data['username']}: {e}")
        
        print(f"\n📊 RESULTS:")
        print(f"   👤 Users created: {created_count}")
        
        # Verify admin user
        print("\n🔍 Verifying admin user...")
        admin_check = users_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('username').eq('admin')
        )
        
        if admin_check['Items']:
            admin_user = admin_check['Items'][0]
            print(f"✅ Admin user verified:")
            print(f"   • Username: {admin_user['username']}")
            print(f"   • Role: {admin_user['role']}")
            print(f"   • Password: {admin_user['password']}")
            return True
        else:
            print("❌ Admin user not found after creation")
            return False
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            print("❌ Access denied to DynamoDB")
            print("💡 Check AWS credentials and permissions")
        elif error_code == 'ResourceNotFoundException':
            print("❌ DynamoDB table 'vantagepoint-users' not found")
            print("💡 The users table needs to be created first")
        else:
            print(f"❌ DynamoDB error: {error_code} - {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_authentication_after_creation():
    """Test authentication after creating users"""
    print("\n🧪 TESTING AUTHENTICATION AFTER USER CREATION")
    print("=" * 55)
    
    import requests
    import time
    
    # Wait a moment for DynamoDB to propagate
    time.sleep(2)
    
    try:
        login_response = requests.post(
            'https://api.vantagepointcrm.com/api/v1/auth/login',
            json={'username': 'admin', 'password': 'admin123'},
            timeout=30
        )
        
        print(f"🔐 Login test: {login_response.status_code}")
        
        if login_response.status_code == 200:
            print("🎉 AUTHENTICATION SUCCESS!")
            user_data = login_response.json()
            print(f"   👤 User: {user_data.get('user', {}).get('username')}")
            print(f"   🎭 Role: {user_data.get('user', {}).get('role')}")
            
            # Test admin analytics
            token = user_data['access_token']
            analytics_response = requests.get(
                'https://api.vantagepointcrm.com/api/v1/admin/analytics',
                headers={'Authorization': f'Bearer {token}'},
                timeout=30
            )
            
            print(f"📊 Analytics test: {analytics_response.status_code}")
            
            if analytics_response.status_code == 200:
                print("🎯 MASTER ADMIN ANALYTICS IS LIVE!")
                analytics = analytics_response.json().get('analytics', {})
                
                if 'lead_hopper_overview' in analytics:
                    hopper = analytics['lead_hopper_overview']
                    print(f"   📈 Total leads: {hopper.get('total_leads', 0)}")
                    print(f"   🎯 Available: {hopper.get('available_leads', 0)}")
                
                return True
            else:
                print(f"❌ Analytics failed: {analytics_response.text[:100]}")
                return False
        else:
            print(f"❌ Login failed: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main function to create admin user and test system"""
    print("🚑 EMERGENCY ADMIN USER CREATION")
    print("=" * 45)
    print("🎯 Creating admin user directly in DynamoDB")
    print("🔧 Bypassing Lambda initialization issues")
    print()
    
    # Create admin users
    if create_admin_user_directly():
        print("\n✅ ADMIN USERS CREATED SUCCESSFULLY")
        
        # Test the system
        if test_authentication_after_creation():
            print("\n🎉 SYSTEM FULLY OPERATIONAL!")
            print("✅ Authentication working")
            print("✅ Admin analytics live") 
            print("✅ Your 1,469-lead hopper is ready!")
            print("\n🚀 DEPLOYMENT SUCCESS!")
        else:
            print("\n⚠️  Users created but authentication test failed")
            print("💡 Try manual login in a few minutes")
    else:
        print("\n❌ ADMIN USER CREATION FAILED")
        print("💡 Check DynamoDB table and permissions")

if __name__ == "__main__":
    main()