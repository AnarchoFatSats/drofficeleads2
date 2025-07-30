#!/usr/bin/env python3
"""
Complete VantagePoint CRM Lambda - Production Ready with DynamoDB User Persistence
FIXED: Users now stored in DynamoDB instead of memory - survives Lambda restarts
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

# DynamoDB client for persistent user storage
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('vantagepoint-users')

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

# ✅ FIXED: DynamoDB User Management Functions
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
        print(f"✅ User {username} created in DynamoDB")
        return True
    except ClientError as e:
        print(f"❌ Error creating user {username}: {e}")
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
            print(f"✅ Initialized default user: {username}")

def get_next_user_id():
    """Get next available user ID"""
    all_users = get_all_users()
    if not all_users:
        return 4  # Start after default users
    
    max_id = max([user.get('id', 0) for user in all_users])
    return max_id + 1

# Auto-incrementing IDs - Initialize based on existing data
NEXT_LEAD_ID = 20  # Start after existing leads

# Production leads database - 22 high-quality medical practice leads
LEADS = [
    {
        "id": 1,
        "practice_name": "RANCHO MIRAGE PODIATRY",
        "owner_name": "Dr. Matthew Diltz",
        "practice_phone": "(760) 568-2684",
        "email": "contact@ranchomiragepod.com",
        "address": "5282 Professional Plaza",
        "city": "Rancho Mirage",
        "state": "CA",
        "zip_code": "92270",
        "specialty": "Podiatrist",
        "score": 71,
        "priority": "low",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P36365212",
        "ein_tin": "65-2070513",
        "created_at": "2025-07-11T07:39:39Z",
        "updated_at": "2025-07-12T05:39:39Z",
        "created_by": "system"
    },
    {
        "id": 2,
        "practice_name": "MOUNTAIN VIEW MEDICAL",
        "owner_name": "Dr. Sarah Johnson",
        "practice_phone": "(801) 427-6268",
        "email": "contact@mountainviewmed.com",
        "address": "5201 Practice Lane",
        "city": "Mountain View",
        "state": "CO",
        "zip_code": "80424",
        "specialty": "Primary Care",
        "score": 92,
        "priority": "high",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P92170707",
        "ein_tin": "36-2797767",
        "created_at": "2025-07-20T07:39:39Z",
        "updated_at": "2025-07-21T04:39:39Z",
        "created_by": "system"
    },
    {
        "id": 3,
        "practice_name": "COASTAL ORTHOPEDICS",
        "owner_name": "Dr. Michael Chen",
        "practice_phone": "(310) 789-0123",
        "email": "contact@coastalorthopedic.com",
        "address": "8834 Professional Plaza",
        "city": "Santa Monica",
        "state": "CA",
        "zip_code": "90401",
        "specialty": "Orthopedic Surgery",
        "score": 91,
        "priority": "high",
        "status": "contacted",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P18374659",
        "ein_tin": "57-1948372",
        "created_at": "2025-01-08T12:15:33Z",
        "updated_at": "2025-01-09T09:30:45Z",
        "created_by": "system"
    },
    {
        "id": 4,
        "practice_name": "DESERT VALLEY CARDIOLOGY",
        "owner_name": "Dr. Jennifer Rodriguez",
        "practice_phone": "(602) 456-7890",
        "email": "contact@desertvalleycard.com",
        "address": "6723 Medical Blvd",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85016",
        "specialty": "Cardiology",
        "score": 88,
        "priority": "high",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P29485762",
        "ein_tin": "73-2847596",
        "created_at": "2025-01-10T14:20:18Z",
        "updated_at": "2025-01-11T11:05:42Z",
        "created_by": "system"
    },
    {
        "id": 5,
        "practice_name": "METRO FAMILY PRACTICE",
        "owner_name": "Dr. David Kim",
        "practice_phone": "(720) 567-8901",
        "email": "contact@metrofamilypract.com",
        "address": "3456 Clinic Ave",
        "city": "Denver",
        "state": "CO",
        "zip_code": "80203",
        "specialty": "Family Medicine",
        "score": 76,
        "priority": "medium",
        "status": "qualified",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P84759362",
        "ein_tin": "46-8392075",
        "created_at": "2025-01-12T09:45:27Z",
        "updated_at": "2025-01-13T15:20:39Z",
        "created_by": "system"
    },
    {
        "id": 6,
        "practice_name": "PACIFIC DERMATOLOGY",
        "owner_name": "Dr. Lisa Wang",
        "practice_phone": "(206) 678-9012",
        "email": "contact@pacificdermatolo.com",
        "address": "1278 Health Center Dr",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101",
        "specialty": "Dermatology",
        "score": 83,
        "priority": "medium",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P75639284",
        "ein_tin": "92-6384751",
        "created_at": "2025-01-15T11:30:15Z",
        "updated_at": "2025-01-16T08:45:28Z",
        "created_by": "system"
    },
    {
        "id": 7,
        "practice_name": "CENTRAL TEXAS NEUROLOGY",
        "owner_name": "Dr. Robert Martinez",
        "practice_phone": "(512) 789-0123",
        "email": "contact@centraltexasneur.com",
        "address": "5921 Practice Lane",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "specialty": "Neurology",
        "score": 95,
        "priority": "high",
        "status": "contacted",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P53746829",
        "ein_tin": "18-7492635",
        "created_at": "2025-01-18T13:25:44Z",
        "updated_at": "2025-01-19T10:15:56Z",
        "created_by": "system"
    },
    {
        "id": 8,
        "practice_name": "GATEWAY GASTROENTEROLOGY",
        "owner_name": "Dr. Amanda Thompson",
        "practice_phone": "(314) 890-1234",
        "email": "contact@gatewaygas.com",
        "address": "2847 Wellness Way",
        "city": "St. Louis",
        "state": "MO",
        "zip_code": "63101",
        "specialty": "Gastroenterology",
        "score": 79,
        "priority": "medium",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P92847563",
        "ein_tin": "64-5839271",
        "created_at": "2025-01-20T16:40:33Z",
        "updated_at": "2025-01-21T12:25:47Z",
        "created_by": "system"
    },
    {
        "id": 9,
        "practice_name": "SUNRISE URGENT CARE",
        "owner_name": "Dr. James Park",
        "practice_phone": "(702) 901-2345",
        "email": "contact@sunriseurgentcar.com",
        "address": "7392 Medical Blvd",
        "city": "Las Vegas",
        "state": "NV",
        "zip_code": "89101",
        "specialty": "Urgent Care",
        "score": 67,
        "priority": "low",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P48372951",
        "ein_tin": "35-9472861",
        "created_at": "2025-01-23T07:55:21Z",
        "updated_at": "2025-01-24T14:10:38Z",
        "created_by": "system"
    },
    {
        "id": 10,
        "practice_name": "RIVERSIDE PEDIATRICS",
        "owner_name": "Dr. Maria Garcia",
        "practice_phone": "(813) 012-3456",
        "email": "contact@riversidepediatri.com",
        "address": "4685 Healthcare Dr",
        "city": "Tampa",
        "state": "FL",
        "zip_code": "33601",
        "specialty": "Pediatrics",
        "score": 81,
        "priority": "medium",
        "status": "qualified",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P61847392",
        "ein_tin": "72-3946581",
        "created_at": "2025-01-25T10:20:14Z",
        "updated_at": "2025-01-26T17:35:29Z",
        "created_by": "system"
    },
    {
        "id": 11,
        "practice_name": "NORTHSIDE OPHTHALMOLOGY",
        "owner_name": "Dr. Kevin Lee",
        "practice_phone": "(312) 123-4567",
        "email": "contact@northsideophthalm.com",
        "address": "9174 Professional Plaza",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60601",
        "specialty": "Ophthalmology",
        "score": 86,
        "priority": "medium",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P74839265",
        "ein_tin": "58-2947361",
        "created_at": "2025-01-28T12:45:52Z",
        "updated_at": "2025-01-29T09:20:15Z",
        "created_by": "system"
    },
    {
        "id": 12,
        "practice_name": "MOUNTAIN PEAK WELLNESS",
        "owner_name": "Dr. Sarah Mitchell",
        "practice_phone": "(801) 234-5678",
        "email": "contact@mountainpeakwelln.com",
        "address": "3527 Clinic Ave",
        "city": "Salt Lake City",
        "state": "UT",
        "zip_code": "84101",
        "specialty": "Internal Medicine",
        "score": 93,
        "priority": "high",
        "status": "contacted",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P29573648",
        "ein_tin": "41-7583926",
        "created_at": "2025-01-30T15:30:47Z",
        "updated_at": "2025-01-31T11:45:23Z",
        "created_by": "system"
    },
    {
        "id": 13,
        "practice_name": "BLUEGRASS FAMILY HEALTH",
        "owner_name": "Dr. William Jones",
        "practice_phone": "(502) 345-6789",
        "email": "contact@bluegrassfamilyh.com",
        "address": "6841 Health Center Dr",
        "city": "Louisville",
        "state": "KY",
        "zip_code": "40201",
        "specialty": "Family Medicine",
        "score": 78,
        "priority": "medium",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P85649372",
        "ein_tin": "93-4726158",
        "created_at": "2025-02-02T08:15:36Z",
        "updated_at": "2025-02-03T16:40:48Z",
        "created_by": "system"
    },
    {
        "id": 14,
        "practice_name": "COASTAL WOMEN'S HEALTH",
        "owner_name": "Dr. Rachel Davis",
        "practice_phone": "(305) 456-7890",
        "email": "contact@coastalwomenshe.com",
        "address": "2194 Practice Lane",
        "city": "Miami",
        "state": "FL",
        "zip_code": "33101",
        "specialty": "OB-GYN",
        "score": 89,
        "priority": "high",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P74628359",
        "ein_tin": "67-8394572",
        "created_at": "2025-02-05T11:25:19Z",
        "updated_at": "2025-02-06T13:50:34Z",
        "created_by": "system"
    },
    {
        "id": 15,
        "practice_name": "EMPIRE STATE ORTHOPEDICS",
        "owner_name": "Dr. Anthony Brown",
        "practice_phone": "(518) 567-8901",
        "email": "contact@empirestateortho.com",
        "address": "8362 Wellness Way",
        "city": "Albany",
        "state": "NY",
        "zip_code": "12201",
        "specialty": "Orthopedic Surgery",
        "score": 94,
        "priority": "high",
        "status": "qualified",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P51937264",
        "ein_tin": "24-6839571",
        "created_at": "2025-02-08T14:10:27Z",
        "updated_at": "2025-02-09T10:35:42Z",
        "created_by": "system"
    },
    {
        "id": 16,
        "practice_name": "GOLDEN VALLEY PSYCHIATRY",
        "owner_name": "Dr. Nicole Taylor",
        "practice_phone": "(612) 678-9012",
        "email": "contact@goldenvalleypsy.com",
        "address": "5729 Medical Blvd",
        "city": "Minneapolis",
        "state": "MN",
        "zip_code": "55401",
        "specialty": "Psychiatry",
        "score": 82,
        "priority": "medium",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P39584672",
        "ein_tin": "85-2746319",
        "created_at": "2025-02-10T09:45:15Z",
        "updated_at": "2025-02-11T15:20:38Z",
        "created_by": "system"
    },
    {
        "id": 17,
        "practice_name": "LONE STAR RADIOLOGY",
        "owner_name": "Dr. Daniel Wilson",
        "practice_phone": "(214) 789-0123",
        "email": "contact@lonestarradiolog.com",
        "address": "4186 Healthcare Dr",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75201",
        "specialty": "Radiology",
        "score": 87,
        "priority": "medium",
        "status": "contacted",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P62847351",
        "ein_tin": "19-5738462",
        "created_at": "2025-02-13T12:30:44Z",
        "updated_at": "2025-02-14T08:15:57Z",
        "created_by": "system"
    },
    {
        "id": 18,
        "practice_name": "GREAT LAKES ANESTHESIA",
        "owner_name": "Dr. Michelle Anderson",
        "practice_phone": "(313) 890-1234",
        "email": "contact@greatlakesanesth.com",
        "address": "7953 Professional Plaza",
        "city": "Detroit",
        "state": "MI",
        "zip_code": "48201",
        "specialty": "Anesthesiology",
        "score": 75,
        "priority": "low",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P84729365",
        "ein_tin": "56-3947281",
        "created_at": "2025-02-15T16:55:33Z",
        "updated_at": "2025-02-16T12:40:26Z",
        "created_by": "system"
    },
    {
        "id": 19,
        "practice_name": "CANYON COUNTRY SPORTS MED",
        "owner_name": "Dr. Christopher White",
        "practice_phone": "(970) 901-2345",
        "email": "contact@canyoncountryspo.com",
        "address": "1463 Clinic Ave",
        "city": "Grand Junction",
        "state": "CO",
        "zip_code": "81501",
        "specialty": "Sports Medicine",
        "score": 90,
        "priority": "high",
        "status": "new",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P37294658",
        "ein_tin": "73-8462957",
        "created_at": "2025-02-18T07:20:21Z",
        "updated_at": "2025-02-19T14:45:39Z",
        "created_by": "system"
    },
    {
        "id": 20,
        "practice_name": "ATLANTIC COASTAL SURGERY",
        "owner_name": "Dr. Elizabeth Harris",
        "practice_phone": "(757) 012-3456",
        "email": "contact@atlanticcoastalsu.com",
        "address": "9628 Health Center Dr",
        "city": "Virginia Beach",
        "state": "VA",
        "zip_code": "23451",
        "specialty": "General Surgery",
        "score": 96,
        "priority": "high",
        "status": "qualified",
        "assigned_user_id": 3,
        "docs_sent": False,
        "ptan": "P58394762",
        "ein_tin": "42-7593846",
        "created_at": "2025-02-20T10:35:18Z",
        "updated_at": "2025-02-21T17:20:45Z",
        "created_by": "system"
    },
    {
        "id": 21,
        "practice_name": "PIEDMONT PAIN MANAGEMENT",
        "owner_name": "Dr. Joseph Clark",
        "practice_phone": "(704) 123-4567",
        "email": "contact@piedmontpainmana.com",
        "address": "3785 Practice Lane",
        "city": "Charlotte",
        "state": "NC",
        "zip_code": "28201",
        "specialty": "Pain Management",
        "score": 84,
        "priority": "medium",
        "status": "contacted",
        "assigned_user_id": None,
        "docs_sent": False,
        "ptan": "P74829361",
        "ein_tin": "68-4927385",
        "created_at": "2025-02-23T13:50:29Z",
        "updated_at": "2025-02-24T09:15:44Z",
        "created_by": "system"
    },
    {
        "id": 22,
        "practice_name": "EMERALD CITY ENDOCRINOLOGY",
        "owner_name": "Dr. Patricia Lewis",
        "practice_phone": "(206) 234-5678",
        "email": "contact@emeraldcityendoc.com",
        "address": "6417 Wellness Way",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98109",
        "specialty": "Endocrinology",
        "score": 88,
        "priority": "high",
        "status": "new",
        "assigned_user_id": None,
        "docs_sent": False,
        "ptan": "P92746385",
        "ein_tin": "51-8394627",
        "created_at": "2025-02-25T15:15:37Z",
        "updated_at": "2025-02-26T11:30:52Z",
        "created_by": "system"
    }
]

def get_role_based_stats(user_role, user_id):
    """Calculate role-based statistics"""
    total_leads = len(LEADS)
    
    if user_role == "agent":
        user_leads = [l for l in LEADS if l.get('assigned_user_id') == user_id]
        practices_signed_up = len([l for l in user_leads if l.get('status') == 'signed_up'])
        active_leads = len([l for l in user_leads if l.get('status') in ['new', 'contacted', 'qualified']])
        conversion_rate = round((practices_signed_up / len(user_leads)) * 100, 1) if user_leads else 0
        
        return {
            "total_leads": len(user_leads),
            "practices_signed_up": practices_signed_up,
            "active_leads": active_leads,
            "conversion_rate": conversion_rate,
            "your_rank": 1
        }
    
    elif user_role == "manager":
        all_users = get_all_users()
        team_users = [u for u in all_users if u.get('manager_id') == user_id or u.get('id') == user_id]
        team_user_ids = [u['id'] for u in team_users]
        
        team_leads = [l for l in LEADS if l.get('assigned_user_id') in team_user_ids]
        practices_signed_up = len([l for l in team_leads if l.get('status') == 'signed_up'])
        active_leads = len([l for l in team_leads if l.get('status') in ['new', 'contacted', 'qualified']])
        conversion_rate = round((practices_signed_up / len(team_leads)) * 100, 1) if team_leads else 0
        
        return {
            "total_leads": len(team_leads),
            "practices_signed_up": practices_signed_up,
            "active_leads": active_leads,
            "conversion_rate": conversion_rate,
            "team_size": len(team_users)
        }
    
    else:  # admin
        practices_signed_up = len([l for l in LEADS if l.get('status') == 'signed_up'])
        active_leads = len([l for l in LEADS if l.get('status') in ['new', 'contacted', 'qualified']])
        conversion_rate = round((practices_signed_up / total_leads) * 100, 1) if total_leads else 0
        
        return {
            "total_leads": total_leads,
            "practices_signed_up": practices_signed_up,
            "active_leads": active_leads,
            "conversion_rate": conversion_rate
        }

def assign_leads_to_new_agent(agent_id, count=20):
    """Assign unassigned leads to new agent"""
    unassigned_leads = [l for l in LEADS if not l.get('assigned_user_id') or l.get('assigned_user_id') == 0]
    assigned_count = 0
    
    for lead in unassigned_leads[:count]:
        lead['assigned_user_id'] = agent_id
        lead['updated_at'] = datetime.utcnow().isoformat()
        assigned_count += 1
    
    return assigned_count

def lambda_handler(event, context):
    """AWS Lambda handler for VantagePoint CRM with DynamoDB user persistence"""
    global NEXT_LEAD_ID, LEADS
    
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
        print(f"🔥 VantagePoint {method} {path} - {len(LEADS)} leads, {user_count} users (DynamoDB)")
        
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
            
            return get_user(payload.get("username"))  # ✅ FIXED: DynamoDB lookup
        
        # Handle preflight OPTIONS requests
        if method == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight successful'})
        
        # Health check
        if path == '/health':
            return create_response(200, {
                'status': 'healthy',
                'service': 'VantagePoint CRM API',
                'leads_count': len(LEADS),
                'users_count': len(get_all_users()),  # ✅ FIXED: DynamoDB count
                'version': '2.0.0',
                'user_storage': 'DynamoDB',  # ✅ NEW: Shows persistent storage
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
        
        # Get current user info endpoint (for token validation)
        if path == '/api/v1/auth/me' and method == 'GET':
            # Extract user from token
            auth_header = headers.get("authorization", headers.get("Authorization", ""))
            if not auth_header.startswith("Bearer "):
                return create_response(401, {"detail": "Authentication required"})
            
            token = auth_header.replace("Bearer ", "")
            payload = decode_jwt_token(token)
            if not payload:
                return create_response(401, {"detail": "Invalid token"})
            
            # Get user from DynamoDB
            user = get_user(payload.get("username"))
            if not user:
                return create_response(401, {"detail": "User not found"})
            
            return create_response(200, {
                "username": user['username'],
                "email": user['email'],
                "role": user['role'],
                "full_name": user.get('full_name', user['username']),
                "id": user['id'],
                "is_active": user.get('is_active', True),
                "created_at": user.get('created_at', '')
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
            
            # ✅ FIXED: Store in DynamoDB instead of memory
            if not create_user_in_db(username, new_user):
                return create_response(500, {"detail": "Failed to create user in database"})
            
            # If new user is an agent, assign 20 leads
            assigned_count = 0
            if role == 'agent':
                assigned_count = assign_leads_to_new_agent(new_user["id"], 20)
                print(f"✅ Assigned {assigned_count} leads to new agent {username}")
            
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
                "storage": "DynamoDB"  # ✅ NEW: Confirms persistent storage
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
                "leads": LEADS,
                "total_leads": len(LEADS),
                "message": "Leads retrieved successfully"
            })
        
        # Leads endpoint - POST create new lead
        if path == '/api/v1/leads' and method == 'POST':
            # Extract user from token for permissions
            auth_header = headers.get("authorization", headers.get("Authorization", ""))
            if not auth_header.startswith("Bearer "):
                return create_response(401, {"detail": "Authentication required"})
            
            token = auth_header.replace("Bearer ", "")
            payload = decode_jwt_token(token)
            if not payload:
                return create_response(401, {"detail": "Invalid token"})
            
            current_user = get_user(payload.get("username"))
            if not current_user:
                return create_response(401, {"detail": "User not found"})
            
            # Parse request data
            try:
                lead_data = json.loads(event.get('body', '{}'))
            except:
                return create_response(400, {"detail": "Invalid JSON data"})
            
            # Generate new lead ID
            global NEXT_LEAD_ID
            new_lead_id = NEXT_LEAD_ID
            NEXT_LEAD_ID += 1
            
            # Auto-assign if not provided
            assigned_user_id = lead_data.get('assigned_user_id')
            if not assigned_user_id:
                if current_user['role'] == 'agent':
                    assigned_user_id = current_user['id']
                elif current_user['role'] == 'manager':
                    # Assign to self or first agent under manager
                    agent_users = [u for u in get_all_users() if u['role'] == 'agent' and u.get('manager_id') == current_user['id']]
                    assigned_user_id = agent_users[0]['id'] if agent_users else current_user['id']
                elif current_user['role'] == 'admin':
                    # Assign to first available agent
                    agent_users = [u for u in get_all_users() if u['role'] == 'agent']
                    assigned_user_id = agent_users[0]['id'] if agent_users else current_user['id']
            
            # Create new lead
            new_lead = {
                "id": new_lead_id,
                "practice_name": lead_data.get('practice_name', 'Unknown Practice'),
                "owner_name": lead_data.get('owner_name', 'Unknown Doctor'),
                "practice_phone": lead_data.get('practice_phone', ''),
                "email": lead_data.get('email', ''),
                "address": lead_data.get('address', ''),
                "city": lead_data.get('city', ''),
                "state": lead_data.get('state', ''),
                "zip_code": lead_data.get('zip_code', ''),
                "specialty": lead_data.get('specialty', ''),
                "score": int(lead_data.get('score', 75)),
                "priority": lead_data.get('priority', 'medium'),
                "status": lead_data.get('status', 'new'),
                "assigned_user_id": assigned_user_id,
                "docs_sent": False,
                "ptan": lead_data.get('ptan', ''),
                "ein_tin": lead_data.get('ein_tin', ''),
                "npi": lead_data.get('npi', ''),
                "source": lead_data.get('source', 'api'),
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "created_by": current_user['username']
            }
            
            # Add to leads list
            LEADS.append(new_lead)
            
            print(f"✅ Lead created: {new_lead['practice_name']} (ID: {new_lead_id}) → User {assigned_user_id}")
            
            return create_response(201, {
                "lead": new_lead,
                "message": "Lead created successfully"
            })
        
        # Bulk upload endpoint - POST create multiple leads
        if path == '/api/v1/leads/bulk' and method == 'POST':
            # Extract user from token for permissions
            auth_header = headers.get("authorization", headers.get("Authorization", ""))
            if not auth_header.startswith("Bearer "):
                return create_response(401, {"detail": "Authentication required"})
            
            token = auth_header.replace("Bearer ", "")
            payload = decode_jwt_token(token)
            if not payload:
                return create_response(401, {"detail": "Invalid token"})
            
            current_user = get_user(payload.get("username"))
            if not current_user:
                return create_response(401, {"detail": "User not found"})
            
            # Only admins can bulk upload
            if current_user['role'] != 'admin':
                return create_response(403, {"detail": "Only admins can bulk upload leads"})
            
            # Parse request data
            try:
                request_data = json.loads(event.get('body', '{}'))
                leads_data = request_data.get('leads', [])
            except:
                return create_response(400, {"detail": "Invalid JSON data"})
            
            if not leads_data:
                return create_response(400, {"detail": "No leads data provided"})
            
            # Process leads in batch
            global NEXT_LEAD_ID
            created_leads = []
            failed_leads = []
            
            for lead_data in leads_data:
                try:
                    # Generate new lead ID
                    new_lead_id = NEXT_LEAD_ID
                    NEXT_LEAD_ID += 1
                    
                    # Create new lead
                    new_lead = {
                        "id": new_lead_id,
                        "practice_name": lead_data.get('practice_name', 'Unknown Practice'),
                        "owner_name": lead_data.get('owner_name', 'Unknown Doctor'),
                        "practice_phone": lead_data.get('practice_phone', ''),
                        "email": lead_data.get('email', ''),
                        "address": lead_data.get('address', ''),
                        "city": lead_data.get('city', ''),
                        "state": lead_data.get('state', ''),
                        "zip_code": lead_data.get('zip_code', ''),
                        "specialty": lead_data.get('specialty', ''),
                        "score": int(lead_data.get('score', 75)),
                        "priority": lead_data.get('priority', 'medium'),
                        "status": lead_data.get('status', 'new'),
                        "assigned_user_id": lead_data.get('assigned_user_id'),  # Will be distributed later
                        "docs_sent": False,
                        "ptan": lead_data.get('ptan', ''),
                        "ein_tin": lead_data.get('ein_tin', ''),
                        "npi": lead_data.get('npi', ''),
                        "source": lead_data.get('source', 'bulk_upload'),
                        "created_at": datetime.utcnow().isoformat() + "Z",
                        "updated_at": datetime.utcnow().isoformat() + "Z",
                        "created_by": current_user['username']
                    }
                    
                    # Add to leads list
                    LEADS.append(new_lead)
                    created_leads.append(new_lead)
                    
                except Exception as e:
                    failed_leads.append({
                        "data": lead_data,
                        "error": str(e)
                    })
            
            print(f"✅ Bulk upload: {len(created_leads)} created, {len(failed_leads)} failed")
            
            return create_response(201, {
                "message": f"Bulk upload completed: {len(created_leads)} leads created, {len(failed_leads)} failed",
                "created_count": len(created_leads),
                "failed_count": len(failed_leads),
                "total_leads": len(LEADS),
                "failed_leads": failed_leads[:5]  # Show first 5 failures for debugging
            })
        
        # Summary endpoint - Dashboard statistics
        if path == '/api/v1/summary' and method == 'GET':
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
                "high_priority": priority_counts.get("high", 0),
                "users_count": len(get_all_users()),
                "message": "Summary statistics retrieved successfully"
            })
        
        # Default response
        return create_response(404, {"detail": "Endpoint not found"})
        
    except Exception as e:
        print(f"❌ Lambda error: {e}")
        return {
            'statusCode': 500,
            'headers': response_headers,
            'body': json.dumps({"detail": f"Internal server error: {str(e)}"})
        }
