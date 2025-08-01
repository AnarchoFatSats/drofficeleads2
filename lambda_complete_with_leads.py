#!/usr/bin/env python3
"""
Complete VantagePoint CRM Lambda - Production Ready with DynamoDB Lead Persistence
FIXED: Both users AND leads now stored in DynamoDB - full persistence solution
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

# DynamoDB clients for persistent storage
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('vantagepoint-users')
leads_table = dynamodb.Table('vantagepoint-leads')  # [OK] NEW: Leads persistent storage

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
    
    # Header
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    
    # Payload
    payload = {
        "username": username,
        "role": role,
        "exp": int(time.time()) + 3600  # 1 hour expiry
    }
    
    # Encode
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    # Create signature
    secret = "your-secret-key"
    signature = hmac.new(
        secret.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def decode_jwt_token(token):
    """Simple JWT token decoding for user info"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode payload
        payload_b64 = parts[1]
        # Add padding if needed
        missing_padding = len(payload_b64) % 4
        if missing_padding:
            payload_b64 += '=' * (4 - missing_padding)
        
        payload_json = base64.urlsafe_b64decode(payload_b64).decode()
        
        return json.loads(payload_json)
    except:
        return None

# [OK] FIXED: DynamoDB User Management Functions
def get_user(username):
    """Get user from DynamoDB - replaces USERS.get(username)"""
    try:
        response = users_table.get_item(Key={'username': username})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting user {username}: {e}")
        return None

def create_user_in_db(username, user_data):
    """Create user in DynamoDB - replaces USERS[username] = new_user"""
    try:
        users_table.put_item(Item=user_data)
        print(f"[OK] User {username} created in DynamoDB")
        return True
    except ClientError as e:
        print(f"[ERROR] Error creating user {username}: {e}")
        return False

def get_all_users():
    """Get all users from DynamoDB - replaces USERS.values()"""
    try:
        response = users_table.scan()
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error scanning users: {e}")
        return []

def get_user_by_id(user_id):
    """Find user by ID in DynamoDB"""
    all_users = get_all_users()
    for user in all_users:
        if user.get('id') == user_id:
            return user
    return None

def initialize_default_users():
    """Initialize default users in DynamoDB if they don't exist"""
    default_users = {
        "admin": {
            "id": 1,
            "username": "admin",
            "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
            "role": "admin",
            "email": "admin@vantagepoint.com",
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
            "email": "manager1@vantagepoint.com",
            "full_name": "Sales Manager",
            "is_active": True,
            "created_at": "2025-01-01T00:00:00Z",
            "manager_id": None
        },
        "agent1": {
            "id": 3,
            "username": "agent1",
            "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
            "role": "agent",
            "email": "agent1@vantagepoint.com",
            "full_name": "Sales Agent",
            "is_active": True,
            "created_at": "2025-01-01T00:00:00Z",
            "manager_id": 2
        }
    }
    
    # Check if users exist, create if they don't
    for username, user_data in default_users.items():
        existing_user = get_user(username)
        if not existing_user:
            create_user_in_db(username, user_data)
            print(f"[OK] Initialized default user: {username}")

def get_next_user_id():
    """Get next available user ID"""
    all_users = get_all_users()
    if not all_users:
        return 4  # Start after default users
    
    max_id = max([user.get('id', 0) for user in all_users])
    return max_id + 1

# Auto-incrementing IDs - Initialize based on existing data
NEXT_LEAD_ID = 1000  # Start lead IDs from 1000

# [OK] DynamoDB Lead Management Functions (replacing in-memory LEADS array)
def get_all_leads():
    """Get all leads from DynamoDB"""
    try:
        response = leads_table.scan()
        return response.get('Items', [])
    except Exception as e:
        print(f"[ERROR] Error getting leads: {e}")
        return []

def get_lead_by_id(lead_id):
    """Get single lead by ID from DynamoDB"""
    try:
        response = leads_table.get_item(Key={'id': int(lead_id)})
        return response.get('Item', None)
    except Exception as e:
        print(f"[ERROR] Error getting lead {lead_id}: {e}")
        return None

def create_lead(lead_data):
    """Create new lead in DynamoDB"""
    try:
        # Ensure numeric fields are properly typed
        if 'id' in lead_data:
            lead_data['id'] = int(lead_data['id'])
        if 'score' in lead_data:
            lead_data['score'] = int(lead_data['score'])
        if 'assigned_user_id' in lead_data and lead_data['assigned_user_id']:
            lead_data['assigned_user_id'] = int(lead_data['assigned_user_id'])
        
        leads_table.put_item(Item=lead_data)
        print(f"[OK] Created lead: {lead_data.get('practice_name', 'Unknown')}")
        return lead_data
    except Exception as e:
        print(f"[ERROR] Error creating lead: {e}")
        return None

