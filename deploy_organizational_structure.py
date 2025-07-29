#!/usr/bin/env python3
"""
🏢 Deploy Organizational Structure Feature
Adds organizational tree view for admins to see manager/agent hierarchy
"""

import boto3
import zipfile
import json
import os
import shutil
from datetime import datetime

def deploy_organizational_structure():
    """Deploy organizational structure feature to production"""
    
    print("🚀 DEPLOYING ORGANIZATIONAL STRUCTURE FEATURE")
    print("=" * 60)
    
    # 1. Create Lambda deployment package
    print("📦 Creating Lambda deployment package...")
    
    # Create deployment zip
    zip_filename = 'lambda_org_structure_deployment.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add main lambda function
        zipf.write('lambda_function.py', 'lambda_function.py')
        
        # Add JWT dependencies if they exist
        if os.path.exists('jwt'):
            for root, dirs, files in os.walk('jwt'):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, file_path)
    
    print(f"✅ Lambda package created: {zip_filename}")
    
    # 2. Update Lambda function
    print("🔄 Updating Lambda function...")
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        with open(zip_filename, 'rb') as zip_file:
            lambda_client.update_function_code(
                FunctionName='vantagepoint-crm-api',
                ZipFile=zip_file.read()
            )
        print("✅ Lambda function updated successfully")
        
    except Exception as e:
        print(f"❌ Lambda update failed: {e}")
        return False
    
    # 3. Update backend handoff files
    print("📋 Updating backend handoff files...")
    
    try:
        # Copy lambda function to backend handoff
        shutil.copy2('lambda_function.py', 'backend_team_handoff/lambda_function.py')
        
        # Copy frontend files to backend handoff
        shutil.copy2('aws_deploy/index.html', 'backend_team_handoff/aws_deploy/index.html')
        shutil.copy2('aws_deploy/login.html', 'backend_team_handoff/aws_deploy/login.html')
        
        print("✅ Backend handoff files updated")
        
    except Exception as e:
        print(f"❌ Backend handoff update failed: {e}")
        return False
    
    # 4. Test the new API endpoint
    print("🧪 Testing organizational structure API...")
    
    test_api_endpoint()
    
    # 5. Cleanup
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
        print(f"🧹 Cleaned up {zip_filename}")
    
    print("\n🎉 ORGANIZATIONAL STRUCTURE DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print("📊 NEW FEATURES ADDED:")
    print("   • Organizational structure API endpoint (/api/v1/organization)")
    print("   • Admin can view manager/agent hierarchy")
    print("   • Clickable expandable manager trees")
    print("   • Team stats for each manager (leads, sales, conversion)")
    print("   • Individual agent stats (leads, sales, email, status)")
    print("   • Unassigned agents section with warnings")
    print("   • Company-wide overview with totals")
    print("")
    print("🔐 CREDENTIALS REFERENCE:")
    print("   👑 Admin:    admin / admin123")
    print("   👨‍💼 Manager:  manager1 / admin123") 
    print("   👤 Agent:    agent1 / admin123")
    print("")
    print("🏢 HOW TO ACCESS:")
    print("   1. Login as admin")
    print("   2. Organizational Structure section appears automatically")
    print("   3. Click on managers to expand and see their agent trees")
    print("   4. View team performance metrics and individual agent stats")
    
    return True

def test_api_endpoint():
    """Test the new organizational structure API"""
    import urllib3
    import time
    
    # Wait a moment for Lambda to update
    print("⏳ Waiting for Lambda to update...")
    time.sleep(3)
    
    try:
        # Test login first to get token
        http = urllib3.PoolManager()
        
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
        
        if login_response.status == 200:
            login_data = json.loads(login_response.data.decode('utf-8'))
            token = login_data.get('access_token')
            
            if token:
                # Test organizational structure endpoint
                org_response = http.request(
                    'GET',
                    'https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod/api/v1/organization',
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if org_response.status == 200:
                    org_data = json.loads(org_response.data.decode('utf-8'))
                    print(f"✅ Organizational API working! Found {org_data.get('total_managers', 0)} managers, {org_data.get('total_agents', 0)} agents")
                else:
                    print(f"❌ Organizational API test failed: {org_response.status}")
            else:
                print("❌ No token received from login")
        else:
            print(f"❌ Login test failed: {login_response.status}")
            
    except Exception as e:
        print(f"⚠️ API test failed: {e}")

if __name__ == "__main__":
    deploy_organizational_structure() 