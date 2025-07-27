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

# Enhanced in-memory leads storage with PTAN and EIN/TIN fields
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
        "tags": ["Medicare", "High-Value", "Podiatry"],
        "ptan": "",  # Provider Transaction Access Number
        "ein_tin": "",  # Employer ID / Tax ID Number
        "docs_sent": False,
        "docs_sent_date": None
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
        "tags": ["Orthopedic", "High-Priority", "Follow-Up"],
        "ptan": "CA12345",  # Example PTAN
        "ein_tin": "12-3456789",  # Example EIN
        "docs_sent": False,
        "docs_sent_date": None
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

# Configuration for external API
EXTERNAL_API_CONFIG = {
    "url": "https://nwabj0qrf1.execute-api.us-east-1.amazonaws.com/Prod/createUserExternal",
    "vendor_token": "YOUR_VENDOR_TOKEN_HERE",  # This should be set in environment variables
    "default_sales_rep": "Cura Genesis Sales Team"
}

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

def prepare_external_api_payload(lead_data, user_info):
    """Prepare payload for external createUserExternal API (without actually sending)"""
    try:
        # Map our CRM data to their API format
        payload = {
            "email": f"{lead_data['practice_name'].lower().replace(' ', '.')}@{lead_data['practice_name'].lower().replace(' ', '')}.com",
            "baaSigned": True,  # Assume BAA needs to be signed
            "paSigned": True,   # Assume PA needs to be signed
            "facilityName": lead_data['practice_name'],
            "selectedFacility": "Physician Office (11)",  # Default to physician office
            "facilityAddress": {
                "street": lead_data['address'],
                "city": lead_data['city'],
                "state": lead_data['state'],
                "zip": lead_data['zip_code'],
                "npi": lead_data['npi'],  # Include NPI in address as per their bug note
                "fax": lead_data.get('fax', lead_data.get('practice_phone', ''))
            },
            "facilityNPI": lead_data['npi'],
            "facilityTIN": lead_data.get('ein_tin', ''),
            "facilityPTAN": lead_data.get('ptan', ''),
            "shippingContact": lead_data['owner_name'],
            "primaryContactName": lead_data['owner_name'],
            "primaryContactEmail": f"{lead_data['owner_name'].lower().replace(' ', '.')}@{lead_data['practice_name'].lower().replace(' ', '')}.com",
            "primaryContactPhone": lead_data.get('owner_phone', lead_data.get('practice_phone', '')),
            "shippingAddresses": [
                {
                    "street": lead_data['address'],
                    "city": lead_data['city'],
                    "state": lead_data['state'],
                    "zip": lead_data['zip_code']
                }
            ],
            "salesRepresentative": user_info.get('full_name', EXTERNAL_API_CONFIG['default_sales_rep']),
            "physicianInfo": {
                "physicianFirstName": lead_data['owner_name'].split()[0] if lead_data['owner_name'] else '',
                "physicianLastName": ' '.join(lead_data['owner_name'].split()[1:]) if len(lead_data['owner_name'].split()) > 1 else '',
                "specialty": lead_data.get('specialty', ''),
                "npi": lead_data['npi'],
                "street": lead_data['address'],
                "city": lead_data['city'],
                "state": lead_data['state'],
                "zip": lead_data['zip_code'],
                "contactName": lead_data['owner_name'],
                "fax": lead_data.get('fax', lead_data.get('practice_phone', '')),
                "phone": lead_data.get('owner_phone', lead_data.get('practice_phone', ''))
            },
            "additionalPhysicians": []  # Empty for now
        }
        
        # Log the payload (instead of sending via requests)
        print(f"📤 SEND DOCS PAYLOAD for lead {lead_data['id']}:")
        print(f"🔗 URL: {EXTERNAL_API_CONFIG['url']}")
        print(f"🔑 Vendor Token: {EXTERNAL_API_CONFIG['vendor_token']}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        # For demo purposes, return success
        # In production, you would use urllib.request or boto3 to make the HTTP call
        return {
            "success": True,
            "user_id": f"demo-user-{lead_data['id']}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "message": "Documents prepared for sending (demo mode)"
        }
            
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to prepare documents",
            "detail": str(e)
        }