def update_lead(lead_id, update_data):
    """Update lead in DynamoDB"""
    try:
        # Build UpdateExpression dynamically
        update_expr = "SET "
        expr_values = {}
        expr_names = {}
        
        for key, value in update_data.items():
            # Handle reserved keywords
            attr_name = f"#{key}"
            attr_value = f":{key}"
            
            update_expr += f"{attr_name} = {attr_value}, "
            expr_names[attr_name] = key
            expr_values[attr_value] = value
        
        update_expr = update_expr.rstrip(", ")
        
        leads_table.update_item(
            Key={'id': int(lead_id)},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        
        print(f"[OK] Updated lead {lead_id}")
        return True
    except Exception as e:
        print(f"[ERROR] Error updating lead {lead_id}: {e}")
        return False

def get_next_lead_id():
    """Get next available lead ID"""
    global NEXT_LEAD_ID
    try:
        all_leads = get_all_leads()
        if all_leads:
            max_id = max([int(lead.get('id', 0)) for lead in all_leads])
            NEXT_LEAD_ID = max_id + 1
        else:
            NEXT_LEAD_ID = 1
        return NEXT_LEAD_ID
    except Exception as e:
        print(f"[ERROR] Error getting next lead ID: {e}")
        NEXT_LEAD_ID += 1
        return NEXT_LEAD_ID

def assign_leads_to_new_agent(agent_id, count=20):
    """Assign unassigned leads to new agent"""
    all_leads = get_all_leads()
    unassigned_leads = [l for l in all_leads if not l.get('assigned_user_id') or l.get('assigned_user_id') == 0]
    assigned_count = 0
    
    for lead in unassigned_leads[:count]:
        update_lead(lead['id'], {
            'assigned_user_id': agent_id,
            'updated_at': datetime.utcnow().isoformat()
        })
        assigned_count += 1
    
    return assigned_count

def lambda_handler(event, context):
    """AWS Lambda handler for VantagePoint CRM with DynamoDB lead persistence"""
    global NEXT_LEAD_ID
    
    try:
        # Initialize default users in DynamoDB
        initialize_default_users()
        
        # Parse the request
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        headers = event.get('headers', {})
        body = event.get('body', '{}')
        path_params = event.get('pathParameters') or {}
        
        # Parse body if it exists
        try:
            if body:
                body_data = json.loads(body)
            else:
                body_data = {}
        except:
            body_data = {}
        
        user_count = len(get_all_users())
        all_leads = get_all_leads()
        print(f"[HOT] VantagePoint {method} {path} - {len(all_leads)} leads, {user_count} users (DynamoDB)")
        
        # CORS headers for all responses
        response_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }
        
        def create_response(status_code, body_dict):
            return {
                'statusCode': status_code,
                'headers': response_headers,
                'body': json_dumps(body_dict)
            }
        
        def get_current_user_from_token(headers):
            """Extract user info from JWT token - FIXED: Uses DynamoDB"""
            auth_header = headers.get("authorization", headers.get("Authorization", ""))
            if not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.replace("Bearer ", "")
            payload = decode_jwt_token(token)
            if not payload:
                return None
            
            return get_user(payload.get("username"))  # [OK] FIXED: DynamoDB lookup
        
        # Handle preflight OPTIONS requests
        if method == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight successful'})
        
        # Health check
        if path == '/health':
            return create_response(200, {
                'status': 'healthy',
                'service': 'VantagePoint CRM API',
                'leads_count': len(all_leads),
                'users_count': len(get_all_users()),  # [OK] FIXED: DynamoDB count
                'version': '2.0.0',
                'user_storage': 'DynamoDB',  # [OK] NEW: Shows persistent storage
                'lead_storage': 'DynamoDB',  # [OK] NEW: Shows lead persistence
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Login endpoint
        if path == '/api/v1/auth/login' and method == 'POST':
            username = body_data.get('username', '')
            password = body_data.get('password', '')
            
            if not username or not password:
                return create_response(400, {"detail": "Username and password required"})
            
            # Get user from DynamoDB - FIXED
            user = get_user(username)
            if not user:
                return create_response(401, {"detail": "Invalid credentials"})
            
            # Verify password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if user['password_hash'] != password_hash:
                return create_response(401, {"detail": "Invalid credentials"})
            
            # Create JWT token
            token = create_jwt_token(username, user['role'])
            
            return create_response(200, {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "username": user['username'],
                    "email": user['email'],
                    "role": user['role'],
                    "full_name": user.get('full_name', username)
                }
            })
        
        # Protected endpoints require authentication
        current_user = get_current_user_from_token(headers)
        if not current_user:
            return create_response(401, {"detail": "Authentication required"})
        
        # Create new user (admin/manager only) - FIXED: DynamoDB storage
        if path == '/api/v1/users' and method == 'POST':
            # Check permissions
            if current_user['role'] not in ['admin', 'manager']:
                return create_response(403, {"detail": "Only admins and managers can create users"})
            
            new_user_data = body_data
            username = new_user_data.get('username')
            password = new_user_data.get('password', 'admin123')  # Default password
            role = new_user_data.get('role', 'agent')
            
            if not username:
                return create_response(400, {"detail": "Username is required"})
            
            # Check if user exists - FIXED: DynamoDB lookup
            if get_user(username):
                return create_response(400, {"detail": "Username already exists"})
            
            # Managers can only create agents
            if current_user['role'] == 'manager' and role != 'agent':
                return create_response(403, {"detail": "Managers can only create agent accounts"})
            
            # Create new user - FIXED: DynamoDB storage
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            new_user = {
                "id": get_next_user_id(),
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "email": f"{username}@vantagepoint.com",
                "full_name": new_user_data.get('full_name', username.title()),
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "manager_id": current_user['id'] if current_user['role'] == 'manager' else new_user_data.get('manager_id')
            }
            
            # [OK] FIXED: Store in DynamoDB instead of memory
            if not create_user_in_db(username, new_user):
                return create_response(500, {"detail": "Failed to create user in database"})
            
            # If new user is an agent, assign 20 leads
            assigned_count = 0
            if role == 'agent':
                assigned_count = assign_leads_to_new_agent(new_user["id"], 20)
                print(f"[OK] Assigned {assigned_count} leads to new agent {username}")
            
            return create_response(201, {
                "message": "User created successfully",
                "user": {
                    "id": new_user["id"],
                    "username": new_user["username"],
                    "role": new_user["role"],
                    "email": new_user["email"],
                    "full_name": new_user["full_name"]
                },
                "leads_assigned": assigned_count,
                "storage": "DynamoDB"  # [OK] NEW: Confirms persistent storage
            })
        
        # Organization structure endpoint - ADDED FOR FRONTEND
        if path == '/api/v1/organization' and method == 'GET':
            # Get all users from DynamoDB
            all_users = get_all_users()
            
            # Build organizational structure
            admins = []
            managers = []
            agents = []
            
            # Categorize users by role
            for user in all_users:
                user_data = {
                    "id": user.get('id'),
                    "username": user.get('username'),
                    "full_name": user.get('full_name', user.get('username', '')),
                    "email": user.get('email', ''),
                    "role": user.get('role', ''),
                    "is_active": user.get('is_active', True),
                    "created_at": user.get('created_at', ''),
                    "manager_id": user.get('manager_id')
                }
                
                if user.get('role') == 'admin':
                    admins.append(user_data)
                elif user.get('role') == 'manager':
                    managers.append(user_data)
                elif user.get('role') == 'agent':
                    agents.append(user_data)
            
            # Build hierarchical structure
            organization = {
                "admins": admins,
                "managers": [],
                "total_users": len(all_users),
                "roles_count": {
                    "admin": len(admins),
                    "manager": len(managers), 
                    "agent": len(agents)
                }
            }
            
            # Add managers with their agents
            for manager in managers:
                manager_with_agents = manager.copy()
                manager_with_agents["agents"] = [
                    agent for agent in agents 
                    if agent.get('manager_id') == manager.get('id')
                ]
                organization["managers"].append(manager_with_agents)
            
            # Add unassigned agents (no manager)
            unassigned_agents = [
                agent for agent in agents 
                if not agent.get('manager_id') or agent.get('manager_id') == 0
            ]
            
            if unassigned_agents:
                organization["unassigned_agents"] = unassigned_agents
            
            return create_response(200, {
                "organization": organization,
                "message": "Organizational structure retrieved successfully",
                "storage": "DynamoDB"
            })
        
        # Leads endpoint - GET all leads
        if path == '/api/v1/leads' and method == 'GET':
            return create_response(200, {
                "leads": all_leads,
                "total_leads": len(all_leads),
                "message": "Leads retrieved successfully"
            })
        
        # Summary endpoint - Dashboard statistics
        if path == '/api/v1/summary' and method == 'GET':
            status_counts = {}
            priority_counts = {}
            
            for lead in all_leads:
                status = lead.get("status", "unknown")
                priority = lead.get("priority", "unknown")
                
                status_counts[status] = status_counts.get(status, 0) + 1
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            return create_response(200, {
                "total_leads": len(all_leads),
                "status_breakdown": status_counts,
                "priority_breakdown": priority_counts,
                "new_leads": status_counts.get("new", 0),
                "contacted_leads": status_counts.get("contacted", 0),
                "high_priority": priority_counts.get("high", 0),
                "users_count": len(get_all_users()),
                "message": "Summary statistics retrieved successfully"
            })
        
        # POST /api/v1/leads - Create single lead
        if path == '/api/v1/leads' and method == 'POST':
            try:
                lead_data = body_data.copy()
                lead_data['id'] = get_next_lead_id()
                lead_data['created_at'] = datetime.utcnow().isoformat()
                lead_data['updated_at'] = datetime.utcnow().isoformat()
                lead_data['status'] = lead_data.get('status', 'new')
                
                created_lead = create_lead(lead_data)
                if created_lead:
                    return create_response(201, {
                        "message": "Lead created successfully",
                        "lead": created_lead
                    })
                else:
                    return create_response(500, {"detail": "Failed to create lead"})
            except Exception as e:
                return create_response(400, {"detail": f"Invalid lead data: {str(e)}"})
        
        # POST /api/v1/leads/bulk - Bulk create leads
        if path == '/api/v1/leads/bulk' and method == 'POST':
            try:
                leads_data = body_data.get('leads', [])
                if not leads_data or not isinstance(leads_data, list):
                    return create_response(400, {"detail": "Invalid format. Expected {\"leads\": [...]}"})
                
                created_leads = []
                failed_leads = []
                
                for lead_data in leads_data:
                    try:
                        lead_data['id'] = get_next_lead_id()
                        lead_data['created_at'] = datetime.utcnow().isoformat()
                        lead_data['updated_at'] = datetime.utcnow().isoformat()
                        lead_data['status'] = lead_data.get('status', 'new')
                        
                        created_lead = create_lead(lead_data)
                        if created_lead:
                            created_leads.append(created_lead)
                        else:
                            failed_leads.append(lead_data.get('practice_name', 'Unknown'))
                    except Exception as e:
                        failed_leads.append(f"{lead_data.get('practice_name', 'Unknown')}: {str(e)}")
                
                return create_response(200, {
                    "message": f"Bulk upload completed. {len(created_leads)} created, {len(failed_leads)} failed",
                    "created_count": len(created_leads),
                    "failed_count": len(failed_leads),
                    "failed_leads": failed_leads
                })
            except Exception as e:
                return create_response(400, {"detail": f"Bulk upload error: {str(e)}"})
        
        # PUT /api/v1/leads/{id} - Update lead (including assignment)
        if path.startswith('/api/v1/leads/') and method == 'PUT':
            try:
                lead_id = path.split('/')[-1]
                if not lead_id.isdigit():
                    return create_response(400, {"detail": "Invalid lead ID"})
                
                # Get current lead
                current_lead = get_lead_by_id(int(lead_id))
                if not current_lead:
                    return create_response(404, {"detail": "Lead not found"})
                
                # Validate update data
                allowed_fields = [
                    'assigned_user_id', 'status', 'docs_sent', 
                    'practice_phone', 'email', 'priority',
                    'practice_name', 'owner_name', 'address', 
                    'city', 'state', 'zip_code', 'specialty',
                    'score', 'ptan', 'ein_tin'
                ]
                
                update_data = {k: v for k, v in body_data.items() if k in allowed_fields}
                if not update_data:
                    return create_response(400, {"detail": "No valid fields to update"})
                
                # Add timestamp
                update_data['updated_at'] = datetime.utcnow().isoformat()
                
                # Update in DynamoDB
                if update_lead(int(lead_id), update_data):
                    updated_lead = get_lead_by_id(int(lead_id))
                    return create_response(200, {
                        "message": "Lead updated successfully",
                        "lead": updated_lead
                    })
                else:
                    return create_response(500, {"detail": "Failed to update lead"})
                    
            except Exception as e:
                return create_response(400, {"detail": f"Update error: {str(e)}"})
        
        # DELETE /api/v1/leads/{id} - Delete lead
        if path.startswith('/api/v1/leads/') and method == 'DELETE':
            try:
                lead_id = path.split('/')[-1]
                if not lead_id.isdigit():
                    return create_response(400, {"detail": "Invalid lead ID"})
                
                # Check if lead exists
                current_lead = get_lead_by_id(int(lead_id))
                if not current_lead:
                    return create_response(404, {"detail": "Lead not found"})
                
                # Delete from DynamoDB
                leads_table.delete_item(Key={'id': int(lead_id)})
                
                return create_response(200, {
                    "message": f"Lead {lead_id} deleted successfully"
                })
                    
            except Exception as e:
                return create_response(400, {"detail": f"Delete error: {str(e)}"})
        
        # Default response
        return create_response(404, {"detail": "Endpoint not found"})
        
    except Exception as e:
        print(f"[ERROR] Lambda error: {e}")
        return {
            'statusCode': 500,
            'headers': response_headers,
            'body': json.dumps({"detail": f"Internal server error: {str(e)}"})
        }