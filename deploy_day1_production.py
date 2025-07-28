#!/usr/bin/env python3
"""
Deploy VantagePoint CRM - Day 1 Fresh Production Data
- All 20 leads reset to status: "new"
- All docs_sent: False
- Clean metrics: 0 practices signed up, 0% conversion rate
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
    zip_filename = 'lambda_day1_production.zip'
    
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
    """Deploy the fresh Day 1 data to AWS Lambda"""
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

def test_day1_production():
    """Test the Day 1 production deployment"""
    api_base = "https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod"
    
    print(f"\n🧪 TESTING DAY 1 PRODUCTION...")
    
    try:
        # Test 1: Health check
        health_response = requests.get(f"{api_base}/health", timeout=10)
        health_data = health_response.json()
        print(f"✅ Health Check: {health_data.get('service')} - {health_data.get('leads_count')} leads")
        
        # Test 2: Agent login and check dashboard stats
        login_response = requests.post(f"{api_base}/api/v1/auth/login", 
                                     json={"username": "agent1", "password": "admin123"})
        token = login_response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"✅ Agent login successful")
        
        # Test 3: Get summary stats (should be all zeros)
        summary_response = requests.get(f"{api_base}/api/v1/summary", headers=headers)
        summary_data = summary_response.json()
        
        practices_signed = summary_data.get('practices_signed_up', -1)
        conversion_rate = summary_data.get('conversion_rate', -1)
        total_leads = summary_data.get('total_leads', -1)
        active_leads = summary_data.get('active_leads', -1)
        
        print(f"\n📊 DAY 1 PRODUCTION METRICS:")
        print(f"   🏢 Practices Signed Up: {practices_signed}")
        print(f"   📈 Conversion Rate: {conversion_rate}%")
        print(f"   📋 Total Leads: {total_leads}")
        print(f"   🎯 Active Leads: {active_leads}")
        
        # Verify expected Day 1 values
        success = True
        if practices_signed != 0:
            print(f"❌ Expected 0 practices signed up, got {practices_signed}")
            success = False
        if conversion_rate != 0:
            print(f"❌ Expected 0% conversion rate, got {conversion_rate}%")
            success = False
        if total_leads != 19:  # Agent sees 19 out of 20 leads (assigned to agent1)
            print(f"❌ Expected 19 agent leads, got {total_leads}")
            success = False
        if active_leads != 0:
            print(f"❌ Expected 0 active leads (none contacted yet), got {active_leads}")
            success = False
        
        if success:
            print(f"\n🎉 DAY 1 PRODUCTION PERFECT!")
            print(f"   ✅ Clean slate - no fake historical data")
            print(f"   ✅ All leads fresh and ready to work")
            print(f"   ✅ Real progress tracking from Day 1")
        
        # Test 4: Verify a sample lead is "new" status
        leads_response = requests.get(f"{api_base}/api/v1/leads", headers=headers)
        leads_data = leads_response.json()
        
        if leads_data.get('leads'):
            sample_lead = leads_data['leads'][0]
            if sample_lead.get('status') == 'new' and sample_lead.get('docs_sent') == False:
                print(f"   ✅ Sample lead: status='{sample_lead.get('status')}', docs_sent={sample_lead.get('docs_sent')}")
            else:
                print(f"   ❌ Sample lead not fresh: status='{sample_lead.get('status')}', docs_sent={sample_lead.get('docs_sent')}")
        
        return success
    
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DEPLOYING DAY 1 FRESH PRODUCTION DATA")
    print("🆕 All leads reset to 'new' status")
    print("🆕 All docs_sent reset to False")
    print("🆕 Clean metrics for real business tracking")
    print("=" * 60)
    
    if deploy_to_lambda():
        test_day1_production()
    else:
        print("❌ Deployment failed - aborting tests") 