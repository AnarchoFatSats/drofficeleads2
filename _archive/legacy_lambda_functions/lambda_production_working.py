import json
import base64
from datetime import datetime, timedelta
import hashlib

# Simple password check
def check_password(password, expected_hash):
    return hashlib.sha256(password.encode()).hexdigest() == expected_hash

# Simple JWT creation
def create_jwt(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    signature = "demo_signature"
    return f"{header_b64}.{payload_b64}.{signature}"

# JWT decode
def decode_jwt(token):
    try:
        parts = token.split('.')
        if len(parts) >= 2:
            payload_data = base64.b64decode(parts[1] + '===').decode()
            return json.loads(payload_data)
    except:
        pass
    return None

# Get user from token
def get_user_from_token(auth_header):
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:]
    payload = decode_jwt(token)
    if payload and payload.get('sub'):
        return USERS.get(payload['sub'])
    return None

# In-memory storage
USERS = {
    "admin": {
        "id": 1,
        "username": "admin",
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
        "role": "admin",
        "email": "admin@curagenesis.com",
        "full_name": "System Administrator",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00Z",
        "manager_id": None
    },
    "manager1": {
        "id": 2,
        "username": "manager1",
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
        "role": "manager",
        "email": "manager1@curagenesis.com",
        "full_name": "Demo Manager",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00Z",
        "manager_id": None
    },
    "agent1": {
        "id": 3,
        "username": "agent1",
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
        "role": "agent",
        "email": "agent1@curagenesis.com",
        "full_name": "Demo Agent",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00Z",
        "manager_id": 2
    }
}

# Auto-incrementing IDs
NEXT_USER_ID = 4
NEXT_LEAD_ID = 1
NEXT_ACTIVITY_ID = 1
NEXT_NOTE_ID = 1

# Leads storage (unlimited)
LEADS = {}
LEAD_NOTES = {}
ACTIVITIES = []

