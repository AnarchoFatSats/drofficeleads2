#!/usr/bin/env python3
"""
Remove Placeholder Emails from VantagePoint CRM
===============================================
Remove all generated placeholder emails and leave fields empty for reps to research.

This will:
1. Identify all generated placeholder emails (contact@[practice].com pattern)
2. Remove them from leads (set email to empty)
3. Add a note that email needs research
4. Preserve any real-looking emails
"""

import requests
import json
import time

def remove_placeholder_emails():
    """Remove generated placeholder emails from all leads"""
    
    base_url = 'https://api.vantagepointcrm.com'
    
    print("🗑️  REMOVING PLACEHOLDER EMAILS")
    print("=" * 50)
    print("🎯 Goal: Remove fake emails, let reps research real ones")
    
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
        
        # Get all active leads
        leads_response = requests.get(f'{base_url}/api/v1/leads',
                                    headers={'Authorization': f'Bearer {token}'},
                                    timeout=30)
        
        if leads_response.status_code != 200:
            print(f"❌ Failed to get leads: {leads_response.text}")
            return
        
        all_leads = leads_response.json()['leads']
        active_leads = [l for l in all_leads if l.get('status') != 'inactive_duplicate']
        
        print(f"📊 Analyzing {len(active_leads)} active leads...")
        
        # Identify placeholder emails
        placeholder_leads = []
        real_email_leads = []
        no_email_leads = []
        
        for lead in active_leads:
            email = lead.get('email', '').strip()
            practice_name = lead.get('practice_name', '')
            
            if not email:
                no_email_leads.append(lead)
            elif email.startswith('contact@') and email.endswith('.com'):
                # Check if it's a generated placeholder
                domain = email.replace('contact@', '').replace('.com', '')
                clean_practice = ''.join(c.lower() for c in practice_name if c.isalnum())[:20]
                
                if domain == clean_practice or len(domain) < 5:
                    # This is definitely a generated placeholder
                    placeholder_leads.append(lead)
                else:
                    # Might be real, keep it
                    real_email_leads.append(lead)
            else:
                # Doesn't match our placeholder pattern, probably real
                real_email_leads.append(lead)
        
        print(f"\\n📋 EMAIL ANALYSIS:")
        print(f"   🗑️  Placeholder emails to remove: {len(placeholder_leads)}")
        print(f"   ✅ Potential real emails to keep: {len(real_email_leads)}")
        print(f"   📭 Already empty: {len(no_email_leads)}")
        
        if placeholder_leads:
            print(f"\\n🔍 EXAMPLES OF PLACEHOLDERS TO REMOVE:")
            for i, lead in enumerate(placeholder_leads[:5]):
                practice = lead.get('practice_name', 'Unknown')[:30]
                email = lead.get('email', '')
                print(f"   {i+1}. {practice} → {email}")
        
        if real_email_leads:
            print(f"\\n✅ EXAMPLES OF EMAILS TO KEEP:")
            for i, lead in enumerate(real_email_leads[:3]):
                practice = lead.get('practice_name', 'Unknown')[:30]
                email = lead.get('email', '')
                print(f"   {i+1}. {practice} → {email}")
        
        # Confirm before proceeding
        if not placeholder_leads:
            print("\\n🎉 No placeholder emails found - all clean!")
            return
            
        proceed = input(f"\\n❓ Remove {len(placeholder_leads)} placeholder emails? (yes/no): ").lower().strip()
        if not proceed.startswith('y'):
            print("❌ Operation cancelled")
            return
        
        # Remove placeholder emails
        print(f"\\n🗑️  REMOVING PLACEHOLDER EMAILS...")
        removed_count = 0
        failed_count = 0
        
        for lead in placeholder_leads:
            try:
                lead_id = lead['id']
                
                # Update lead to remove email and add note
                update_data = {
                    'email': '',  # Remove the fake email
                    'notes': f"Email needs research - placeholder removed. Original: {lead.get('email', '')}"
                }
                
                response = requests.put(f'{base_url}/api/v1/leads/{lead_id}',
                                      json=update_data,
                                      headers={'Authorization': f'Bearer {token}'},
                                      timeout=15)
                
                if response.status_code == 200:
                    removed_count += 1
                    if removed_count % 10 == 0:
                        print(f"   ✅ Processed {removed_count} removals...")
                else:
                    failed_count += 1
                    print(f"   ❌ Failed to update lead {lead_id}: {response.status_code}")
                
                # Rate limiting
                time.sleep(0.05)
                
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Error updating lead {lead.get('id', 'unknown')}: {e}")
        
        # Final summary
        print(f"\\n" + "="*50)
        print(f"🎉 PLACEHOLDER EMAIL REMOVAL COMPLETE!")
        print(f"="*50)
        print(f"✅ Successfully removed: {removed_count} placeholder emails")
        print(f"❌ Failed to update: {failed_count} leads")
        print(f"📧 Real emails preserved: {len(real_email_leads)}")
        print(f"📭 Empty email fields: {len(no_email_leads) + removed_count}")
        
        print(f"\\n💡 NEXT STEPS FOR REPS:")
        print(f"   1. Work leads with empty email fields")
        print(f"   2. Research practice websites to find real contact emails")
        print(f"   3. Update lead with genuine email when found")
        print(f"   4. Much better than wasting time on fake emails!")
        
        print(f"\\n🎯 RESULT: Clean leads with honest 'needs research' status")
        
    except Exception as e:
        print(f"❌ Error during email cleanup: {e}")

if __name__ == "__main__":
    remove_placeholder_emails()