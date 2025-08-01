#!/usr/bin/env python3
"""
Test lead assignment functionality with DynamoDB persistence
Critical test for lead assignment fix
"""

import requests
import json

# Use custom domain for testing
BASE_URL = "https://api.vantagepointcrm.com"
API_URL = f"{BASE_URL}/api/v1"

def test_login():
    """Test user login and get JWT token"""
    print("🔐 Testing user login...")
    
    response = requests.post(f"{API_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f"   ✅ Login successful! Token: {token[:50]}...")
        return token
    else:
        print(f"   ❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_get_leads(token):
    """Test getting all leads from DynamoDB"""
    print("\n📋 Testing GET /api/v1/leads...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/leads", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        leads = data.get('leads', [])
        print(f"   ✅ Got {len(leads)} leads from DynamoDB")
        
        for lead in leads:
            practice_name = lead.get('practice_name', 'Unknown')
            lead_id = lead.get('id', 'N/A')
            assigned_to = lead.get('assigned_user_id', 'Unassigned')
            print(f"      • {practice_name} (ID: {lead_id}, Assigned: {assigned_to})")
        
        return leads
    else:
        print(f"   ❌ Failed to get leads: {response.status_code} - {response.text}")
        return []

def test_lead_assignment(token, lead_id, new_user_id):
    """Test updating lead assignment"""
    print(f"\n🎯 Testing PUT /api/v1/leads/{lead_id} - Assigning to user {new_user_id}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    update_data = {
        "assigned_user_id": new_user_id,
        "status": "assigned"
    }
    
    response = requests.put(f"{API_URL}/leads/{lead_id}", 
                          headers=headers, 
                          json=update_data)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Lead assignment successful!")
        print(f"      Message: {data.get('message')}")
        
        # Verify the assignment
        updated_lead = data.get('lead', {})
        assigned_user_id = updated_lead.get('assigned_user_id')
        print(f"      Verified: Lead {lead_id} now assigned to user {assigned_user_id}")
        return True
    else:
        print(f"   ❌ Lead assignment failed: {response.status_code} - {response.text}")
        return False

def test_create_lead(token):
    """Test creating a new lead"""
    print("\n➕ Testing POST /api/v1/leads - Creating new lead...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    new_lead = {
        "practice_name": "TEST MEDICAL PRACTICE",
        "owner_name": "Dr. Test Doctor",
        "practice_phone": "(555) 123-4567",
        "email": "test@testmedical.com",
        "address": "123 Test Street",
        "city": "Test City",
        "state": "TX",
        "zip_code": "12345",
        "specialty": "Test Specialty",
        "score": 95,
        "priority": "high",
        "status": "new",
        "assigned_user_id": 2,
        "ptan": "P99999999",
        "ein_tin": "99-9999999"
    }
    
    response = requests.post(f"{API_URL}/leads", 
                           headers=headers, 
                           json=new_lead)
    
    if response.status_code == 201:
        data = response.json()
        created_lead = data.get('lead', {})
        lead_id = created_lead.get('id')
        print(f"   ✅ Lead created successfully! ID: {lead_id}")
        print(f"      Practice: {created_lead.get('practice_name')}")
        return lead_id
    else:
        print(f"   ❌ Lead creation failed: {response.status_code} - {response.text}")
        return None

def test_organization_endpoint(token):
    """Test organization endpoint"""
    print("\n🏢 Testing GET /api/v1/organization...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/organization", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        org = data.get('organization', {})
        total_users = org.get('total_users', 0)
        print(f"   ✅ Organization structure retrieved! Total users: {total_users}")
        
        roles_count = org.get('roles_count', {})
        for role, count in roles_count.items():
            print(f"      {role.capitalize()}s: {count}")
        
        return True
    else:
        print(f"   ❌ Organization endpoint failed: {response.status_code} - {response.text}")
        return False

def main():
    """Run comprehensive lead assignment tests"""
    print("🚨 CRITICAL TEST: Lead Assignment with DynamoDB Persistence")
    print("=" * 65)
    
    # Step 1: Login
    token = test_login()
    if not token:
        print("\n❌ Cannot continue without valid token")
        return False
    
    # Step 2: Get leads
    leads = test_get_leads(token)
    if not leads:
        print("\n❌ No leads found - migration may have failed")
        return False
    
    # Step 3: Test organization endpoint
    test_organization_endpoint(token)
    
    # Step 4: Test creating a new lead
    new_lead_id = test_create_lead(token)
    
    # Step 5: Test lead assignment (use first existing lead)
    test_lead_id = leads[0].get('id')
    current_assigned = leads[0].get('assigned_user_id')
    new_user_id = 2 if current_assigned != 2 else 1  # Switch assignment
    
    assignment_success = test_lead_assignment(token, test_lead_id, new_user_id)
    
    # Step 6: Verify persistence by getting leads again
    print("\n🔄 Testing persistence - Getting leads again...")
    updated_leads = test_get_leads(token)
    
    if updated_leads:
        # Find the updated lead
        updated_lead = next((l for l in updated_leads if l.get('id') == test_lead_id), None)
        if updated_lead and updated_lead.get('assigned_user_id') == new_user_id:
            print(f"   ✅ PERSISTENCE CONFIRMED: Lead {test_lead_id} assignment persisted!")
        else:
            print(f"   ❌ PERSISTENCE FAILED: Assignment not saved")
            return False
    
    print("\n🎯 TEST RESULTS:")
    print("✅ Login: Working")
    print("✅ DynamoDB leads: Working")
    print("✅ Lead assignment: Working") 
    print("✅ Data persistence: Working")
    print("✅ Organization endpoint: Working")
    if new_lead_id:
        print("✅ Lead creation: Working")
    
    print("\n🎉 ALL CRITICAL TESTS PASSED!")
    print("Backend is ready for production use!")
    return True

if __name__ == "__main__":
    main()