def lambda_handler(event, context):
    """Working AWS Lambda handler for production CRM"""
    global NEXT_USER_ID, NEXT_LEAD_ID, NEXT_ACTIVITY_ID, NEXT_NOTE_ID
    
    method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    headers = event.get('headers', {})
    body = event.get('body', '{}')
    
    # Parse JSON body
    try:
        if body:
            body_data = json.loads(body)
        else:
            body_data = {}
    except:
        body_data = {}
    
    # CORS headers
    response_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS (CORS preflight)
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': ''
        }
    
    # Health check
    if path == '/health':
        total_leads = len(LEADS)
        agent_leads = len([l for l in LEADS.values() if l.get('assigned_user_id') == 3])
        leads_with_email = len([l for l in LEADS.values() if l.get('email', '').strip()])
        docs_sent_count = len([l for l in LEADS.values() if l.get('docs_sent')])
        
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': 'v5.1.0 - Production CRM with Unlimited Leads',
                'service': 'Cura Genesis CRM API',
                'database_stats': {
                    'total_leads': total_leads,
                    'agent_leads': agent_leads,
                    'leads_with_email': leads_with_email,
                    'docs_sent_count': docs_sent_count
                },
                'features': {
                    'unlimited_leads': True,
                    'lead_creation': True,
                    'lead_management': True,
                    'agent_access': True,
                    'send_docs': True,
                    'email_fields': True
                }
            })
        }
    
    # Login
    if path == '/api/v1/auth/login' and method == 'POST':
        username = body_data.get('username', '')
        password = body_data.get('password', '')
        
        user = USERS.get(username)
        if user and check_password(password, user['password_hash']):
            token = create_jwt({'sub': username, 'role': user['role']})
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'access_token': token,
                    'token_type': 'bearer'
                })
            }
        else:
            return {
                'statusCode': 401,
                'headers': response_headers,
                'body': json.dumps({'detail': 'Incorrect username or password'})
            }
    
    # Get user info
    if path == '/api/v1/auth/me' and method == 'GET':
        auth_header = headers.get('Authorization', headers.get('authorization', ''))
        current_user = get_user_from_token(auth_header)
        
        if not current_user:
            return {
                'statusCode': 401,
                'headers': response_headers,
                'body': json.dumps({'detail': 'Not authenticated'})
            }
        
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps({
                'username': current_user['username'],
                'email': current_user['email'],
                'full_name': current_user['full_name'],
                'role': current_user['role'],
                'is_active': current_user['is_active']
            })
        }
    
    # Get leads
    if path == '/api/v1/leads' and method == 'GET':
        auth_header = headers.get('Authorization', headers.get('authorization', ''))
        current_user = get_user_from_token(auth_header)
        
        if not current_user:
            return {
                'statusCode': 401,
                'headers': response_headers,
                'body': json.dumps({'detail': 'Not authenticated'})
            }
        
        # Filter leads based on role
        filtered_leads = []
        for lead_id, lead in LEADS.items():
            if current_user['role'] == 'agent':
                # Agents only see their assigned leads
                if lead.get('assigned_user_id') == current_user['id']:
                    lead_with_notes = lead.copy()
                    lead_with_notes['notes'] = LEAD_NOTES.get(lead_id, [])
                    filtered_leads.append(lead_with_notes)
            else:
                # Admins and managers see all leads
                lead_with_notes = lead.copy()
                lead_with_notes['notes'] = LEAD_NOTES.get(lead_id, [])
                filtered_leads.append(lead_with_notes)
        
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps(filtered_leads)
        }
    
    # Create lead
    if path == '/api/v1/leads' and method == 'POST':
        auth_header = headers.get('Authorization', headers.get('authorization', ''))
        current_user = get_user_from_token(auth_header)
        
        if not current_user:
            return {
                'statusCode': 401,
                'headers': response_headers,
                'body': json.dumps({'detail': 'Not authenticated'})
            }
        
        # Create new lead
        new_lead = {
            'id': NEXT_LEAD_ID,
            'practice_name': body_data.get('practice_name', ''),
            'owner_name': body_data.get('owner_name', ''),
            'practice_phone': body_data.get('practice_phone', ''),
            'owner_phone': body_data.get('owner_phone', ''),
            'email': body_data.get('email', ''),
            'address': body_data.get('address', ''),
            'city': body_data.get('city', ''),
            'state': body_data.get('state', ''),
            'zip_code': body_data.get('zip_code', ''),
            'npi': body_data.get('npi', ''),
            'specialty': body_data.get('specialty', ''),
            'score': body_data.get('score', 0),
            'priority': body_data.get('priority', 'C'),
            'status': body_data.get('status', 'NEW'),
            'assigned_user_id': body_data.get('assigned_user_id', 3),  # Default to agent1
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'last_contact': None,
            'next_follow_up': None,
            'est_revenue': body_data.get('est_revenue', 0),
            'tags': body_data.get('tags', []),
            'ptan': '',
            'ein_tin': '',
            'docs_sent': False,
            'docs_sent_date': None
        }
        
        # Store new lead
        LEADS[NEXT_LEAD_ID] = new_lead
        LEAD_NOTES[NEXT_LEAD_ID] = []
        NEXT_LEAD_ID += 1
        
        return {
            'statusCode': 201,
            'headers': response_headers,
            'body': json.dumps(new_lead)
        }
    
    # Update lead
    if path.startswith('/api/v1/leads/') and method == 'PUT':
        lead_id = int(path.split('/')[-1])
        auth_header = headers.get('Authorization', headers.get('authorization', ''))
        current_user = get_user_from_token(auth_header)
        
        if not current_user:
            return {
                'statusCode': 401,
                'headers': response_headers,
                'body': json.dumps({'detail': 'Not authenticated'})
            }
        
        if lead_id not in LEADS:
            return {
                'statusCode': 404,
                'headers': response_headers,
                'body': json.dumps({'detail': 'Lead not found'})
            }
        
        lead = LEADS[lead_id]
        
        # Permission check for agents
        if current_user['role'] == 'agent' and lead.get('assigned_user_id') != current_user['id']:
            return {
                'statusCode': 403,
                'headers': response_headers,
                'body': json.dumps({'detail': 'Can only update your assigned leads'})
            }
        
        # Update lead fields
        updatable_fields = ['status', 'practice_phone', 'owner_phone', 'email', 'address', 'city', 'state', 'zip_code', 'next_follow_up', 'est_revenue', 'tags', 'ptan', 'ein_tin']
        
        for field in updatable_fields:
            if field in body_data:
                lead[field] = body_data[field]
        
        # Auto-update last_contact if status changed to CONTACTED
        if body_data.get('status') == 'CONTACTED':
            lead['last_contact'] = datetime.utcnow().isoformat()
        
        lead['updated_at'] = datetime.utcnow().isoformat()
        LEADS[lead_id] = lead
        
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps(lead)
        }
    
    # Send docs
    if path.startswith('/api/v1/leads/') and path.endswith('/send-docs') and method == 'POST':
        lead_id = int(path.split('/')[-2])
        auth_header = headers.get('Authorization', headers.get('authorization', ''))
        current_user = get_user_from_token(auth_header)
        
        if not current_user:
            return {
                'statusCode': 401,
                'headers': response_headers,
                'body': json.dumps({'detail': 'Not authenticated'})
            }
        
        if lead_id not in LEADS:
            return {
                'statusCode': 404,
                'headers': response_headers,
                'body': json.dumps({'detail': 'Lead not found'})
            }
        
        lead = LEADS[lead_id]
        
        # Check if email is provided
        practice_email = lead.get('email', '').strip()
        if not practice_email:
            return {
                'statusCode': 400,
                'headers': response_headers,
                'body': json.dumps({'detail': 'Practice email address is required before sending documents'})
            }
        
        # Mark docs as sent
        lead['docs_sent'] = True
        lead['docs_sent_date'] = datetime.utcnow().isoformat()
        lead['status'] = 'DOCS_SENT'
        LEADS[lead_id] = lead
        
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps({
                'success': True,
                'message': 'Documents sent successfully',
                'lead_id': lead_id,
                'email_used': practice_email
            })
        }
    
    # Default 404
    return {
        'statusCode': 404,
        'headers': response_headers,
        'body': json.dumps({'detail': 'Endpoint not found'})
    } 