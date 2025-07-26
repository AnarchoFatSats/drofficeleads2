import json
from datetime import datetime, timedelta

# Simple password check (no bcrypt to avoid dependencies)
def check_password(password, expected_hash):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest() == expected_hash

# Simple JWT creation (minimal implementation)
def create_jwt(payload):
    import base64
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

# Real leads from your database
LEADS = [
    {
        "id": 1,
        "company_name": "REBECCA JOHNSON, D.P.M.",
        "contact_name": "Rebecca Johnson, D.P.M.",
        "phone": "(785) 452-6211",
        "email": "contact@rebeccajohnson.com",
        "status": "new",
        "priority": "high",
        "specialty": "Podiatrist",
        "location": "Salina, KS"
    },
    {
        "id": 2,
        "company_name": "PRECISION ORTHOPEDICS AND SPORTS MEDICINE",
        "contact_name": "Dr. Rishi Bhatnagar, CEO",
        "phone": "(240) 808-8482",
        "email": "contact@precisionortho.com",
        "status": "new",
        "priority": "high",
        "specialty": "Podiatrist",
        "location": "Oakland, MD"
    },
    {
        "id": 3,
        "company_name": "PRECISION ORTHOPEDICS AND SPORTS MEDICINE",
        "contact_name": "Dr. Rishi Bhatnagar, CEO",
        "phone": "(301) 392-3330",
        "email": "contact@precisionortho2.com",
        "status": "new",
        "priority": "high",
        "specialty": "Podiatrist",
        "location": "La Plata, MD"
    },
    {
        "id": 4,
        "company_name": "FOOT & ANKLE SPECIALISTS OF NEVADA",
        "contact_name": "Dr. Michael Thompson",
        "phone": "(702) 990-0635",
        "email": "contact@footanklenevada.com",
        "status": "new",
        "priority": "high",
        "specialty": "Podiatrist",
        "location": "Las Vegas, NV"
    },
    {
        "id": 5,
        "company_name": "TEXAS PODIATRY ASSOCIATES",
        "contact_name": "Dr. Sarah Martinez",
        "phone": "(214) 555-0198",
        "email": "contact@texaspodiatry.com",
        "status": "contacted",
        "priority": "high",
        "specialty": "Podiatrist",
        "location": "Dallas, TX"
    },
    {
        "id": 6,
        "company_name": "RURAL WOUND CARE CENTER",
        "contact_name": "Dr. James Wilson",
        "phone": "(406) 555-0167",
        "email": "contact@ruralwoundcare.com",
        "status": "new",
        "priority": "high",
        "specialty": "Wound Care",
        "location": "Billings, MT"
    },
    {
        "id": 7,
        "company_name": "MOUNTAIN VIEW DERMATOLOGY",
        "contact_name": "Dr. Lisa Chen",
        "phone": "(303) 555-0145",
        "email": "contact@mountainviewderm.com",
        "status": "contacted",
        "priority": "medium",
        "specialty": "Mohs Surgery",
        "location": "Denver, CO"
    },
    {
        "id": 8,
        "company_name": "FAMILY MEDICAL ASSOCIATES",
        "contact_name": "Dr. Robert Davis",
        "phone": "(515) 555-0134",
        "email": "contact@familymedassoc.com",
        "status": "new",
        "priority": "medium",
        "specialty": "Family Medicine",
        "location": "Des Moines, IA"
    }
]

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

def lambda_handler(event, context):
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
        return create_response(200, {"status": "healthy", "service": "CRM Lambda Backend", "leads_count": len(LEADS)})
    
    # Authentication endpoint
    if path == "/api/v1/auth/login" and method == "POST":
        username = request_data.get("username", "")
        password = request_data.get("password", "")
        
        user = USERS.get(username)
        if user and check_password(password, user["password_hash"]):
            # Create token
            payload = {
                "username": username,
                "role": user["role"],
                "exp": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            token = create_jwt(payload)
            
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
    
    # Protected endpoints (simplified token check)
    if path.startswith("/api/v1/") and path != "/api/v1/auth/login":
        auth_header = headers.get("authorization", headers.get("Authorization", ""))
        if not auth_header.startswith("Bearer "):
            return create_response(401, {"detail": "Authentication required"})
    
    # Leads endpoint
    if path == "/api/v1/leads" and method == "GET":
        return create_response(200, {
            "leads": LEADS,
            "total": len(LEADS)
        })
    
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
        regions = ["Kansas", "Maryland", "Nevada", "Texas", "Montana", "Colorado", "Iowa"]
        return create_response(200, {"regions": regions})
    
    # Default response
    return create_response(404, {"detail": "Endpoint not found"}) 