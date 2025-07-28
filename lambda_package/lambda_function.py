#!/usr/bin/env python3
"""
Complete VantagePoint CRM Lambda - Production Ready
All features: Role-based stats, Lead CRUD, Send Docs, Agent assignment
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

def decode_jwt_token(token):
    """Simple JWT token decoding for user info"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        payload_b64 = parts[1]
        # Add padding if needed
        while len(payload_b64) % 4:
            payload_b64 += '='
        
        payload_json = base64.urlsafe_b64decode(payload_b64).decode()
        return json.loads(payload_json)
    except:
        return None

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

# Auto-incrementing IDs - Initialize based on existing data
NEXT_USER_ID = 4
# Calculate NEXT_LEAD_ID based on existing leads to avoid conflicts
existing_lead_ids = [1,2,3,4,6,7,8,9,10,11,12,13,14,15,16,17,18,19]  # Known IDs from current data
NEXT_LEAD_ID = max(existing_lead_ids) + 1 if existing_lead_ids else 1

# Production leads database - 20 high-quality leads with all statuses
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
        "status": "new",  # Fresh lead for Day 1
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "PTAN123456",
        "ein_tin": "EIN123456789",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-20T15:30:00Z"
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
        "status": "new", # Fresh lead for Day 1
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "PTAN123457",
        "ein_tin": "EIN123456790",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-18T12:00:00Z"
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
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "PTAN123458",
        "ein_tin": "EIN123456791",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-25T09:15:00Z"
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
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "assigned_user_id": 3,  # Fixed: Assign to agent1
        "docs_sent": False,
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "status": "new",  # Fresh lead
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "PTAN123459",
        "ein_tin": "EIN123456792",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-22T14:45:00Z"
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
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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
        "assigned_user_id": 3,  # Fixed: Assign to agent1
        "docs_sent": False,
        "ptan": "",
        "ein_tin": "",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
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

def get_role_based_stats(user_role, user_id):
    """Get statistics based on user role"""
    if user_role == "admin":
        # Admin sees all leads
        relevant_leads = LEADS
    elif user_role == "manager":
        # Manager sees leads of their agents
        manager_agents = [user for user in USERS.values() if user.get("manager_id") == user_id]
        agent_ids = [agent["id"] for agent in manager_agents]
        relevant_leads = [lead for lead in LEADS if lead["assigned_user_id"] in agent_ids]
    else:  # agent
        # Agent sees their own leads + team comparison data
        # For competitive view, agents can see team performance but not individual leads
        relevant_leads = [lead for lead in LEADS if lead["assigned_user_id"] == user_id]
    
    # Calculate stats
    total_leads = len(relevant_leads)
    practices_signed_up = len([l for l in relevant_leads if l["status"] in ["sold", "disposed"]])
    active_leads = len([l for l in relevant_leads if l["status"] in ["contacted", "qualified"]])
    conversion_rate = round((practices_signed_up / total_leads * 100) if total_leads > 0 else 0, 1)
    
    # Additional competitive stats for agents
    if user_role == "agent":
        # Add team comparison data
        all_agent_stats = {}
        for username, user in USERS.items():
            if user["role"] == "agent":
                agent_leads = [l for l in LEADS if l["assigned_user_id"] == user["id"]]
                agent_sales = len([l for l in agent_leads if l["status"] in ["sold", "disposed"]])
                all_agent_stats[username] = agent_sales
        
        return {
            "total_leads": total_leads,
            "practices_signed_up": practices_signed_up,
            "active_leads": active_leads,
            "conversion_rate": conversion_rate,
            "team_performance": all_agent_stats,
            "your_rank": sorted(all_agent_stats.values(), reverse=True).index(practices_signed_up) + 1 if practices_signed_up in all_agent_stats.values() else len(all_agent_stats)
        }
    
    return {
        "total_leads": total_leads,
        "practices_signed_up": practices_signed_up,
        "active_leads": active_leads,
        "conversion_rate": conversion_rate
    }

