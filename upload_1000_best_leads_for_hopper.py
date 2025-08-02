#!/usr/bin/env python3
"""
🚀 UPLOAD TOP 850 LEADS FOR ROBUST LEAD HOPPER
Build a massive lead inventory to sustain multiple agents long-term
"""

import json
import urllib3
import os
import glob
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

def load_all_local_leads():
    """Load and score all local leads from all sources"""
    
    print("📋 LOADING COMPREHENSIVE LOCAL LEAD INVENTORY")
    print("=" * 60)
    
    # Find all lead files
    lead_files = []
    for pattern in ['*lead*.json', '*medical*.json', '*practice*.json', '*hot*.json', '*warm*.json', '*converted*.json']:
        files = glob.glob(pattern, recursive=True)
        lead_files.extend(files)
    
    # Also check subdirectories
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.json') and any(keyword in file.lower() for keyword in ['lead', 'medical', 'practice', 'hot', 'warm', 'converted']):
                filepath = os.path.join(root, file)
                if filepath not in lead_files:
                    lead_files.append(filepath)
    
    # Remove duplicates and tracking files
    unique_files = []
    seen = set()
    for f in lead_files:
        normalized = os.path.normpath(f)
        if (normalized not in seen and 
            'tracking' not in f.lower() and
            'botocore' not in f and
            'site-packages' not in f):
            seen.add(normalized)
            unique_files.append(f)
    
    print(f"Found {len(unique_files)} lead source files")
    
    all_leads = []
    for filename in unique_files:
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Handle different data structures
            if isinstance(data, list):
                leads = data
            elif isinstance(data, dict):
                if 'leads' in data:
                    leads = data['leads']
                elif 'data' in data:
                    leads = data['data'] if isinstance(data['data'], list) else [data['data']]
                else:
                    leads = [data]
            else:
                continue
            
            # Add source tracking
            for lead in leads if isinstance(leads, list) else []:
                if isinstance(lead, dict):
                    lead['source_file'] = filename
                    all_leads.append(lead)
            
            print(f"  ✅ {os.path.basename(filename)}: {len(leads)} leads")
            
        except Exception as e:
            print(f"  ❌ {os.path.basename(filename)}: {e}")
    
    print(f"\n🏆 Total leads loaded: {len(all_leads)}")
    return all_leads

def score_and_rank_leads(all_leads):
    """Score all leads and return top quality ones"""
    
    print(f"\n🔢 SCORING AND RANKING ALL LEADS...")
    
    scored_leads = []
    
    for lead in all_leads:
        if not isinstance(lead, dict):
            continue
        
        # Get practice name
        practice_name = lead.get('practice_name', lead.get('name', 'Unknown'))
        
        # Skip test data
        if (practice_name.startswith('Medical Practice') or 
            practice_name == 'Unknown Practice' or
            '<UNAVAIL>' in practice_name or
            'TEST' in practice_name.upper() or
            len(practice_name) < 5):
            continue
        
        # Calculate enhanced score
        base_score = lead.get('score', 50)
        specialty = str(lead.get('specialty', lead.get('specialties', ''))).lower()
        
        enhanced_score = base_score
        
        # High-value specialty bonuses
        if 'cardio' in specialty: enhanced_score += 30
        if 'nephro' in specialty: enhanced_score += 35
        if 'orthop' in specialty or 'ortho' in specialty: enhanced_score += 25
        if 'podiat' in specialty: enhanced_score += 20
        if 'wound' in specialty: enhanced_score += 20
        if 'dermat' in specialty: enhanced_score += 15
        if 'surgery' in specialty: enhanced_score += 15
        if 'spine' in specialty: enhanced_score += 20
        if 'sports medicine' in specialty: enhanced_score += 15
        
        # Provider count bonus
        providers = lead.get('providers', 1)
        if providers and providers > 1:
            enhanced_score += min(providers * 3, 25)
        
        # Contact completeness bonus
        if lead.get('practice_phone') or lead.get('phone'): enhanced_score += 5
        if lead.get('email'): enhanced_score += 10
        if lead.get('address'): enhanced_score += 5
        if lead.get('npi'): enhanced_score += 5
        
        enhanced_score = min(enhanced_score, 200)
        
        lead['enhanced_score'] = enhanced_score
        lead['clean_practice_name'] = practice_name
        scored_leads.append(lead)
    
    # Sort by enhanced score
    scored_leads.sort(key=lambda x: x['enhanced_score'], reverse=True)
    
    print(f"✅ Scored {len(scored_leads)} quality leads")
    if scored_leads:
        print(f"📊 Score range: {scored_leads[-1]['enhanced_score']} - {scored_leads[0]['enhanced_score']}")
    
    return scored_leads

