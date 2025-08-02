#!/usr/bin/env python3
"""
Upload 1000 Highest-Scoring Leads to CRM Hopper
==============================================

This script loads leads from Excel/CSV files with existing scores,
sorts by highest scores, and uploads 1000 top leads to the CRM.
"""

import pandas as pd
import requests
import json
import time
from datetime import datetime
import os

# Configuration
API_BASE = "https://api.vantagepointcrm.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
TARGET_UPLOAD_COUNT = 1000
BATCH_SIZE = 10  # Smaller batches to avoid timeouts
MAX_RETRIES = 3  # Retry failed batches

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
        print(response.text)
        return None

def load_scored_leads():
    """Load leads from files with existing scores"""
    all_leads = []
    
    print("📊 Loading scored leads from local files...")
    
    # Load recalibrated leads (has Recalibrated_Score)
    try:
        print("   📈 Loading recalibrated_rural_physician_leads.xlsx...")
        df1 = pd.read_excel('recalibrated_rural_physician_leads.xlsx')
        print(f"   ✅ Loaded {len(df1):,} recalibrated leads")
        
        # Standardize the score column
        df1['final_score'] = df1['Recalibrated_Score']
        df1['source_file'] = 'recalibrated'
        all_leads.append(df1)
        
    except Exception as e:
        print(f"   ❌ Error loading recalibrated file: {e}")
    
    # Load CRM leads (has Score)
    try:
        print("   📈 Loading rural_physician_leads_crm.xlsx...")
        df2 = pd.read_excel('rural_physician_leads_crm.xlsx')
        print(f"   ✅ Loaded {len(df2):,} CRM leads")
        
        # Standardize the score column
        df2['final_score'] = df2['Score']
        df2['source_file'] = 'crm'
        all_leads.append(df2)
        
    except Exception as e:
        print(f"   ❌ Error loading CRM file: {e}")
    
    if not all_leads:
        print("❌ No scored lead files could be loaded!")
        return None
    
    # Combine all leads
    print("🔗 Combining and sorting leads...")
    combined_df = pd.concat(all_leads, ignore_index=True, sort=False)
    
    # Sort by score (highest first)
    combined_df = combined_df.sort_values('final_score', ascending=False)
    
    print(f"✅ Combined {len(combined_df):,} total leads, sorted by score")
    print(f"   📊 Score range: {combined_df['final_score'].min():.2f} - {combined_df['final_score'].max():.2f}")
    
    return combined_df

def convert_to_crm_format(df_row, source_file):
    """Convert a DataFrame row to CRM lead format"""
    
    if source_file == 'recalibrated':
        # Use recalibrated file format
        practice_name = df_row.get('Legal_Business_Name', '')
        if pd.isna(practice_name) or not practice_name:
            # Fallback to provider name
            first_name = df_row.get('Provider_First_Name', '')
            last_name = df_row.get('Provider_Last_Name', '')
            practice_name = f"{first_name} {last_name}".strip()
        
        lead = {
            "practice_name": practice_name,
            "contact_name": f"{df_row.get('Provider_First_Name', '')} {df_row.get('Provider_Last_Name', '')}".strip(),
            "phone": df_row.get('Practice_Phone', ''),
            "email": "",  # Not available in this dataset
            "address": df_row.get('Practice_Address_Line1', ''),
            "city": df_row.get('Practice_City', ''),
            "state": df_row.get('Practice_State', ''),
            "zip_code": str(df_row.get('Practice_ZIP', '')),
            "specialty": df_row.get('Primary_Specialty', ''),
            "score": float(df_row.get('final_score', 0)),
            "lead_type": "Rural Physician",
            "source": "NPPES Recalibrated",
            "notes": f"NPI: {df_row.get('NPI', '')}, Group Size: {df_row.get('Practice_Group_Size', '')}"
        }
        
    elif source_file == 'crm':
        # Use CRM file format (adapt based on actual columns)
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
            "score": float(df_row.get('final_score', 0)),
            "lead_type": "CRM Import",
            "source": "Rural Physician CRM",
            "notes": f"CRM Lead Import"
        }
    
    else:
        # Generic format
        lead = {
            "practice_name": "Unknown Practice",
            "contact_name": "Unknown Contact",
            "phone": "",
            "email": "",
            "address": "",
            "city": "",
            "state": "",
            "zip_code": "",
            "specialty": "",
            "score": float(df_row.get('final_score', 0)),
            "lead_type": "Import",
            "source": f"File: {source_file}",
            "notes": ""
        }
    
    # Clean up empty strings and NaN values
    for key, value in lead.items():
        if pd.isna(value) or value == 'nan':
            lead[key] = ""
        elif isinstance(value, str):
            lead[key] = value.strip()
    
    return lead

