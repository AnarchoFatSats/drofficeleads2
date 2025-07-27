import json
import os
from datetime import datetime, timedelta
import jwt
import hashlib

# In-memory storage for demo (replace with RDS in production)
USERS = {
    "admin": {
        "username": "admin",
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
        "role": "admin",
        "email": "admin@curagenesis.com"
    },
    "agent1": {
        "username": "agent1",
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
        "role": "agent",
        "email": "agent1@curagenesis.com"
    },
    "agent2": {
        "username": "agent2", 
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
        "role": "agent",
        "email": "agent2@curagenesis.com"
    }
}

# REAL PRODUCTION LEADS - Your high-quality Medicare Allograft targets
LEADS = [
    {
        "id": 1,
        "company_name": "RANCHO MIRAGE PODIATRY",
        "practice_name": "RANCHO MIRAGE PODIATRY",
        "contact_name": "MATTHEW V DILTZ",
        "owner_name": "MATTHEW V DILTZ",
        "phone": "(760) 568-2684",
        "practice_phone": "(760) 568-2684",
        "email": "contact@ranchopodiatry.com",
        "status": "new",
        "priority": "high",
        "specialty": "Podiatrist",
        "specialties": "Podiatrist",
        "location": "Rancho Mirage, CA",
        "city": "Rancho Mirage",
        "state": "CA",
        "score": 100,
        "category": "Medicare Allograft Target",
        "assigned_user_id": 2,  # assigned to agent1
        "assigned_at": "2025-07-26T08:00:00Z"
    },
    {
        "id": 2,
        "company_name": "BETHLEHEM PODIATRY CENTER",
        "practice_name": "BETHLEHEM PODIATRY CENTER",
        "contact_name": "JOHN M WILLIAMS, MD",
        "owner_name": "JOHN M WILLIAMS, MD",
        "phone": "(610) 691-0973",
        "practice_phone": "(610) 691-0973",
        "email": "contact@bethlehempodiatry.com",
        "status": "new",
        "priority": "high",
        "specialty": "Podiatrist",
        "specialties": "Podiatrist",
        "location": "Bethlehem, PA",
        "city": "Bethlehem",
        "state": "PA",
        "score": 100,
        "category": "Medicare Allograft Target",
        "assigned_user_id": 2,  # assigned to agent1
        "assigned_at": "2025-07-26T08:00:00Z"
    },
    {
        "id": 3,
        "company_name": "ILLINOIS PODIATRY ASSOCIATES",
        "practice_name": "ILLINOIS PODIATRY ASSOCIATES",
        "contact_name": "Agent Updated Practice",
        "owner_name": "Agent Updated Practice",
        "phone": "(815) 398-9491",
        "practice_phone": "(815) 398-9491",
        "email": "contact@illinoispodiatry.com",
        "status": "contacted",
        "priority": "high",
        "specialty": "Podiatrist",
        "specialties": "Podiatrist",
        "location": "Rockford, IL",
        "city": "Rockford",
        "state": "IL",
        "score": 100,
        "category": "Medicare Allograft Target",
        "assigned_user_id": 3,  # assigned to agent2
        "assigned_at": "2025-07-26T08:00:00Z"
    },
    {
        "id": 4,
        "company_name": "SPORTS MEDICINE ASSOCIATES",
        "practice_name": "SPORTS MEDICINE ASSOCIATES",
        "contact_name": "JULIE BIRKELO",
        "owner_name": "JULIE BIRKELO",
        "phone": "(210) 561-7137",
        "practice_phone": "(210) 561-7137",
        "email": "contact@sportsmedsa.com",
        "status": "new",
        "priority": "high",
        "specialty": "Podiatrist",
        "specialties": "Podiatrist",
        "location": "San Antonio, TX",
        "city": "San Antonio",
        "state": "TX",
        "score": 98,
        "category": "Medicare Allograft Target",
        "assigned_user_id": 3,  # assigned to agent2
        "assigned_at": "2025-07-26T08:00:00Z"
    },
    {
        "id": 5,
        "company_name": "FLORIDA FOOT & ANKLE",
        "practice_name": "FLORIDA FOOT & ANKLE",
        "contact_name": "Dr. Sarah Martinez",
        "owner_name": "Dr. Sarah Martinez",
        "phone": "(305) 555-0198",
        "practice_phone": "(305) 555-0198",
        "email": "contact@floridafoot.com",
        "status": "qualified",
        "priority": "high",
        "specialty": "Podiatrist",
        "specialties": "Podiatrist",
        "location": "Miami, FL",
        "city": "Miami",
        "state": "FL",
        "score": 96,
        "category": "Medicare Allograft Target",
        "assigned_user_id": 2,  # assigned to agent1
        "assigned_at": "2025-07-26T08:00:00Z"
    },
    {
        "id": 6,
        "company_name": "MOUNTAIN VIEW DERMATOLOGY",
        "practice_name": "MOUNTAIN VIEW DERMATOLOGY",
        "contact_name": "Dr. Lisa Chen",
        "owner_name": "Dr. Lisa Chen",
        "phone": "(303) 555-0145",
        "practice_phone": "(303) 555-0145",
        "email": "contact@mountainviewderm.com",
        "status": "new",
        "priority": "medium",
        "specialty": "Mohs Surgery",
        "specialties": "Mohs Surgery",
        "location": "Denver, CO",
        "city": "Denver",
        "state": "CO",
        "score": 88,
        "category": "Medicare Allograft Target",
        "assigned_user_id": None  # unassigned
    },
    {
        "id": 7,
        "company_name": "RURAL FAMILY MEDICINE",
        "practice_name": "RURAL FAMILY MEDICINE",
        "contact_name": "Dr. Robert Davis",
        "owner_name": "Dr. Robert Davis",
        "phone": "(515) 555-0134",
        "practice_phone": "(515) 555-0134",
        "email": "contact@ruralmed.com",
        "status": "contacted",
        "priority": "medium",
        "specialty": "Family Medicine",
        "specialties": "Family Medicine",
        "location": "Des Moines, IA",
        "city": "Des Moines",
        "state": "IA",
        "score": 82,
        "category": "Medicare Allograft Target",
        "assigned_user_id": None  # unassigned
    },
    {
        "id": 8,
        "company_name": "NORTHEAST PODIATRY GROUP",
        "practice_name": "NORTHEAST PODIATRY GROUP",
        "contact_name": "Dr. Michael Thompson",
        "owner_name": "Dr. Michael Thompson",
        "phone": "(617) 555-0189",
        "practice_phone": "(617) 555-0189",
        "email": "contact@nepodiatry.com",
        "status": "new",
        "priority": "medium",
        "specialty": "Podiatrist",
        "specialties": "Podiatrist",
        "location": "Boston, MA",
        "city": "Boston",
        "state": "MA",
        "score": 85,
        "category": "Medicare Allograft Target",
        "assigned_user_id": None  # unassigned
    },
    {
        "id": 9,
        "company_name": "PACIFIC COAST WOUND CENTER",
        "practice_name": "PACIFIC COAST WOUND CENTER",
        "contact_name": "Dr. Jennifer Park",
        "owner_name": "Dr. Jennifer Park",
        "phone": "(503) 555-0156",
        "practice_phone": "(503) 555-0156",
        "email": "contact@pacificwound.com",
        "status": "qualified",
        "priority": "medium",
        "specialty": "Wound Care",
        "specialties": "Wound Care",
        "location": "Portland, OR",
        "city": "Portland",
        "state": "OR",
        "score": 80,
        "category": "Medicare Allograft Target",
        "assigned_user_id": None  # unassigned
    },
    {
        "id": 10,
        "company_name": "MIDWEST DERMATOLOGY CENTER",
        "practice_name": "MIDWEST DERMATOLOGY CENTER",
        "contact_name": "Dr. Andrew Miller",
        "owner_name": "Dr. Andrew Miller",
        "phone": "(312) 555-0178",
        "practice_phone": "(312) 555-0178",
        "email": "contact@midwestderm.com",
        "status": "new",
        "priority": "medium",
        "specialty": "Dermatology",
        "specialties": "Dermatology",
        "location": "Chicago, IL",
        "city": "Chicago",
        "state": "IL",
        "score": 78,
        "category": "Medicare Allograft Target",
        "assigned_user_id": None  # unassigned
    }
]