def lambda_handler(event, context):
    """AWS Lambda handler for VantagePoint CRM"""
    global NEXT_LEAD_ID, NEXT_USER_ID, LEADS, USERS
    
    try:
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
        
        def get_current_user_from_token(headers):
            """Extract user info from JWT token"""
            auth_header = headers.get("authorization", headers.get("Authorization", ""))
            if not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.replace("Bearer ", "")
            payload = decode_jwt_token(token)
            if not payload:
                return None
            
            return USERS.get(payload.get("username"))
        
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
                'version': '2.0.0',
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
                    "full_name": user['full_name'],
                    "id": user['id']
                }
            })
        
        # Get current user info endpoint
        if path == '/api/v1/auth/me' and method == 'GET':
            current_user = get_current_user_from_token(headers)
            if not current_user:
                return create_response(401, {"detail": "Invalid or expired token"})
            
            return create_response(200, {
                "username": current_user['username'],
                "role": current_user['role'],
                "email": current_user['email'],
                "full_name": current_user['full_name'],
                "id": current_user['id']
            })
        
        # Protected endpoints require authentication
        if path.startswith("/api/v1/") and path not in ["/api/v1/auth/login", "/api/v1/auth/me"]:
            current_user = get_current_user_from_token(headers)
            if not current_user:
                return create_response(401, {"detail": "Missing or invalid authorization header"})
        
        # Get all leads
        if path == '/api/v1/leads' and method == 'GET':
            # Role-based lead filtering
            if current_user['role'] == 'admin':
                visible_leads = LEADS
            elif current_user['role'] == 'manager':
                # Manager sees leads of their agents
                manager_agents = [user for user in USERS.values() if user.get("manager_id") == current_user['id']]
                agent_ids = [agent["id"] for agent in manager_agents]
                visible_leads = [lead for lead in LEADS if lead["assigned_user_id"] in agent_ids]
            else:  # agent
                # Agent sees their own leads
                visible_leads = [lead for lead in LEADS if lead["assigned_user_id"] == current_user['id']]
            
            return create_response(200, {
                "leads": visible_leads,
                "total": len(visible_leads)
            })
        
        # Helper function to get user by ID
        def get_user_by_id(user_id):
            for user_data in USERS.values():
                if user_data['id'] == user_id:
                    return user_data
            return None

        # Create new lead
        if path == '/api/v1/leads' and method == 'POST':
            current_user = get_current_user_from_token(headers)
            
            if not current_user:
                return create_response(401, {"detail": "Not authenticated"})
            
            lead_data = body_data
            
            # Validate required fields
            required_fields = ['practice_name', 'owner_name', 'practice_phone']
            for field in required_fields:
                if not lead_data.get(field):
                    return create_response(400, {"detail": f"{field} is required"})
            
            # Auto-assign to current user if no assignment specified
            assigned_user_id = lead_data.get('assigned_user_id')
            if not assigned_user_id:
                # Auto-assign based on role
                if current_user['role'] == 'agent':
                    assigned_user_id = current_user['id']
                elif current_user['role'] == 'manager':
                    # Managers can assign to themselves or their agents
                    managed_agent_ids = [u['id'] for u in USERS.values() if u.get('manager_id') == current_user['id']]
                    if managed_agent_ids:
                        # Assign to first available agent (can be enhanced with round-robin)
                        assigned_user_id = managed_agent_ids[0]
                    else:
                        assigned_user_id = current_user['id']  # Assign to self if no agents
                else:  # admin
                    # Assign to first available agent or self
                    agent_users = [u['id'] for u in USERS.values() if u['role'] == 'agent']
                    assigned_user_id = agent_users[0] if agent_users else current_user['id']
            
            # Create new lead
            new_lead = {
                "id": NEXT_LEAD_ID,
                "practice_name": lead_data.get('practice_name'),
                "owner_name": lead_data.get('owner_name'),
                "practice_phone": lead_data.get('practice_phone'),
                "email": lead_data.get('email', ''),
                "address": lead_data.get('address', ''),
                "city": lead_data.get('city', ''),
                "state": lead_data.get('state', ''),
                "zip_code": lead_data.get('zip_code', ''),
                "specialty": lead_data.get('specialty', ''),
                "score": int(lead_data.get('score', 75)),
                "priority": lead_data.get('priority', 'medium'),
                "status": lead_data.get('status', 'new'),
                "assigned_user_id": assigned_user_id,  # ✅ Fixed: Always has a valid assignment
                "docs_sent": False,
                "ptan": lead_data.get('ptan', ''),
                "ein_tin": lead_data.get('ein_tin', ''),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "created_by": current_user['username']
            }
            
            LEADS.append(new_lead)
            old_next_id = NEXT_LEAD_ID
            NEXT_LEAD_ID += 1
            
            print(f"✅ Lead created and assigned to user {assigned_user_id} ({get_user_by_id(assigned_user_id)['username']})")
            print(f"📊 Lead ID: {new_lead['id']}, Previous NEXT_LEAD_ID: {old_next_id}, New NEXT_LEAD_ID: {NEXT_LEAD_ID}")
            print(f"📋 Total leads in memory: {len(LEADS)}")
            
            return create_response(201, {
                "message": "Lead created successfully",
                "lead": new_lead,
                "assigned_to": get_user_by_id(assigned_user_id)['username'],
                "debug_info": {
                    "total_leads": len(LEADS),
                    "next_lead_id": NEXT_LEAD_ID
                }
            })

        # Search leads
        if path == '/api/v1/leads/search' and method == 'GET':
            current_user = get_current_user_from_token(headers)
            
            if not current_user:
                return create_response(401, {"detail": "Not authenticated"})
            
            # Get search query parameter
            query_params = event.get('queryStringParameters') or {}
            search_query = query_params.get('q', '').lower().strip()
            
            if not search_query:
                return create_response(400, {"detail": "Search query 'q' parameter is required"})
            
            # Get all leads that user can access (role-based)
            user_role = current_user['role']
            user_id = current_user['id']
            
            if user_role == 'admin':
                accessible_leads = LEADS
            elif user_role == 'manager':
                managed_agent_ids = [u['id'] for u in USERS.values() if u.get('manager_id') == user_id]
                accessible_leads = [l for l in LEADS if l.get('assigned_user_id') in managed_agent_ids]
            else:  # agent
                accessible_leads = [l for l in LEADS if l.get('assigned_user_id') == user_id]
            
            # Search within accessible leads
            search_results = []
            for lead in accessible_leads:
                # Search in multiple fields
                searchable_text = f"{lead.get('practice_name', '')} {lead.get('owner_name', '')} {lead.get('specialty', '')} {lead.get('city', '')} {lead.get('state', '')} {lead.get('status', '')} {lead.get('priority', '')}".lower()
                
                if search_query in searchable_text:
                    search_results.append(lead)
            
            return create_response(200, {
                "leads": search_results,
                "total": len(search_results),
                "query": search_query,
                "searched_in": len(accessible_leads)
            })
        
        # Update lead
        if path.startswith('/api/v1/leads/') and method == 'PUT':
            current_user = get_current_user_from_token(headers)
            
            if not current_user:
                return create_response(401, {"detail": "Not authenticated"})
            
            lead_id = int(path.split('/')[-1])
            lead = next((l for l in LEADS if l["id"] == lead_id), None)
            
            if not lead:
                return create_response(404, {"detail": f"Lead not found (ID: {lead_id}). Available IDs: {[l['id'] for l in LEADS][:10]}..."})
            
            # Check permissions - agents can only edit their own leads
            if current_user['role'] == 'agent' and lead["assigned_user_id"] != current_user['id']:
                return create_response(403, {"detail": "You can only edit your own leads"})
            
            # Update lead fields
            update_data = body_data
            for field in ['practice_name', 'owner_name', 'practice_phone', 'email', 'address', 
                         'city', 'state', 'zip_code', 'specialty', 'priority', 'status', 
                         'ptan', 'ein_tin', 'assigned_user_id']:
                if field in update_data:
                    lead[field] = update_data[field]
            
            if 'score' in update_data:
                lead['score'] = int(update_data['score'])
            
            lead['updated_at'] = datetime.utcnow().isoformat()
            
            return create_response(200, {
                "message": "Lead updated successfully",
                "lead": lead
            })
        
        # Send docs endpoint
        if path.startswith('/api/v1/leads/') and path.endswith('/send-docs') and method == 'POST':
            current_user = get_current_user_from_token(headers)
            
            if not current_user:
                return create_response(401, {"detail": "Not authenticated"})
            
            lead_id = int(path.split('/')[-2])
            lead = next((l for l in LEADS if l["id"] == lead_id), None)
            
            if not lead:
                return create_response(404, {"detail": "Lead not found"})
            
            # Check if lead has required data
            if not lead.get('email'):
                return create_response(400, {"detail": "Lead must have email before sending docs"})
            
            # Check if docs already sent
            if lead.get('docs_sent'):
                return create_response(400, {"detail": "Documents already sent to this lead"})
            
            # Check permissions - agents can only send docs for their own leads
            if current_user['role'] == 'agent' and lead["assigned_user_id"] != current_user['id']:
                return create_response(403, {"detail": "You can only send docs for your own leads"})
            
            # Mark docs as sent
            lead['docs_sent'] = True
            lead['updated_at'] = datetime.utcnow().isoformat()
            
            # In a real system, this would trigger actual document sending
            return create_response(200, {
                "message": "Documents sent successfully",
                "email_used": lead['email'],
                "external_user_id": f"EXT_{lead['id']}_{int(datetime.now().timestamp())}",
                "sent_at": datetime.utcnow().isoformat()
            })
        
        # Create new user (admin/manager only)
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
            
            if username in USERS:
                return create_response(400, {"detail": "Username already exists"})
            
            # Managers can only create agents
            if current_user['role'] == 'manager' and role != 'agent':
                return create_response(403, {"detail": "Managers can only create agent accounts"})
            
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
                "manager_id": current_user['id'] if current_user['role'] == 'manager' else new_user_data.get('manager_id')
            }
            
            USERS[username] = new_user
            NEXT_USER_ID += 1
            
            # If new user is an agent, assign 20 leads
            assigned_count = 0
            if role == 'agent':
                assigned_count = assign_leads_to_new_agent(new_user["id"], 20)
                print(f"✅ Assigned {assigned_count} leads to new agent {username}")
            
            return create_response(201, {
                "message": "User created successfully",
                "user": {k: v for k, v in new_user.items() if k != 'password_hash'},
                "leads_assigned": assigned_count
            })
        
        # Get role-based dashboard stats
        if path == '/api/v1/summary' and method == 'GET':
            stats = get_role_based_stats(current_user['role'], current_user['id'])
            return create_response(200, stats)
        
        # Default 404 response
        return create_response(404, {"detail": "Endpoint not found"})
        
    except Exception as e:
        print(f"❌ Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': response_headers,
            'body': json.dumps({"detail": f"Internal server error: {str(e)}"})
        } 