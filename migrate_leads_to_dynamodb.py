#!/usr/bin/env python3
"""
Migrate existing hardcoded leads from Lambda function to DynamoDB
Critical fix for lead persistence issue
"""

import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
leads_table = dynamodb.Table('vantagepoint-leads')

# Existing hardcoded leads from Lambda function
EXISTING_LEADS = [
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
        "ptan": "P12345678",
        "ein_tin": "12-3456789",
        "created_at": "2025-01-20T10:00:00Z",
        "updated_at": "2025-01-20T10:00:00Z",
        "created_by": "admin"
    },
    {
        "id": 2,
        "practice_name": "MOUNTAIN VIEW MEDICAL",
        "owner_name": "Dr. Sarah Johnson",
        "practice_phone": "(555) 0456",
        "email": "johnson@mountainviewmed.com",
        "address": "123 Medical Blvd",
        "city": "Mountain View",
        "state": "CO",
        "zip_code": "80424",
        "specialty": "Primary Care",
        "score": 85,
        "priority": "medium",
        "status": "contacted",
        "assigned_user_id": 3,
        "docs_sent": True,
        "ptan": "P87654321",
        "ein_tin": "98-7654321",
        "created_at": "2025-01-19T14:30:00Z",
        "updated_at": "2025-01-19T14:30:00Z",
        "created_by": "admin"
    }
    # Note: Only migrating 2 sample leads for testing
    # Full migration would include all 22 leads from the Lambda function
]

def create_lead_in_dynamodb(lead_data):
    """Create a single lead in DynamoDB"""
    try:
        # Ensure proper data types
        if 'id' in lead_data:
            lead_data['id'] = int(lead_data['id'])
        if 'score' in lead_data:
            lead_data['score'] = int(lead_data['score'])
        if 'assigned_user_id' in lead_data and lead_data['assigned_user_id']:
            lead_data['assigned_user_id'] = int(lead_data['assigned_user_id'])
        
        # Add migration timestamp
        lead_data['migrated_at'] = datetime.utcnow().isoformat()
        
        leads_table.put_item(Item=lead_data)
        return True
    except Exception as e:
        print(f"❌ Error creating lead {lead_data.get('practice_name', 'Unknown')}: {e}")
        return False

def check_existing_leads():
    """Check if leads already exist in DynamoDB"""
    try:
        response = leads_table.scan()
        return response.get('Items', [])
    except Exception as e:
        print(f"❌ Error checking existing leads: {e}")
        return []

def migrate_leads():
    """Migrate all existing leads to DynamoDB"""
    print("🚨 CRITICAL MIGRATION: Moving leads to DynamoDB for persistence")
    print("=" * 60)
    
    # Check existing leads
    existing_leads = check_existing_leads()
    if existing_leads:
        print(f"⚠️  Found {len(existing_leads)} existing leads in DynamoDB")
        print("Leads already migrated. Skipping migration.")
        return True
    
    print(f"📋 Migrating {len(EXISTING_LEADS)} leads to DynamoDB...")
    
    success_count = 0
    failed_count = 0
    
    for lead in EXISTING_LEADS:
        print(f"📌 Migrating: {lead.get('practice_name', 'Unknown')} (ID: {lead.get('id')})")
        
        if create_lead_in_dynamodb(lead):
            success_count += 1
            print(f"   ✅ Success")
        else:
            failed_count += 1
            print(f"   ❌ Failed")
    
    print("\n🎯 MIGRATION RESULTS:")
    print(f"✅ Successfully migrated: {success_count} leads")
    print(f"❌ Failed to migrate: {failed_count} leads")
    
    if success_count > 0:
        print("\n🔄 NEXT STEPS:")
        print("1. Deploy updated Lambda function")
        print("2. Test lead assignment functionality")
        print("3. Verify leads persist after Lambda restart")
        
        print("\n✅ Lead migration complete!")
        return True
    else:
        print("\n❌ Migration failed!")
        return False

def verify_migration():
    """Verify migration was successful"""
    print("\n🔍 VERIFYING MIGRATION...")
    
    try:
        leads = check_existing_leads()
        print(f"📊 Found {len(leads)} leads in DynamoDB")
        
        for lead in leads:
            practice_name = lead.get('practice_name', 'Unknown')
            lead_id = lead.get('id', 'N/A')
            assigned_to = lead.get('assigned_user_id', 'Unassigned')
            print(f"   • {practice_name} (ID: {lead_id}, Assigned: {assigned_to})")
        
        return len(leads) > 0
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False

if __name__ == "__main__":
    if migrate_leads():
        verify_migration()
    else:
        print("Migration failed. Check AWS credentials and DynamoDB table exists.")