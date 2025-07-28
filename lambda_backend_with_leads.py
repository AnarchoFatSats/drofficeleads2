import json
import os
from datetime import datetime, timedelta
import jwt
import hashlib

# In-memory storage for demo (replace with RDS in production)
USERS = {
    "admin": {
        "username": "admin",
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
        "role": "admin",
        "email": "admin@curagenesis.com"
    }
}

# Real leads storage - will be loaded from hot_leads.json or database
LEADS = []
LEAD_COUNTER = 0

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

def load_initial_leads():
    """Load initial demo leads if LEADS is empty"""
    global LEADS, LEAD_COUNTER
    
    if not LEADS:
        # Demo leads for testing
        LEADS = [
            {
                "id": 1,
                "company_name": "Rural Health Clinic",
                "contact_name": "Dr. Smith",
                "phone": "555-0123",
                "email": "dr.smith@ruralhealthclinic.com",
                "status": "new",
                "priority": "high",
                "specialty": "Primary Care",
                "location": "Rural County, TX",
                "score": 85,
                "created_at": datetime.utcnow().isoformat()
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
                "location": "Mountain View, CO",
                "score": 75,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        LEAD_COUNTER = len(LEADS)

def create_lead(lead_data, user_data):
    """Create a new lead"""
    global LEADS, LEAD_COUNTER
    
    LEAD_COUNTER += 1
    
    # Create new lead with required fields
    new_lead = {
        "id": LEAD_COUNTER,
        "company_name": lead_data.get("company_name", ""),
        "contact_name": lead_data.get("contact_name", ""),
        "phone": lead_data.get("phone", ""),
        "email": lead_data.get("email", ""),
        "status": lead_data.get("status", "new"),
        "priority": lead_data.get("priority", "medium"),
        "specialty": lead_data.get("specialty", ""),
        "location": lead_data.get("location", ""),
        "score": lead_data.get("score", 50),
        "created_at": datetime.utcnow().isoformat(),
        "created_by": user_data.get("username", "system")
    }
    
    # Add optional fields if provided
    optional_fields = ["practice_name", "owner_name", "practice_phone", "owner_phone", 
                      "providers", "city", "state", "zip", "address", "ein", 
                      "is_sole_proprietor", "entity_type", "npi", "category"]
    
    for field in optional_fields:
        if field in lead_data:
            new_lead[field] = lead_data[field]
    
    LEADS.append(new_lead)
    return new_lead

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    # Load initial leads if empty
    load_initial_leads()
    
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
        return create_response(200, {
            "status": "healthy", 
            "service": "CRM Lambda Backend with Lead Creation",
            "total_leads": len(LEADS),
            "timestamp": datetime.utcnow().isoformat()
        })
    
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
    if path == "/api/v1/leads":
        if method == "GET":
            return create_response(200, {
                "leads": LEADS,
                "total": len(LEADS),
                "message": f"Retrieved {len(LEADS)} leads"
            })
        
        elif method == "POST":
            try:
                new_lead = create_lead(request_data, user_data)
                return create_response(201, {
                    "lead": new_lead,
                    "message": "Lead created successfully"
                })
            except Exception as e:
                return create_response(400, {
                    "detail": f"Error creating lead: {str(e)}"
                })
    
    # Update specific lead
    if path.startswith("/api/v1/leads/") and method == "PUT":
        try:
            lead_id = int(path.split("/")[-1])
            
            # Find and update lead
            for i, lead in enumerate(LEADS):
                if lead["id"] == lead_id:
                    # Update lead with new data
                    LEADS[i].update(request_data)
                    LEADS[i]["updated_at"] = datetime.utcnow().isoformat()
                    LEADS[i]["updated_by"] = user_data.get("username", "system")
                    return create_response(200, LEADS[i])
            
            return create_response(404, {"detail": "Lead not found"})
        except ValueError:
            return create_response(400, {"detail": "Invalid lead ID"})
        except Exception as e:
            return create_response(400, {"detail": f"Error updating lead: {str(e)}"})
    
    # Delete specific lead
    if path.startswith("/api/v1/leads/") and method == "DELETE":
        try:
            lead_id = int(path.split("/")[-1])
            
            # Find and remove lead
            for i, lead in enumerate(LEADS):
                if lead["id"] == lead_id:
                    removed_lead = LEADS.pop(i)
                    return create_response(200, {
                        "message": "Lead deleted successfully",
                        "deleted_lead": removed_lead
                    })
            
            return create_response(404, {"detail": "Lead not found"})
        except ValueError:
            return create_response(400, {"detail": "Invalid lead ID"})
        except Exception as e:
            return create_response(400, {"detail": f"Error deleting lead: {str(e)}"})
    
    # Bulk load leads endpoint (for uploading hot_leads.json data)
    if path == "/api/v1/leads/bulk" and method == "POST":
        try:
            leads_data = request_data.get("leads", [])
            if not leads_data:
                return create_response(400, {"detail": "No leads data provided"})
            
            created_leads = []
            for lead_data in leads_data:
                try:
                    new_lead = create_lead(lead_data, user_data)
                    created_leads.append(new_lead)
                except Exception as e:
                    print(f"Error creating lead: {e}")
                    continue
            
            return create_response(201, {
                "message": f"Successfully created {len(created_leads)} leads",
                "created_count": len(created_leads),
                "total_leads": len(LEADS)
            })
            
        except Exception as e:
            return create_response(400, {
                "detail": f"Error in bulk load: {str(e)}"
            })
    
    # Summary endpoint
    if path == "/api/v1/summary" and method == "GET":
        status_counts = {}
        priority_counts = {}
        
        for lead in LEADS:
            status = lead.get("status", "unknown")
            priority = lead.get("priority", "unknown")
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return create_response(200, {
            "total_leads": len(LEADS),
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "new_leads": status_counts.get("new", 0),
            "contacted_leads": status_counts.get("contacted", 0),
            "high_priority": priority_counts.get("high", 0)
        })
    
    # Hot leads endpoint  
    if path == "/api/v1/hot-leads" and method == "GET":
        hot_leads = [l for l in LEADS if l.get("priority") == "high" or l.get("score", 0) >= 90]
        return create_response(200, {"hot_leads": hot_leads, "count": len(hot_leads)})
    
    # Regions endpoint
    if path == "/api/v1/regions" and method == "GET":
        regions = list(set([lead.get("state", "Unknown") for lead in LEADS if lead.get("state")]))
        return create_response(200, {"regions": sorted(regions)})
    
    # Default response
    return create_response(404, {"detail": "Endpoint not found"}) 