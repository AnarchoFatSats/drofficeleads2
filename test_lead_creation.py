#!/usr/bin/env python3
"""
Test script to debug lead creation issue
"""

import sys
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import our CRM models
sys.path.append('.')
from crm_main import User, Lead, LeadStatus, Base

# Production database configuration
DATABASE_URL = "postgresql://crmuser:CuraGenesis2024%21SecurePassword@cura-genesis-crm-db.c6ds4c4qok1n.us-east-1.rds.amazonaws.com:5432/cura_genesis_crm"

def test_single_lead_creation():
    """Test creating a single lead to debug the issue"""
    print("🔗 Connecting to database...")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Load one lead from our data
    with open('web/data/hot_leads.json', 'r') as f:
        leads = json.load(f)
    
    test_lead = leads[0]  # Use the first lead
    print(f"Testing with lead: {test_lead['practice_name']}")
    
    # Convert boolean properly
    sole_prop_value = test_lead.get('is_sole_proprietor', False)
    if isinstance(sole_prop_value, str):
        if sole_prop_value.lower() in ['true', '1', 'yes', 'y']:
            is_sole_proprietor = True
        elif sole_prop_value.lower() in ['false', '0', 'no', 'n']:
            is_sole_proprietor = False  
        else:
            is_sole_proprietor = False  # Default for 'nan' or other values
    else:
        is_sole_proprietor = bool(sole_prop_value)
    
    print(f"Converted is_sole_proprietor: {is_sole_proprietor} (type: {type(is_sole_proprietor)})")
    
    # Create lead with minimal required fields first
    try:
        new_lead = Lead(
            practice_name=test_lead.get('practice_name', 'Test Practice'),
            owner_name=test_lead.get('owner_name', ''),
            practice_phone=test_lead.get('practice_phone', ''),
            specialties=test_lead.get('specialties', ''),
            city=test_lead.get('city', ''),
            state=test_lead.get('state', ''),
            score=test_lead.get('score', 0),
            priority='A+',
            category=test_lead.get('category', 'Test'),
            status=LeadStatus.NEW,
            source='nppes_extraction',
            is_sole_proprietor=is_sole_proprietor,
            # Let SQLAlchemy handle the default for previous_agents array
            created_at=datetime.utcnow()
        )
        
        print("✅ Lead object created successfully")
        
        # Try to add and commit
        db.add(new_lead)
        print("✅ Lead added to session")
        
        db.commit()
        print("✅ Lead committed to database successfully!")
        print(f"Lead ID: {new_lead.id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_single_lead_creation() 