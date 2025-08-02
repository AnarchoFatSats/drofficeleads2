#!/usr/bin/env python3
"""
Complete High-Scoring Lead Upload with Optimized Backend
======================================================

Now that our backend optimization is working, upload larger batches efficiently
"""

import pandas as pd
import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE = "https://api.vantagepointcrm.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
TARGET_TOTAL_LEADS = 2000  # Aim for 2000 total high-quality leads
BATCH_SIZE = 100  # Use larger batches with optimized backend

def authenticate():
    """Authenticate as admin and get token"""
    print("🔐 Authenticating as admin...")
    
    login_url = f"{API_BASE}/api/v1/auth/login"
    login_payload = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(login_url, json=login_payload)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Admin authentication successful")
        return token
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def get_current_leads(token):
    """Get current leads to see what we have"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/api/v1/leads", headers=headers)
    
    if response.status_code == 200:
        return response.json()["leads"]
    else:
        print(f"❌ Error getting current leads: {response.status_code}")
        return []

def load_additional_top_leads(current_lead_count, target_count):
    """Load additional highest-scoring leads from our massive databases"""
    needed_leads = target_count - current_lead_count
    
    print(f"📊 Loading additional {needed_leads} top leads from databases...")
    
    # Load from our massive scored files
    all_leads = []
    
    # Load recalibrated leads (highest quality)
    try:
        df1 = pd.read_excel('recalibrated_rural_physician_leads.xlsx')
        df1['final_score'] = df1['Recalibrated_Score']
        df1['source_file'] = 'recalibrated'
        all_leads.append(df1)
        print(f"   ✅ Loaded {len(df1):,} recalibrated leads")
    except Exception as e:
        print(f"   ❌ Error loading recalibrated file: {e}")
    
    # Load CRM leads
    try:
        df2 = pd.read_excel('rural_physician_leads_crm.xlsx')
        df2['final_score'] = df2['Score']
        df2['source_file'] = 'crm'
        all_leads.append(df2)
        print(f"   ✅ Loaded {len(df2):,} CRM leads")
    except Exception as e:
        print(f"   ❌ Error loading CRM file: {e}")
    
    if not all_leads:
        return []
    
    # Combine and get top leads
    combined_df = pd.concat(all_leads, ignore_index=True)
    
    # Sort by score (highest first) and take more than needed to account for potential duplicates
    top_leads = combined_df.sort_values('final_score', ascending=False).head(needed_leads + 500)
    
    print(f"✅ Selected {len(top_leads)} top leads for processing")
    print(f"   📊 Score range: {top_leads['final_score'].min():.1f} - {top_leads['final_score'].max():.1f}")
    
    return top_leads

def convert_to_crm_format(df_row, source_file):
    """Convert DataFrame row to CRM format"""
    if source_file == 'recalibrated':
        practice_name = df_row.get('Legal_Business_Name', '')
        if pd.isna(practice_name) or not practice_name:
            first_name = df_row.get('Provider_First_Name', '')
            last_name = df_row.get('Provider_Last_Name', '')
            practice_name = f"{first_name} {last_name}".strip()
        
        lead = {
            "practice_name": practice_name,
            "contact_name": f"{df_row.get('Provider_First_Name', '')} {df_row.get('Provider_Last_Name', '')}".strip(),
            "phone": df_row.get('Practice_Phone', ''),
            "email": "",
            "address": df_row.get('Practice_Address_Line1', ''),
            "city": df_row.get('Practice_City', ''),
            "state": df_row.get('Practice_State', ''),
            "zip_code": str(df_row.get('Practice_ZIP', '')),
            "specialty": df_row.get('Primary_Specialty', ''),
            "score": int(float(df_row.get('final_score', 0))),
            "lead_type": "High-Value Rural Physician",
            "source": "NPPES Recalibrated Top Tier",
            "notes": f"NPI: {df_row.get('NPI', '')}, Top Score: {df_row.get('final_score', 0)}"
        }
    else:  # CRM file
        practice_name = df_row.get('Contact Name', '')
        lead = {
            "practice_name": practice_name,
            "contact_name": practice_name,
            "phone": df_row.get('Phone', ''),
            "email": df_row.get('Email', ''),
            "address": df_row.get('Address', ''),
            "city": df_row.get('City', ''),
            "state": df_row.get('State', ''),
            "zip_code": str(df_row.get('ZIP', '')),
            "specialty": df_row.get('Specialty', ''),
            "score": int(float(df_row.get('final_score', 0))),
            "lead_type": "CRM Premium",
            "source": "Rural Physician CRM Top Tier",
            "notes": f"Premium CRM Lead, Score: {df_row.get('final_score', 0)}"
        }
    
    # Clean up data
    for key, value in lead.items():
        if pd.isna(value) or value == 'nan':
            lead[key] = ""
        elif isinstance(value, str):
            lead[key] = value.strip()
    
    return lead

def upload_optimized_batch(token, leads_batch):
    """Upload using our optimized backend (larger batches)"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{API_BASE}/api/v1/leads/bulk"
    payload = {"leads": leads_batch}
    
    try:
        # Optimized backend can handle larger batches
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            created_count = result.get('created_count', 0)
            
            # Check if optimization flag is present
            if result.get('performance') == 'optimized_batch_write':
                print(f"      ⚡ OPTIMIZED: {created_count} leads created with batch operations")
            else:
                print(f"      ✅ {created_count} leads created")
            
            return True, created_count
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    
    except requests.Timeout:
        return False, "Request timeout"
    except Exception as e:
        return False, str(e)

