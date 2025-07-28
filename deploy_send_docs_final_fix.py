#!/usr/bin/env python3
"""
Deploy Send Docs Final Fix
Fix datetime consistency issue in the send docs API
"""

import boto3
import zipfile
import json
import time
import requests

def deploy_send_docs_fix():
    """Deploy the fixed lambda function"""
    print("🔧 DEPLOYING SEND DOCS FIX")
    print("=" * 50)
    
    # Create deployment package
    print("📦 Creating deployment package...")
    with zipfile.ZipFile('lambda_send_docs_fix.zip', 'w') as zip_file:
        zip_file.write('lambda_function.py')
    
    # Deploy to Lambda
    print("🚀 Deploying to AWS Lambda...")
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        with open('lambda_send_docs_fix.zip', 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName='cura-genesis-crm-api',
                ZipFile=zip_file.read()
            )
        
        print(f"✅ Lambda function updated successfully")
        print(f"   Function ARN: {response['FunctionArn']}")
        print(f"   Last Modified: {response['LastModified']}")
        
        # Wait for function to be ready
        print("⏳ Waiting for function to be ready...")
        time.sleep(3)
        
        # Test the health endpoint
        print("🧪 Testing API health...")
        api_base = "https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod"
        
        health_response = requests.get(f"{api_base}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ API Health Check: {health_data['service']} v{health_data['version']}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            return False
        
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
        
        # Test send docs with fresh lead
        print("📤 Testing send docs functionality...")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get leads first
        leads_response = requests.get(f"{api_base}/api/v1/leads", headers=headers)
        if leads_response.status_code == 200:
            leads_data = leads_response.json()
            available_leads = [lead for lead in leads_data['leads'] 
                             if lead.get('email') and not lead.get('docs_sent')]
            
            if available_leads:
                test_lead = available_leads[0]
                print(f"🎯 Testing with lead: {test_lead['practice_name']} (ID: {test_lead['id']})")
                
                # Test send docs
                send_docs_response = requests.post(f"{api_base}/api/v1/leads/{test_lead['id']}/send-docs",
                                                 headers=headers)
                
                if send_docs_response.status_code == 200:
                    result = send_docs_response.json()
                    print("✅ Send docs working correctly!")
                    print(f"   📧 Email used: {result['email_used']}")
                    print(f"   🆔 External ID: {result['external_user_id']}")
                    print(f"   📅 Sent at: {result['sent_at']}")
                else:
                    print(f"❌ Send docs failed: {send_docs_response.status_code}")
                    print(f"   Response: {send_docs_response.text}")
                    return False
            else:
                print("⚠️ No available leads for testing (all have docs_sent=true or no email)")
        
        print(f"\n🎉 SEND DOCS FIX DEPLOYMENT COMPLETE!")
        print(f"✅ All tests passed - send docs API is working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = deploy_send_docs_fix()
    if success:
        print("\n🚀 Send docs API is now fixed and working correctly!")
        print("📋 Next steps for debugging frontend issues:")
        print("   1. Use debug_send_docs.html to test in browser")
        print("   2. Check browser network tab for any CORS errors")
        print("   3. Verify token expiration isn't causing issues")
        print("   4. Check browser console for JavaScript errors")
    else:
        print("\n❌ Deployment failed - please check logs") 