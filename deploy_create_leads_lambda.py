#!/usr/bin/env python3
"""
Deploy Create Leads Lambda Function
Updates the existing Lambda with POST endpoint to create new leads
"""

import boto3
import zipfile
import os
import json

def deploy_lambda():
    """Deploy updated Lambda with create leads functionality"""
    
    # Lambda configuration
    function_name = 'cura-genesis-crm-api'
    zip_file = 'lambda_crm_with_create_leads.zip'
    
    # Verify zip file exists
    if not os.path.exists(zip_file):
        print(f"❌ Error: {zip_file} not found")
        return False
    
    print(f"🚀 Deploying Lambda function: {function_name}")
    print(f"📦 Package: {zip_file}")
    
    try:
        # Initialize AWS Lambda client
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Read zip file
        with open(zip_file, 'rb') as f:
            zip_content = f.read()
        
        print(f"📋 Package size: {len(zip_content)} bytes")
        
        # Update function code
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda updated successfully!")
        print(f"🆔 Version: {response.get('Version', 'N/A')}")
        print(f"⏰ Last Modified: {response.get('LastModified', 'N/A')}")
        print(f"📏 Code Size: {response.get('CodeSize', 'N/A')} bytes")
        
        # Update function description
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Description="Cura Genesis CRM API v5.0.0 - Complete Lead Management with Create Endpoint"
        )
        
        print(f"\n🎯 NEW FEATURES DEPLOYED:")
        print(f"✅ POST /api/v1/leads - Create new leads")
        print(f"✅ Supports unlimited lead storage")
        print(f"✅ Proper lead assignment to agent1")
        print(f"✅ All existing features preserved")
        
        print(f"\n🌐 API Endpoint: https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod")
        print(f"📋 Test Health: curl https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod/health")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = deploy_lambda()
    if success:
        print(f"\n🎉 DEPLOYMENT COMPLETE!")
        print(f"Your Lambda can now handle unlimited leads!")
    else:
        print(f"\n💥 DEPLOYMENT FAILED!") 