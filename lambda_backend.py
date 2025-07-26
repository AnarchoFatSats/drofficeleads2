import json
import os
from datetime import datetime, timedelta
import jwt
import hashlib

# Load real leads from hot_leads.json
def load_real_leads():
    """Load real scored leads from hot_leads.json"""
    try:
        # In Lambda, this file would be included in the deployment package
        with open('hot_leads.json', 'r') as f:
            leads_data = json.load(f)
        
        # Convert to backend format and take top 50 for performance
        real_leads = []
        for i, lead in enumerate(leads_data[:50]):  # Top 50 highest scored leads
            real_leads.append({
                "id": i + 1,
                "company_name": lead.get("practice_name", "Unknown Practice"),
                "contact_name": lead.get("owner_name", "Unknown Owner"),
                "phone": lead.get("practice_phone", ""),
                "email": f"contact@{lead.get('practice_name', 'unknown').lower().replace(' ', '')}.com",
                "status": "new" if lead.get("priority") == "A+ Priority" else "contacted",
                "priority": "high" if lead.get("priority") in ["A+ Priority", "A Priority"] else "medium",
                "specialty": lead.get("category", "Unknown"),
                "location": f"{lead.get('city', '')}, {lead.get('state', '')}",
                "score": lead.get("score", 0),
                "lead_priority": lead.get("priority", "C Priority"),
                "specialties": lead.get("specialties", lead.get("category", "")),
                "providers": lead.get("providers", 1),
                "address": lead.get("address", ""),
                "zip_code": lead.get("zip_code", ""),
                "practice_phone": lead.get("practice_phone", ""),
                "owner_phone": lead.get("owner_phone", "")
            })
        
        print(f"✅ Loaded {len(real_leads)} real scored leads")
        return real_leads
        
    except Exception as e:
        print(f"⚠️ Could not load real leads: {e}")
        # Fallback to demo leads
        return [
            {
                "id": 1,
                "company_name": "Rural Health Clinic",
                "contact_name": "Dr. Smith",
                "phone": "555-0123",
                "email": "dr.smith@ruralhealthclinic.com",
                "status": "new",
                "priority": "high",
                "specialty": "Primary Care",
                "location": "Rural County, TX"
            },
            {
                "id": 2,
                "company_name": "Mountain View Medical",
                "contact_name": "Dr. Johnson", 
                "phone": "555-0456",
                "email": "johnson@mountainviewmed.com",
                "status": "contacted",
                "priority": "medium",
                "specialty": "Podiatry",
                "location": "Mountain View, CO"
            }
        ]

# In-memory storage for demo (replace with RDS in production)
USERS = {
    "admin": {
        "username": "admin",
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
        "role": "admin",
        "email": "admin@curagenesis.com"
    }
}

# Load real leads instead of hardcoded demo leads
LEADS = load_real_leads()

SECRET_KEY = "cura-genesis-crm-super-secret-key-lambda-2025"

def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
    }

def create_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": cors_headers(),
        "body": json.dumps(body)
    }

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        return None

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    method = event.get("httpMethod", "GET")
    path = event.get("path", "/")
    headers = event.get("headers", {})
    body = event.get("body", "{}")
    
    # Handle CORS preflight
    if method == "OPTIONS":
        return create_response(200, {"message": "CORS preflight"})
    
    # Parse body
    try:
        if body:
            request_data = json.loads(body)
        else:
            request_data = {}
    except:
        request_data = {}
    
    # Health check
    if path == "/health":
        return create_response(200, {"status": "healthy", "service": "CRM Lambda Backend"})
    
    # Authentication endpoint
    if path == "/api/v1/auth/login" and method == "POST":
        username = request_data.get("username", "")
        password = request_data.get("password", "")
        
        # Hash the provided password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        user = USERS.get(username)
        if user and user["password_hash"] == password_hash:
            # Create JWT token
            payload = {
                "username": username,
                "role": user["role"],
                "exp": datetime.utcnow() + timedelta(hours=24)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            
            return create_response(200, {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"]
                }
            })
        else:
            return create_response(401, {"detail": "Invalid credentials"})
    
    # Get token from Authorization header
    auth_header = headers.get("authorization", headers.get("Authorization", ""))
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    # Protected endpoints require authentication
    if path.startswith("/api/v1/") and path != "/api/v1/auth/login":
        if not token:
            return create_response(401, {"detail": "Authentication required"})
        
        user_data = verify_token(token)
        if not user_data:
            return create_response(401, {"detail": "Invalid token"})
    
    # Leads endpoints
    if path == "/api/v1/leads" and method == "GET":
        return create_response(200, {
            "leads": LEADS,
            "total": len(LEADS)
        })
    
    if path.startswith("/api/v1/leads/") and method == "PUT":
        lead_id = int(path.split("/")[-1])
        
        # Find and update lead
        for i, lead in enumerate(LEADS):
            if lead["id"] == lead_id:
                LEADS[i].update(request_data)
                return create_response(200, LEADS[i])
        
        return create_response(404, {"detail": "Lead not found"})
    
    # Summary endpoint
    if path == "/api/v1/summary" and method == "GET":
        return create_response(200, {
            "total_leads": len(LEADS),
            "new_leads": len([l for l in LEADS if l["status"] == "new"]),
            "contacted_leads": len([l for l in LEADS if l["status"] == "contacted"]),
            "high_priority": len([l for l in LEADS if l["priority"] == "high"])
        })
    
    # Hot leads endpoint  
    if path == "/api/v1/hot-leads" and method == "GET":
        hot_leads = [l for l in LEADS if l["priority"] == "high"]
        return create_response(200, {"hot_leads": hot_leads})
    
    # Regions endpoint
    if path == "/api/v1/regions" and method == "GET":
        regions = ["Texas", "Colorado", "Rural Counties"]
        return create_response(200, {"regions": regions})
    
    # Default response
    return create_response(404, {"detail": "Endpoint not found"}) 