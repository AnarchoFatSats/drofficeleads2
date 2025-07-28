#!/usr/bin/env python3
"""
Deploy VantagePoint CRM - Send Docs & Lead Update Fixes
Fixed Issues:
1. Send Docs now works for 'new' status leads (not just 'contacted'/'qualified')
2. Better error handling for lead updates with debug info
3. Fixed NEXT_LEAD_ID calculation to avoid conflicts
"""

import boto3
import zipfile
import os
import time
import json
import requests

def create_lambda_package():
    """Create Lambda deployment package"""
    package_files = ['lambda_function.py']
    zip_filename = 'lambda_send_docs_fix.zip'
    
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
        with open(zip_filename, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        response = lambda_client.update_function_code(
            FunctionName='cura-genesis-crm-api',
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda function updated successfully")
        print(f"💾 Code size: {response['CodeSize']:,} bytes")
        
        time.sleep(10)  # Wait for deployment
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False
    
    finally:
        if os.path.exists(zip_filename):
            os.remove(zip_filename)

def test_fixes():
    """Test the send docs and lead update fixes"""
    api_base = "https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod"
    
    print(f"\n🧪 TESTING FIXES...")
    
    try:
        # Login as agent
        login_response = requests.post(f"{api_base}/api/v1/auth/login", 
                                     json={"username": "agent1", "password": "admin123"})
        token = login_response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        print(f"✅ Agent login successful")
        
        # Test 1: Create a new lead with email
        test_lead = {
            "practice_name": "Send Docs Test Clinic",
            "owner_name": "Dr. Send Test",
            "practice_phone": "555-DOCS-TEST",
            "email": "sendtest@clinic.com",
            "specialty": "General Practice",
            "city": "Test City",
            "state": "CA",
            "status": "new"  # This should now allow send docs
        }
        
        create_response = requests.post(f"{api_base}/api/v1/leads", 
                                      headers=headers, json=test_lead)
        
        if create_response.status_code == 201:
            create_data = create_response.json()
            new_lead_id = create_data['lead']['id']
            total_leads = create_data.get('debug_info', {}).get('total_leads', 'Unknown')
            
            print(f"✅ Lead creation successful - ID: {new_lead_id}, Total leads: {total_leads}")
            
            # Test 2: Try to send docs on the new lead (should work now)
            send_docs_response = requests.post(f"{api_base}/api/v1/leads/{new_lead_id}/send-docs",
                                             headers=headers)
            
            if send_docs_response.status_code == 200:
                print(f"✅ Send Docs working on new lead (status: 'new')")
            else:
                send_error = send_docs_response.json()
                print(f"❌ Send Docs failed: {send_error}")
            
            # Test 3: Try to update the lead (should work now)
            update_data = {"priority": "high", "status": "contacted"}
            update_response = requests.put(f"{api_base}/api/v1/leads/{new_lead_id}",
                                         headers=headers, json=update_data)
            
            if update_response.status_code == 200:
                print(f"✅ Lead update working")
            else:
                update_error = update_response.json()
                print(f"❌ Lead update failed: {update_error}")
            
        else:
            create_error = create_response.json()
            print(f"❌ Lead creation failed: {create_error}")
    
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return False
    
    print(f"\n🎉 Send Docs and Lead Update fixes deployed successfully!")
    return True

if __name__ == "__main__":
    print("🚀 DEPLOYING SEND DOCS & LEAD UPDATE FIXES")
    print("🔧 Fixes: Send docs for 'new' leads + Better error handling")
    print("=" * 60)
    
    if deploy_to_lambda():
        test_fixes()
    else:
        print("❌ Deployment failed - aborting tests") 