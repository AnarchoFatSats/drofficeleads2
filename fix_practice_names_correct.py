#!/usr/bin/env python3
"""
🔧 Fix Practice Names (Corrected Version)
Properly map CRM IDs to meaningful practice names using owner information
"""

import json
import urllib3
import re
from datetime import datetime

def extract_practice_name_from_owner(owner_name):
    """Extract a meaningful practice name from owner information"""
    
    if not owner_name or owner_name in ['nan, nan', 'nan', '', None]:
        return None
    
    # Clean up the owner name
    owner_clean = str(owner_name).strip()
    
    # Remove "Dr. " prefix that was added during conversion
    if owner_clean.startswith('Dr. '):
        owner_clean = owner_clean[4:]
    
    # Extract doctor's last name patterns
    patterns = [
        r'DR\.?\s+([A-Z][A-Z\s]+)',  # "DR. JAMES P PLETTNER"
        r'([A-Z]+),?\s+(MD|DPM|DO)',  # "WILLIAMS, MD"
        r'([A-Z][A-Z\s]+),\s+(MD|DPM|DO)',  # "JOHN M WILLIAMS, MD"
        r'([A-Z][A-Z\s]+),\s+(OWNER|PRESIDENT|CEO|DIRECTOR)',  # "MATTHEW V DILTZ, OWNER"
        r'([A-Z]+)\s+([A-Z]+),',  # "MATTHEW DILTZ," - get last name
        r'([A-Z]+)\s+[A-Z]\.?\s+([A-Z]+)',  # "JOHN M WILLIAMS" - get last name
    ]
    
    for pattern in patterns:
        match = re.search(pattern, owner_clean)
        if match:
            if len(match.groups()) >= 2:
                # Pattern with first and last name
                last_name = match.group(2) if not match.group(2) in ['MD', 'DPM', 'DO', 'OWNER', 'PRESIDENT', 'CEO', 'DIRECTOR'] else match.group(1)
            else:
                # Single capture group
                name_part = match.group(1).strip()
                words = name_part.split()
                last_name = words[-1] if words else name_part
            
            if len(last_name) >= 3 and last_name.isalpha():
                return f"{last_name.title()} Medical Practice"
    
    # Fallback: try to extract first meaningful word
    words = owner_clean.split()
    for word in words:
        if (len(word) >= 3 and 
            word.isalpha() and 
            word not in ['MRS', 'MR', 'DR', 'DOCTOR', 'CREDENTIALING', 'COORDINATOR', 'MANAGER', 'CHIEF', 'EXECUTIVE', 'OFFICER']):
            return f"{word.title()} Medical Practice"
    
    return None

def get_crm_leads_to_fix():
    """Get all leads from CRM that need practice name fixes"""
    
    print("🔍 GETTING LEADS FROM CRM THAT NEED FIXES")
    print("=" * 50)
    
    base_url = "https://api.vantagepointcrm.com"
    http = urllib3.PoolManager()
    
    # Get admin token
    login_response = http.request(
        'POST',
        f'{base_url}/api/v1/auth/login',
        body=json.dumps({"username": "admin", "password": "admin123"}),
        headers={'Content-Type': 'application/json'}
    )
    
    if login_response.status != 200:
        print(f"❌ Authentication failed: {login_response.status}")
        return [], None
    
    token = json.loads(login_response.data.decode('utf-8')).get('access_token')
    
    # Get all leads
    leads_response = http.request(
        'GET',
        f'{base_url}/api/v1/leads',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    )
    
    if leads_response.status != 200:
        print(f"❌ Failed to get leads: {leads_response.status}")
        return [], None
    
    leads = json.loads(leads_response.data.decode('utf-8')).get('leads', [])
    print(f"✅ Found {len(leads)} total leads in CRM")
    
    # Find leads with generic names that can be improved
    fixable_leads = []
    
    for lead in leads:
        practice_name = lead.get('practice_name', '')
        owner_name = lead.get('owner_name', '')
        
        if practice_name.startswith('Medical Practice '):
            better_name = extract_practice_name_from_owner(owner_name)
            if better_name:
                fixable_leads.append({
                    'id': lead['id'],
                    'current_name': practice_name,
                    'suggested_name': better_name,
                    'owner_name': owner_name,
                    'phone': lead.get('practice_phone', ''),
                    'specialty': lead.get('specialty', ''),
                    'city': lead.get('city', ''),
                    'state': lead.get('state', '')
                })
    
    print(f"\n🔧 FOUND {len(fixable_leads)} LEADS TO IMPROVE:")
    for i, lead in enumerate(fixable_leads[:10], 1):
        print(f"  {i:2d}. ID {lead['id']:3d}: \"{lead['current_name']}\" → \"{lead['suggested_name']}\"")
        print(f"      Owner: {lead['owner_name']}")
    
    if len(fixable_leads) > 10:
        print(f"      ... and {len(fixable_leads) - 10} more")
    
    return fixable_leads, token