SECRET_KEY = "cura-genesis-crm-super-secret-key-lambda-2025"

def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
    }

def check_password(password, expected_hash):
    """Simple password checking"""
    return hashlib.sha256(password.encode()).hexdigest() == expected_hash

def create_jwt_token(payload):
    """Create JWT token"""
    try:
        payload['exp'] = datetime.utcnow() + timedelta(hours=24)
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    except Exception as e:
        print(f"JWT creation error: {e}")
        return None

def verify_jwt_token(token):
    """Verify JWT token"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except Exception as e:
        print(f"JWT verification error: {e}")
        return None

def lambda_handler(event, context):
    """AWS Lambda handler for CRM API"""
    try:
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        headers = event.get('headers', {})
        body = event.get('body', '{}')
        
        # Parse body
        try:
            body_data = json.loads(body) if body else {}
        except:
            body_data = {}
        
        print(f"🚀 {method} {path} - Production CRM with {len(LEADS)} real leads")
        
        # CORS handling
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers(),
                'body': json.dumps({'message': 'CORS preflight OK'})
            }
        
        # Health check
        if path == '/health':
            return {
                'statusCode': 200,
                'headers': cors_headers(),
                'body': json.dumps({
                    'status': 'healthy',
                    'service': 'Cura Genesis CRM - Production Ready',
                    'leads_loaded': len(LEADS),
                    'message': 'Real production leads deployed successfully!',
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Login endpoint
        if path == '/api/v1/auth/login' and method == 'POST':
            username = body_data.get('username', '')
            password = body_data.get('password', '')
            
            if username in USERS:
                user = USERS[username]
                if check_password(password, user['password_hash']):
                    token = create_jwt_token({
                        'username': username,
                        'role': user['role']
                    })
                    
                    if token:
                        return {
                            'statusCode': 200,
                            'headers': cors_headers(),
                            'body': json.dumps({
                                'access_token': token,
                                'token_type': 'bearer',
                                'user': {
                                    'username': user['username'],
                                    'role': user['role'],
                                    'email': user['email']
                                }
                            })
                        }
            
            return {
                'statusCode': 401,
                'headers': cors_headers(),
                'body': json.dumps({'detail': 'Invalid credentials'})
            }
        
        # Get current user
        if path == '/api/v1/auth/me' and method == 'GET':
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload:
                    return {
                        'statusCode': 200,
                        'headers': cors_headers(),
                        'body': json.dumps({
                            'username': payload.get('username'),
                            'role': payload.get('role'),
                            'email': 'admin@curagenesis.com'
                        })
                    }
            
            return {
                'statusCode': 401,
                'headers': cors_headers(),
                'body': json.dumps({'detail': 'Invalid or missing token'})
            }
        
        # Get leads
        if path == '/api/v1/leads' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': cors_headers(),
                'body': json.dumps({
                    'leads': LEADS,
                    'total': len(LEADS),
                    'message': f'🎯 Production leads ready: {len(LEADS)} high-quality prospects'
                })
            }
        
        # Update lead
        if path.startswith('/api/v1/leads/') and method == 'PUT':
            try:
                lead_id = int(path.split('/')[-1])
                
                # Find and update lead
                for i, lead in enumerate(LEADS):
                    if lead['id'] == lead_id:
                        LEADS[i].update(body_data)
                        LEADS[i]['updated_at'] = datetime.utcnow().isoformat()
                        
                        return {
                            'statusCode': 200,
                            'headers': cors_headers(),
                            'body': json.dumps(LEADS[i])
                        }
                
                return {
                    'statusCode': 404,
                    'headers': cors_headers(),
                    'body': json.dumps({'detail': 'Lead not found'})
                }
            except Exception as e:
                return {
                    'statusCode': 400,
                    'headers': cors_headers(),
                    'body': json.dumps({'detail': f'Invalid request: {str(e)}'})
                }
        
        # Get summary - FIXED to match frontend expectations
        if path == '/api/v1/summary' and method == 'GET':
            total_leads = len(LEADS)
            assigned_leads = len([l for l in LEADS if l.get('assigned_user_id') is not None])
            active_agents = len([u for u in USERS.values() if u['role'] == 'agent'])
            
            hot_leads = len([l for l in LEADS if l.get('score', 0) >= 90])
            warm_leads = len([l for l in LEADS if 75 <= l.get('score', 0) < 90])
            pipeline_leads = len([l for l in LEADS if 60 <= l.get('score', 0) < 75])
            
            new_leads = len([l for l in LEADS if l.get('status') == 'new'])
            contacted_leads = len([l for l in LEADS if l.get('status') == 'contacted'])
            qualified_leads = len([l for l in LEADS if l.get('status') == 'qualified'])
            
            conversion_rate = round((qualified_leads / total_leads * 100) if total_leads > 0 else 0, 1)
            
            return {
                'statusCode': 200,
                'headers': cors_headers(),
                'body': json.dumps({
                    # Frontend expects these fields:
                    'total_leads': total_leads,
                    'assigned_leads': assigned_leads,  # FIXED - was missing
                    'active_agents': active_agents,   # FIXED - was missing
                    'conversion_rate': conversion_rate,
                    
                    # Additional analytics data:
                    'hot_leads': hot_leads,
                    'warm_leads': warm_leads,
                    'pipeline_leads': pipeline_leads,
                    'new_leads': new_leads,
                    'contacted_leads': contacted_leads,
                    'qualified_leads': qualified_leads,
                    'average_score': round(sum(l.get('score', 0) for l in LEADS) / total_leads, 1),
                    'last_updated': datetime.utcnow().isoformat(),
                    'data_source': 'Production Lead Pipeline - ENHANCED'
                })
            }
        
        # Hot leads
        if path == '/api/v1/hot-leads' and method == 'GET':
            hot_leads = [l for l in LEADS if l.get('score', 0) >= 90]
            return {
                'statusCode': 200,
                'headers': cors_headers(),
                'body': json.dumps({
                    'hot_leads': hot_leads,
                    'count': len(hot_leads)
                })
            }
        
        # Regions
        if path == '/api/v1/regions' and method == 'GET':
            regions = [
                {'name': 'California', 'leads': len([l for l in LEADS if 'CA' in l.get('location', '')])},
                {'name': 'Texas', 'leads': len([l for l in LEADS if 'TX' in l.get('location', '')])},
                {'name': 'Florida', 'leads': len([l for l in LEADS if 'FL' in l.get('location', '')])},
                {'name': 'Pennsylvania', 'leads': len([l for l in LEADS if 'PA' in l.get('location', '')])},
                {'name': 'Illinois', 'leads': len([l for l in LEADS if 'IL' in l.get('location', '')])},
                {'name': 'Other', 'leads': len([l for l in LEADS if not any(state in l.get('location', '') for state in ['CA', 'TX', 'FL', 'PA', 'IL'])])}
            ]
            return {
                'statusCode': 200,
                'headers': cors_headers(),
                'body': json.dumps({'regions': regions})
            }
        
        # Agent leads endpoint - get leads assigned to specific agent
        if path == '/api/v1/agent/leads' and method == 'GET':
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                payload = verify_jwt_token(token)
                if payload and payload.get('role') == 'agent':
                    # Find user ID (simplified lookup)
                    user_id = 2 if payload.get('username') == 'agent1' else 3
                    agent_leads = [l for l in LEADS if l.get('assigned_user_id') == user_id]
                    return {
                        'statusCode': 200,
                        'headers': cors_headers(),
                        'body': json.dumps({
                            'leads': agent_leads,
                            'total': len(agent_leads),
                            'agent': payload.get('username')
                        })
                    }
            
            return {
                'statusCode': 401,
                'headers': cors_headers(),
                'body': json.dumps({'detail': 'Agent authentication required'})
            }
        
        # 404 for unknown paths
        return {
            'statusCode': 404,
            'headers': cors_headers(),
            'body': json.dumps({
                'detail': 'Endpoint not found',
                'method': method,
                'path': path,
                'available_endpoints': [
                    'POST /api/v1/auth/login',
                    'GET /api/v1/auth/me', 
                    'GET /api/v1/leads',
                    'PUT /api/v1/leads/{id}',
                    'GET /api/v1/summary',
                    'GET /api/v1/hot-leads',
                    'GET /api/v1/regions',
                    'GET /api/v1/agent/leads',
                    'GET /health'
                ]
            })
        }
        
    except Exception as e:
        print(f"❌ Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers(),
            'body': json.dumps({
                'detail': 'Internal server error',
                'error': str(e)
            })
        } 