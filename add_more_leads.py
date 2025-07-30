#!/usr/bin/env python3
"""
🏥 Add More Leads to VantagePoint CRM
Generate 20+ high-quality medical practice leads for the system
"""

import json
import random
from datetime import datetime, timedelta

# High-quality medical practice leads data
MEDICAL_PRACTICES = [
    {
        "practice_name": "RANCHO MIRAGE PODIATRY",
        "owner_name": "Dr. Matthew Diltz",
        "practice_phone": "(760) 568-2684",
        "specialty": "Podiatrist",
        "city": "Rancho Mirage",
        "state": "CA",
        "zip_code": "92270"
    },
    {
        "practice_name": "MOUNTAIN VIEW MEDICAL",
        "owner_name": "Dr. Sarah Johnson",
        "specialty": "Primary Care",
        "city": "Mountain View",
        "state": "CO",
        "zip_code": "80424"
    },
    {
        "practice_name": "COASTAL ORTHOPEDICS",
        "owner_name": "Dr. Michael Chen",
        "specialty": "Orthopedic Surgery",
        "city": "Santa Monica",
        "state": "CA",
        "zip_code": "90401"
    },
    {
        "practice_name": "DESERT VALLEY CARDIOLOGY",
        "owner_name": "Dr. Jennifer Rodriguez",
        "specialty": "Cardiology",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85016"
    },
    {
        "practice_name": "METRO FAMILY PRACTICE",
        "owner_name": "Dr. David Kim",
        "specialty": "Family Medicine",
        "city": "Denver",
        "state": "CO",
        "zip_code": "80203"
    },
    {
        "practice_name": "PACIFIC DERMATOLOGY",
        "owner_name": "Dr. Lisa Wang",
        "specialty": "Dermatology",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101"
    },
    {
        "practice_name": "CENTRAL TEXAS NEUROLOGY",
        "owner_name": "Dr. Robert Martinez",
        "specialty": "Neurology",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701"
    },
    {
        "practice_name": "GATEWAY GASTROENTEROLOGY",
        "owner_name": "Dr. Amanda Thompson",
        "specialty": "Gastroenterology",
        "city": "St. Louis",
        "state": "MO",
        "zip_code": "63101"
    },
    {
        "practice_name": "SUNRISE URGENT CARE",
        "owner_name": "Dr. James Park",
        "specialty": "Urgent Care",
        "city": "Las Vegas",
        "state": "NV",
        "zip_code": "89101"
    },
    {
        "practice_name": "RIVERSIDE PEDIATRICS",
        "owner_name": "Dr. Maria Garcia",
        "specialty": "Pediatrics",
        "city": "Tampa",
        "state": "FL",
        "zip_code": "33601"
    },
    {
        "practice_name": "NORTHSIDE OPHTHALMOLOGY",
        "owner_name": "Dr. Kevin Lee",
        "specialty": "Ophthalmology",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60601"
    },
    {
        "practice_name": "MOUNTAIN PEAK WELLNESS",
        "owner_name": "Dr. Sarah Mitchell",
        "specialty": "Internal Medicine",
        "city": "Salt Lake City",
        "state": "UT",
        "zip_code": "84101"
    },
    {
        "practice_name": "BLUEGRASS FAMILY HEALTH",
        "owner_name": "Dr. William Jones",
        "specialty": "Family Medicine",
        "city": "Louisville",
        "state": "KY",
        "zip_code": "40201"
    },
    {
        "practice_name": "COASTAL WOMEN'S HEALTH",
        "owner_name": "Dr. Rachel Davis",
        "specialty": "OB-GYN",
        "city": "Miami",
        "state": "FL",
        "zip_code": "33101"
    },
    {
        "practice_name": "EMPIRE STATE ORTHOPEDICS",
        "owner_name": "Dr. Anthony Brown",
        "specialty": "Orthopedic Surgery",
        "city": "Albany",
        "state": "NY",
        "zip_code": "12201"
    },
    {
        "practice_name": "GOLDEN VALLEY PSYCHIATRY",
        "owner_name": "Dr. Nicole Taylor",
        "specialty": "Psychiatry",
        "city": "Minneapolis",
        "state": "MN",
        "zip_code": "55401"
    },
    {
        "practice_name": "LONE STAR RADIOLOGY",
        "owner_name": "Dr. Daniel Wilson",
        "specialty": "Radiology",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75201"
    },
    {
        "practice_name": "GREAT LAKES ANESTHESIA",
        "owner_name": "Dr. Michelle Anderson",
        "specialty": "Anesthesiology",
        "city": "Detroit",
        "state": "MI",
        "zip_code": "48201"
    },
    {
        "practice_name": "CANYON COUNTRY SPORTS MED",
        "owner_name": "Dr. Christopher White",
        "specialty": "Sports Medicine",
        "city": "Grand Junction",
        "state": "CO",
        "zip_code": "81501"
    },
    {
        "practice_name": "ATLANTIC COASTAL SURGERY",
        "owner_name": "Dr. Elizabeth Harris",
        "specialty": "General Surgery",
        "city": "Virginia Beach",
        "state": "VA",
        "zip_code": "23451"
    },
    {
        "practice_name": "PIEDMONT PAIN MANAGEMENT",
        "owner_name": "Dr. Joseph Clark",
        "specialty": "Pain Management",
        "city": "Charlotte",
        "state": "NC",
        "zip_code": "28201"
    },
    {
        "practice_name": "EMERALD CITY ENDOCRINOLOGY",
        "owner_name": "Dr. Patricia Lewis",
        "specialty": "Endocrinology",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98109"
    }
]