def upload_leads_batch(token, leads_batch, retry_count=0):
    """Upload a batch of leads with retry logic"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{API_BASE}/api/v1/leads/bulk"
    payload = {"leads": leads_batch}
    
    try:
        # Longer timeout for bulk operations
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return True, result.get('created_count', len(leads_batch))
        elif response.status_code == 504 and retry_count < MAX_RETRIES:
            # Retry on timeout with exponential backoff
            wait_time = (retry_count + 1) * 5
            print(f"     ⏳ Timeout, retrying in {wait_time}s (attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(wait_time)
            return upload_leads_batch(token, leads_batch, retry_count + 1)
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except requests.Timeout:
        if retry_count < MAX_RETRIES:
            wait_time = (retry_count + 1) * 5
            print(f"     ⏳ Timeout, retrying in {wait_time}s (attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(wait_time)
            return upload_leads_batch(token, leads_batch, retry_count + 1)
        else:
            return False, "Request timeout after retries"
    except Exception as e:
        return False, str(e)

def main():
    print("🚀 UPLOADING 1000 TOP-SCORED LEADS TO CRM HOPPER")
    print("=" * 60)
    
    # Authenticate
    token = authenticate()
    if not token:
        return
    
    # Load scored leads
    leads_df = load_scored_leads()
    if leads_df is None:
        return
    
    # Take top 1000 leads
    top_leads = leads_df.head(TARGET_UPLOAD_COUNT)
    print(f"\n🎯 Selected top {len(top_leads)} leads for upload")
    print(f"   📊 Score range: {top_leads['final_score'].min():.2f} - {top_leads['final_score'].max():.2f}")
    
    # Convert to CRM format
    print("\n🔄 Converting leads to CRM format...")
    crm_leads = []
    
    for idx, row in top_leads.iterrows():
        try:
            source = row.get('source_file', 'unknown')
            lead = convert_to_crm_format(row, source)
            crm_leads.append(lead)
        except Exception as e:
            print(f"   ⚠️ Error converting lead at index {idx}: {e}")
            continue
    
    print(f"✅ Converted {len(crm_leads)} leads for upload")
    
    # Upload in batches
    print(f"\n📤 Uploading {len(crm_leads)} leads in batches of {BATCH_SIZE}...")
    total_uploaded = 0
    batch_num = 1
    
    for i in range(0, len(crm_leads), BATCH_SIZE):
        batch = crm_leads[i:i + BATCH_SIZE]
        
        print(f"   📦 Batch {batch_num}: Uploading {len(batch)} leads...")
        
        success, result = upload_leads_batch(token, batch)
        
        if success:
            uploaded_count = result if isinstance(result, int) else len(batch)
            total_uploaded += uploaded_count
            print(f"   ✅ Batch {batch_num}: {uploaded_count} leads uploaded")
        else:
            print(f"   ❌ Batch {batch_num} failed: {result}")
        
        batch_num += 1
        
        # Longer pause between batches to avoid overwhelming backend
        time.sleep(5)
    
    # Summary
    print(f"\n🎉 UPLOAD COMPLETE")
    print(f"   📊 Total leads uploaded: {total_uploaded}")
    print(f"   📈 Success rate: {(total_uploaded/len(crm_leads)*100):.1f}%")
    print(f"   🏥 Lead hopper significantly expanded!")
    
    # Save tracking
    tracking = {
        "timestamp": datetime.now().isoformat(),
        "total_leads_processed": len(crm_leads),
        "total_uploaded": total_uploaded,
        "source_files": ["recalibrated_rural_physician_leads.xlsx", "rural_physician_leads_crm.xlsx"],
        "score_range": {
            "min": float(top_leads['final_score'].min()),
            "max": float(top_leads['final_score'].max())
        }
    }
    
    tracking_file = f"top_1000_upload_tracking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(tracking_file, 'w') as f:
        json.dump(tracking, f, indent=2)
    
    print(f"   📋 Tracking saved to: {tracking_file}")

if __name__ == "__main__":
    main()