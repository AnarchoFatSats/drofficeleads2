#!/usr/bin/env python3
"""
Fix Authentication - Add Admin User Initialization
================================================

Add the missing initialize_default_users function to fix authentication
"""

def create_user_initialization_code():
    """Create the user initialization code to add to Lambda function"""
    return '''
def initialize_default_users():
    """Initialize default users in DynamoDB if they don't exist"""
    default_users = [
        {
            "id": 1,
            "username": "admin",
            "password": "admin123",  # Plain text for current system
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
    
    try:
        # Check if users exist, create if they don't
        for user_data in default_users:
            existing_user = get_user_by_username(user_data["username"])
            if not existing_user:
                # Add user to DynamoDB
                users_table.put_item(Item=user_data)
                print(f"✅ Initialized default user: {user_data['username']}")
            else:
                print(f"👤 User exists: {user_data['username']}")
    except Exception as e:
        print(f"❌ Error initializing users: {e}")
'''

def fix_lambda_authentication():
    """Add user initialization to Lambda function"""
    print("🔧 FIXING AUTHENTICATION - ADDING ADMIN USER INITIALIZATION")
    print("=" * 70)
    
    # Read current Lambda function
    with open('lambda_package/lambda_function.py', 'r') as f:
        content = f.read()
    
    # Check if initialization already exists
    if 'initialize_default_users' in content:
        print("✅ User initialization already exists")
        return True
    
    # Add the initialization function after the get_user_by_id function
    user_init_code = create_user_initialization_code()
    
    # Find the right place to insert (after get_user_by_id function)
    insertion_point = content.find('def get_next_lead_ids_batch(count):')
    if insertion_point == -1:
        print("❌ Could not find insertion point")
        return False
    
    # Insert the user initialization function
    new_content = content[:insertion_point] + user_init_code + '\n\n' + content[insertion_point:]
    
    # Add initialization call in the lambda_handler (before endpoints)
    # Find the lambda_handler function
    handler_start = new_content.find('def lambda_handler(event, context):')
    if handler_start == -1:
        print("❌ Could not find lambda_handler function")
        return False
    
    # Find where to add the initialization call (after initial setup, before endpoints)
    health_endpoint = new_content.find('# Health check endpoint')
    if health_endpoint == -1:
        print("❌ Could not find health endpoint")
        return False
    
    # Add initialization call before health endpoint
    initialization_call = '''        # Initialize default users on first run
        initialize_default_users()
        
        '''
    
    new_content = new_content[:health_endpoint] + initialization_call + new_content[health_endpoint:]
    
    # Write the updated content
    with open('lambda_package/lambda_function.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Added user initialization to Lambda function")
    print("👤 Default users will be created on next deployment:")
    print("   • admin / admin123 (admin role)")
    print("   • manager1 / admin123 (manager role)") 
    print("   • agent1 / admin123 (agent role)")
    print("   • testagent1 / admin123 (agent role)")
    
    return True

def main():
    """Fix authentication by adding admin user initialization"""
    print("🚑 AUTHENTICATION FIX")
    print("=" * 30)
    print("🎯 Problem: Admin user doesn't exist in DynamoDB")
    print("🔧 Solution: Add user initialization to Lambda")
    print()
    
    if fix_lambda_authentication():
        print("\n🎉 AUTHENTICATION FIX COMPLETE!")
        print("✅ Lambda function updated with user initialization")
        print("📋 Next steps:")
        print("   1. Deploy updated Lambda function")
        print("   2. Test admin login")
        print("   3. Verify admin analytics access")
        print("\n🚀 Ready to redeploy!")
    else:
        print("\n❌ Authentication fix failed")
        print("📋 Manual intervention required")

if __name__ == "__main__":
    main()