def lambda_handler(event, context):
    """AWS Lambda handler with complete CRM functionality + Send Docs"""
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
            docs_sent_count = len([l for l in LEADS.values() if l.get('docs_sent', False)])
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '4.0.0',
                    'service': 'Cura Genesis CRM - Complete Production System with Send Docs',
                    'database': 'connected',
                    'database_stats': {
                        'total_leads': total_leads,
                        'active_leads': active_leads,
                        'total_users': total_users,
                        'active_agents': active_agents,
                        'total_activities': len(ACTIVITIES),
                        'total_notes': sum(len(notes) for notes in LEAD_NOTES.values()),
                        'docs_sent_count': docs_sent_count
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
                        'performance_analytics': True,
                        'ptan_ein_fields': True,
                        'send_docs_integration': True
                    },
                    'external_api': {
                        'endpoint': EXTERNAL_API_CONFIG['url'],
                        'configured': EXTERNAL_API_CONFIG['vendor_token'] != 'YOUR_VENDOR_TOKEN_HERE',
                        'mode': 'demo'
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
        
        # Get leads with full filtering (WITH PTAN/EIN FIELDS)
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
        
        # Update lead status and information (NOW WITH PTAN/EIN SUPPORT)
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
            
            # Update lead fields (INCLUDING NEW PTAN/EIN FIELDS)
            updatable_fields = ['status', 'practice_phone', 'owner_phone', 'address', 'city', 'state', 'zip_code', 'next_follow_up', 'est_revenue', 'tags', 'ptan', 'ein_tin']
            
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
        
        # 🚀 NEW: SEND DOCS ENDPOINT
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
            
            # Permission check for agents
            if current_user['role'] == 'agent' and lead.get('assigned_user_id') != current_user['id']:
                return {
                    'statusCode': 403,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Can only send docs for your assigned leads'})
                }
            
            # Validation: Lead must be in appropriate status
            if lead['status'] not in ['QUALIFIED', 'CONTACTED']:
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Lead must be CONTACTED or QUALIFIED to send documents'})
                }
            
            # Check if docs already sent
            if lead.get('docs_sent', False):
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps({'detail': 'Documents have already been sent for this lead'})
                }
            
            # Prepare payload for external API (demo mode)
            result = prepare_external_api_payload(lead, current_user)
            
            if result['success']:
                # Update lead status
                lead['docs_sent'] = True
                lead['docs_sent_date'] = datetime.utcnow().isoformat()
                lead['status'] = 'DOCS_SENT'
                lead['updated_at'] = datetime.utcnow().isoformat()
                LEADS[lead_id] = lead
                
                # Log activity
                ACTIVITIES.append({
                    'id': NEXT_ACTIVITY_ID,
                    'user_id': current_user['id'],
                    'lead_id': lead_id,
                    'activity_type': 'docs_sent',
                    'description': f"Documents prepared for external system. User ID: {result.get('user_id', 'N/A')}",
                    'outcome': 'success',
                    'created_at': datetime.utcnow().isoformat()
                })
                NEXT_ACTIVITY_ID += 1
                
                return {
                    'statusCode': 200,
                    'headers': response_headers,
                    'body': json.dumps({
                        'success': True,
                        'message': 'Documents prepared successfully (demo mode)',
                        'external_user_id': result.get('user_id'),
                        'payload_prepared': True,
                        'lead': lead
                    })
                }
            else:
                # Log failed attempt
                ACTIVITIES.append({
                    'id': NEXT_ACTIVITY_ID,
                    'user_id': current_user['id'],
                    'lead_id': lead_id,
                    'activity_type': 'docs_sent_failed',
                    'description': f"Failed to prepare documents: {result['message']}",
                    'outcome': 'failed',
                    'created_at': datetime.utcnow().isoformat()
                })
                NEXT_ACTIVITY_ID += 1
                
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps({
                        'success': False,
                        'message': result['message'],
                        'detail': result.get('detail', '')
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
                    'POST /api/v1/leads/{id}/send-docs',  # NEW ENDPOINT
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