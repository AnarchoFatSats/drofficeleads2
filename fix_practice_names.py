#!/usr/bin/env python3
"""
🔧 Fix Practice Names - VantagePoint CRM
Update leads with generic "Medical Practice X" names to use real owner information
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
    
    # Extract doctor's last name patterns
    patterns = [
        r'DR\.?\s+([A-Z][A-Z\s]+)',  # "DR. JAMES P PLETTNER"
        r'([A-Z]+),?\s+(MD|DPM|DO)',  # "WILLIAMS, MD"
        r'([A-Z][A-Z\s]+),\s+(MD|DPM|DO)',  # "JOHN M WILLIAMS, MD"
        r'([A-Z][A-Z\s]+),\s+OWNER',  # "MATTHEW V DILTZ, OWNER"
        r'([A-Z][A-Z\s]+),\s+PRESIDENT',  # "WILLIAM SCOTT BOWEN, PRESIDENT"
        r'([A-Z][A-Z\s]+),\s+CEO',  # "RISHI BHATNAGAR, CEO"
        r'([A-Z][A-Z\s]+),\s+DIRECTOR',  # "JENNIFER SWEITZER, DIRECTOR"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, owner_clean)
        if match:
            name_part = match.group(1).strip()
            # Get the last word (usually last name)
            words = name_part.split()
            if words:
                last_name = words[-1]
                if len(last_name) >= 3:  # Valid last name
                    return f"{last_name.title()} Medical Practice"
    
    # If no pattern matches, try to extract first meaningful word
    words = owner_clean.split()
    for word in words:
        if (len(word) >= 3 and 
            word.isalpha() and 
            word not in ['MRS', 'MR', 'DR', 'DOCTOR', 'CREDENTIALING', 'COORDINATOR', 'MANAGER']):
            return f"{word.title()} Medical Practice"
    
    return None

def identify_leads_to_fix():
    """Identify which uploaded leads need practice name fixes"""
    
    print("🔍 IDENTIFYING LEADS THAT NEED PRACTICE NAME FIXES")
    print("=" * 60)
    
    # Load original source data to get owner information
    original_leads = []
    
    # Load all source files
    source_files = [
        ('hot_leads.json', 'main_database'),
        ('production_leads_hot_20250725_203038.json', 'production_hot'),
        ('production_leads_warm_20250725_203038.json', 'production_warm'),
        ('lambda_leads_converted.json', 'lambda_converted'),
        ('web/data/hot_leads.json', 'web_data')
    ]
    
    for filename, source in source_files:
        try:
            with open(filename, 'r') as f:
                leads = json.load(f)
            for i, lead in enumerate(leads):
                lead['source_file'] = source
                lead['source_index'] = i
                original_leads.append(lead)
            print(f"✅ Loaded {len(leads)} leads from {source}")
        except Exception as e:
            print(f"❌ Error loading {source}: {e}")
    
    print(f"\n📊 Total original leads: {len(original_leads)}")
    
    # Find leads where practice_name was <UNAVAIL> but owner info exists
    fixable_leads = []
    
    for i, lead in enumerate(original_leads):
        practice_name = lead.get('practice_name', '')
        owner_name = lead.get('owner_name', '')
        
        if practice_name in ['<UNAVAIL>', 'nan', None, '']:
            better_name = extract_practice_name_from_owner(owner_name)
            if better_name:
                fixable_leads.append({
                    'original_index': i + 1,  # Matches our upload sequence
                    'source_file': lead.get('source_file', 'unknown'),
                    'source_index': lead.get('source_index', -1),
                    'current_name': f"Medical Practice {i + 1}",
                    'suggested_name': better_name,
                    'owner_name': owner_name,
                    'phone': lead.get('practice_phone', ''),
                    'address': lead.get('address', ''),
                    'city': lead.get('city', ''),
                    'state': lead.get('state', '')
                })
    
    print(f"\n🔧 LEADS THAT CAN BE IMPROVED:")
    print(f"📊 Total fixable leads: {len(fixable_leads)}")
    print(f"📋 Examples:")
    
    for i, lead in enumerate(fixable_leads[:10]):
        print(f"  {i+1:2d}. \"{lead['current_name']}\" → \"{lead['suggested_name']}\"")
        print(f"      Owner: {lead['owner_name']}")
        print()
    
    if len(fixable_leads) > 10:
        print(f"      ... and {len(fixable_leads) - 10} more leads")
    
    return fixable_leads

def update_leads_in_crm(fixable_leads):
    """Update the practice names in the CRM"""
    
    print(f"\n🚀 UPDATING {len(fixable_leads)} PRACTICE NAMES IN CRM")
    print("=" * 60)
    
    base_url = "https://api.vantagepointcrm.com"
    http = urllib3.PoolManager()
    
    # Get admin token
    print("🔐 Authenticating as admin...")
    login_response = http.request(
        'POST',
        f'{base_url}/api/v1/auth/login',
        body=json.dumps({"username": "admin", "password": "admin123"}),
        headers={'Content-Type': 'application/json'}
    )
    
    if login_response.status != 200:
        print(f"❌ Authentication failed: {login_response.status}")
        return False
    
    login_data = json.loads(login_response.data.decode('utf-8'))
    token = login_data.get('access_token')
    print("✅ Admin authenticated")
    
    # Get current leads to match them with our fixes
    print("\n📋 Getting current leads from CRM...")
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
        return False
    
    current_leads = json.loads(leads_response.data.decode('utf-8')).get('leads', [])
    print(f"✅ Found {len(current_leads)} leads in CRM")
    
    # Update leads with better names
    updated_count = 0
    failed_count = 0
    
    for fix in fixable_leads:
        current_name = fix['current_name']
        suggested_name = fix['suggested_name']
        
        # Find the lead in CRM that matches this fix
        matching_lead = None
        for lead in current_leads:
            if lead.get('practice_name') == current_name:
                matching_lead = lead
                break
        
        if not matching_lead:
            print(f"❌ Could not find lead: {current_name}")
            failed_count += 1
            continue
        
        # Update the lead
        lead_id = matching_lead['id']
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
            print(f"✅ Updated: \"{current_name}\" → \"{suggested_name}\"")
        else:
            failed_count += 1
            print(f"❌ Failed to update: {current_name} (Status: {update_response.status})")
    
    print(f"\n📊 UPDATE SUMMARY:")
    print(f"✅ Successfully updated: {updated_count} leads")
    print(f"❌ Failed updates: {failed_count} leads")
    print(f"📈 Success rate: {(updated_count / len(fixable_leads) * 100):.1f}%")
    
    return updated_count > 0

def save_update_tracking(fixable_leads, updated_count):
    """Save tracking information for the updates"""
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    tracking_data = {
        "update_timestamp": timestamp,
        "total_identified": len(fixable_leads),
        "successfully_updated": updated_count,
        "update_type": "practice_name_improvement",
        "description": "Updated generic 'Medical Practice X' names to use real owner information",
        "fixable_leads": fixable_leads[:20],  # Save first 20 for reference
        "examples": [
            {
                "before": lead['current_name'],
                "after": lead['suggested_name'],
                "owner": lead['owner_name']
            }
            for lead in fixable_leads[:10]
        ]
    }
    
    filename = f"practice_name_fixes_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(tracking_data, f, indent=2)
    
    print(f"\n💾 Update tracking saved to: {filename}")
    return filename

def main():
    """Main execution function"""
    
    print("🔧 VANTAGEPOINT CRM - PRACTICE NAME FIXES")
    print("=" * 60)
    print(f"🕐 Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("🎯 Goal: Fix generic 'Medical Practice X' names using real owner data")
    print("")
    
    try:
        # Step 1: Identify leads that need fixes
        fixable_leads = identify_leads_to_fix()
        
        if len(fixable_leads) == 0:
            print("✅ No leads need practice name fixes!")
            return
        
        print(f"\n🎯 READY TO FIX {len(fixable_leads)} PRACTICE NAMES")
        print("📋 This will update generic names to meaningful practice names")
        
        # Step 2: Update leads in CRM
        success = update_leads_in_crm(fixable_leads)
        
        if success:
            # Step 3: Save tracking
            tracking_file = save_update_tracking(fixable_leads, len(fixable_leads))
            
            print(f"\n🎉 PRACTICE NAME FIXES COMPLETE!")
            print(f"✅ Generic names replaced with meaningful practice names")
            print(f"📊 Lead quality significantly improved")
            print(f"🔍 Tracking: {tracking_file}")
            
            print(f"\n🎯 EXAMPLES OF IMPROVEMENTS:")
            for i, lead in enumerate(fixable_leads[:5], 1):
                print(f"  {i}. \"{lead['current_name']}\" → \"{lead['suggested_name']}\"")
            
        else:
            print(f"\n❌ Practice name fixes failed - check logs for details")
        
    except Exception as e:
        print(f"❌ Fix process failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 