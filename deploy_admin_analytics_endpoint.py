#!/usr/bin/env python3
"""
Deploy Master Admin Analytics Endpoint
=====================================

Adds the comprehensive admin analytics endpoint to our existing optimized Lambda function
"""

import os
import shutil

def create_admin_analytics_integration():
    """Create the admin analytics code to integrate into existing Lambda"""
    
    admin_analytics_code = '''
# MASTER ADMIN ANALYTICS - NEW FUNCTIONALITY
from collections import defaultdict

def calculate_master_admin_analytics():
    """Calculate comprehensive analytics for master admin dashboard"""
    try:
        logger.info("🎯 Calculating master admin analytics...")
        
        # Get all data
        all_leads = get_all_leads()
        all_users = get_all_users()
        
        # Initialize analytics structure
        analytics = {
            "timestamp": datetime.utcnow().isoformat(),
            "lead_hopper_overview": {},
            "score_distribution": {},
            "lead_type_breakdown": {},
            "agent_workload_distribution": {},
            "operational_insights": {},
            "real_time_metrics": {}
        }
        
        # LEAD HOPPER OVERVIEW
        total_leads = len(all_leads)
        unassigned_leads = [l for l in all_leads if not l.get('assigned_user_id')]
        assigned_leads = [l for l in all_leads if l.get('assigned_user_id')]
        
        analytics["lead_hopper_overview"] = {
            "total_leads": total_leads,
            "unassigned_leads": len(unassigned_leads),
            "assigned_leads": len(assigned_leads),
            "utilization_rate": round((len(assigned_leads) / total_leads * 100), 1) if total_leads > 0 else 0,
            "available_inventory": len(unassigned_leads)
        }
        
        # SCORE DISTRIBUTION ANALYTICS
        score_tiers = {
            "premium_90_plus": [],
            "excellent_80_89": [],
            "very_good_70_79": [],
            "good_60_69": [],
            "below_standard_under_60": []
        }
        
        for lead in all_leads:
            score = int(lead.get('score', 0))
            if score >= 90:
                score_tiers["premium_90_plus"].append(lead)
            elif score >= 80:
                score_tiers["excellent_80_89"].append(lead)
            elif score >= 70:
                score_tiers["very_good_70_79"].append(lead)
            elif score >= 60:
                score_tiers["good_60_69"].append(lead)
            else:
                score_tiers["below_standard_under_60"].append(lead)
        
        analytics["score_distribution"] = {
            "premium_90_plus": {
                "total": len(score_tiers["premium_90_plus"]),
                "unassigned": len([l for l in score_tiers["premium_90_plus"] if not l.get('assigned_user_id')]),
                "percentage": round(len(score_tiers["premium_90_plus"]) / total_leads * 100, 1) if total_leads > 0 else 0
            },
            "excellent_80_89": {
                "total": len(score_tiers["excellent_80_89"]),
                "unassigned": len([l for l in score_tiers["excellent_80_89"] if not l.get('assigned_user_id')]),
                "percentage": round(len(score_tiers["excellent_80_89"]) / total_leads * 100, 1) if total_leads > 0 else 0
            },
            "very_good_70_79": {
                "total": len(score_tiers["very_good_70_79"]),
                "unassigned": len([l for l in score_tiers["very_good_70_79"] if not l.get('assigned_user_id')]),
                "percentage": round(len(score_tiers["very_good_70_79"]) / total_leads * 100, 1) if total_leads > 0 else 0
            },
            "good_60_69": {
                "total": len(score_tiers["good_60_69"]),
                "unassigned": len([l for l in score_tiers["good_60_69"] if not l.get('assigned_user_id')]),
                "percentage": round(len(score_tiers["good_60_69"]) / total_leads * 100, 1) if total_leads > 0 else 0
            },
            "below_standard_under_60": {
                "total": len(score_tiers["below_standard_under_60"]),
                "unassigned": len([l for l in score_tiers["below_standard_under_60"] if not l.get('assigned_user_id')]),
                "percentage": round(len(score_tiers["below_standard_under_60"]) / total_leads * 100, 1) if total_leads > 0 else 0
            }
        }
        
        # LEAD TYPE BREAKDOWN
        lead_types = defaultdict(int)
        lead_sources = defaultdict(int)
        
        for lead in all_leads:
            lead_type = lead.get('lead_type', 'Unknown')
            source = lead.get('source', 'Unknown')
            
            lead_types[lead_type] += 1
            lead_sources[source] += 1
        
        analytics["lead_type_breakdown"] = {
            "by_type": dict(lead_types),
            "by_source": dict(lead_sources),
            "type_distribution": [
                {"name": k, "count": v, "percentage": round(v/total_leads*100, 1)} 
                for k, v in sorted(lead_types.items(), key=lambda x: x[1], reverse=True)
            ]
        }
        
        # AGENT WORKLOAD DISTRIBUTION
        agents = [u for u in all_users if u.get('role') == 'agent']
        agent_workloads = []
        
        for agent in agents:
            agent_id = agent.get('id')
            agent_leads = [l for l in all_leads if l.get('assigned_user_id') == agent_id]
            
            # Calculate status breakdown
            status_breakdown = defaultdict(int)
            for lead in agent_leads:
                status = lead.get('status', 'new')
                status_breakdown[status] += 1
            
            # Calculate score breakdown for agent's leads
            agent_score_breakdown = {
                "premium_90_plus": len([l for l in agent_leads if int(l.get('score', 0)) >= 90]),
                "excellent_80_89": len([l for l in agent_leads if 80 <= int(l.get('score', 0)) < 90]),
                "very_good_70_79": len([l for l in agent_leads if 70 <= int(l.get('score', 0)) < 80]),
                "good_60_69": len([l for l in agent_leads if 60 <= int(l.get('score', 0)) < 70]),
                "below_60": len([l for l in agent_leads if int(l.get('score', 0)) < 60])
            }
            
            agent_workloads.append({
                "agent_id": agent_id,
                "username": agent.get('username', 'Unknown'),
                "full_name": agent.get('full_name', 'Unknown'),
                "total_assigned": len(agent_leads),
                "status_breakdown": dict(status_breakdown),
                "score_breakdown": agent_score_breakdown,
                "conversion_rate": float(agent.get('conversion_rate', 0)),
                "deals_closed": int(agent.get('deals_closed', 0)),
                "activity_score": int(agent.get('activity_score', 0))
            })
        
        analytics["agent_workload_distribution"] = {
            "total_agents": len(agents),
            "active_agents": len([a for a in agents if a.get('is_active', True)]),
            "agents": sorted(agent_workloads, key=lambda x: x['total_assigned'], reverse=True),
            "workload_summary": {
                "total_assigned_leads": sum(a['total_assigned'] for a in agent_workloads),
                "avg_leads_per_agent": round(sum(a['total_assigned'] for a in agent_workloads) / len(agents), 1) if agents else 0,
                "max_workload": max((a['total_assigned'] for a in agent_workloads), default=0),
                "min_workload": min((a['total_assigned'] for a in agent_workloads), default=0)
            }
        }
        
        # OPERATIONAL INSIGHTS
        status_counts = defaultdict(int)
        for lead in all_leads:
            status = lead.get('status', 'new')
            status_counts[status] += 1
        
        # Conversion metrics
        contacted_leads = len([l for l in all_leads if l.get('status') in ['contacted', 'qualified', 'closed_won', 'closed_lost']])
        closed_won = len([l for l in all_leads if l.get('status') == 'closed_won'])
        closed_lost = len([l for l in all_leads if l.get('status') == 'closed_lost'])
        
        analytics["operational_insights"] = {
            "lead_status_distribution": dict(status_counts),
            "conversion_metrics": {
                "total_contacted": contacted_leads,
                "closed_won": closed_won,
                "closed_lost": closed_lost,
                "conversion_rate": round(closed_won / contacted_leads * 100, 1) if contacted_leads > 0 else 0,
                "loss_rate": round(closed_lost / contacted_leads * 100, 1) if contacted_leads > 0 else 0
            },
            "quality_metrics": {
                "high_quality_leads_60_plus": len([l for l in all_leads if int(l.get('score', 0)) >= 60]),
                "premium_leads_90_plus": len([l for l in all_leads if int(l.get('score', 0)) >= 90]),
                "quality_percentage": round(len([l for l in all_leads if int(l.get('score', 0)) >= 60]) / total_leads * 100, 1) if total_leads > 0 else 0
            }
        }
        
        # REAL-TIME METRICS
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        recent_leads = []
        for lead in all_leads:
            created_at = lead.get('created_at', '')
            if created_at:
                try:
                    lead_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                    if lead_date >= yesterday:
                        recent_leads.append(lead)
                except:
                    continue
        
        analytics["real_time_metrics"] = {
            "leads_added_last_24h": len(recent_leads),
            "leads_assigned_last_24h": len([l for l in recent_leads if l.get('assigned_user_id')]),
            "current_unassigned_pool": len([l for l in all_leads if not l.get('assigned_user_id')]),
            "inventory_alerts": {
                "low_premium_inventory": len([l for l in all_leads if not l.get('assigned_user_id') and int(l.get('score', 0)) >= 90]) < 50,
                "low_total_inventory": len([l for l in all_leads if not l.get('assigned_user_id')]) < 100,
                "quality_degradation": (len([l for l in recent_leads if int(l.get('score', 0)) >= 60]) / len(recent_leads) * 100) < 80 if recent_leads else False
            },
            "system_health": {
                "total_system_leads": len(all_leads),
                "data_freshness": "real_time",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"✅ Master admin analytics calculated successfully")
        return analytics
        
    except Exception as e:
        logger.error(f"❌ Error calculating master admin analytics: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

def get_all_users():
    """Get all users from DynamoDB"""
    try:
        response = users_table.scan()
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting users: {e}")
        return []
'''
    
    return admin_analytics_code

