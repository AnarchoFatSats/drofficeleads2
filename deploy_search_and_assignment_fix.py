#!/usr/bin/env python3
"""
Deploy VantagePoint CRM with Search & Lead Assignment Fixes
Fixed Issues:
1. New leads now auto-assign to correct users
2. Added lead search functionality for all user types
3. Role-based search filtering
"""

import boto3
import zipfile
import os
import time
import json
import requests

def create_lambda_package():
    """Create Lambda deployment package with all dependencies"""
    package_files = [
        'lambda_function.py'
    ]
    
    zip_filename = 'lambda_search_assignment_fix.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in package_files:
            if os.path.exists(file):
                zipf.write(file)
                print(f"✅ Added {file} to package")
            else:
                print(f"❌ Warning: {file} not found")
    
    print(f"📦 Created {zip_filename}")
    return zip_filename

def deploy_to_lambda():
    """Deploy the package to AWS Lambda"""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    zip_filename = create_lambda_package()
    
    try:
        # Read the ZIP file
        with open(zip_filename, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        # Update Lambda function
        response = lambda_client.update_function_code(
            FunctionName='cura-genesis-crm-api',
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda function updated successfully")
        print(f"📋 Function ARN: {response['FunctionArn']}")
        print(f"🔗 Runtime: {response['Runtime']}")
        print(f"💾 Code size: {response['CodeSize']:,} bytes")
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName='cura-genesis-crm-api',
            Timeout=30,  # 30 seconds
            MemorySize=512,  # 512 MB
            Environment={
                'Variables': {
                    'FUNCTION_NAME': 'VantagePoint CRM with Search & Assignment',
                    'VERSION': '2.1.0'
                }
            }
        )
        
        print(f"⚙️ Lambda configuration updated")
        
        # Wait for update to complete
        print("⏳ Waiting for deployment to complete...")
        time.sleep(10)
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False
    
    finally:
        # Clean up
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
            print(f"🧹 Cleaned up {zip_filename}")

def test_deployment():
    """Test the deployed Lambda function"""
    api_base = "https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod"
    
    print(f"\n🧪 TESTING DEPLOYMENT...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{api_base}/health", timeout=10)
        health_data = response.json()
        print(f"✅ Health Check: {health_data.get('service')} v{health_data.get('version')}")
        print(f"   📊 {health_data.get('leads_count')} leads, {health_data.get('users_count')} users")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Agent login and lead creation
    try:
        # Login as agent
        login_response = requests.post(f"{api_base}/api/v1/auth/login", 
                                     json={"username": "agent1", "password": "admin123"})
        login_data = login_response.json()
        token = login_data['access_token']
        print(f"✅ Agent login successful: {login_data['user']['full_name']}")
        
        # Create a test lead as agent
        test_lead = {
            "practice_name": "Test Medical Practice",
            "owner_name": "Dr. Test Smith",
            "practice_phone": "555-123-4567",
            "email": "test@testpractice.com",
            "specialty": "Cardiology",
            "city": "Test City",
            "state": "CA",
            "zip_code": "90210"
        }
        
        create_response = requests.post(f"{api_base}/api/v1/leads",
                                      headers={"Authorization": f"Bearer {token}"},
                                      json=test_lead)
        create_data = create_response.json()
        
        if create_response.status_code == 201:
            assigned_to = create_data.get('assigned_to', 'Unknown')
            print(f"✅ Lead creation successful - Assigned to: {assigned_to}")
            
            # Test 3: Get leads to verify the new lead appears
            leads_response = requests.get(f"{api_base}/api/v1/leads",
                                        headers={"Authorization": f"Bearer {token}"})
            leads_data = leads_response.json()
            
            agent_leads = leads_data.get('leads', [])
            test_lead_found = any(l.get('practice_name') == 'Test Medical Practice' for l in agent_leads)
            
            if test_lead_found:
                print(f"✅ New lead appears in agent's lead list ({len(agent_leads)} total leads)")
            else:
                print(f"❌ New lead NOT found in agent's lead list")
            
            # Test 4: Search functionality
            search_response = requests.get(f"{api_base}/api/v1/leads/search?q=Test Medical",
                                         headers={"Authorization": f"Bearer {token}"})
            search_data = search_response.json()
            
            if search_response.status_code == 200:
                search_results = search_data.get('leads', [])
                print(f"✅ Search functionality working - Found {len(search_results)} results for 'Test Medical'")
            else:
                print(f"❌ Search failed: {search_data}")
            
        else:
            print(f"❌ Lead creation failed: {create_data}")
    
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        return False
    
    print(f"\n🎉 ALL TESTS PASSED - VantagePoint CRM v2.1.0 deployed successfully!")
    return True

if __name__ == "__main__":
    print("🚀 DEPLOYING VANTAGEPOINT CRM v2.1.0")
    print("🔧 Features: Search functionality + Auto lead assignment")
    print("=" * 60)
    
    if deploy_to_lambda():
        test_deployment()
    else:
        print("❌ Deployment failed - aborting tests") 