def get_unique_top_leads(scored_leads, target_count=850):
    """Get unique top leads, avoiding duplicates"""
    
    print(f"\n🎯 SELECTING TOP {target_count} UNIQUE LEADS...")
    
    unique_leads = []
    seen_names = set()
    seen_npis = set()
    
    for lead in scored_leads:
        practice_name = lead['clean_practice_name'].lower().strip()
        npi = lead.get('npi', '')
        
        # Skip duplicates
        if practice_name in seen_names:
            continue
        if npi and npi in seen_npis:
            continue
        
        seen_names.add(practice_name)
        if npi:
            seen_npis.add(npi)
        
        unique_leads.append(lead)
        
        if len(unique_leads) >= target_count:
            break
    
    print(f"✅ Selected {len(unique_leads)} unique high-quality leads")
    
    # Show sample
    print(f"\n🏆 TOP 15 LEADS FOR UPLOAD:")
    for i, lead in enumerate(unique_leads[:15], 1):
        name = lead['clean_practice_name']
        score = lead['enhanced_score']
        specialty = lead.get('specialty', lead.get('specialties', 'Unknown'))
        print(f"{i:2d}. {name} - {specialty} (Score: {score})")
    
    return unique_leads

def bulk_upload_to_crm(leads):
    """Upload leads to CRM in efficient batches"""
    
    print(f"\n🚀 BULK UPLOADING {len(leads)} LEADS TO CRM")
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
        print(f"❌ Login failed: {login_response.status}")
        return False
    
    token = json.loads(login_response.data.decode('utf-8'))['access_token']
    print("✅ Admin authenticated")
    
    # Convert leads to CRM format
    print(f"\n🔄 Converting {len(leads)} leads to CRM format...")
    crm_leads = []
    
    for lead in leads:
        crm_lead = {
            "practice_name": lead['clean_practice_name'],
            "owner_name": lead.get('owner_name', ''),
            "practice_phone": lead.get('practice_phone', lead.get('phone', '')),
            "email": lead.get('email', ''),
            "city": lead.get('city', ''),
            "state": lead.get('state', ''),
            "zip_code": lead.get('zip_code', ''),
            "address": lead.get('address', ''),
            "specialties": lead.get('specialty', lead.get('specialties', '')),
            "score": lead['enhanced_score'],
            "priority": "high" if lead['enhanced_score'] > 100 else "medium",
            "status": "new",
            "npi": lead.get('npi', ''),
            "providers": lead.get('providers', 1)
        }
        crm_leads.append(crm_lead)
    
    print(f"✅ Converted {len(crm_leads)} leads to CRM format")
    
    # Upload in batches
    batch_size = 25  # Smaller batches for reliability
    total_batches = (len(crm_leads) + batch_size - 1) // batch_size
    uploaded_count = 0
    failed_count = 0
    
    print(f"\n📦 Uploading in {total_batches} batches of {batch_size}...")
    
    for i in range(0, len(crm_leads), batch_size):
        batch = crm_leads[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        
        try:
            upload_response = http.request(
                'POST',
                f'{base_url}/api/v1/leads/bulk',
                body=json.dumps({"leads": batch}),
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            if upload_response.status == 200:
                result = json.loads(upload_response.data.decode('utf-8'))
                created = result.get('created_count', len(batch))
                uploaded_count += created
                print(f"   ✅ Batch {batch_num}/{total_batches}: {created} uploaded")
            else:
                failed_count += len(batch)
                print(f"   ❌ Batch {batch_num}/{total_batches}: Failed ({upload_response.status})")
                
        except Exception as e:
            failed_count += len(batch)
            print(f"   ❌ Batch {batch_num}/{total_batches}: Error - {e}")
    
    print(f"\n📊 BULK UPLOAD SUMMARY:")
    print(f"✅ Successfully uploaded: {uploaded_count} leads")
    print(f"❌ Failed uploads: {failed_count} leads") 
    print(f"📈 Success rate: {uploaded_count/(uploaded_count+failed_count)*100:.1f}%")
    
    return uploaded_count > 0

def main():
    """Main execution"""
    
    print("🚀 MASSIVE LEAD HOPPER BUILD - TOP 850 LEADS")
    print("=" * 60)
    print("🎯 Goal: Build robust lead inventory for long-term agent sustainability")
    print("📊 Target: Upload 850 highest-scoring unique medical practices")
    print("")
    
    # Load all leads
    all_leads = load_all_local_leads()
    
    if len(all_leads) < 100:
        print("❌ Insufficient leads found")
        return
    
    # Score and rank
    scored_leads = score_and_rank_leads(all_leads)
    
    if len(scored_leads) < 100:
        print("❌ Insufficient quality leads after scoring")
        return
    
    # Get unique top leads
    top_leads = get_unique_top_leads(scored_leads, target_count=850)
    
    if len(top_leads) < 50:
        print("❌ Insufficient unique leads")
        return
    
    # Upload to CRM
    success = bulk_upload_to_crm(top_leads)
    
    if success:
        print(f"\n🎉 MASSIVE LEAD HOPPER BUILD COMPLETE!")
        print(f"✅ System now has robust lead inventory")
        print(f"🎯 Ready to sustain multiple agents long-term")
    else:
        print(f"\n❌ Upload failed - please check system status")

if __name__ == "__main__":
    main()