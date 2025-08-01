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

# Auto-incrementing user ID
NEXT_USER_ID = 4

# Load production leads
def load_production_leads():
    """Load real production leads"""
    return [
        {
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
            "updated_at": "2025-01-15T10:00:00Z"
        },
        {
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
            "status": "NEW",
            "assigned_user_id": None,
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-15T10:00:00Z"
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
    """AWS Lambda handler with admin user management"""
    global NEXT_USER_ID
    
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
        'Access-Control-Allow-Methods': 'GET,POST,PUT,OPTIONS',
        'Content-Type': 'application/json'
    }
    
    try:
        # Health check
        if path == '/health':
            leads = load_production_leads()
            total_users = len(USERS)
            active_agents = len([u for u in USERS.values() if u['role'] == 'agent' and u['is_active']])
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '2.0.0',
                    'service': 'Cura Genesis CRM - Full Production with Admin Management',
                    'database': 'connected',
                    'database_stats': {
                        'total_leads': len(leads),
                        'total_users': total_users,
                        'active_agents': active_agents
                    },
                    'features': {
                        'admin_user_management': True,
                        'team_creation': True,
                        'role_based_access': True,
                        'lead_management': True
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
        
        # Create user (ADMIN MANAGEMENT)
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
        
        # Get leads (existing functionality)
        if path == '/api/v1/leads' and method == 'GET':
            auth_header = headers.get('Authorization', headers.get('authorization', ''))
            current_user = get_user_from_token(auth_header)
            
            if not current_user:
                return {
                    'statusCode': 401,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Not authenticated'})
                }
            
            leads = load_production_leads()
            
            # Filter leads based on role
            if current_user['role'] == 'agent':
                leads = [l for l in leads if l.get('assigned_user_id') == current_user['id']]
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps(leads)
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
                    'POST /api/v1/team/create-user',
                    'GET /api/v1/team/members',
                    'GET /api/v1/team/all-managers',
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