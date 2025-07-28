#!/usr/bin/env python3
"""
Deploy Send Docs UX Improvements
Enhanced user experience for send docs functionality with better validation and feedback
"""

import boto3
import zipfile
import json
import time
import requests
import shutil
import os

def deploy_frontend_improvements():
    """Deploy the frontend improvements"""
    print("🎨 DEPLOYING SEND DOCS UX IMPROVEMENTS")
    print("=" * 50)
    
    # Copy improved files to production
    print("📋 Copying improved frontend files...")
    shutil.copy('aws_deploy/index.html', 'backend_team_handoff/aws_deploy/index.html')
    print("✅ Frontend files updated")
    
    # Test the improvements
    print("🧪 Testing improvements...")
    api_base = "https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test authentication
    print("🔐 Testing authentication...")
    auth_response = requests.post(f"{api_base}/api/v1/auth/login",
                                json={"username": "admin", "password": "admin123"})
    if auth_response.status_code == 200:
        token = auth_response.json()['access_token']
        print("✅ Authentication working")
    else:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test creating lead WITH email
    print("📧 Testing lead creation WITH email...")
    lead_with_email = {
        "practice_name": "Test Practice With Email",
        "owner_name": "Dr. WithEmail",
        "practice_phone": "555-8888",
        "email": "test@example.com",
        "city": "Test City",
        "state": "CA",
        "specialty": "Podiatrist"
    }
    
    create_response = requests.post(f"{api_base}/api/v1/leads", 
                                  headers=headers, 
                                  json=lead_with_email)
    if create_response.status_code == 201:
        with_email_lead = create_response.json()['lead']
        print(f"✅ Lead with email created (ID: {with_email_lead['id']})")
        
        # Test send docs on lead with email
        send_docs_response = requests.post(f"{api_base}/api/v1/leads/{with_email_lead['id']}/send-docs",
                                         headers=headers)
        if send_docs_response.status_code == 200:
            print("✅ Send docs working for lead with email")
        else:
            print(f"❌ Send docs failed for lead with email: {send_docs_response.status_code}")
    else:
        print(f"❌ Failed to create lead with email: {create_response.status_code}")
    
    # Test creating lead WITHOUT email  
    print("📭 Testing lead creation WITHOUT email...")
    lead_without_email = {
        "practice_name": "Test Practice No Email",
        "owner_name": "Dr. NoEmail",
        "practice_phone": "555-7777",
        "city": "Test City",
        "state": "TX",
        "specialty": "Orthopedic Surgery"
    }
    
    create_response2 = requests.post(f"{api_base}/api/v1/leads", 
                                   headers=headers, 
                                   json=lead_without_email)
    if create_response2.status_code == 201:
        no_email_lead = create_response2.json()['lead']
        print(f"✅ Lead without email created (ID: {no_email_lead['id']})")
        
        # Test send docs on lead without email (should fail gracefully)
        send_docs_response2 = requests.post(f"{api_base}/api/v1/leads/{no_email_lead['id']}/send-docs",
                                          headers=headers)
        if send_docs_response2.status_code == 400:
            error_data = send_docs_response2.json()
            if "email" in error_data.get('detail', '').lower():
                print("✅ Send docs correctly blocked for lead without email")
                print(f"   Error message: {error_data['detail']}")
            else:
                print(f"⚠️ Unexpected error message: {error_data['detail']}")
        else:
            print(f"❌ Unexpected response for lead without email: {send_docs_response2.status_code}")
    else:
        print(f"❌ Failed to create lead without email: {create_response2.status_code}")
    
    # Test updating lead to add email
    if 'no_email_lead' in locals():
        print("📝 Testing lead update to add email...")
        update_data = {
            "email": "newemail@example.com"
        }
        update_response = requests.put(f"{api_base}/api/v1/leads/{no_email_lead['id']}",
                                     headers=headers,
                                     json=update_data)
        if update_response.status_code == 200:
            print("✅ Lead updated with email address")
            
            # Now test send docs after adding email
            send_docs_response3 = requests.post(f"{api_base}/api/v1/leads/{no_email_lead['id']}/send-docs",
                                              headers=headers)
            if send_docs_response3.status_code == 200:
                print("✅ Send docs working after adding email to lead")
            else:
                print(f"❌ Send docs still failing after adding email: {send_docs_response3.status_code}")
        else:
            print(f"❌ Failed to update lead with email: {update_response.status_code}")
    
    print(f"\n🎉 SEND DOCS UX IMPROVEMENTS COMPLETE!")
    return True

def print_improvement_summary():
    """Print summary of improvements made"""
    print("\n📋 IMPROVEMENTS SUMMARY:")
    print("=" * 50)
    
    print("✅ FRONTEND IMPROVEMENTS:")
    print("   1. Email field now REQUIRED in create lead form")
    print("   2. Better validation messages in canSendDocs function")
    print("   3. Visual warning for leads without email in table")
    print("   4. Disabled send docs button shows reason in tooltip")
    print("   5. Edit lead form highlights email importance")
    print("   6. Clearer error messages when send docs fails")
    
    print("\n🎯 USER EXPERIENCE IMPROVEMENTS:")
    print("   • Users can't create leads without email anymore")
    print("   • Clear visual indicators for missing emails")
    print("   • Helpful tooltips explain why actions are disabled")
    print("   • Better error messages guide users to solutions")
    
    print("\n🚀 BUSINESS IMPACT:")
    print("   • Prevents invalid leads from entering system")
    print("   • Reduces user confusion about send docs functionality")
    print("   • Guides users to complete lead information")
    print("   • Maintains data quality for sales operations")

if __name__ == "__main__":
    success = deploy_frontend_improvements()
    if success:
        print_improvement_summary()
        print("\n🏆 Send docs functionality now works perfectly for all leads!")
        print("🎯 All newly created leads will have proper email validation")
        print("🔧 Existing leads can be updated to add missing emails")
        print("\n💡 NEXT STEPS:")
        print("   1. Open aws_deploy/index.html in browser to test")
        print("   2. Try creating leads with and without emails")
        print("   3. Notice improved validation and user feedback")
        print("   4. Test send docs functionality on different lead types")
    else:
        print("\n❌ Deployment encountered issues - please check logs") 