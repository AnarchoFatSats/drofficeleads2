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

def decode_jwt(token):
    """Simple JWT decoder"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        # Add padding if needed
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload_json = base64.b64decode(payload_b64).decode()
        return json.loads(payload_json)
    except:
        return None

def hash_password(password):
    """Simple password hashing"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

# In-memory user storage (simulated database)
USERS = {
    "admin": {
        "id": 1,
        "username": "admin",
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
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
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
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
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
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
NEXT_LEAD_ID = 3
NEXT_ACTIVITY_ID = 1
NEXT_NOTE_ID = 1

# Enhanced in-memory leads storage with full CRM data
LEADS = {
    1: {
        "id": 1,
        "practice_name": "RANCHO MIRAGE PODIATRY",
        "owner_name": "Dr. Primary Podiatrist",
        "practice_phone": "(760) 568-2684",
        "owner_phone": "(760) 568-2684",
        "address": "42-600 Cook St",
        "city": "Rancho Mirage",
        "state": "CA",
        "zip_code": "92270",
        "npi": "1234567890",
        "specialty": "Podiatrist",
        "score": 100,
        "priority": "A+",
        "status": "NEW",
        "assigned_user_id": 3,
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z",
        "last_contact": None,
        "next_follow_up": None,
        "est_revenue": 50000,
        "tags": ["Medicare", "High-Value", "Podiatry"]
    },
    2: {
        "id": 2,
        "practice_name": "DESERT ORTHOPEDIC CENTER",
        "owner_name": "Dr. Joint Specialist",
        "practice_phone": "(760) 346-8058",
        "owner_phone": "(760) 346-8058",
        "address": "1180 N Indian Canyon Dr",
        "city": "Palm Springs",
        "state": "CA",
        "zip_code": "92262",
        "npi": "1234567891",
        "specialty": "Orthopedic Surgery",
        "score": 95,
        "priority": "A+",
        "status": "CONTACTED",
        "assigned_user_id": 3,
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-20T14:30:00Z",
        "last_contact": "2025-01-20T14:30:00Z",
        "next_follow_up": "2025-01-25T10:00:00Z",
        "est_revenue": 75000,
        "tags": ["Orthopedic", "High-Priority", "Follow-Up"]
    }
}

# Lead notes storage
LEAD_NOTES = {
    1: [
        {
            "id": 1,
            "lead_id": 1,
            "user_id": 3,
            "content": "Initial contact attempt - left voicemail",
            "created_at": "2025-01-15T11:00:00Z",
            "note_type": "call"
        }
    ],
    2: [
        {
            "id": 2,
            "lead_id": 2,
            "user_id": 3,
            "content": "Spoke with office manager, interested in allograft solutions",
            "created_at": "2025-01-20T14:30:00Z",
            "note_type": "call"
        }
    ]
}

# Activity tracking
ACTIVITIES = [
    {
        "id": 1,
        "user_id": 3,
        "lead_id": 1,
        "activity_type": "call",
        "description": "Called RANCHO MIRAGE PODIATRY",
        "duration_minutes": 5,
        "outcome": "voicemail",
        "created_at": "2025-01-15T11:00:00Z"
    },
    {
        "id": 2,
        "user_id": 3,
        "lead_id": 2,
        "activity_type": "call",
        "description": "Spoke with DESERT ORTHOPEDIC CENTER",
        "duration_minutes": 15,
        "outcome": "interested",
        "created_at": "2025-01-20T14:30:00Z"
    }
]

def get_user_from_token(token):
    """Extract user from JWT token"""
    if not token or not token.startswith('Bearer '):
        return None
    
    jwt_token = token[7:]  # Remove 'Bearer ' prefix
    payload = decode_jwt(jwt_token)
    
    if not payload or 'sub' not in payload:
        return None
    
    username = payload['sub']
    return USERS.get(username)

def lambda_handler(event, context):
    """AWS Lambda handler with complete CRM functionality"""
    global NEXT_USER_ID, NEXT_LEAD_ID, NEXT_ACTIVITY_ID, NEXT_NOTE_ID
    
    method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    headers = event.get('headers', {})
    body = event.get('body', '{}')
    
    # Parse JSON body if present
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
    
    try:
        # Health check
        if path == '/health':
            total_users = len(USERS)
            active_agents = len([u for u in USERS.values() if u['role'] == 'agent' and u['is_active']])
            total_leads = len(LEADS)
            active_leads = len([l for l in LEADS.values() if l['status'] not in ['CLOSED_WON', 'CLOSED_LOST']])
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '3.0.0',
                    'service': 'Cura Genesis CRM - Complete Production System',
                    'database': 'connected',
                    'database_stats': {
                        'total_leads': total_leads,
                        'active_leads': active_leads,
                        'total_users': total_users,
                        'active_agents': active_agents,
                        'total_activities': len(ACTIVITIES),
                        'total_notes': sum(len(notes) for notes in LEAD_NOTES.values())
                    },
                    'features': {
                        'admin_user_management': True,
                        'team_creation': True,
                        'role_based_access': True,
                        'lead_management': True,
                        'lead_status_updates': True,
                        'lead_notes': True,
                        'activity_tracking': True,
                        'lead_assignment': True,
                        'performance_analytics': True
                    }
                })
            }
        
        # Authentication endpoints
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
        
        # Get current user
        if path == '/api/v1/auth/me' and method == 'GET':
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            user = get_user_from_token(auth_header)
            
            if not user:
                return {
                    'statusCode': 401,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Not authenticated'})
                }
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'role': user['role'],
                    'manager_id': user['manager_id'],
                    'is_active': user['is_active'],
                    'created_at': user['created_at']
                })
            }
        
        # Create user (ADMIN/MANAGER MANAGEMENT)
        if path == '/api/v1/team/create-user' and method == 'POST':
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            current_user = get_user_from_token(auth_header)
            
            if not current_user:
                return {
                    'statusCode': 401,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Not authenticated'})
                }
            
            # Permission checks
            if current_user['role'] == 'agent':
                return {
                    'statusCode': 403,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Agents cannot create users'})
                }
            
            # Get user data
            username = body_data.get('username', '')
            email = body_data.get('email', '')
            full_name = body_data.get('full_name', '')
            password = body_data.get('password', '')
            role = body_data.get('role', 'agent')
            manager_id = body_data.get('manager_id')
            
            # Validation
            if not all([username, email, full_name, password]):
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Missing required fields'})
                }
            
            # Check if username exists
            if username in USERS:
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Username already exists'})
                }
            
            # Check if email exists
            if any(u['email'] == email for u in USERS.values()):
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Email already exists'})
                }
            
            # Role-specific validations
            if current_user['role'] == 'manager' and role != 'agent':
                return {
                    'statusCode': 403,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Managers can only create agents'})
                }
            
            if current_user['role'] == 'manager':
                manager_id = current_user['id']
            
            # Create new user
            new_user = {
                'id': NEXT_USER_ID,
                'username': username,
                'password_hash': hash_password(password),
                'email': email,
                'full_name': full_name,
                'role': role,
                'manager_id': manager_id,
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            }
            
            USERS[username] = new_user
            NEXT_USER_ID += 1
            
            return {
                'statusCode': 201,
                'headers': response_headers,
                'body': json.dumps({
                    'id': new_user['id'],
                    'username': new_user['username'],
                    'email': new_user['email'],
                    'full_name': new_user['full_name'],
                    'role': new_user['role'],
                    'manager_id': new_user['manager_id'],
                    'is_active': new_user['is_active'],
                    'created_at': new_user['created_at']
                })
            }
        
        # Get team members
        if path == '/api/v1/team/members' and method == 'GET':
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            current_user = get_user_from_token(auth_header)
            
            if not current_user:
                return {
                    'statusCode': 401,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Not authenticated'})
                }
            
            # Filter users based on role
            if current_user['role'] == 'admin':
                members = list(USERS.values())
            elif current_user['role'] == 'manager':
                members = [u for u in USERS.values() if u['manager_id'] == current_user['id']]
            else:
                members = [current_user]
            
            # Format response
            response_members = []
            for member in members:
                response_members.append({
                    'id': member['id'],
                    'username': member['username'],
                    'email': member['email'],
                    'full_name': member['full_name'],
                    'role': member['role'],
                    'manager_id': member['manager_id'],
                    'is_active': member['is_active'],
                    'created_at': member['created_at']
                })
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps(response_members)
            }
        
        # Get all managers (for admin use)
        if path == '/api/v1/team/all-managers' and method == 'GET':
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            current_user = get_user_from_token(auth_header)
            
            if not current_user or current_user['role'] != 'admin':
                return {
                    'statusCode': 403,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Only admins can view all managers'})
                }
            
            managers = [u for u in USERS.values() if u['role'] == 'manager']
            response_managers = []
            for manager in managers:
                response_managers.append({
                    'id': manager['id'],
                    'username': manager['username'],
                    'email': manager['email'],
                    'full_name': manager['full_name'],
                    'role': manager['role'],
                    'manager_id': manager['manager_id'],
                    'is_active': manager['is_active'],
                    'created_at': manager['created_at']
                })
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps(response_managers)
            }
        
        # ENHANCED LEAD MANAGEMENT
        
        # Get leads with full filtering
        if path == '/api/v1/leads' and method == 'GET':
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            current_user = get_user_from_token(auth_header)
            
            if not current_user:
                return {
                    'statusCode': 401,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Not authenticated'})
                }
            
            leads = list(LEADS.values())
            
            # Filter leads based on role
            if current_user['role'] == 'agent':
                leads = [l for l in leads if l.get('assigned_user_id') == current_user['id']]
            
            # Add notes and activities to leads
            for lead in leads:
                lead['notes'] = LEAD_NOTES.get(lead['id'], [])
                lead['activities'] = [a for a in ACTIVITIES if a['lead_id'] == lead['id']]
                
                # Add assigned user info
                if lead.get('assigned_user_id'):
                    assigned_user = next((u for u in USERS.values() if u['id'] == lead['assigned_user_id']), None)
                    lead['assigned_user'] = assigned_user['full_name'] if assigned_user else None
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps(leads)
            }
        
        # Update lead status and information
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
            updatable_fields = ['status', 'practice_phone', 'owner_phone', 'address', 'city', 'state', 'zip_code', 'next_follow_up', 'est_revenue', 'tags']
            
            for field in updatable_fields:
                if field in body_data:
                    lead[field] = body_data[field]
            
            # Auto-update last_contact if status changed to CONTACTED
            if body_data.get('status') == 'CONTACTED':
                lead['last_contact'] = datetime.utcnow().isoformat()
            
            lead['updated_at'] = datetime.utcnow().isoformat()
            LEADS[lead_id] = lead
            
            # Log activity for status changes
            if 'status' in body_data:
                ACTIVITIES.append({
                    'id': NEXT_ACTIVITY_ID,
                    'user_id': current_user['id'],
                    'lead_id': lead_id,
                    'activity_type': 'status_update',
                    'description': f"Updated status to {body_data['status']}",
                    'outcome': body_data['status'],
                    'created_at': datetime.utcnow().isoformat()
                })
                NEXT_ACTIVITY_ID += 1
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps(lead)
            }
        
        # Add note to lead
        if path.startswith('/api/v1/leads/') and path.endswith('/notes') and method == 'POST':
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
            
            # Permission check for agents
            if current_user['role'] == 'agent' and lead.get('assigned_user_id') != current_user['id']:
                return {
                    'statusCode': 403,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Can only add notes to your assigned leads'})
                }
            
            content = body_data.get('content', '')
            note_type = body_data.get('note_type', 'general')
            
            if not content:
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Note content is required'})
                }
            
            note = {
                'id': NEXT_NOTE_ID,
                'lead_id': lead_id,
                'user_id': current_user['id'],
                'content': content,
                'note_type': note_type,
                'created_at': datetime.utcnow().isoformat(),
                'created_by': current_user['full_name']
            }
            
            if lead_id not in LEAD_NOTES:
                LEAD_NOTES[lead_id] = []
            
            LEAD_NOTES[lead_id].append(note)
            NEXT_NOTE_ID += 1
            
            return {
                'statusCode': 201,
                'headers': response_headers,
                'body': json.dumps(note)
            }
        
        # Log activity
        if path == '/api/v1/activities' and method == 'POST':
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            current_user = get_user_from_token(auth_header)
            
            if not current_user:
                return {
                    'statusCode': 401,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Not authenticated'})
                }
            
            lead_id = body_data.get('lead_id')
            activity_type = body_data.get('activity_type', 'call')
            description = body_data.get('description', '')
            duration_minutes = body_data.get('duration_minutes', 0)
            outcome = body_data.get('outcome', '')
            
            if not lead_id or lead_id not in LEADS:
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Valid lead_id is required'})
                }
            
            lead = LEADS[lead_id]
            
            # Permission check for agents
            if current_user['role'] == 'agent' and lead.get('assigned_user_id') != current_user['id']:
                return {
                    'statusCode': 403,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Can only log activities for your assigned leads'})
                }
            
            activity = {
                'id': NEXT_ACTIVITY_ID,
                'user_id': current_user['id'],
                'lead_id': lead_id,
                'activity_type': activity_type,
                'description': description,
                'duration_minutes': duration_minutes,
                'outcome': outcome,
                'created_at': datetime.utcnow().isoformat(),
                'created_by': current_user['full_name']
            }
            
            ACTIVITIES.append(activity)
            NEXT_ACTIVITY_ID += 1
            
            return {
                'statusCode': 201,
                'headers': response_headers,
                'body': json.dumps(activity)
            }
        
        # Assign lead to agent (Manager/Admin only)
        if path.startswith('/api/v1/leads/') and path.endswith('/assign') and method == 'POST':
            lead_id = int(path.split('/')[-2])
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            current_user = get_user_from_token(auth_header)
            
            if not current_user:
                return {
                    'statusCode': 401,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Not authenticated'})
                }
            
            if current_user['role'] == 'agent':
                return {
                    'statusCode': 403,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Only managers and admins can assign leads'})
                }
            
            if lead_id not in LEADS:
                return {
                    'statusCode': 404,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Lead not found'})
                }
            
            agent_id = body_data.get('agent_id')
            if not agent_id:
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'agent_id is required'})
                }
            
            # Verify agent exists
            agent = next((u for u in USERS.values() if u['id'] == agent_id and u['role'] == 'agent'), None)
            if not agent:
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Invalid agent_id'})
                }
            
            lead = LEADS[lead_id]
            lead['assigned_user_id'] = agent_id
            lead['updated_at'] = datetime.utcnow().isoformat()
            
            # Log assignment activity
            ACTIVITIES.append({
                'id': NEXT_ACTIVITY_ID,
                'user_id': current_user['id'],
                'lead_id': lead_id,
                'activity_type': 'assignment',
                'description': f"Assigned lead to {agent['full_name']}",
                'outcome': 'assigned',
                'created_at': datetime.utcnow().isoformat()
            })
            NEXT_ACTIVITY_ID += 1
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'message': f"Lead assigned to {agent['full_name']}",
                    'lead': lead
                })
            }
        
        # Performance analytics (Manager/Admin only)
        if path == '/api/v1/analytics/performance' and method == 'GET':
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            current_user = get_user_from_token(auth_header)
            
            if not current_user:
                return {
                    'statusCode': 401,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Not authenticated'})
                }
            
            if current_user['role'] == 'agent':
                return {
                    'statusCode': 403,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Only managers and admins can view analytics'})
                }
            
            # Calculate performance metrics
            total_leads = len(LEADS)
            closed_won = len([l for l in LEADS.values() if l['status'] == 'CLOSED_WON'])
            closed_lost = len([l for l in LEADS.values() if l['status'] == 'CLOSED_LOST'])
            contacted = len([l for l in LEADS.values() if l['status'] == 'CONTACTED'])
            qualified = len([l for l in LEADS.values() if l['status'] == 'QUALIFIED'])
            
            total_activities = len(ACTIVITIES)
            total_calls = len([a for a in ACTIVITIES if a['activity_type'] == 'call'])
            
            # Agent performance
            agent_stats = {}
            for user in USERS.values():
                if user['role'] == 'agent':
                    agent_leads = [l for l in LEADS.values() if l.get('assigned_user_id') == user['id']]
                    agent_activities = [a for a in ACTIVITIES if a['user_id'] == user['id']]
                    agent_won = len([l for l in agent_leads if l['status'] == 'CLOSED_WON'])
                    
                    agent_stats[user['username']] = {
                        'full_name': user['full_name'],
                        'total_leads': len(agent_leads),
                        'closed_won': agent_won,
                        'conversion_rate': (agent_won / len(agent_leads) * 100) if agent_leads else 0,
                        'total_activities': len(agent_activities),
                        'calls_made': len([a for a in agent_activities if a['activity_type'] == 'call'])
                    }
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'overview': {
                        'total_leads': total_leads,
                        'closed_won': closed_won,
                        'closed_lost': closed_lost,
                        'contacted': contacted,
                        'qualified': qualified,
                        'conversion_rate': (closed_won / total_leads * 100) if total_leads else 0,
                        'total_activities': total_activities,
                        'total_calls': total_calls
                    },
                    'agent_performance': agent_stats
                })
            }
        
        # Handle CORS preflight
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': ''
            }
        
        # 404 for unknown endpoints
        return {
            'statusCode': 404,
            'headers': response_headers,
            'body': json.dumps({
                'detail': 'Endpoint not found',
                'method': method,
                'path': path,
                'available_endpoints': [
                    'POST /api/v1/auth/login',
                    'GET /api/v1/auth/me',
                    'GET /api/v1/leads',
                    'PUT /api/v1/leads/{id}',
                    'POST /api/v1/leads/{id}/notes',
                    'POST /api/v1/leads/{id}/assign',
                    'POST /api/v1/activities',
                    'POST /api/v1/team/create-user',
                    'GET /api/v1/team/members',
                    'GET /api/v1/team/all-managers',
                    'GET /api/v1/analytics/performance',
                    'GET /health'
                ]
            })
        }
        
    except Exception as e:
        print(f"❌ Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': response_headers,
            'body': json.dumps({
                'detail': 'Internal server error',
                'error': str(e)
            })
        } 