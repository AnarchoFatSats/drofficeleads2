#!/usr/bin/env python3
"""
Enhanced VantagePoint CRM Lambda with Master Admin Analytics
==========================================================
Adds comprehensive admin analytics for lead hopper management and conversion tracking
"""

import json
import hashlib
import base64
import hmac
from datetime import datetime, timedelta
import random
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
import logging
from collections import defaultdict

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB clients for persistent storage
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('vantagepoint-users')
leads_table = dynamodb.Table('vantagepoint-leads')

# Helper function to handle DynamoDB Decimal types in JSON
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def json_dumps(obj):
    """JSON dumps that handles DynamoDB Decimal types"""
    return json.dumps(obj, default=decimal_default)

def create_jwt_token(username, role):
    """Create a simple JWT token"""
    import time
    
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    
    payload = {
        "username": username,
        "role": role,
        "exp": int(time.time()) + 3600  # 1 hour expiry
    }
    
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    secret = "your-secret-key"
    signature = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
    ).decode().rstrip('=')
    
    return f"{header_b64}.{payload_b64}.{signature}"

def verify_jwt_token(token):
    """Verify JWT token and return payload"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
            
        header_b64, payload_b64, signature = parts
        
        secret = "your-secret-key"
        expected_signature = base64.urlsafe_b64encode(
            hmac.new(secret.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
        ).decode().rstrip('=')
        
        if signature != expected_signature:
            return None
        
        payload_json = base64.urlsafe_b64decode(payload_b64 + '==').decode()
        payload = json.loads(payload_json)
        
        import time
        if payload.get('exp', 0) < time.time():
            return None
            
        return payload
    except:
        return None

def create_response(status_code, body):
    """Create proper CORS response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json_dumps(body)
    }

def get_user_by_username(username):
    """Get user from DynamoDB by username"""
    try:
        response = users_table.scan(
            FilterExpression='username = :username',
            ExpressionAttributeValues={':username': username}
        )
        users = response.get('Items', [])
        return users[0] if users else None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def get_all_leads():
    """Get all leads from DynamoDB"""
    try:
        response = leads_table.scan(
            FilterExpression='attribute_exists(id) AND id > :zero',
            ExpressionAttributeValues={':zero': 0}
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting leads: {e}")
        return []

def get_all_users():
    """Get all users from DynamoDB"""
    try:
        response = users_table.scan()
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting users: {e}")
        return []

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
        # Lead status distribution
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
        # Recent activity (last 24 hours)
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        recent_leads = []
        for lead in all_leads:
            created_at = lead.get('created_at', '')
            if created_at:
                try:
                    # Parse ISO format datetime
                    lead_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                    if lead_date >= yesterday:
                        recent_leads.append(lead)
                except:
                    continue
        
        analytics["real_time_metrics"] = {
            "leads_added_last_24h": len(recent_leads),
            "leads_assigned_last_24h": len([l for l in recent_leads if l.get('assigned_user_id')]),
            "current_unassigned_pool": len(unassigned_leads),
            "inventory_alerts": {
                "low_premium_inventory": len([l for l in unassigned_leads if int(l.get('score', 0)) >= 90]) < 50,
                "low_total_inventory": len(unassigned_leads) < 100,
                "quality_degradation": (len([l for l in recent_leads if int(l.get('score', 0)) >= 60]) / len(recent_leads) * 100) < 80 if recent_leads else False
            },
            "system_health": {
                "total_system_leads": total_leads,
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

# ... (keep all existing functions for authentication, lead management, etc.) ...

def lambda_handler(event, context):
    """AWS Lambda handler with master admin analytics"""
    
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return create_response(200, {})
        
        # Extract request info
        path = event.get('path', '')
        method = event.get('httpMethod', 'GET')
        headers = event.get('headers', {})
        
        # Parse body
        body = event.get('body', '{}')
        if body:
            try:
                body_data = json.loads(body)
            except:
                body_data = {}
        else:
            body_data = {}
        
        print(f"Request: {method} {path}")
        
        # Health check
        if path == '/health' and method == 'GET':
            return create_response(200, {
                "status": "healthy", 
                "service": "VantagePoint CRM", 
                "features": ["optimized_bulk_upload", "master_admin_analytics"],
                "version": "2.0"
            })
        
        # Authentication endpoint
        if path == '/api/v1/auth/login' and method == 'POST':
            username = body_data.get('username')
            password = body_data.get('password')
            
            if not username or not password:
                return create_response(400, {"detail": "Username and password required"})
            
            user = get_user_by_username(username)
            if user and user.get('password') == password:
                token = create_jwt_token(username, user.get('role', 'agent'))
                return create_response(200, {
                    "access_token": token,
                    "token_type": "bearer",
                    "user": {
                        "id": user.get('id'),
                        "username": user.get('username'),
                        "role": user.get('role')
                    }
                })
            else:
                return create_response(401, {"detail": "Invalid credentials"})
        
        # Authentication check for protected endpoints
        protected_endpoints = ['/api/v1/leads', '/api/v1/auth/me', '/api/v1/admin']
        if any(path.startswith(endpoint) for endpoint in protected_endpoints):
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            if not auth_header or not auth_header.startswith('Bearer '):
                return create_response(401, {"detail": "Authorization header required"})
            
            token = auth_header.replace('Bearer ', '')
            payload = verify_jwt_token(token)
            if not payload:
                return create_response(401, {"detail": "Invalid or expired token"})
            
            current_user = get_user_by_username(payload.get('username'))
            if not current_user:
                return create_response(401, {"detail": "User not found"})
        
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
            })
        
        # ... (keep all existing endpoints) ...
        
        return create_response(404, {"detail": "Endpoint not found"})
        
    except Exception as e:
        logger.error(f"Lambda error: {e}")
        return create_response(500, {"detail": f"Internal server error: {str(e)}"})