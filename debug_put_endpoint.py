#!/usr/bin/env python3
"""
Debug the PUT endpoint issue
"""

import requests
import json

BASE_URL = "https://api.vantagepointcrm.com"
API_URL = f"{BASE_URL}/api/v1"

# Login first
print("🔐 Getting token...")
response = requests.post(f"{API_URL}/auth/login", json={
    "username": "admin",
    "password": "admin123"
})

if response.status_code == 200:
    token = response.json().get('access_token')
    print(f"✅ Token: {token[:50]}...")
else:
    print(f"❌ Login failed: {response.text}")
    exit()

# Test PUT with different lead IDs
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

test_cases = [
    {"url": f"{API_URL}/leads/1", "id": "1"},
    {"url": f"{API_URL}/leads/400", "id": "400"},  # Known existing lead
    {"url": f"{API_URL}/leads/999", "id": "999"},  # Non-existent lead
]

update_data = {"assigned_user_id": 2, "status": "assigned"}

for case in test_cases:
    print(f"\n🎯 Testing PUT {case['url']} (ID: {case['id']})...")
    
    response = requests.put(case['url'], headers=headers, json=update_data)
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    if response.status_code == 200:
        print("   ✅ SUCCESS!")
    else:
        print("   ❌ FAILED")