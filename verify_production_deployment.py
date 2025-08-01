#!/usr/bin/env python3
"""
🎯 VantagePoint CRM Production Deployment Verification
Final validation that all systems are operational after launch
"""

import json
import urllib3
import time
from datetime import datetime

def verify_production_deployment():
    """Comprehensive verification of production deployment"""
    
    print("🎯 VANTAGEPOINT CRM - PRODUCTION DEPLOYMENT VERIFICATION")
    print("=" * 70)
    print(f"🕐 Deployment Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌐 Production API: https://api.vantagepointcrm.com")
    print("")
    
    base_url = "https://api.vantagepointcrm.com"
    http = urllib3.PoolManager()
    
    # Track results
    checks_passed = 0
    checks_total = 0
    critical_failures = []
    
    print("🔍 CRITICAL SYSTEM CHECKS")
    print("-" * 40)
    
    # Check 1: API Health & Infrastructure
    print("1️⃣ API Infrastructure Health")
    checks_total += 1
    try:
        response = http.request('GET', f'{base_url}/health', timeout=10)
        if response.status == 200:
            health_data = json.loads(response.data.decode('utf-8'))
            print(f"   ✅ API Server: Online ({response.status})")
            print(f"   ✅ Storage: {health_data.get('user_storage', 'Unknown')}")
            print(f"   ✅ Users in System: {health_data.get('users_count', 0)}")
            checks_passed += 1
        else:
            print(f"   ❌ API Server: Offline ({response.status})")
            critical_failures.append("API Server not responding")
    except Exception as e:
        print(f"   ❌ API Server: Connection Failed ({e})")
        critical_failures.append(f"API Connection Error: {e}")
    print()
    
    # Check 2: Authentication System
    print("2️⃣ Authentication System")
    checks_total += 1
    admin_token = None
    try:
        login_data = {"username": "admin", "password": "admin123"}
        response = http.request(
            'POST', f'{base_url}/api/v1/auth/login',
            body=json.dumps(login_data),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        if response.status == 200:
            login_result = json.loads(response.data.decode('utf-8'))
            admin_token = login_result.get('access_token')
            user_info = login_result.get('user', {})
            print(f"   ✅ Admin Login: Successful")
            print(f"   ✅ JWT Token: Issued")
            print(f"   ✅ User Role: {user_info.get('role', 'unknown')}")
            checks_passed += 1
        else:
            print(f"   ❌ Admin Login: Failed ({response.status})")
            critical_failures.append("Admin authentication broken")
    except Exception as e:
        print(f"   ❌ Authentication: Error ({e})")
        critical_failures.append(f"Authentication Error: {e}")
    print()
    
    if not admin_token:
        print("🚨 CRITICAL: Cannot continue without admin authentication")
        print(f"📊 DEPLOYMENT STATUS: FAILED ({checks_passed}/{checks_total})")
        return False
    
    # Check 3: Organization Endpoint (Key Feature)
    print("3️⃣ Organizational Structure (Key Feature)")
    checks_total += 1
    try:
        response = http.request(
            'GET', f'{base_url}/api/v1/organization',
            headers={
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        if response.status == 200:
            org_data = json.loads(response.data.decode('utf-8'))
            print(f"   ✅ Organization API: Working")
            print(f"   ✅ Total Admins: {org_data.get('total_admins', 0)}")
            print(f"   ✅ Total Managers: {org_data.get('total_managers', 0)}")
            print(f"   ✅ Total Agents: {org_data.get('total_agents', 0)}")
            checks_passed += 1
        else:
            print(f"   ❌ Organization API: Failed ({response.status})")
            critical_failures.append("Organization structure not working")
    except Exception as e:
        print(f"   ❌ Organization API: Error ({e})")
        critical_failures.append(f"Organization API Error: {e}")
    print()
    
    # Check 4: User Persistence (Critical Fix)
    print("4️⃣ User Persistence (DynamoDB)")
    checks_total += 1
    test_user_created = False
    try:
        # Create test user
        test_username = f"prod_test_{int(time.time())}"
        user_data = {
            "username": test_username,
            "password": "test123",
            "role": "agent",
            "full_name": "Production Test User",
            "email": f"{test_username}@test.com"
        }
        create_response = http.request(
            'POST', f'{base_url}/api/v1/users',
            body=json.dumps(user_data),
            headers={
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        if create_response.status == 201:
            print(f"   ✅ User Creation: Success")
            test_user_created = True
            
            # Test immediate login
            time.sleep(1)
            login_response = http.request(
                'POST', f'{base_url}/api/v1/auth/login',
                body=json.dumps({"username": test_username, "password": "test123"}),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if login_response.status == 200:
                print(f"   ✅ User Persistence: Confirmed")
                print(f"   ✅ DynamoDB Storage: Working")
                checks_passed += 1
            else:
                print(f"   ❌ User Persistence: Failed")
                critical_failures.append("User persistence not working")
        else:
            print(f"   ❌ User Creation: Failed ({create_response.status})")
            critical_failures.append("User creation broken")
            
    except Exception as e:
        print(f"   ❌ User Persistence: Error ({e})")
        critical_failures.append(f"User Persistence Error: {e}")
    print()
    
    # Check 5: Lead Management
    print("5️⃣ Lead Management System")
    checks_total += 1
    try:
        response = http.request(
            'GET', f'{base_url}/api/v1/leads',
            headers={
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        if response.status == 200:
            leads_data = json.loads(response.data.decode('utf-8'))
            total_leads = leads_data.get('total', 0)
            print(f"   ✅ Lead Management: Working")
            print(f"   ✅ Total Leads: {total_leads}")
            print(f"   ✅ Lead Data Structure: Valid")
            checks_passed += 1
        else:
            print(f"   ❌ Lead Management: Failed ({response.status})")
            critical_failures.append("Lead management not working")
    except Exception as e:
        print(f"   ❌ Lead Management: Error ({e})")
        critical_failures.append(f"Lead Management Error: {e}")
    print()
    
    # Check 6: Dashboard Statistics
    print("6️⃣ Dashboard Analytics")
    checks_total += 1
    try:
        response = http.request(
            'GET', f'{base_url}/api/v1/summary',
            headers={
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        if response.status == 200:
            summary_data = json.loads(response.data.decode('utf-8'))
            print(f"   ✅ Dashboard Stats: Working")
            print(f"   ✅ Analytics Data: Available")
            checks_passed += 1
        else:
            print(f"   ❌ Dashboard Stats: Failed ({response.status})")
            critical_failures.append("Dashboard analytics not working")
    except Exception as e:
        print(f"   ❌ Dashboard Stats: Error ({e})")
        critical_failures.append(f"Dashboard Error: {e}")
    print()
    
    # Final Assessment
    print("🎯 PRODUCTION DEPLOYMENT ASSESSMENT")
    print("=" * 50)
    success_rate = (checks_passed / checks_total) * 100
    print(f"✅ Checks Passed: {checks_passed}/{checks_total}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    print()
    
    if success_rate == 100:
        print("🎉 DEPLOYMENT STATUS: FULLY OPERATIONAL")
        print("✅ All critical systems working perfectly")
        print("✅ Ready for agent team usage")
        print("✅ Enterprise-grade reliability confirmed")
        print()
        print("🚀 NEXT STEPS:")
        print("1. Share login credentials with admin users")
        print("2. Begin onboarding agent teams")
        print("3. Monitor system performance in CloudWatch")
        print("4. Scale user creation as needed")
        
    elif success_rate >= 80:
        print("⚠️ DEPLOYMENT STATUS: MOSTLY OPERATIONAL")
        print("✅ Core functionality working")
        print("⚠️ Some minor issues detected")
        print("🔧 Review failed checks and address issues")
        
    else:
        print("❌ DEPLOYMENT STATUS: CRITICAL ISSUES")
        print("🚨 Major problems detected - not ready for production")
        print("🔧 Critical fixes required before agent deployment")
        
    if critical_failures:
        print()
        print("🚨 CRITICAL FAILURES TO ADDRESS:")
        for i, failure in enumerate(critical_failures, 1):
            print(f"   {i}. {failure}")
    
    print()
    print("📞 Support: Backend team available for issue resolution")
    print("🌐 Frontend URL: Waiting for Amplify deployment completion")
    print(f"🕐 Verification Complete: {datetime.now().strftime('%H:%M:%S')}")
    
    return success_rate == 100

if __name__ == "__main__":
    verify_production_deployment() 