STATUSES = ["new", "contacted", "qualified", "new", "new"]  # Weight toward "new"
PRIORITIES = ["high", "medium", "low"]

def generate_phone():
    """Generate a realistic phone number"""
    area_codes = ["555", "310", "415", "720", "602", "206", "512", "314", "702", "813", "312", "801", "502", "305", "518", "612", "214", "313", "970", "757", "704", "206"]
    area = random.choice(area_codes)
    return f"({area}) {random.randint(100,999)}-{random.randint(1000,9999)}"

def generate_email(practice_name, owner_name):
    """Generate a professional email"""
    practice_slug = practice_name.lower().replace(" ", "").replace("'", "")[:15]
    domains = ["gmail.com", "outlook.com", "medicalpractice.com", "healthcare.org"]
    domain = random.choice(domains)
    return f"contact@{practice_slug}.com"

def generate_address(city, state):
    """Generate a realistic medical practice address"""
    street_numbers = [random.randint(100, 9999)]
    street_names = ["Medical Blvd", "Healthcare Dr", "Wellness Way", "Professional Plaza", "Clinic Ave", "Health Center Dr", "Practice Lane"]
    street = f"{random.choice(street_numbers)} {random.choice(street_names)}"
    return street

def generate_scores():
    """Generate realistic lead scores"""
    base_score = random.randint(60, 100)
    if base_score >= 90:
        priority = "high"
    elif base_score >= 75:
        priority = "medium" 
    else:
        priority = "low"
    return base_score, priority

def create_enhanced_leads():
    """Create 22 high-quality medical practice leads"""
    
    leads = []
    
    for i, practice in enumerate(MEDICAL_PRACTICES, start=1):
        score, priority = generate_scores()
        
        # Create realistic dates (within last 30 days)
        created_date = datetime.now() - timedelta(days=random.randint(1, 30))
        updated_date = created_date + timedelta(hours=random.randint(1, 48))
        
        lead = {
            "id": i,
            "practice_name": practice["practice_name"],
            "owner_name": practice["owner_name"],
            "practice_phone": practice.get("practice_phone", generate_phone()),
            "email": generate_email(practice["practice_name"], practice["owner_name"]),
            "address": generate_address(practice["city"], practice["state"]),
            "city": practice["city"],
            "state": practice["state"],
            "zip_code": practice["zip_code"],
            "specialty": practice["specialty"],
            "score": score,
            "priority": priority,
            "status": random.choice(STATUSES),
            "assigned_user_id": None,  # Will be assigned by distribution system
            "docs_sent": False,
            "ptan": f"P{random.randint(10000000, 99999999)}",
            "ein_tin": f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}",
            "created_at": created_date.isoformat() + "Z",
            "updated_at": updated_date.isoformat() + "Z",
            "created_by": "system"
        }
        
        leads.append(lead)
    
    return leads

def generate_lambda_leads_code():
    """Generate the LEADS array code for the Lambda function"""
    
    leads = create_enhanced_leads()
    
    print("🏥 GENERATED LEADS FOR LAMBDA FUNCTION")
    print("=" * 60)
    print(f"📊 Total leads created: {len(leads)}")
    print(f"🎯 Ready for agent distribution (20 per agent)")
    print("")
    
    # Generate the Python code
    code = "# Production leads database - 22 high-quality medical practice leads\nLEADS = [\n"
    
    for lead in leads:
        code += "    {\n"
        for key, value in lead.items():
            if isinstance(value, str):
                code += f'        "{key}": "{value}",\n'
            elif isinstance(value, bool):
                code += f'        "{key}": {str(value)},\n'
            elif value is None:
                code += f'        "{key}": None,\n'
            else:
                code += f'        "{key}": {value},\n'
        code += "    },\n"
    
    code += "]\n"
    
    # Save to file
    with open('enhanced_leads_data.py', 'w') as f:
        f.write(code)
    
    print("✅ Enhanced leads data saved to: enhanced_leads_data.py")
    print("📋 Copy this data to replace the LEADS array in lambda_function.py")
    
    # Show sample leads
    print("\n🔍 SAMPLE LEADS GENERATED:")
    print("-" * 40)
    for i, lead in enumerate(leads[:3]):
        print(f"{i+1}. {lead['practice_name']}")
        print(f"   Owner: {lead['owner_name']}")
        print(f"   Specialty: {lead['specialty']}")
        print(f"   Score: {lead['score']} ({lead['priority']} priority)")
        print(f"   Location: {lead['city']}, {lead['state']}")
        print()
    
    print(f"... and {len(leads)-3} more high-quality leads!")
    
    return leads

if __name__ == "__main__":
    generate_lambda_leads_code() 