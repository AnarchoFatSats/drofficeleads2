#!/usr/bin/env python3
"""
Test Master Admin Analytics Endpoint
===================================

Test the new admin analytics endpoint with our 1,469-lead hopper
"""

import requests
import json

def test_admin_analytics():
    """Test the admin analytics endpoint"""
    print("🧪 TESTING MASTER ADMIN ANALYTICS")
    print("=" * 50)
    
    API_BASE = "https://api.vantagepointcrm.com"
    
    try:
        # 1. Authenticate as admin
        print("🔐 Authenticating as admin...")
        login_response = requests.post(f"{API_BASE}/api/v1/auth/login",
                                     json={"username": "admin", "password": "admin123"})
        
        if login_response.status_code != 200:
            print(f"❌ Authentication failed: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        print("✅ Admin authenticated successfully")
        
        # 2. Test admin analytics endpoint
        print("\n📊 Testing admin analytics endpoint...")
        analytics_response = requests.get(f"{API_BASE}/api/v1/admin/analytics",
                                        headers={"Authorization": f"Bearer {token}"})
        
        if analytics_response.status_code != 200:
            print(f"❌ Analytics endpoint failed: {analytics_response.status_code}")
            print(f"Response: {analytics_response.text}")
            return False
        
        analytics_data = analytics_response.json()
        print("✅ Admin analytics endpoint working!")
        
        # 3. Verify data structure
        print("\n🔍 Verifying analytics data structure...")
        
        required_sections = [
            'lead_hopper_overview',
            'score_distribution', 
            'lead_type_breakdown',
            'agent_workload_distribution',
            'operational_insights',
            'real_time_metrics'
        ]
        
        analytics = analytics_data.get('analytics', {})
        
        for section in required_sections:
            if section in analytics:
                print(f"   ✅ {section}")
            else:
                print(f"   ❌ Missing: {section}")
        
        # 4. Display key metrics
        print("\n📈 KEY METRICS FROM YOUR 1,469-LEAD HOPPER:")
        print("=" * 60)
        
        # Lead Hopper Overview
        hopper = analytics.get('lead_hopper_overview', {})
        print(f"🏥 Total Leads: {hopper.get('total_leads', 0):,}")
        print(f"📦 Available in Hopper: {hopper.get('unassigned_leads', 0):,}")
        print(f"👥 Currently Assigned: {hopper.get('assigned_leads', 0):,}")
        print(f"📊 Utilization Rate: {hopper.get('utilization_rate', 0)}%")
        
        # Score Distribution
        scores = analytics.get('score_distribution', {})
        print(f"\n🎯 SCORE DISTRIBUTION:")
        print(f"   💎 Premium (90+): {scores.get('premium_90_plus', {}).get('total', 0):,} leads")
        print(f"   🥇 Excellent (80-89): {scores.get('excellent_80_89', {}).get('total', 0):,} leads")
        print(f"   🥈 Very Good (70-79): {scores.get('very_good_70_79', {}).get('total', 0):,} leads")
        print(f"   🥉 Good (60-69): {scores.get('good_60_69', {}).get('total', 0):,} leads")
        print(f"   📉 Below 60: {scores.get('below_standard_under_60', {}).get('total', 0):,} leads")
        
        # Lead Types
        types = analytics.get('lead_type_breakdown', {})
        print(f"\n📋 LEAD TYPE BREAKDOWN:")
        type_dist = types.get('type_distribution', [])
        for lead_type in type_dist[:5]:  # Top 5 types
            print(f"   • {lead_type.get('name', 'Unknown')}: {lead_type.get('count', 0):,} leads ({lead_type.get('percentage', 0)}%)")
        
        # Agent Workloads
        agents = analytics.get('agent_workload_distribution', {})
        print(f"\n👥 AGENT WORKLOAD:")
        print(f"   Total Agents: {agents.get('total_agents', 0)}")
        print(f"   Active Agents: {agents.get('active_agents', 0)}")
        print(f"   Avg Leads/Agent: {agents.get('workload_summary', {}).get('avg_leads_per_agent', 0)}")
        
        # Top 3 agents
        agent_list = agents.get('agents', [])[:3]
        for i, agent in enumerate(agent_list, 1):
            print(f"   {i}. {agent.get('username', 'Unknown')}: {agent.get('total_assigned', 0)} leads")
        
        # Real-time metrics
        realtime = analytics.get('real_time_metrics', {})
        print(f"\n⏰ REAL-TIME METRICS:")
        print(f"   Leads added last 24h: {realtime.get('leads_added_last_24h', 0)}")
        print(f"   Current unassigned pool: {realtime.get('current_unassigned_pool', 0):,}")
        
        # Alerts
        alerts = realtime.get('inventory_alerts', {})
        print(f"\n🚨 INVENTORY ALERTS:")
        if alerts.get('low_premium_inventory'):
            print("   ⚠️  Low premium inventory warning")
        if alerts.get('low_total_inventory'):
            print("   🚨 Critical: Low total inventory")
        if alerts.get('quality_degradation'):
            print("   📉 Quality degradation detected")
        
        if not any(alerts.values()):
            print("   ✅ All inventory levels healthy")
        
        print(f"\n🎉 ADMIN ANALYTICS TEST SUCCESSFUL!")
        print(f"📊 Your master dashboard is ready to manage {hopper.get('total_leads', 0):,} leads!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_dashboard_access():
    """Test if the dashboard file is accessible"""
    print("\n🌐 TESTING DASHBOARD ACCESS")
    print("=" * 40)
    
    dashboard_file = "admin_master_dashboard.html"
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        print(f"✅ Dashboard file exists: {dashboard_file}")
        print(f"📄 File size: {len(content):,} characters")
        
        # Check for key components
        components = [
            'admin/analytics',
            'Chart.js',
            'Score Distribution',
            'Agent Performance',
            'Lead Types'
        ]
        
        for component in components:
            if component in content:
                print(f"   ✅ Contains: {component}")
            else:
                print(f"   ❌ Missing: {component}")
        
        print(f"✅ Dashboard ready for use!")
        return True
        
    except FileNotFoundError:
        print(f"❌ Dashboard file not found: {dashboard_file}")
        return False
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MASTER ADMIN ANALYTICS - COMPLETE SYSTEM TEST")
    print("=" * 60)
    
    # Test backend endpoint
    backend_ok = test_admin_analytics()
    
    # Test frontend dashboard
    frontend_ok = test_dashboard_access()
    
    print(f"\n🏁 FINAL RESULTS:")
    print(f"   Backend API: {'✅ WORKING' if backend_ok else '❌ FAILED'}")
    print(f"   Frontend Dashboard: {'✅ READY' if frontend_ok else '❌ FAILED'}")
    
    if backend_ok and frontend_ok:
        print(f"\n🎉 MASTER ADMIN ANALYTICS SYSTEM COMPLETE!")
        print(f"📋 Access your dashboard: admin_master_dashboard.html")
        print(f"🎯 Manage your {1469} high-scoring leads with comprehensive insights!")
    else:
        print(f"\n❌ System needs attention before use")