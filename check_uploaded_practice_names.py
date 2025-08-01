#!/usr/bin/env python3
"""
🔍 Check Uploaded Practice Names
See what generic practice names actually exist in the CRM and map them back to original data
"""

import json
import urllib3

def check_crm_practice_names():
    """Check what practice names are in the CRM"""
    
    print("🔍 CHECKING ACTUAL PRACTICE NAMES IN CRM")
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
        return []
    
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
        return []
    
    leads = json.loads(leads_response.data.decode('utf-8')).get('leads', [])
    print(f"✅ Found {len(leads)} total leads in CRM")
    
    # Find generic practice names
    generic_leads = []
    real_practice_names = []
    
    for lead in leads:
        practice_name = lead.get('practice_name', '')
        if practice_name.startswith('Medical Practice '):
            generic_leads.append(lead)
        else:
            real_practice_names.append(practice_name)
    
    print(f"\n📊 PRACTICE NAME BREAKDOWN:")
    print(f"✅ Real practice names: {len(real_practice_names)}")
    print(f"❌ Generic 'Medical Practice X' names: {len(generic_leads)}")
    
    if len(generic_leads) > 0:
        print(f"\n🔧 GENERIC PRACTICE NAMES THAT NEED FIXING:")
        for i, lead in enumerate(generic_leads[:20]):  # Show first 20
            print(f"  {i+1:2d}. ID {lead['id']:3d}: \"{lead['practice_name']}\" (Owner: {lead.get('owner_name', 'Unknown')})")
        
        if len(generic_leads) > 20:
            print(f"      ... and {len(generic_leads) - 20} more")
    
    print(f"\n📋 SAMPLE REAL PRACTICE NAMES:")
    for name in real_practice_names[:10]:
        print(f"  ✅ {name}")
    
    return generic_leads

def load_original_data_mapping():
    """Load original data to understand the mapping"""
    
    print(f"\n🔍 LOADING ORIGINAL DATA FOR MAPPING")
    print("=" * 50)
    
    original_leads = []
    
    # Load all source files in the same order as upload
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
            for lead in leads:
                lead['source_file'] = source
                original_leads.append(lead)
            print(f"✅ {source}: {len(leads)} leads")
        except Exception as e:
            print(f"❌ {source}: {e}")
    
    print(f"\n📊 Total original leads loaded: {len(original_leads)}")
    
    # Count how many had <UNAVAIL> practice names
    unavail_count = 0
    unavail_with_owners = 0
    
    for lead in original_leads:
        practice_name = lead.get('practice_name', '')
        owner_name = lead.get('owner_name', '')
        
        if practice_name in ['<UNAVAIL>', 'nan', None, '']:
            unavail_count += 1
            if owner_name and owner_name not in ['nan, nan', 'nan', '', None]:
                unavail_with_owners += 1
    
    print(f"\n📋 ORIGINAL DATA ANALYSIS:")
    print(f"❌ Leads with <UNAVAIL> practice names: {unavail_count}")
    print(f"🔧 Of those, have useful owner info: {unavail_with_owners}")
    print(f"✅ These became 'Medical Practice X' in upload")
    
    return original_leads

def main():
    """Main execution"""
    
    print("🔍 VANTAGEPOINT CRM - PRACTICE NAME ANALYSIS")
    print("=" * 60)
    
    # Check what's actually in the CRM
    generic_leads = check_crm_practice_names()
    
    # Load original data for context
    original_leads = load_original_data_mapping()
    
    if len(generic_leads) > 0:
        print(f"\n💡 SUMMARY:")
        print(f"📊 {len(generic_leads)} leads have generic 'Medical Practice X' names")
        print(f"🔧 These can be improved using owner information from original data")
        print(f"🎯 Next step: Create a proper mapping between CRM IDs and original owner data")
    else:
        print(f"\n✅ No generic practice names found - all leads have proper names!")

if __name__ == "__main__":
    main() 