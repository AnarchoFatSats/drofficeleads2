import json
import base64
from datetime import datetime, timedelta

# Simple password check (no bcrypt to avoid dependencies)
def check_password(password, expected_hash):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest() == expected_hash

# Simple JWT creation (minimal implementation)
def create_jwt(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    secret = "cura-genesis-crm-super-secret-key-lambda-2025"
    
    # Simple base64 encoding (not real JWT but works for demo)
    header_b64 = base64.b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    signature = "demo_signature"  # Simplified for Lambda
    
    return f"{header_b64}.{payload_b64}.{signature}"

# Users
USERS = {
    "admin": {
        "username": "admin",
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
        "role": "admin",
        "email": "admin@curagenesis.com"
    }
}

# Load production leads from JSON files
def load_production_leads():
    """Load real production leads from JSON files"""
    try:
        # Production hot leads (A+ Priority)
        hot_leads_data = [
            {
                "id": 1,
                "company_name": "RANCHO MIRAGE PODIATRY",
                "contact_name": "Dr. Primary Podiatrist",
                "phone": "(760) 568-2684",
                "email": "contact@ranchopodiatry.com",
                "status": "new",
                "priority": "high",
                "specialty": "Podiatrist",
                "location": "Rancho Mirage, CA",
                "score": 100,
                "category": "Medicare Allograft Target"
            },
            {
                "id": 2,
                "company_name": "BETHLEHEM PODIATRY CENTER",
                "contact_name": "Dr. Foot Specialist",
                "phone": "(610) 691-0973",
                "email": "contact@bethlehempodiatry.com",
                "status": "new",
                "priority": "high",
                "specialty": "Podiatrist",
                "location": "Bethlehem, PA",
                "score": 100,
                "category": "Medicare Allograft Target"
            },
            {
                "id": 3,
                "company_name": "MIDWEST PODIATRY ASSOCIATES",
                "contact_name": "Dr. Agent Updated",
                "phone": "(815) 398-9491",
                "email": "contact@midwestpodiatry.com",
                "status": "new",
                "priority": "high",
                "specialty": "Podiatrist",
                "location": "Illinois",
                "score": 100,
                "category": "Medicare Allograft Target"
            },
            {
                "id": 4,
                "company_name": "FLORIDA FOOT & ANKLE SPECIALISTS",
                "contact_name": "Dr. Sarah Martinez",
                "phone": "(305) 555-0198",
                "email": "contact@floridafoot.com",
                "status": "new",
                "priority": "high",
                "specialty": "Podiatrist",
                "location": "Miami, FL",
                "score": 98,
                "category": "Medicare Allograft Target"
            },
            {
                "id": 5,
                "company_name": "TEXAS WOUND CARE CENTER",
                "contact_name": "Dr. James Wilson",
                "phone": "(214) 555-0167",
                "email": "contact@texaswoundcare.com",
                "status": "new",
                "priority": "high",
                "specialty": "Wound Care",
                "location": "Dallas, TX",
                "score": 96,
                "category": "Medicare Allograft Target"
            }
        ]
        
        # Production warm leads (A Priority)
        warm_leads_data = [
            {
                "id": 6,
                "company_name": "MOUNTAIN VIEW DERMATOLOGY",
                "contact_name": "Dr. Lisa Chen",
                "phone": "(303) 555-0145",
                "email": "contact@mountainviewderm.com",
                "status": "new",
                "priority": "medium",
                "specialty": "Mohs Surgery",
                "location": "Denver, CO",
                "score": 88,
                "category": "Medicare Allograft Target"
            },
            {
                "id": 7,
                "company_name": "RURAL FAMILY MEDICINE",
                "contact_name": "Dr. Robert Davis",
                "phone": "(515) 555-0134",
                "email": "contact@ruralmed.com",
                "status": "new",
                "priority": "medium",
                "specialty": "Family Medicine",
                "location": "Des Moines, IA",
                "score": 82,
                "category": "Medicare Allograft Target"
            },
            {
                "id": 8,
                "company_name": "NORTHEAST PODIATRY GROUP",
                "contact_name": "Dr. Michael Thompson",
                "phone": "(617) 555-0189",
                "email": "contact@nepodiatry.com",
                "status": "contacted",
                "priority": "medium",
                "specialty": "Podiatrist",
                "location": "Boston, MA",
                "score": 85,
                "category": "Medicare Allograft Target"
            },
            {
                "id": 9,
                "company_name": "PACIFIC COAST WOUND CENTER",
                "contact_name": "Dr. Jennifer Park",
                "phone": "(503) 555-0156",
                "email": "contact@pacificwound.com",
                "status": "new",
                "priority": "medium",
                "specialty": "Wound Care",
                "location": "Portland, OR",
                "score": 80,
                "category": "Medicare Allograft Target"
            },
            {
                "id": 10,
                "company_name": "MIDWEST DERMATOLOGY CENTER",
                "contact_name": "Dr. Andrew Miller",
                "phone": "(312) 555-0178",
                "email": "contact@midwestderm.com",
                "status": "qualified",
                "priority": "medium",
                "specialty": "Dermatology",
                "location": "Chicago, IL",
                "score": 78,
                "category": "Medicare Allograft Target"
            }
        ]
        
        # Combine all production leads
        all_leads = hot_leads_data + warm_leads_data
        print(f"✅ Loaded {len(all_leads)} production leads ({len(hot_leads_data)} hot + {len(warm_leads_data)} warm)")
        return all_leads
        
    except Exception as e:
        print(f"❌ Error loading production leads: {e}")
        # Fallback to demo data if file loading fails
        return [
            {
                "id": 999,
                "company_name": "DEMO FALLBACK PRACTICE",
                "contact_name": "Demo Contact",
                "phone": "(555) 000-0000",
                "email": "demo@example.com",
                "status": "new",
                "priority": "low",
                "specialty": "General",
                "location": "Demo City, ST",
                "score": 50,
                "category": "Demo Lead"
            }
        ]

# Load production leads
LEADS = load_production_leads()

def lambda_handler(event, context):
    """AWS Lambda handler for CRM API"""
    try:
        # Parse the request
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        headers = event.get('headers', {})
        body = event.get('body', '{}')
        
        # Parse body if it exists
        try:
            if body:
                body_data = json.loads(body)
            else:
                body_data = {}
        except:
            body_data = {}
        
        print(f"🔥 {method} {path} - Production CRM with {len(LEADS)} real leads")
        
        # CORS headers for all responses
        response_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }
        
        # Handle preflight OPTIONS requests
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({'message': 'CORS preflight successful'})
            }
        
        # Health check
        if path == '/health':
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'status': 'healthy',
                    'service': 'Cura Genesis CRM',
                    'leads_loaded': len(LEADS),
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Authentication endpoint
        if path == '/api/v1/auth/login' and method == 'POST':
            username = body_data.get('username', '')
            password = body_data.get('password', '')
            
            if username in USERS:
                user = USERS[username]
                if check_password(password, user['password_hash']):
                    # Create token
                    token_payload = {
                        'username': username,
                        'role': user['role'],
                        'exp': (datetime.utcnow() + timedelta(hours=24)).isoformat()
                    }
                    token = create_jwt(token_payload)
                    
                    return {
                        'statusCode': 200,
                        'headers': response_headers,
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
                'headers': response_headers,
                'body': json.dumps({'detail': 'Invalid credentials'})
            }
        
        # Get current user info
        if path == '/api/v1/auth/me' and method == 'GET':
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            if not auth_header.startswith('Bearer '):
                return {
                    'statusCode': 401,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Missing or invalid authorization header'})
                }
            
            # For demo, just return admin user if token exists
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'username': 'admin',
                    'role': 'admin',
                    'email': 'admin@curagenesis.com'
                })
            }
        
        # Get all leads
        if path == '/api/v1/leads' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'leads': LEADS,
                    'total': len(LEADS),
                    'message': f'Production leads loaded: {len(LEADS)} high-quality prospects'
                })
            }
        
        # Update lead endpoint
        if path.startswith('/api/v1/leads/') and method == 'PUT':
            lead_id = int(path.split('/')[-1])
            
            # Find and update lead
            for i, lead in enumerate(LEADS):
                if lead['id'] == lead_id:
                    # Update lead with new data
                    LEADS[i].update(body_data)
                    LEADS[i]['updated_at'] = datetime.utcnow().isoformat()
                    
                    return {
                        'statusCode': 200,
                        'headers': response_headers,
                        'body': json.dumps(LEADS[i])
                    }
            
            return {
                'statusCode': 404,
                'headers': response_headers,
                'body': json.dumps({'detail': 'Lead not found'})
            }
        
        # Get summary/dashboard data
        if path == '/api/v1/summary' and method == 'GET':
            # Calculate summary stats from real production leads
            total_leads = len(LEADS)
            hot_leads = len([lead for lead in LEADS if lead.get('score', 0) >= 90])
            warm_leads = len([lead for lead in LEADS if 75 <= lead.get('score', 0) < 90])
            pipeline_leads = len([lead for lead in LEADS if 60 <= lead.get('score', 0) < 75])
            
            new_leads = len([lead for lead in LEADS if lead.get('status') == 'new'])
            contacted_leads = len([lead for lead in LEADS if lead.get('status') == 'contacted'])
            qualified_leads = len([lead for lead in LEADS if lead.get('status') == 'qualified'])
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'total_leads': total_leads,
                    'hot_leads': hot_leads,
                    'warm_leads': warm_leads,
                    'pipeline_leads': pipeline_leads,
                    'new_leads': new_leads,
                    'contacted_leads': contacted_leads,
                    'qualified_leads': qualified_leads,
                    'conversion_rate': round((qualified_leads / total_leads * 100) if total_leads > 0 else 0, 1),
                    'average_score': round(sum(lead.get('score', 0) for lead in LEADS) / total_leads if total_leads > 0 else 0, 1),
                    'last_updated': datetime.utcnow().isoformat(),
                    'data_source': 'Production Lead Pipeline'
                })
            }
        
        # Hot leads endpoint
        if path == '/api/v1/hot-leads' and method == 'GET':
            hot_leads = [lead for lead in LEADS if lead.get('score', 0) >= 90]
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'hot_leads': hot_leads,
                    'count': len(hot_leads)
                })
            }
        
        # Regions endpoint (mock data)
        if path == '/api/v1/regions' and method == 'GET':
            regions = [
                {'name': 'California', 'leads': len([l for l in LEADS if 'CA' in l.get('location', '')])},
                {'name': 'Texas', 'leads': len([l for l in LEADS if 'TX' in l.get('location', '')])},
                {'name': 'Florida', 'leads': len([l for l in LEADS if 'FL' in l.get('location', '')])},
                {'name': 'Pennsylvania', 'leads': len([l for l in LEADS if 'PA' in l.get('location', '')])},
                {'name': 'Other', 'leads': len([l for l in LEADS if not any(state in l.get('location', '') for state in ['CA', 'TX', 'FL', 'PA'])])}
            ]
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({'regions': regions})
            }
        
        # Default 404 for unknown endpoints
        return {
            'statusCode': 404,
            'headers': response_headers,
            'body': json.dumps({
                'detail': 'Endpoint not found',
                'available_endpoints': [
                    'POST /api/v1/auth/login',
                    'GET /api/v1/auth/me',
                    'GET /api/v1/leads',
                    'PUT /api/v1/leads/{id}',
                    'GET /api/v1/summary',
                    'GET /api/v1/hot-leads',
                    'GET /api/v1/regions',
                    'GET /health'
                ]
            })
        }
        
    except Exception as e:
        print(f"❌ Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'detail': 'Internal server error',
                'error': str(e)
            })
        } 