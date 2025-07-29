#!/usr/bin/env python3
"""
👥 Add Permanent Users to VantagePoint CRM
Helps add users directly to the lambda_function.py code so they persist
"""

import hashlib

def add_permanent_users():
    """Help add users permanently to the code"""
    
    print("👥 ADD PERMANENT USERS TO VANTAGEPOINT CRM")
    print("=" * 50)
    print("This script helps you add users directly to the code so they persist")
    print("through Lambda restarts.\n")
    
    # Example of how to add users
    print("📝 EXAMPLE: Adding a new agent")
    print("-" * 30)
    
    # Generate password hash for admin123
    password_hash = hashlib.sha256("admin123".encode()).hexdigest()
    
    user_template = f'''
    "agent2": {{
        "id": 4,
        "username": "agent2",
        "password_hash": "{password_hash}",  # admin123
        "role": "agent",
        "email": "agent2@vantagepoint.com",
        "full_name": "Sales Agent 2",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00Z",
        "manager_id": 2  # Assigned to manager1
    }}'''
    
    print("Add this to the USERS dictionary in lambda_function.py:")
    print(user_template)
    
    print("\n📝 STEPS TO ADD PERMANENT USERS:")
    print("1. Open lambda_function.py")
    print("2. Find the USERS = { section (around line 170)")
    print("3. Add new user entries before the closing }")
    print("4. Update NEXT_USER_ID to be higher than your highest user ID")
    print("5. Deploy the updated lambda function")
    
    print("\n💡 REMEMBER TO:")
    print("• Use unique IDs (4, 5, 6, etc.)")
    print("• Use unique usernames")
    print("• Set manager_id for agents (2 = manager1)")
    print("• Keep the same password_hash for 'admin123' password")
    
    print(f"\n🔑 PASSWORD HASH FOR 'admin123': {password_hash}")
    
    # Ask user what users they want to add
    print("\n❓ What users would you like me to help you add permanently?")
    print("Please provide:")
    print("• Username")
    print("• Role (admin/manager/agent)")
    print("• Full name")
    print("• Manager assignment (for agents)")
    
    return password_hash

if __name__ == "__main__":
    add_permanent_users() 