def main():
    print("🚀 COMPLETING HIGH-SCORING LEAD UPLOAD (OPTIMIZED)")
    print("=" * 60)
    
    # Authenticate
    token = authenticate()
    if not token:
        return
    
    # Check current status
    print("\n📊 Checking current lead status...")
    current_leads = get_current_leads(token)
    current_count = len(current_leads)
    high_score_count = len([l for l in current_leads if l.get('score', 0) >= 60])
    
    print(f"✅ Current status:")
    print(f"   📈 Total leads: {current_count}")
    print(f"   🎯 High-scoring leads (60+): {high_score_count}")
    
    if high_score_count >= TARGET_TOTAL_LEADS:
        print(f"🎉 GOAL ACHIEVED! We already have {high_score_count} high-scoring leads!")
        print(f"   Target was {TARGET_TOTAL_LEADS}, we have {high_score_count}")
        return
    
    # Load additional top leads
    additional_leads = load_additional_top_leads(high_score_count, TARGET_TOTAL_LEADS)
    if not len(additional_leads):
        print("❌ No additional leads to upload")
        return
    
    # Convert to CRM format
    print(f"\n🔄 Converting {len(additional_leads)} leads to CRM format...")
    crm_leads = []
    
    for idx, row in additional_leads.iterrows():
        try:
            source = row.get('source_file', 'unknown')
            lead = convert_to_crm_format(row, source)
            
            # Only include very high-quality leads
            if lead['score'] >= 65:  # Higher threshold for additional uploads
                crm_leads.append(lead)
                
        except Exception as e:
            continue
    
    print(f"✅ Prepared {len(crm_leads)} high-quality leads (score ≥ 65)")
    
    if not crm_leads:
        print("❌ No qualifying leads found")
        return
    
    # Upload with optimized backend (larger batches)
    print(f"\n📤 Uploading with OPTIMIZED batches of {BATCH_SIZE}...")
    total_uploaded = 0
    batch_num = 1
    
    for i in range(0, len(crm_leads), BATCH_SIZE):
        batch = crm_leads[i:i + BATCH_SIZE]
        
        print(f"   📦 Batch {batch_num}: Uploading {len(batch)} leads...")
        
        success, result = upload_optimized_batch(token, batch)
        
        if success:
            uploaded_count = result if isinstance(result, int) else len(batch)
            total_uploaded += uploaded_count
            print(f"   ✅ Batch {batch_num}: {uploaded_count} leads uploaded")
        else:
            print(f"   ❌ Batch {batch_num} failed: {result}")
        
        batch_num += 1
        
        # Short pause between batches
        time.sleep(2)
    
    # Final summary
    print(f"\n🎉 UPLOAD COMPLETE!")
    print(f"   📊 Additional leads uploaded: {total_uploaded}")
    print(f"   📈 Success rate: {(total_uploaded/len(crm_leads)*100):.1f}%")
    
    # Check final status
    final_leads = get_current_leads(token)
    final_high_score = len([l for l in final_leads if l.get('score', 0) >= 60])
    
    print(f"\n🏁 FINAL STATUS:")
    print(f"   📈 Total leads: {len(final_leads)}")
    print(f"   🎯 High-scoring leads (60+): {final_high_score}")
    print(f"   🚀 HOPPER IS LOADED with {final_high_score} quality leads!")

if __name__ == "__main__":
    main()