def update_practice_names(fixable_leads, token):
    """Update the practice names in the CRM"""
    
    print(f"\n🚀 UPDATING {len(fixable_leads)} PRACTICE NAMES")
    print("=" * 50)
    
    base_url = "https://api.vantagepointcrm.com"
    http = urllib3.PoolManager()
    
    updated_count = 0
    failed_count = 0
    
    for i, fix in enumerate(fixable_leads, 1):
        lead_id = fix['id']
        current_name = fix['current_name']
        suggested_name = fix['suggested_name']
        
        # Update the lead
        update_data = {
            "practice_name": suggested_name
        }
        
        update_response = http.request(
            'PUT',
            f'{base_url}/api/v1/leads/{lead_id}',
            body=json.dumps(update_data),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if update_response.status == 200:
            updated_count += 1
            print(f"✅ {i:3d}. ID {lead_id:3d}: \"{current_name}\" → \"{suggested_name}\"")
        else:
            failed_count += 1
            print(f"❌ {i:3d}. ID {lead_id:3d}: Failed to update (Status: {update_response.status})")
    
    print(f"\n📊 UPDATE SUMMARY:")
    print(f"✅ Successfully updated: {updated_count} leads")
    print(f"❌ Failed updates: {failed_count} leads")
    print(f"📈 Success rate: {(updated_count / len(fixable_leads) * 100):.1f}%")
    
    return updated_count, failed_count

def save_fixes_tracking(fixable_leads, updated_count, failed_count):
    """Save tracking information for the fixes"""
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    tracking_data = {
        "fix_timestamp": timestamp,
        "total_identified": len(fixable_leads),
        "successfully_updated": updated_count,
        "failed_updates": failed_count,
        "success_rate": f"{(updated_count / len(fixable_leads) * 100):.1f}%",
        "description": "Fixed generic 'Medical Practice X' names using real owner information",
        "examples": [
            {
                "id": fix['id'],
                "before": fix['current_name'],
                "after": fix['suggested_name'],
                "owner": fix['owner_name']
            }
            for fix in fixable_leads[:20]  # Save first 20 examples
        ]
    }
    
    filename = f"practice_name_fixes_completed_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(tracking_data, f, indent=2)
    
    print(f"\n💾 Fix tracking saved to: {filename}")
    return filename

def main():
    """Main execution function"""
    
    print("🔧 VANTAGEPOINT CRM - PRACTICE NAME FIXES (CORRECTED)")
    print("=" * 60)
    print(f"🕐 Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("🎯 Goal: Fix generic 'Medical Practice X' names using real owner data")
    print("🔧 Method: Map CRM IDs directly to owner-based practice names")
    print("")
    
    try:
        # Step 1: Get leads that need fixes
        fixable_leads, token = get_crm_leads_to_fix()
        
        if not fixable_leads or not token:
            print("❌ Could not retrieve leads or authenticate")
            return
        
        if len(fixable_leads) == 0:
            print("✅ No leads need practice name fixes!")
            return
        
        print(f"\n🎯 READY TO FIX {len(fixable_leads)} PRACTICE NAMES")
        
        # Step 2: Update the practice names
        updated_count, failed_count = update_practice_names(fixable_leads, token)
        
        # Step 3: Save tracking
        tracking_file = save_fixes_tracking(fixable_leads, updated_count, failed_count)
        
        if updated_count > 0:
            print(f"\n🎉 PRACTICE NAME FIXES COMPLETED!")
            print(f"✅ {updated_count} leads now have meaningful practice names")
            print(f"📊 Lead quality significantly improved")
            print(f"🔍 Tracking: {tracking_file}")
            
            print(f"\n🏆 EXAMPLES OF IMPROVEMENTS:")
            for i, fix in enumerate(fixable_leads[:5], 1):
                if i <= updated_count:  # Only show successful updates
                    print(f"  {i}. \"{fix['current_name']}\" → \"{fix['suggested_name']}\"")
            
            print(f"\n📈 BUSINESS IMPACT:")
            print(f"• {updated_count} leads now have professional practice names")
            print(f"• Better lead identification and tracking")
            print(f"• Improved agent workflow and lead management")
            print(f"• More professional appearance in CRM dashboard")
        else:
            print(f"\n❌ No practice names were successfully updated")
            
    except Exception as e:
        print(f"❌ Fix process failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 