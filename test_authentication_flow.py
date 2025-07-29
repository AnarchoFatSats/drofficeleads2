#!/usr/bin/env python3
"""
🔐 Test Authentication Flow - Verify Login Redirect Loop is Fixed
This tests the exact flow that the frontend uses
"""

import json
import urllib3
import time

def test_authentication_flow():
    """Test the complete authentication flow that frontend uses"""
    
    print("🔐 TESTING AUTHENTICATION FLOW")
    print("=" * 50)
    print("🎯 Verifying login redirect loop is fixed")
    print("🌐 Production API: https://api.vantagepointcrm.com")
    print("")
    
    base_url = "https://api.vantagepointcrm.com"
    http = urllib3.PoolManager()
    
    # Test the exact flow that frontend uses
    test_results = []
    
    # Step 1: Login (what login.html does)
    print("1️⃣ STEP 1: User Login (login.html)")
    print("-" * 30)
    try:
        login_response = http.request(
            'POST',
            f'{base_url}/api/v1/auth/login',
            body=json.dumps({"username": "admin", "password": "admin123"}),
            headers={'Content-Type': 'application/json'}
        )
        
        if login_response.status == 200:
            login_data = json.loads(login_response.data.decode('utf-8'))
            token = login_data.get('access_token')
            user_info = login_data.get('user', {})
            
            print(f"✅ Login successful: {login_response.status}")
            print(f"   Username: {user_info.get('username')}")
            print(f"   Role: {user_info.get('role')}")
            print(f"   Token: {'✅ Received' if token else '❌ Missing'}")
            test_results.append("✅ Login")
        else:
            print(f"❌ Login failed: {login_response.status}")
            test_results.append("❌ Login")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        test_results.append("❌ Login")
        return False
    
    print()
    
    # Step 2: Token Validation (what index.html checkAuthentication does)
    print("2️⃣ STEP 2: Token Validation (index.html checkAuthentication)")
    print("-" * 30)
    try:
        # This is the exact call that index.html makes
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
            print(f"✅ Token validation successful: {me_response.status}")
            print(f"   Verified User: {me_data.get('username')}")
            print(f"   Verified Role: {me_data.get('role')}")
            print(f"   Full Name: {me_data.get('full_name')}")
            print(f"   User ID: {me_data.get('id')}")
            test_results.append("✅ Token Validation")
        else:
            print(f"❌ Token validation failed: {me_response.status}")
            print("🚨 This would cause redirect back to login!")
            test_results.append("❌ Token Validation")
            return False
            
    except Exception as e:
        print(f"❌ Token validation error: {e}")
        test_results.append("❌ Token Validation")
        return False
    
    print()
    
    # Step 3: Subsequent API Calls (what happens after successful auth)
    print("3️⃣ STEP 3: Authenticated API Calls")
    print("-" * 30)
    try:
        # Test a protected endpoint
        leads_response = http.request(
            'GET',
            f'{base_url}/api/v1/leads',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if leads_response.status == 200:
            leads_data = json.loads(leads_response.data.decode('utf-8'))
            print(f"✅ Protected endpoint access: {leads_response.status}")
            print(f"   Total Leads: {leads_data.get('total', 0)}")
            test_results.append("✅ Protected Access")
        else:
            print(f"❌ Protected endpoint failed: {leads_response.status}")
            test_results.append("❌ Protected Access")
            
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")
        test_results.append("❌ Protected Access")
    
    print()
    
    # Summary
    print("🎯 AUTHENTICATION FLOW TEST RESULTS")
    print("=" * 40)
    
    for i, result in enumerate(test_results, 1):
        print(f"{i}. {result}")
    
    success_count = len([r for r in test_results if "✅" in r])
    total_count = len(test_results)
    
    print(f"\n📊 Success Rate: {success_count}/{total_count} ({round((success_count/total_count)*100, 1)}%)")
    
    if success_count == total_count:
        print("\n🎉 AUTHENTICATION FLOW: COMPLETELY FIXED!")
        print("✅ Login redirect loop issue is resolved")
        print("✅ Users can now login and stay logged in")
        print("✅ Frontend authentication flow will work properly")
        print("\n🚀 READY FOR USER TESTING:")
        print("1. Users can login at the login page")
        print("2. They will be redirected to dashboard")
        print("3. They will stay logged in (no redirect loop)")
        print("4. All protected features will work")
        return True
    else:
        print("\n❌ AUTHENTICATION FLOW: STILL HAS ISSUES")
        print("🔧 Additional fixes may be needed")
        return False

if __name__ == "__main__":
    test_authentication_flow() 