#!/usr/bin/env python3
"""
🧪 Test VantagePoint CRM Production Endpoints
Verify all backend fixes are working with new custom domain
"""

import json
import urllib3
import time

def test_production_endpoints():
    """Test all production endpoints with new custom domain"""
    
    print("🧪 TESTING VANTAGEPOINT CRM PRODUCTION ENDPOINTS")
    print("=" * 60)
    print("🌐 Custom Domain: https://api.vantagepointcrm.com")
    print("🎯 Testing all critical fixes from backend handoff")
    print("")
    
    base_url = "https://api.vantagepointcrm.com"
    http = urllib3.PoolManager()
    
    # Test results tracking
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Health Check
    print("🔍 Test 1: Health Check")
    tests_total += 1
    try:
        response = http.request('GET', f'{base_url}/health')
        if response.status == 200:
            health_data = json.loads(response.data.decode('utf-8'))
            print(f"✅ Health check passed: {response.status}")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Users: {health_data.get('users_count', 'unknown')}")
            print(f"   Storage: {health_data.get('user_storage', 'unknown')}")
            tests_passed += 1
        else:
            print(f"❌ Health check failed: {response.status}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    print()
    
    # Test 2: Admin Login
    print("🔍 Test 2: Admin Authentication")
    tests_total += 1
    admin_token = None
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = http.request(
            'POST',
            f'{base_url}/api/v1/auth/login',
            body=json.dumps(login_data),
            headers={'Content-Type': 'application/json'}
        )
        if response.status == 200:
            login_result = json.loads(response.data.decode('utf-8'))
            admin_token = login_result.get('access_token')
            user_info = login_result.get('user', {})
            print(f"✅ Admin login successful: {response.status}")
            print(f"   Username: {user_info.get('username', 'unknown')}")
            print(f"   Role: {user_info.get('role', 'unknown')}")
            print(f"   Token: {'✅ Received' if admin_token else '❌ Missing'}")
            tests_passed += 1
        else:
            print(f"❌ Admin login failed: {response.status}")
    except Exception as e:
        print(f"❌ Admin login error: {e}")
    print()
    
    if not admin_token:
        print("❌ Cannot continue tests without admin token")
        return tests_passed, tests_total
    
    # Test 3: Organization Endpoint (THE BIG ONE!)
    print("🔍 Test 3: Organizational Structure Endpoint")
    tests_total += 1
    try:
        response = http.request(
            'GET',
            f'{base_url}/api/v1/organization',
            headers={
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
        )
        if response.status == 200:
            org_data = json.loads(response.data.decode('utf-8'))
            managers = org_data.get('managers', [])
            total_agents = org_data.get('total_agents', 0)
            total_admins = org_data.get('total_admins', 0)
            
            print(f"✅ Organization endpoint working: {response.status}")
            print(f"   Total Admins: {total_admins}")
            print(f"   Total Managers: {len(managers)}")
            print(f"   Total Agents: {total_agents}")
            
            # Show first manager details
            if managers:
                manager = managers[0]
                print(f"   Manager Example: {manager.get('full_name', 'unknown')}")
                print(f"   Manager Agents: {manager.get('agent_count', 0)}")
                print(f"   Manager Team Leads: {manager.get('team_leads', 0)}")
            
            tests_passed += 1
        else:
            print(f"❌ Organization endpoint failed: {response.status}")
            print(f"   This was the main issue - checking if still needs API Gateway config")
    except Exception as e:
        print(f"❌ Organization endpoint error: {e}")
    print()
    
    # Test 4: User Persistence (Create Test User)
    print("🔍 Test 4: User Persistence (DynamoDB Test)")
    tests_total += 1
    test_username = f"test_persistence_{int(time.time())}"
    try:
        user_data = {
            "username": test_username,
            "password": "test123",
            "role": "agent",
            "full_name": "Test Persistence User",
            "email": f"{test_username}@test.com"
        }
        response = http.request(
            'POST',
            f'{base_url}/api/v1/users',
            body=json.dumps(user_data),
            headers={
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
        )
        if response.status == 201:
            create_result = json.loads(response.data.decode('utf-8'))
            print(f"✅ User creation successful: {response.status}")
            print(f"   Created User: {create_result.get('user', {}).get('username', 'unknown')}")
            print(f"   User ID: {create_result.get('user', {}).get('id', 'unknown')}")
            
            # Test if user persists by trying to login
            time.sleep(1)  # Brief wait
            login_test = http.request(
                'POST',
                f'{base_url}/api/v1/auth/login',
                body=json.dumps({"username": test_username, "password": "test123"}),
                headers={'Content-Type': 'application/json'}
            )
            if login_test.status == 200:
                print(f"✅ User persistence confirmed - new user can login!")
                print(f"   DynamoDB storage working correctly")
                tests_passed += 1
            else:
                print(f"❌ User persistence failed - user cannot login: {login_test.status}")
        else:
            print(f"❌ User creation failed: {response.status}")
    except Exception as e:
        print(f"❌ User persistence test error: {e}")
    print()
    
    # Test 5: Leads Endpoint
    print("🔍 Test 5: Leads Management")
    tests_total += 1
    try:
        response = http.request(
            'GET',
            f'{base_url}/api/v1/leads',
            headers={
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
        )
        if response.status == 200:
            leads_data = json.loads(response.data.decode('utf-8'))
            leads = leads_data.get('leads', [])
            total = leads_data.get('total', 0)
            print(f"✅ Leads endpoint working: {response.status}")
            print(f"   Total Leads: {total}")
            print(f"   Leads Array: {len(leads)} items")
            tests_passed += 1
        else:
            print(f"❌ Leads endpoint failed: {response.status}")
    except Exception as e:
        print(f"❌ Leads endpoint error: {e}")
    print()
    
    # Test 6: Dashboard Summary
    print("🔍 Test 6: Dashboard Summary")
    tests_total += 1
    try:
        response = http.request(
            'GET',
            f'{base_url}/api/v1/summary',
            headers={
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
        )
        if response.status == 200:
            summary_data = json.loads(response.data.decode('utf-8'))
            print(f"✅ Dashboard summary working: {response.status}")
            print(f"   Total Leads: {summary_data.get('total_leads', 'unknown')}")
            print(f"   Practices Signed Up: {summary_data.get('practices_signed_up', 'unknown')}")
            print(f"   Conversion Rate: {summary_data.get('conversion_rate', 'unknown')}%")
            tests_passed += 1
        else:
            print(f"❌ Dashboard summary failed: {response.status}")
    except Exception as e:
        print(f"❌ Dashboard summary error: {e}")
    print()
    
    # Results Summary
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 40)
    print(f"✅ Tests Passed: {tests_passed}/{tests_total}")
    print(f"📊 Success Rate: {round((tests_passed/tests_total)*100, 1)}%")
    print()
    
    if tests_passed == tests_total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Backend fixes are working perfectly")
        print("✅ Custom domain is functional")
        print("✅ User persistence is working")
        print("✅ Organization endpoint is live")
        print("✅ Ready for frontend deployment!")
    elif tests_passed >= tests_total * 0.8:
        print("🎯 MOSTLY WORKING - Minor issues")
        print("⚠️ Some endpoints may need additional configuration")
        print("✅ Core functionality is operational")
    else:
        print("❌ MAJOR ISSUES DETECTED")
        print("🔧 Backend team may need to investigate")
        print("⚠️ Not ready for production use")
    
    return tests_passed, tests_total

if __name__ == "__main__":
    test_production_endpoints() 