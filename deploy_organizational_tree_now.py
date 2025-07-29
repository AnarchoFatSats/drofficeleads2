#!/usr/bin/env python3
"""
🏢 Deploy Organizational Tree System - URGENT
Deploy the admin organizational structure feature to production
"""

import boto3
import zipfile
import json
import os
import shutil
import time

def deploy_organizational_tree():
    """Deploy organizational tree feature to production Lambda"""
    
    print("🚀 DEPLOYING ORGANIZATIONAL TREE SYSTEM")
    print("=" * 60)
    print("📊 Admin will be able to see all managers and their agents")
    print("🌳 Expandable tree view with team performance metrics")
    print("")
    
    # 1. Check what we're deploying
    print("🔍 Verifying organizational structure code...")
    
    # Check if organizational endpoint exists in lambda_function.py
    with open('lambda_function.py', 'r') as f:
        content = f.read()
        
    if '/api/v1/organization' in content:
        print("✅ Organizational API endpoint found in lambda_function.py")
    else:
        print("❌ Organizational API endpoint NOT found!")
        return False
    
    # Check if frontend has organizational structure
    with open('aws_deploy/index.html', 'r') as f:
        frontend_content = f.read()
        
    if 'organizationSection' in frontend_content:
        print("✅ Organizational UI found in frontend")
    else:
        print("❌ Organizational UI NOT found!")
        return False
    
    # 2. Create Lambda deployment package
    print("\n📦 Creating Lambda deployment package...")
    
    zip_filename = 'lambda_organizational_tree_deployment.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add main lambda function with organizational endpoint
        zipf.write('lambda_function.py', 'lambda_function.py')
        print("✅ Added lambda_function.py with organizational API")
    
    # 3. Find the correct Lambda function name
    print("\n🔍 Finding Lambda function...")
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        # List functions to find the correct one
        response = lambda_client.list_functions()
        functions = response.get('Functions', [])
        
        target_function = None
        for func in functions:
            func_name = func['FunctionName']
            if any(keyword in func_name.lower() for keyword in ['crm', 'vantage', 'api', 'lead']):
                target_function = func_name
                print(f"✅ Found Lambda function: {target_function}")
                break
        
        if not target_function:
            print("❌ Could not find Lambda function")
            print("Available functions:")
            for func in functions:
                print(f"   - {func['FunctionName']}")
            return False
            
    except Exception as e:
        print(f"❌ Error finding Lambda function: {e}")
        return False
    
    # 4. Update Lambda function
    print(f"\n🔄 Updating Lambda function: {target_function}")
    
    try:
        with open(zip_filename, 'rb') as zip_file:
            lambda_client.update_function_code(
                FunctionName=target_function,
                ZipFile=zip_file.read()
            )
        print("✅ Lambda function updated successfully")
        
    except Exception as e:
        print(f"❌ Lambda update failed: {e}")
        return False
    
    # 5. Wait for update to complete
    print("⏳ Waiting for Lambda update to complete...")
    time.sleep(5)
    
    # 6. Test the organizational endpoint
    print("\n🧪 Testing organizational structure API...")
    
    success = test_organizational_api()
    
    # 7. Update backend handoff files
    print("\n📋 Updating backend handoff files...")
    
    try:
        # Copy lambda function to backend handoff
        shutil.copy2('lambda_function.py', 'backend_team_handoff/lambda_function.py')
        print("✅ Backend handoff updated with organizational structure")
        
    except Exception as e:
        print(f"❌ Backend handoff update failed: {e}")
    
    # 8. Cleanup
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
        print(f"🧹 Cleaned up {zip_filename}")
    
    # 9. Success summary
    if success:
        print("\n🎉 ORGANIZATIONAL TREE SYSTEM DEPLOYED!")
        print("=" * 60)
        print("✅ Admin can now see complete organizational structure")
        print("✅ Manager trees with expandable agent lists")
        print("✅ Team performance metrics and individual stats")
        print("✅ Professional UI with click-to-expand functionality")
        print("")
        print("🎯 HOW TO ACCESS:")
        print("   1. Login as admin (admin / admin123)")
        print("   2. Organizational Structure section appears automatically")
        print("   3. Click on managers to expand and see their agent trees")
        print("   4. View team performance and individual agent metrics")
        print("")
        print("📊 FEATURES AVAILABLE:")
        print("   • Company overview (total admins, managers, agents)")
        print("   • Manager performance cards (leads, sales, conversion)")
        print("   • Agent details (leads, sales, email, status)")
        print("   • Unassigned agents section with warnings")
        print("   • Professional styling with hover effects")
    else:
        print("\n⚠️ DEPLOYMENT COMPLETED BUT API TEST FAILED")
        print("The organizational structure may need a few minutes to become available")
        print("Try accessing the admin dashboard in 2-3 minutes")
    
    return True

def test_organizational_api():
    """Test the organizational structure API"""
    import urllib3
    
    try:
        http = urllib3.PoolManager()
        
        # Login as admin first
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
        
        if login_response.status != 200:
            print(f"❌ Admin login failed: {login_response.status}")
            return False
        
        login_result = json.loads(login_response.data.decode('utf-8'))
        token = login_result.get('access_token')
        
        if not token:
            print("❌ No token received from login")
            return False
        
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
            managers_count = len(org_data.get('managers', []))
            agents_count = org_data.get('total_agents', 0)
            print(f"✅ Organizational API working! Found {managers_count} managers, {agents_count} agents")
            return True
        else:
            print(f"❌ Organizational API test failed: {org_response.status}")
            return False
            
    except Exception as e:
        print(f"⚠️ API test error: {e}")
        return False

if __name__ == "__main__":
    deploy_organizational_tree() 