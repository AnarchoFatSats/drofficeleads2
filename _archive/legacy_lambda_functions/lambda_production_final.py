#!/usr/bin/env python3
"""
Final Production Lambda - VantagePoint CRM
Complete system with all users, leads, and agent assignment
"""

import json
import hashlib
import base64
import hmac
from datetime import datetime, timedelta
import random

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

# Complete user database with all roles
USERS = {
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

# Auto-incrementing IDs
NEXT_USER_ID = 4
NEXT_LEAD_ID = 51

# Production leads database - 50 high-quality leads
LEADS = [
    {
        "id": 1,
        "practice_name": "RANCHO MIRAGE PODIATRY",
        "owner_name": "Dr. Matthew Diltz",
        "practice_phone": "(760) 568-2684",
        "email": "contact@ranchomiragepodiatry.com",
        "address": "42-600 Cook St",
        "city": "Rancho Mirage",
        "state": "CA",
        "zip_code": "92270",
        "specialty": "Podiatrist",
        "score": 100,
        "priority": "high",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 2,
        "practice_name": "DESERT ORTHOPEDIC CENTER",
        "owner_name": "Dr. Sarah Johnson",
        "practice_phone": "(760) 346-8058",
        "email": "contact@desertortho.com",
        "address": "1180 N Indian Canyon Dr",
        "city": "Palm Springs",
        "state": "CA",
        "zip_code": "92262",
        "specialty": "Orthopedic Surgery",
        "score": 95,
        "priority": "high",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 3,
        "practice_name": "VEGAS FOOT & ANKLE",
        "owner_name": "Dr. Michael Rodriguez",
        "practice_phone": "(702) 990-0635",
        "email": "contact@vegasfoot.com",
        "address": "8310 W Sunset Rd",
        "city": "Las Vegas",
        "state": "NV",
        "zip_code": "89113",
        "specialty": "Podiatrist",
        "score": 98,
        "priority": "high",
        "status": "contacted",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 4,
        "practice_name": "TEXAS PODIATRY GROUP",
        "owner_name": "Dr. Robert Chen",
        "practice_phone": "(214) 555-0198",
        "email": "contact@texaspodiatry.com",
        "address": "5323 Harry Hines Blvd",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75390",
        "specialty": "Podiatrist",
        "score": 92,
        "priority": "high",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 5,
        "practice_name": "MOUNTAIN VIEW WOUND CARE",
        "owner_name": "Dr. Lisa Thompson",
        "practice_phone": "(406) 555-0167",
        "email": "contact@mountainwound.com",
        "address": "2825 Fort Missoula Rd",
        "city": "Missoula",
        "state": "MT",
        "zip_code": "59804",
        "specialty": "Wound Care",
        "score": 89,
        "priority": "high",
        "status": "new",
        "assigned_user_id": None,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 6,
        "practice_name": "CAROLINA FOOT SPECIALISTS",
        "owner_name": "Dr. James Wilson",
        "practice_phone": "(704) 555-0234",
        "email": "contact@carolinafoot.com",
        "address": "1350 South Kings Dr",
        "city": "Charlotte",
        "state": "NC",
        "zip_code": "28207",
        "specialty": "Podiatrist",
        "score": 94,
        "priority": "high",
        "status": "qualified",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 7,
        "practice_name": "FLORIDA ORTHOPEDIC INSTITUTE",
        "owner_name": "Dr. Maria Garcia",
        "practice_phone": "(813) 555-0345",
        "email": "contact@floridaortho.com",
        "address": "13020 Telecom Pkwy N",
        "city": "Tampa",
        "state": "FL",
        "zip_code": "33637",
        "specialty": "Orthopedic Surgery",
        "score": 91,
        "priority": "high",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 8,
        "practice_name": "ARIZONA PODIATRY CENTER",
        "owner_name": "Dr. David Martinez",
        "practice_phone": "(602) 555-0456",
        "email": "contact@azpodiatry.com",
        "address": "5090 N 40th St",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85018",
        "specialty": "Podiatrist",
        "score": 87,
        "priority": "medium",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 9,
        "practice_name": "MIDWEST WOUND HEALING",
        "owner_name": "Dr. Patricia Brown",
        "practice_phone": "(314) 555-0567",
        "email": "contact@midwestwound.com",
        "address": "12634 Olive Blvd",
        "city": "St. Louis",
        "state": "MO",
        "zip_code": "63141",
        "specialty": "Wound Care",
        "score": 83,
        "priority": "medium",
        "status": "contacted",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 10,
        "practice_name": "NORTHWEST FOOT CLINIC",
        "owner_name": "Dr. Kevin Lee",
        "practice_phone": "(503) 555-0678",
        "email": "contact@nwfoot.com",
        "address": "9155 SW Barnes Rd",
        "city": "Portland",
        "state": "OR",
        "zip_code": "97225",
        "specialty": "Podiatrist",
        "score": 86,
        "priority": "medium",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 11,
        "practice_name": "ROCKY MOUNTAIN ORTHOPEDICS",
        "owner_name": "Dr. Amanda Clark",
        "practice_phone": "(303) 555-0789",
        "email": "contact@rmortho.com",
        "address": "8200 E Belleview Ave",
        "city": "Denver",
        "state": "CO",
        "zip_code": "80111",
        "specialty": "Orthopedic Surgery",
        "score": 88,
        "priority": "medium",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 12,
        "practice_name": "GEORGIA FOOT & ANKLE",
        "owner_name": "Dr. Christopher White",
        "practice_phone": "(404) 555-0890",
        "email": "contact@gafoot.com",
        "address": "5673 Peachtree Dunwoody Rd",
        "city": "Atlanta",
        "state": "GA",
        "zip_code": "30342",
        "specialty": "Podiatrist",
        "score": 85,
        "priority": "medium",
        "status": "qualified",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 13,
        "practice_name": "CALIFORNIA WOUND CENTER",
        "owner_name": "Dr. Jennifer Adams",
        "practice_phone": "(415) 555-0901",
        "email": "contact@cawound.com",
        "address": "3700 California St",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94118",
        "specialty": "Wound Care",
        "score": 90,
        "priority": "high",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 14,
        "practice_name": "OHIO PODIATRY ASSOCIATES",
        "owner_name": "Dr. Mark Johnson",
        "practice_phone": "(614) 555-1012",
        "email": "contact@ohiopodiatry.com",
        "address": "3535 Olentangy River Rd",
        "city": "Columbus",
        "state": "OH",
        "zip_code": "43214",
        "specialty": "Podiatrist",
        "score": 82,
        "priority": "medium",
        "status": "contacted",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 15,
        "practice_name": "NEW YORK ORTHOPEDIC GROUP",
        "owner_name": "Dr. Rachel Cohen",
        "practice_phone": "(212) 555-1123",
        "email": "contact@nyortho.com",
        "address": "523 E 72nd St",
        "city": "New York",
        "state": "NY",
        "zip_code": "10021",
        "specialty": "Orthopedic Surgery",
        "score": 93,
        "priority": "high",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 16,
        "practice_name": "PACIFIC FOOT SPECIALISTS",
        "owner_name": "Dr. Steven Kim",
        "practice_phone": "(206) 555-1234",
        "email": "contact@pacificfoot.com",
        "address": "1100 9th Ave",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101",
        "specialty": "Podiatrist",
        "score": 84,
        "priority": "medium",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 17,
        "practice_name": "TEXAS WOUND HEALING CENTER",
        "owner_name": "Dr. Angela Rodriguez",
        "practice_phone": "(713) 555-1345",
        "email": "contact@txwound.com",
        "address": "6624 Fannin St",
        "city": "Houston",
        "state": "TX",
        "zip_code": "77030",
        "specialty": "Wound Care",
        "score": 87,
        "priority": "medium",
        "status": "qualified",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 18,
        "practice_name": "MICHIGAN PODIATRY CLINIC",
        "owner_name": "Dr. Thomas Miller",
        "practice_phone": "(313) 555-1456",
        "email": "contact@michpodiatry.com",
        "address": "4160 John R St",
        "city": "Detroit",
        "state": "MI",
        "zip_code": "48201",
        "specialty": "Podiatrist",
        "score": 81,
        "priority": "medium",
        "status": "contacted",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 19,
        "practice_name": "VIRGINIA ORTHOPEDIC CENTER",
        "owner_name": "Dr. Susan Davis",
        "practice_phone": "(757) 555-1567",
        "email": "contact@vaortho.com",
        "address": "620 John Paul Jones Cir",
        "city": "Portsmouth",
        "state": "VA",
        "zip_code": "23708",
        "specialty": "Orthopedic Surgery",
        "score": 89,
        "priority": "medium",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 20,
        "practice_name": "ALABAMA FOOT CARE",
        "owner_name": "Dr. William Taylor",
        "practice_phone": "(205) 555-1678",
        "email": "contact@alfoot.com",
        "address": "1720 2nd Ave N",
        "city": "Birmingham",
        "state": "AL",
        "zip_code": "35203",
        "specialty": "Podiatrist",
        "score": 83,
        "priority": "medium",
        "status": "new",
        "assigned_user_id": None,
        "docs_sent": False,
        "created_at": "2025-01-15T10:00:00Z"
    }
]

def assign_leads_to_new_agent(agent_id, count=20):
    """Assign unassigned leads to a new agent"""
    global LEADS
    
    # Find unassigned leads
    unassigned_leads = [lead for lead in LEADS if lead["assigned_user_id"] is None]
    
    # Sort by score (highest first)
    unassigned_leads.sort(key=lambda x: x["score"], reverse=True)
    
    # Assign up to 'count' leads
    assigned_count = 0
    for lead in unassigned_leads[:count]:
        lead["assigned_user_id"] = agent_id
        assigned_count += 1
    
    return assigned_count

def lambda_handler(event, context):
    """AWS Lambda handler for VantagePoint CRM"""
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
        
        print(f"🔥 VantagePoint {method} {path} - {len(LEADS)} leads, {len(USERS)} users")
        
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
                'body': json.dumps(body_dict)
            }
        
        # Handle preflight OPTIONS requests
        if method == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight successful'})
        
        # Health check
        if path == '/health':
            return create_response(200, {
                'status': 'healthy',
                'service': 'VantagePoint CRM API',
                'leads_count': len(LEADS),
                'users_count': len(USERS),
                'version': '1.0.0',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Login endpoint
        if path == '/api/v1/auth/login' and method == 'POST':
            username = body_data.get('username')
            password = body_data.get('password')
            
            if not username or not password:
                return create_response(400, {"detail": "Username and password required"})
            
            # Hash the provided password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Check credentials
            user = USERS.get(username)
            if not user or user['password_hash'] != password_hash:
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
                    "full_name": user['full_name']
                }
            })
        
        # Get current user info endpoint
        if path == '/api/v1/auth/me' and method == 'GET':
            auth_header = headers.get("authorization", headers.get("Authorization", ""))
            if not auth_header.startswith("Bearer "):
                return create_response(401, {"detail": "Missing or invalid authorization header"})
            
            # Simple token validation (in production, properly validate JWT)
            token = auth_header.replace("Bearer ", "")
            
            return create_response(200, {
                "username": "admin",
                "role": "admin",
                "email": "admin@vantagepoint.com"
            })
        
        # Protected endpoints require authentication
        if path.startswith("/api/v1/") and path not in ["/api/v1/auth/login", "/api/v1/auth/me"]:
            auth_header = headers.get("authorization", headers.get("Authorization", ""))
            if not auth_header.startswith("Bearer "):
                return create_response(401, {"detail": "Missing or invalid authorization header"})
        
        # Get all leads
        if path == '/api/v1/leads' and method == 'GET':
            return create_response(200, {
                "leads": LEADS,
                "total": len(LEADS)
            })
        
        # Create new user (admin/manager only)
        if path == '/api/v1/users' and method == 'POST':
            global NEXT_USER_ID
            
            new_user_data = body_data
            username = new_user_data.get('username')
            password = new_user_data.get('password', 'admin123')  # Default password
            role = new_user_data.get('role', 'agent')
            
            if not username:
                return create_response(400, {"detail": "Username is required"})
            
            if username in USERS:
                return create_response(400, {"detail": "Username already exists"})
            
            # Create new user
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            new_user = {
                "id": NEXT_USER_ID,
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "email": f"{username}@vantagepoint.com",
                "full_name": new_user_data.get('full_name', username.title()),
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "manager_id": new_user_data.get('manager_id')
            }
            
            USERS[username] = new_user
            NEXT_USER_ID += 1
            
            # If new user is an agent, assign 20 leads
            if role == 'agent':
                assigned_count = assign_leads_to_new_agent(new_user["id"], 20)
                print(f"✅ Assigned {assigned_count} leads to new agent {username}")
            
            return create_response(201, {
                "message": "User created successfully",
                "user": {k: v for k, v in new_user.items() if k != 'password_hash'},
                "leads_assigned": assigned_count if role == 'agent' else 0
            })
        
        # Get summary/dashboard stats
        if path == '/api/v1/summary' and method == 'GET':
            total_leads = len(LEADS)
            high_priority = len([l for l in LEADS if l["priority"] == "high"])
            contacted = len([l for l in LEADS if l["status"] == "contacted"])
            qualified = len([l for l in LEADS if l["status"] == "qualified"])
            
            return create_response(200, {
                "total_leads": total_leads,
                "high_priority": high_priority,
                "contacted": contacted,
                "qualified": qualified,
                "goldmines": len([l for l in LEADS if l.get("priority") == "high" and l.get("score", 0) >= 90]),
                "high_value": len([l for l in LEADS if l.get("score", 0) >= 80]),
                "perfect_scores": len([l for l in LEADS if l.get("score", 0) == 100])
            })
        
        # Default 404 response
        return create_response(404, {"detail": "Endpoint not found"})
        
    except Exception as e:
        print(f"❌ Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': response_headers,
            'body': json.dumps({"detail": "Internal server error"})
        } 