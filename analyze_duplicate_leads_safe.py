#!/usr/bin/env python3
"""
VantagePoint CRM - Safe Duplicate Analysis
==========================================
Analyze duplicate leads and create detailed report WITHOUT making changes.

This script will:
1. Identify all types of duplicates
2. Rank them by removal priority
3. Create a detailed report
4. Recommend specific actions
"""

import requests
import json
from collections import defaultdict, Counter

def analyze_lead_duplicates():
    """Comprehensive duplicate analysis"""
    
    base_url = 'https://api.vantagepointcrm.com'
    
    print("🔍 SAFE DUPLICATE LEAD ANALYSIS")
    print("=" * 50)
    print("📋 This analysis will NOT modify any data")
    
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
        total_leads = len(all_leads)
        
        print(f"📊 Analyzing {total_leads} leads...")
        
        # Category 1: Test/Placeholder Data
        test_leads = []
        for lead in all_leads:
            practice_name = lead.get('practice_name', '').upper()
            if any(keyword in practice_name for keyword in 
                   ['UNKNOWN', 'TEST', 'PLACEHOLDER', 'SAMPLE']):
                test_leads.append(lead)
        
        # Category 2: Generic Email Templates
        generic_email_leads = []
        generic_emails = [
            'contact@medicalpractice.com',
            'contact@unknownpractice.com', 
            'info@medicalpractice.com',
            'admin@medicalpractice.com'
        ]
        
        for lead in all_leads:
            email = lead.get('email', '').lower()
            if email in generic_emails or (email.startswith('contact@') and 'practice' in email):
                generic_email_leads.append(lead)
        
        # Category 3: Exact NPI Duplicates
        npi_groups = defaultdict(list)
        for lead in all_leads:
            npi = lead.get('npi', '').strip()
            if npi and npi != 'N/A' and len(npi) >= 10:
                npi_groups[npi].append(lead)
        
        npi_duplicates = {npi: leads for npi, leads in npi_groups.items() if len(leads) > 1}
        
        # Category 4: Phone Number Duplicates
        phone_groups = defaultdict(list)
        for lead in all_leads:
            phone = lead.get('phone', '').strip()
            clean_phone = ''.join(c for c in phone if c.isdigit())
            if len(clean_phone) >= 10:
                phone_groups[clean_phone].append(lead)
        
        phone_duplicates = {phone: leads for phone, leads in phone_groups.items() if len(leads) > 1}
        
        # Category 5: Practice Name + City Duplicates
        name_city_groups = defaultdict(list)
        for lead in all_leads:
            practice_name = lead.get('practice_name', '').strip().upper()
            city = lead.get('city', '').strip().upper()
            if practice_name and practice_name != 'UNKNOWN PRACTICE' and city:
                key = f"{practice_name}|||{city}"
                name_city_groups[key].append(lead)
        
        name_duplicates = {key: leads for key, leads in name_city_groups.items() if len(leads) > 1}
        
        # Generate Report
        print("\\n" + "="*60)
        print("🎯 DUPLICATE ANALYSIS REPORT")
        print("="*60)
        
        # Summary stats
        total_problematic = 0
        
        print(f"\\n1️⃣  TEST/PLACEHOLDER DATA:")
        print(f"   📊 Found: {len(test_leads)} leads")
        if test_leads:
            total_problematic += len(test_leads)
            print("   🔍 Examples:")
            for lead in test_leads[:5]:
                print(f"      • ID {lead['id']}: {lead.get('practice_name', 'N/A')}")
            print(f"   💡 RECOMMENDATION: Safe to remove all {len(test_leads)} test leads")
        
        print(f"\\n2️⃣  GENERIC EMAIL TEMPLATES:")
        print(f"   📊 Found: {len(generic_email_leads)} leads")
        if generic_email_leads:
            total_problematic += len(generic_email_leads)
            email_counter = Counter([l.get('email', '') for l in generic_email_leads])
            print("   🔍 Most common generic emails:")
            for email, count in email_counter.most_common(3):
                print(f"      • {email}: {count} leads")
            print(f"   💡 RECOMMENDATION: Replace with real emails or remove")
        
        print(f"\\n3️⃣  EXACT NPI DUPLICATES:")
        print(f"   📊 Found: {len(npi_duplicates)} NPI groups with duplicates")
        if npi_duplicates:
            npi_duplicate_count = sum(len(leads)-1 for leads in npi_duplicates.values())
            total_problematic += npi_duplicate_count
            print(f"   🗑️  Excess leads: {npi_duplicate_count}")
            print("   🔍 Worst offenders:")
            sorted_npi = sorted(npi_duplicates.items(), key=lambda x: len(x[1]), reverse=True)
            for npi, leads in sorted_npi[:3]:
                scores = [l.get('score', 0) for l in leads]
                print(f"      • NPI {npi}: {len(leads)} leads (scores: {scores})")
            print(f"   💡 RECOMMENDATION: Keep highest-scoring lead per NPI")
        
        print(f"\\n4️⃣  PHONE NUMBER DUPLICATES:")
        print(f"   📊 Found: {len(phone_duplicates)} phone groups with duplicates")
        if phone_duplicates:
            phone_duplicate_count = sum(len(leads)-1 for leads in phone_duplicates.values())
            total_problematic += phone_duplicate_count
            print(f"   🗑️  Excess leads: {phone_duplicate_count}")
            print("   🔍 Worst offenders:")
            sorted_phone = sorted(phone_duplicates.items(), key=lambda x: len(x[1]), reverse=True)
            for phone, leads in sorted_phone[:3]:
                practices = [l.get('practice_name', 'Unknown')[:30] for l in leads]
                print(f"      • Phone {phone}: {len(leads)} leads")
                for practice in practices[:2]:
                    print(f"         - {practice}")
            print(f"   💡 RECOMMENDATION: Keep highest-scoring lead per phone")
        
        print(f"\\n5️⃣  PRACTICE NAME + CITY DUPLICATES:")
        print(f"   📊 Found: {len(name_duplicates)} name/city groups with duplicates")
        if name_duplicates:
            name_duplicate_count = sum(len(leads)-1 for leads in name_duplicates.values())
            total_problematic += name_duplicate_count
            print(f"   🗑️  Excess leads: {name_duplicate_count}")
            print("   🔍 Examples:")
            for key, leads in list(name_duplicates.items())[:3]:
                practice_name, city = key.split('|||')
                scores = [l.get('score', 0) for l in leads]
                print(f"      • {practice_name[:40]} ({city}): {len(leads)} leads (scores: {scores})")
            print(f"   💡 RECOMMENDATION: Keep highest-scoring lead per practice+city")
        
        # Overall summary
        print(f"\\n" + "="*60)
        print(f"📊 OVERALL DUPLICATE SUMMARY")
        print(f"="*60)
        print(f"📈 Current leads: {total_leads}")
        print(f"🗑️  Problematic leads: {total_problematic}")
        print(f"✅ Clean leads after dedup: {total_leads - total_problematic}")
        print(f"📉 Potential reduction: {total_problematic/total_leads*100:.1f}%")
        
        # Impact on assigned leads
        assigned_problematic = 0
        for lead in all_leads:
            lead_id = lead.get('id')
            is_assigned = bool(lead.get('assigned_user_id'))
            is_problematic = (
                lead in test_leads or 
                lead in generic_email_leads or
                any(lead in leads for leads in npi_duplicates.values()) or
                any(lead in leads for leads in phone_duplicates.values()) or
                any(lead in leads for leads in name_duplicates.values())
            )
            if is_assigned and is_problematic:
                assigned_problematic += 1
        
        print(f"\\n⚠️  ASSIGNMENT IMPACT:")
        print(f"   • Currently assigned leads: {len([l for l in all_leads if l.get('assigned_user_id')])}")
        print(f"   • Assigned problematic leads: {assigned_problematic}")
        print(f"   💡 Need to reassign {assigned_problematic} leads before cleanup")
        
        # Recommendations
        print(f"\\n🎯 RECOMMENDED ACTION PLAN:")
        print(f"=" * 40)
        print(f"1. 🧪 Remove {len(test_leads)} test/placeholder leads (safe)")
        print(f"2. 📧 Fix {len(generic_email_leads)} generic email addresses")  
        print(f"3. 🔢 Deduplicate {len(npi_duplicates)} NPI groups (keep highest score)")
        print(f"4. 📞 Deduplicate {len(phone_duplicates)} phone groups (keep highest score)")
        print(f"5. 🏥 Deduplicate {len(name_duplicates)} practice name groups (keep highest score)")
        print(f"\\n💾 RESULT: Clean database with ~{total_leads - total_problematic} quality leads")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")

if __name__ == "__main__":
    analyze_lead_duplicates()