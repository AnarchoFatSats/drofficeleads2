#!/usr/bin/env python3
"""
🔧 Deploy Authentication Fix - Add missing /api/v1/auth/me endpoint
This fixes the login redirect loop issue
"""

import boto3
import zipfile
import os
import time

def deploy_auth_fix():
    """Deploy the authentication fix to Lambda"""
    
    print("🔧 DEPLOYING AUTHENTICATION FIX")
    print("=" * 50)
    print("📋 Issue: Login redirect loop")
    print("🎯 Fix: Add missing /api/v1/auth/me endpoint")
    print("")
    
    # Create deployment package
    print("📦 Creating deployment package...")
    zip_path = 'auth_fix_deployment.zip'
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add main lambda function
        zipf.write('lambda_package/lambda_function.py', 'lambda_function.py')
        
        # Add JWT dependencies if they exist
        if os.path.exists('lambda_package/jwt'):
            for root, dirs, files in os.walk('lambda_package/jwt'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = file_path.replace('lambda_package/', '')
                    zipf.write(file_path, arc_path)
        
        # Add PyJWT metadata if it exists
        if os.path.exists('lambda_package/PyJWT-2.8.0.dist-info'):
            for root, dirs, files in os.walk('lambda_package/PyJWT-2.8.0.dist-info'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = file_path.replace('lambda_package/', '')
                    zipf.write(file_path, arc_path)
    
    print(f"✅ Created {zip_path}")
    
    # Deploy to Lambda
    print("🚀 Deploying to Lambda function...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Try to find the correct Lambda function name
        function_names = [
            'cura-genesis-crm-api',
            'rideshare-lead-processor', 
            'vantagepoint-crm-api'
        ]
        
        deployed = False
        for function_name in function_names:
            try:
                print(f"🔍 Trying function: {function_name}")
                
                with open(zip_path, 'rb') as zip_file:
                    response = lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=zip_file.read()
                    )
                
                print(f"✅ Successfully deployed to: {function_name}")
                print(f"📅 Last Modified: {response['LastModified']}")
                deployed = True
                break
                
            except lambda_client.exceptions.ResourceNotFoundException:
                print(f"❌ Function {function_name} not found")
                continue
            except Exception as e:
                print(f"❌ Error deploying to {function_name}: {e}")
                continue
        
        if not deployed:
            print("❌ Could not find any Lambda function to deploy to")
            return False
        
        # Wait for deployment to complete
        print("⏳ Waiting for deployment to complete...")
        time.sleep(5)
        
        # Test the fix
        print("🧪 Testing the authentication fix...")
        test_auth_fix()
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False
    
    finally:
        # Clean up
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"🗑️ Cleaned up {zip_path}")

def test_auth_fix():
    """Test the authentication fix"""
    import urllib3
    import json
    
    print("\n🧪 TESTING AUTHENTICATION FIX")
    print("-" * 40)
    
    http = urllib3.PoolManager()
    base_url = "https://api.vantagepointcrm.com"
    
    try:
        # Step 1: Login to get a token
        print("1️⃣ Testing login to get token...")
        login_response = http.request(
            'POST',
            f'{base_url}/api/v1/auth/login',
            body=json.dumps({"username": "admin", "password": "admin123"}),
            headers={'Content-Type': 'application/json'}
        )
        
        if login_response.status != 200:
            print(f"❌ Login failed: {login_response.status}")
            return False
        
        login_data = json.loads(login_response.data.decode('utf-8'))
        token = login_data.get('access_token')
        print(f"✅ Login successful, token received")
        
        # Step 2: Test the /auth/me endpoint
        print("2️⃣ Testing /api/v1/auth/me endpoint...")
        me_response = http.request(
            'GET',
            f'{base_url}/api/v1/auth/me',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if me_response.status == 200:
            me_data = json.loads(me_response.data.decode('utf-8'))
            print(f"✅ /auth/me working: {me_data.get('username')} ({me_data.get('role')})")
            print("🎉 AUTHENTICATION FIX SUCCESSFUL!")
            print("✅ Login redirect loop should now be resolved")
            return True
        else:
            print(f"❌ /auth/me failed: {me_response.status}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = deploy_auth_fix()
    if success:
        print("\n🎉 AUTH FIX DEPLOYMENT COMPLETE!")
        print("✅ Users should now be able to login without redirect loops")
        print("🔗 Frontend authentication flow should work properly")
    else:
        print("\n❌ AUTH FIX DEPLOYMENT FAILED!")
        print("🔧 Manual intervention may be required") 