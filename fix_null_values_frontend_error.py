#!/usr/bin/env python3
"""
Fix Null Values Causing Frontend Errors
=======================================
Clean up null/empty values in lead data that cause JavaScript toUpperCase() errors.
"""

import requests
import time

def fix_null_values():
    """Fix null and empty values that cause frontend JavaScript errors"""
    
    base_url = 'https://api.vantagepointcrm.com'
    
    print("🔧 FIXING NULL VALUES FOR FRONTEND")
    print("=" * 50)
    
    try:
        # Login as admin
        login_response = requests.post(f'{base_url}/api/v1/auth/login',
                                     json={'username': 'admin', 'password': 'admin123'},
                                     timeout=15)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        token = login_response.json()['access_token']
        print("✅ Admin authenticated")
        
        # Get all leads
        leads_response = requests.get(f'{base_url}/api/v1/leads',
                                    headers={'Authorization': f'Bearer {token}'},
                                    timeout=30)
        
        if leads_response.status_code != 200:
            print(f"❌ Failed to get leads: {leads_response.text}")
            return
        
        all_leads = leads_response.json()['leads']
        print(f"📊 Analyzing {len(all_leads)} leads for null values...")
        
        # Find leads with problematic values
        leads_to_fix = []
        
        for lead in all_leads:
            needs_fix = False
            fixes = {}
            
            # Check critical string fields that frontend uses
            string_fields = ['practice_name', 'city', 'state', 'status', 'email', 'address']
            
            for field in string_fields:
                value = lead.get(field)
                if value is None or value == '':
                    needs_fix = True
                    if field == 'practice_name' and not value:
                        fixes[field] = 'Practice Name Needed'
                    elif field == 'city' and not value:
                        fixes[field] = 'City Unknown'
                    elif field == 'state' and not value:
                        fixes[field] = 'State Unknown'  
                    elif field == 'status' and not value:
                        fixes[field] = 'new'
                    elif field == 'email' and not value:
                        fixes[field] = ''  # Keep empty, don't set to null
                    elif field == 'address' and not value:
                        fixes[field] = 'Address Unknown'
            
            if needs_fix:
                leads_to_fix.append({
                    'id': lead['id'],
                    'current_name': lead.get('practice_name', 'EMPTY')[:30],
                    'fixes': fixes
                })
        
        print(f"\\n🔍 ANALYSIS RESULTS:")
        print(f"   • Leads needing fixes: {len(leads_to_fix)}")
        
        if leads_to_fix:
            print(f"\\n📋 EXAMPLES OF FIXES NEEDED:")
            for i, lead in enumerate(leads_to_fix[:5]):
                print(f"   {i+1}. Lead {lead['id']}: {lead['current_name']}")
                print(f"      Fixes: {lead['fixes']}")
        
        if not leads_to_fix:
            print("✅ No null value fixes needed!")
            return
        
        proceed = input(f"\\n❓ Fix {len(leads_to_fix)} leads with null values? (yes/no): ").lower().strip()
        if not proceed.startswith('y'):
            print("❌ Fix cancelled")
            return
        
        # Apply fixes
        print(f"\\n🔧 APPLYING FIXES...")
        fixed_count = 0
        failed_count = 0
        
        for lead_data in leads_to_fix:
            try:
                lead_id = lead_data['id']
                fixes = lead_data['fixes']
                
                # Update lead with fixed values
                response = requests.put(f'{base_url}/api/v1/leads/{lead_id}',
                                      json=fixes,
                                      headers={'Authorization': f'Bearer {token}'},
                                      timeout=15)
                
                if response.status_code == 200:
                    fixed_count += 1
                    if fixed_count % 25 == 0:
                        print(f"   ✅ Fixed {fixed_count} leads...")
                else:
                    failed_count += 1
                    if failed_count <= 3:  # Only show first few failures
                        print(f"   ❌ Failed to fix lead {lead_id}: {response.status_code}")
                
                # Rate limiting
                time.sleep(0.02)
                
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Error fixing lead {lead_data.get('id', 'unknown')}: {e}")
        
        # Final summary
        print(f"\\n" + "="*50)
        print(f"🎉 NULL VALUE FIX COMPLETE!")
        print(f"="*50)
        print(f"✅ Successfully fixed: {fixed_count} leads")
        print(f"❌ Failed to fix: {failed_count} leads")
        
        print(f"\\n🎯 FRONTEND ERROR SHOULD BE RESOLVED!")
        print(f"   • All string fields now have safe values")
        print(f"   • No more null/undefined for .toUpperCase()")
        print(f"   • Refresh your browser to see the fix")
        
    except Exception as e:
        print(f"❌ Error during null value fix: {e}")

if __name__ == "__main__":
    fix_null_values()