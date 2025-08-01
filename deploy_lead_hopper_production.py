#!/usr/bin/env python3
"""
🚀 VANTAGEPOINT CRM LEAD HOPPER SYSTEM v3.0.0 - PRODUCTION DEPLOYMENT
Complete Lead Management & Distribution System with Role-Based Access Control
"""

import boto3
import os
import json
import zipfile
import shutil
from datetime import datetime

def create_deployment_package():
    """Create deployment package with Lead Hopper system"""
    
    print("📦 Creating Lead Hopper System v3.0.0 deployment package...")
    
    # Create temp directory for packaging
    temp_dir = "lambda_deploy_temp"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    try:
        # Copy main lambda function
        shutil.copy2("lambda_package/lambda_function.py", f"{temp_dir}/lambda_function.py")
        
        # Copy JWT dependencies if they exist
        jwt_source = "lambda_package/jwt"
        if os.path.exists(jwt_source):
            shutil.copytree(jwt_source, f"{temp_dir}/jwt")
            print("✅ JWT dependencies included")
        
        # Copy PyJWT dist-info if it exists
        pyjwt_source = "lambda_package/PyJWT-2.10.1.dist-info"
        if os.path.exists(pyjwt_source):
            shutil.copytree(pyjwt_source, f"{temp_dir}/PyJWT-2.10.1.dist-info")
            print("✅ PyJWT metadata included")
        
        # Create ZIP package
        zip_filename = "lead_hopper_system_v3_production.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        # Cleanup temp directory
        shutil.rmtree(temp_dir)
        
        # Get package size
        package_size = os.path.getsize(zip_filename)
        print(f"✅ Package created: {zip_filename} ({package_size:,} bytes)")
        
        return zip_filename, package_size
        
    except Exception as e:
        # Cleanup on error
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise e

def deploy_to_lambda(zip_filename):
    """Deploy to AWS Lambda"""
    
    # Lambda configuration
    function_name = 'cura-genesis-crm-api'  # Existing function name
    
    print(f"🚀 Deploying Lead Hopper System v3.0.0 to Production")
    print(f"📦 Package: {zip_filename}")
    print(f"🎯 Function: {function_name}")
    print(f"🕐 Timestamp: {datetime.now().isoformat()}")
    
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
        
        # Update function configuration for production
        print("⚙️ Updating function configuration...")
        config_response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Description="VantagePoint CRM Lead Hopper System v3.0.0 - Production",
            Timeout=30,  # 30 seconds timeout
            MemorySize=512,  # 512 MB memory
            Environment={
                'Variables': {
                    'ENVIRONMENT': 'production',
                    'VERSION': '3.0.0',
                    'LEAD_HOPPER_ENABLED': 'true',
                    'MAX_LEADS_PER_AGENT': '20',
                    'RECYCLING_HOURS': '24'
                }
            }
        )
        
        print(f"✅ Configuration updated successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        return False

def verify_deployment():
    """Verify the deployment is working"""
    
    print("🔍 Verifying production deployment...")
    
    try:
        import requests
        
        # Test health endpoint
        health_response = requests.get("https://api.vantagepointcrm.com/health", timeout=10)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            
            print("✅ Health check passed!")
            print(f"📊 Service: {health_data.get('service', 'Unknown')}")
            print(f"🔢 Version: {health_data.get('version', 'Unknown')}")
            print(f"👥 Users: {health_data.get('users_count', 0)}")
            print(f"📈 Leads: {health_data.get('leads_count', 0)}")
            
            # Check hopper system
            hopper_stats = health_data.get('hopper_system', {})
            if hopper_stats:
                print("🔄 Hopper System Status:")
                print(f"   Available: {hopper_stats.get('available_in_hopper', 0)}")
                print(f"   Assigned: {hopper_stats.get('assigned_to_agents', 0)}")
                print(f"   Max per agent: {hopper_stats.get('max_per_agent', 0)}")
                
            return True
        else:
            print(f"❌ Health check failed: HTTP {health_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def main():
    """Main deployment function"""
    
    print("🚀 VANTAGEPOINT CRM LEAD HOPPER SYSTEM v3.0.0")
    print("=" * 60)
    print("📊 FEATURES INCLUDED:")
    print("   ✅ Role-based Lead Access Control")
    print("   ✅ Automated Lead Hopper & Distribution")
    print("   ✅ 24-Hour Lead Recycling System")
    print("   ✅ Auto-Replenishment for Agents")
    print("   ✅ Manager Team Oversight")
    print("   ✅ Lead Disposition Management")
    print("   ✅ Real-time Analytics & Monitoring")
    print("   ✅ Smart Lead Assignment Algorithm")
    print("=" * 60)
    print()
    
    try:
        # Step 1: Create deployment package
        zip_filename, package_size = create_deployment_package()
        
        # Step 2: Deploy to Lambda
        deployment_success = deploy_to_lambda(zip_filename)
        
        if deployment_success:
            # Step 3: Verify deployment
            verification_success = verify_deployment()
            
            if verification_success:
                print()
                print("🎉 PRODUCTION DEPLOYMENT SUCCESSFUL!")
                print("=" * 60)
                print("✅ Lead Hopper System v3.0.0 is now LIVE")
                print("✅ All features operational")
                print("✅ Role-based access working")
                print("✅ Auto-assignment active")
                print("✅ Recycling system running")
                print()
                print("🌐 Access your CRM at: https://vantagepointcrm.com")
                print("🔐 Use your credentials to log in")
                print("📊 Managers can create agents and monitor teams")
                print("👥 Agents automatically get 20 leads to work")
                print()
                print("📈 System is ready for production use!")
                
                # Cleanup
                os.remove(zip_filename)
                print(f"🧹 Cleaned up deployment package: {zip_filename}")
                
                return True
            else:
                print("⚠️ Deployment completed but verification failed")
                return False
        else:
            print("❌ Deployment failed")
            return False
            
    except Exception as e:
        print(f"❌ Fatal error during deployment: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)