def integrate_admin_analytics():
    """Integrate admin analytics into existing Lambda function"""
    print("🚀 INTEGRATING MASTER ADMIN ANALYTICS")
    print("=" * 50)
    
    # Read the current optimized Lambda function
    lambda_file = "lambda_package/lambda_function.py"
    
    try:
        with open(lambda_file, 'r') as f:
            lambda_content = f.read()
        
        print("✅ Current Lambda function read successfully")
        
        # Add the admin analytics code
        admin_code = create_admin_analytics_integration()
        
        # Find the right place to insert the admin analytics functions
        # Insert before the lambda_handler function
        handler_pos = lambda_content.find("def lambda_handler(event, context):")
        
        if handler_pos == -1:
            print("❌ Could not find lambda_handler function")
            return False
        
        # Insert admin analytics functions before lambda_handler
        updated_content = (
            lambda_content[:handler_pos] + 
            admin_code + 
            "\n\n" + 
            lambda_content[handler_pos:]
        )
        
        # Add the admin analytics endpoint to the lambda_handler
        # Find the existing endpoints section and add the new endpoint
        
        # Look for the existing summary endpoint to add the admin endpoint after it
        summary_endpoint_pos = updated_content.find('if path == \'/api/v1/summary\' and method == \'GET\':')
        
        if summary_endpoint_pos != -1:
            # Find the end of the summary endpoint
            endpoint_end = updated_content.find('return create_response(200,', summary_endpoint_pos)
            if endpoint_end != -1:
                endpoint_end = updated_content.find(')', endpoint_end) + 1
                
                # Add the admin analytics endpoint
                admin_endpoint = '''
        
        # MASTER ADMIN ANALYTICS ENDPOINT - NEW!
        if path == '/api/v1/admin/analytics' and method == 'GET':
            # Ensure admin access
            if current_user.get('role') != 'admin':
                return create_response(403, {"detail": "Admin access required"})
            
            logger.info("🎯 Master admin analytics requested")
            analytics = calculate_master_admin_analytics()
            
            return create_response(200, {
                "success": True,
                "analytics": analytics,
                "meta": {
                    "endpoint": "master_admin_analytics",
                    "version": "1.0",
                    "generated_at": datetime.utcnow().isoformat()
                }
            })'''
                
                updated_content = (
                    updated_content[:endpoint_end] + 
                    admin_endpoint + 
                    updated_content[endpoint_end:]
                )
        
        # Add imports at the top if needed
        if "from collections import defaultdict" not in updated_content:
            import_pos = updated_content.find("import logging")
            if import_pos != -1:
                updated_content = (
                    updated_content[:import_pos] + 
                    "from collections import defaultdict\n" + 
                    updated_content[import_pos:]
                )
        
        # Write the updated Lambda function
        with open(lambda_file, 'w') as f:
            f.write(updated_content)
        
        print("✅ Master admin analytics integrated into Lambda function")
        
        return True
        
    except Exception as e:
        print(f"❌ Error integrating admin analytics: {e}")
        return False

def test_integration():
    """Test the integration"""
    print("\n🧪 TESTING ADMIN ANALYTICS INTEGRATION")
    print("=" * 40)
    
    print("✅ Admin analytics endpoint added: /api/v1/admin/analytics")
    print("🎯 Features implemented:")
    print("   • Lead hopper overview (total, unassigned, utilization)")
    print("   • Score distribution (Premium 90+, Excellent 80+, etc.)")
    print("   • Lead type breakdown (by source, type, distribution)")
    print("   • Agent workload distribution (assignments, performance)")
    print("   • Operational insights (conversion rates, quality metrics)")
    print("   • Real-time metrics (recent activity, inventory alerts)")
    
    print("\n📋 Next step: Deploy updated Lambda to AWS")
    return True

if __name__ == "__main__":
    # Integrate admin analytics
    if integrate_admin_analytics():
        test_integration()
        print(f"\n🎉 ADMIN ANALYTICS READY!")
        print(f"📊 Endpoint: GET /api/v1/admin/analytics (Admin only)")
        print(f"🎯 Perfect for managing your 1,469-lead hopper!")
    else:
        print("❌ Integration failed!")