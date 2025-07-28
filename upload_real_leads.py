#!/usr/bin/env python3
"""
Upload Real Leads to Production Lambda Backend
Loads 100 high-quality leads from hot_leads.json and uploads them to the CRM system
"""

import json
import requests
import sys
from datetime import datetime

# Configuration
LAMBDA_URL = "https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod"
USERNAME = "admin"
PASSWORD = "admin123"

def get_auth_token():
    """Get JWT authentication token"""
    print("🔐 Getting authentication token...")
    
    login_url = f"{LAMBDA_URL}/api/v1/auth/login"
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        
        data = response.json()
        token = data.get("access_token")
        
        if token:
            print(f"✅ Authentication successful")
            return token
        else:
            print("❌ No token in response")
            return None
            
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def load_leads_data():
    """Load leads from hot_leads.json"""
    print("📋 Loading leads from hot_leads.json...")
    
    try:
        with open("hot_leads.json", "r") as f:
            leads_data = json.load(f)
        
        print(f"✅ Loaded {len(leads_data)} leads from file")
        return leads_data
        
    except Exception as e:
        print(f"❌ Error loading leads: {e}")
        return None

def convert_lead_format(raw_lead):
    """Convert hot_leads.json format to CRM API format"""
    
    # Map the fields from hot_leads.json to CRM format
    converted = {
        "company_name": raw_lead.get("practice_name", "N/A"),
        "contact_name": raw_lead.get("owner_name", ""),
        "phone": raw_lead.get("practice_phone", ""),
        "email": "",  # Not provided in hot_leads data
        "status": "new",
        "priority": "high" if raw_lead.get("score", 0) >= 90 else "medium",
        "specialty": raw_lead.get("specialties", ""),
        "location": f"{raw_lead.get('city', '')}, {raw_lead.get('state', '')}",
        "score": raw_lead.get("score", 50),
        
        # Additional fields from hot_leads.json
        "practice_name": raw_lead.get("practice_name", ""),
        "owner_name": raw_lead.get("owner_name", ""),
        "practice_phone": raw_lead.get("practice_phone", ""),
        "owner_phone": raw_lead.get("owner_phone", ""),
        "providers": raw_lead.get("providers", 1),
        "city": raw_lead.get("city", ""),
        "state": raw_lead.get("state", ""),
        "zip": raw_lead.get("zip", ""),
        "address": raw_lead.get("address", ""),
        "ein": raw_lead.get("ein"),
        "is_sole_proprietor": raw_lead.get("is_sole_proprietor"),
        "entity_type": raw_lead.get("entity_type", ""),
        "npi": raw_lead.get("npi", ""),
        "category": raw_lead.get("category", "")
    }
    
    return converted

def upload_leads_bulk(token, leads_data):
    """Upload leads using bulk endpoint"""
    print(f"🚀 Uploading {len(leads_data)} leads to production...")
    
    # Convert leads to CRM format
    converted_leads = []
    for raw_lead in leads_data:
        converted = convert_lead_format(raw_lead)
        converted_leads.append(converted)
    
    # Prepare bulk upload request
    bulk_url = f"{LAMBDA_URL}/api/v1/leads/bulk"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "leads": converted_leads
    }
    
    try:
        print("📤 Sending bulk upload request...")
        response = requests.post(bulk_url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        created_count = result.get("created_count", 0)
        total_leads = result.get("total_leads", 0)
        
        print(f"✅ SUCCESS: Created {created_count} leads")
        print(f"📊 Total leads in system: {total_leads}")
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return False

def verify_upload(token):
    """Verify the upload by checking lead count"""
    print("🔍 Verifying upload...")
    
    try:
        # Check health endpoint
        health_url = f"{LAMBDA_URL}/health"
        response = requests.get(health_url)
        response.raise_for_status()
        
        health_data = response.json()
        total_leads = health_data.get("total_leads", 0)
        
        print(f"✅ Health check: {total_leads} leads in system")
        
        # Check summary endpoint
        summary_url = f"{LAMBDA_URL}/api/v1/summary"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(summary_url, headers=headers)
        response.raise_for_status()
        
        summary = response.json()
        print(f"📊 Summary: {summary.get('total_leads', 0)} total leads")
        print(f"   - New: {summary.get('new_leads', 0)}")
        print(f"   - High Priority: {summary.get('high_priority', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main execution function"""
    print("🎯 UPLOADING REAL LEADS TO PRODUCTION CRM")
    print("=" * 50)
    
    # Step 1: Authenticate
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token")
        sys.exit(1)
    
    # Step 2: Load leads data
    leads_data = load_leads_data()
    if not leads_data:
        print("❌ Failed to load leads data")
        sys.exit(1)
    
    # Step 3: Upload leads
    success = upload_leads_bulk(token, leads_data)
    if not success:
        print("❌ Failed to upload leads")
        sys.exit(1)
    
    # Step 4: Verify upload
    verify_upload(token)
    
    print("\n" + "=" * 50)
    print("🎉 REAL LEADS UPLOAD COMPLETE!")
    print("✅ 100 high-quality leads now available in production")
    print("✅ Frontend team can now access real data")
    print("✅ Remote agents can start working leads")
    print("=" * 50)

if __name__ == "__main__":
    main() 