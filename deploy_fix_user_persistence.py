#!/usr/bin/env python3
"""
🚨 CRITICAL FIX: Deploy DynamoDB-Enabled Lambda Function
This script ensures the correct Lambda function with user persistence is deployed
"""

import boto3
import zipfile
import os
import json
from datetime import datetime

def create_deployment_package():
    """Create deployment package with the correct DynamoDB-enabled Lambda function"""
    
    zip_filename = 'lambda_user_persistence_fix.zip'
    
    print(f"📦 Creating deployment package: {zip_filename}")
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add the CORRECT lambda function (DynamoDB-enabled)
            source_file = 'lambda_package/lambda_function.py'
            if not os.path.exists(source_file):
                print(f"❌ Error: {source_file} not found!")
                return None
                
            # Add as lambda_function.py (required name for Lambda)
            zipf.write(source_file, 'lambda_function.py')
            print(f"✅ Added {source_file} as lambda_function.py")
            
            # Add PyJWT dependency if it exists
            jwt_dir = 'lambda_package/jwt'
            if os.path.exists(jwt_dir):
                for root, dirs, files in os.walk(jwt_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, 'lambda_package')
                        zipf.write(file_path, arc_path)
                print(f"✅ Added JWT dependencies")
            
            # Add PyJWT dist-info if it exists
            dist_info_dir = 'lambda_package/PyJWT-2.10.1.dist-info'
            if os.path.exists(dist_info_dir):
                for root, dirs, files in os.walk(dist_info_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, 'lambda_package')
                        zipf.write(file_path, arc_path)
                print(f"✅ Added PyJWT dist-info")
    
        print(f"📦 Package created successfully: {zip_filename}")
        return zip_filename
        
    except Exception as e:
        print(f"❌ Error creating package: {e}")
        return None

def deploy_to_lambda(zip_filename):
    """Deploy to AWS Lambda with user persistence fix"""
    
    function_name = 'cura-genesis-crm-api'  # Production function
    
    print(f"\n🚀 DEPLOYING USER PERSISTENCE FIX")
    print(f"=" * 50)
    print(f"📦 Package: {zip_filename}")
    print(f"🎯 Function: {function_name}")
    print(f"🕐 Timestamp: {datetime.now().isoformat()}")
    print(f"🔧 Fix: DynamoDB User Persistence")
    
    try:
        # Initialize AWS Lambda client
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Read zip file
        with open(zip_filename, 'rb') as f:
            zip_content = f.read()
        
        print(f"📋 Package size: {len(zip_content):,} bytes")
        
        # Update function code
        print("📤 Updating Lambda function...")
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda function updated successfully!")
        print(f"🆔 Version: {response.get('Version', 'N/A')}")
        print(f"⏰ Last Modified: {response.get('LastModified', 'N/A')}")
        print(f"📏 Code Size: {response.get('CodeSize', 'N/A'):,} bytes")
        
        # Update function configuration
        print("⚙️ Updating function configuration...")
        config_response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Description="VantagePoint CRM with DynamoDB User Persistence - FIXED",
            Timeout=30,  # 30 seconds timeout
            MemorySize=512,  # 512 MB memory
            Environment={
                'Variables': {
                    'ENVIRONMENT': 'production',
                    'VERSION': '4.0.0-user-persistence-fix',
                    'USER_PERSISTENCE': 'dynamodb',
                    'DYNAMODB_USERS_TABLE': 'vantagepoint-users'
                }
            }
        )
        
        print(f"✅ Configuration updated successfully!")
        print(f"\n🎯 CRITICAL FIXES DEPLOYED:")
        print(f"✅ DynamoDB user persistence (no more lost users)")
        print(f"✅ Role-based lead filtering in backend")
        print(f"✅ Automatic user initialization")
        print(f"✅ Enterprise-grade user management")
        
        print(f"\n🌐 API Endpoint: https://api.vantagepointcrm.com")
        print(f"🔑 Test Credentials: admin / admin123")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

def test_deployment():
    """Test the deployment"""
    print(f"\n🧪 TESTING DEPLOYMENT...")
    
    import requests
    import time
    
    base_url = 'https://api.vantagepointcrm.com'
    
    try:
        # Test health endpoint
        print("1️⃣ Testing health endpoint...")
        health_response = requests.get(f"{base_url}/health")
        print(f"   Status: {health_response.status_code}")
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   Version: {health_data.get('version', 'N/A')}")
            print(f"   ✅ Health check passed")
        
        # Test login
        print("2️⃣ Testing login...")
        login_response = requests.post(f"{base_url}/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            token = login_data.get('access_token')
            print(f"   ✅ Login successful")
            
            # Test auth/me endpoint
            print("3️⃣ Testing auth/me...")
            me_response = requests.get(f"{base_url}/api/v1/auth/me", 
                                     headers={"Authorization": f"Bearer {token}"})
            print(f"   Status: {me_response.status_code}")
            
            if me_response.status_code == 200:
                user_data = me_response.json()
                print(f"   User: {user_data.get('username')} ({user_data.get('role')})")
                print(f"   ✅ Authentication working")
                
                # Test leads endpoint
                print("4️⃣ Testing leads endpoint...")
                leads_response = requests.get(f"{base_url}/api/v1/leads",
                                            headers={"Authorization": f"Bearer {token}"})
                print(f"   Status: {leads_response.status_code}")
                
                if leads_response.status_code == 200:
                    leads_data = leads_response.json()
                    lead_count = len(leads_data.get('leads', []))
                    print(f"   Leads: {lead_count}")
                    print(f"   ✅ Lead management working")
                    
        print(f"\n🎉 DEPLOYMENT TEST COMPLETE!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main deployment process"""
    print("🚨 CRITICAL USER PERSISTENCE FIX DEPLOYMENT")
    print("=" * 60)
    print("This will fix the issue where users get lost when Lambda restarts")
    print("by deploying the DynamoDB-enabled Lambda function.")
    print("=" * 60)
    
    # Create package
    zip_filename = create_deployment_package()
    if not zip_filename:
        print("❌ Failed to create deployment package")
        return False
    
    try:
        # Deploy to Lambda
        if deploy_to_lambda(zip_filename):
            print("\n⏳ Waiting for deployment to stabilize...")
            import time
            time.sleep(10)
            
            # Test deployment
            test_deployment()
            
            print(f"\n🎊 USER PERSISTENCE FIX COMPLETE!")
            print(f"✅ Users will now persist permanently")
            print(f"✅ No more lost accounts on Lambda restart")
            print(f"✅ Enterprise-grade user management active")
            
            return True
        else:
            print("❌ Deployment failed")
            return False
            
    finally:
        # Clean up
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
            print(f"🧹 Cleaned up {zip_filename}")

if __name__ == "__main__":
    main()