#!/usr/bin/env python3
"""
Quick Web Dashboard Update
Efficiently updates web dashboard with key stats from comprehensive leads
"""

import pandas as pd
import json
from datetime import datetime
import re

def clean_phone(phone):
    """Clean and format phone number"""
    if pd.isna(phone) or phone == '':
        return None
    phone_str = str(phone).replace('.0', '').replace('.', '')
    phone_clean = re.sub(r'[^\d]', '', phone_str)
    return phone_clean if len(phone_clean) >= 10 else None

def quick_update():
    """Quick update of web dashboard data"""
    print("Reading comprehensive leads data (this may take a moment)...")
    
    # Read only the columns we need for faster processing
    needed_cols = [
        'Primary_Specialty', 'Practice_Group_Size', 'Practice_ZIP', 
        'Practice_Phone', 'Owner_Phone', 'Practice_Address_Line1',
        'Practice_City', 'Practice_State'
    ]
    
    try:
        # Try to read with specific columns for speed
        df = pd.read_excel('comprehensive_rural_physician_leads.xlsx', usecols=needed_cols)
    except:
        # Fallback to reading all columns if column selection fails
        print("Reading full file...")
        df = pd.read_excel('comprehensive_rural_physician_leads.xlsx')
    
    print(f"Loaded {len(df):,} leads")
    
    # Quick calculations
    total_leads = len(df)
    
    # Count specialties
    df['Primary_Specialty'] = df['Primary_Specialty'].astype(str)
    podiatrist_count = df['Primary_Specialty'].str.contains('Podiatrist', na=False).sum()
    wound_care_count = df['Primary_Specialty'].str.contains('Wound Care', na=False).sum()
    mohs_count = df['Primary_Specialty'].str.contains('Mohs', na=False).sum()
    
    # Count phones
    df['Clean_Practice_Phone'] = df['Practice_Phone'].apply(clean_phone)
    df['Clean_Owner_Phone'] = df['Owner_Phone'].apply(clean_phone)
    
    # Quick priority scoring for hot leads
    df['Score'] = 0
    df.loc[df['Primary_Specialty'].str.contains('Podiatrist', na=False), 'Score'] += 40
    df.loc[df['Primary_Specialty'].str.contains('Wound Care', na=False), 'Score'] += 35
    df.loc[df['Primary_Specialty'].str.contains('Mohs', na=False), 'Score'] += 30
    df.loc[df['Primary_Specialty'].str.contains('Family Medicine', na=False), 'Score'] += 20
    df.loc[df['Primary_Specialty'].str.contains('Internal Medicine', na=False), 'Score'] += 15
    
    # Group size bonus
    df.loc[df['Practice_Group_Size'] == 1, 'Score'] += 20
    df.loc[df['Practice_Group_Size'] == 2, 'Score'] += 15
    df.loc[df['Practice_Group_Size'].between(3, 5), 'Score'] += 10
    
    # Phone bonus
    df.loc[df['Clean_Practice_Phone'].notna(), 'Score'] += 10
    df.loc[df['Clean_Owner_Phone'].notna(), 'Score'] += 5
    
    hot_leads_count = (df['Score'] >= 80).sum()
    unique_zips = df['Practice_ZIP'].nunique()
    
    # Update summary.json
    summary_data = {
        "total_leads": total_leads,
        "hot_leads": int(hot_leads_count),
        "podiatrist_groups": int(podiatrist_count),
        "wound_care_groups": int(wound_care_count),
        "mohs_groups": int(mohs_count),
        "zip_codes_covered": int(unique_zips),
        "avg_population": 16903,  # Use previous average
        "last_updated": datetime.now().isoformat()
    }
    
    with open('web/data/summary.json', 'w') as f:
        json.dump(summary_data, f, indent=2)
    print("✅ Updated summary.json")
    
    # Create top 100 hot leads
    hot_leads_df = df.nlargest(100, 'Score')
    hot_leads_data = []
    
    for idx, row in hot_leads_df.iterrows():
        phone = row['Clean_Practice_Phone'] or row['Clean_Owner_Phone'] or 'N/A'
        
        # Priority category
        score = row['Score']
        if score >= 90:
            priority = "A+ Priority"
        elif score >= 80:
            priority = "A Priority"
        elif score >= 70:
            priority = "B+ Priority"
        else:
            priority = "B Priority"
        
        # Category type
        specialty = str(row['Primary_Specialty']).lower()
        if 'podiatrist' in specialty and 'wound care' in specialty:
            category = "Podiatrist + Wound Care"
        elif 'podiatrist' in specialty:
            category = "Podiatrist"
        elif 'wound care' in specialty:
            category = "Wound Care"
        elif 'mohs' in specialty:
            category = "Mohs Surgery"
        else:
            category = "Primary Care"
        
        # Address
        address_parts = []
        for field in ['Practice_Address_Line1', 'Practice_City', 'Practice_State', 'Practice_ZIP']:
            if pd.notna(row.get(field)):
                address_parts.append(str(row[field]))
        address = ' '.join(address_parts) if address_parts else 'N/A'
        
        lead_data = {
            "id": len(hot_leads_data) + 1,
            "priority": priority,
            "category": category,
            "providers": int(row.get('Practice_Group_Size', 1)),
            "specialties": str(row.get('Primary_Specialty', 'N/A')),
            "phone": phone,
            "address": address,
            "zip": str(row.get('Practice_ZIP', 'N/A')),
            "population": 16903,  # Default population
            "score": int(score)
        }
        hot_leads_data.append(lead_data)
    
    with open('web/data/hot_leads.json', 'w') as f:
        json.dump(hot_leads_data, f, indent=2)
    print(f"✅ Updated hot_leads.json with {len(hot_leads_data)} leads")
    
    # Create regions data
    regions_data = {}
    region_counts = df['Practice_ZIP'].astype(str).str[:2].value_counts()
    
    for region, count in region_counts.items():
        if len(region) == 2:
            regions_data[region] = {"count": int(count), "leads": []}
    
    with open('web/data/regions.json', 'w') as f:
        json.dump(regions_data, f, indent=2)
    print(f"✅ Updated regions.json with {len(regions_data)} regions")
    
    # Summary
    print("\n" + "="*60)
    print("WEB DASHBOARD QUICK UPDATE SUMMARY")
    print("="*60)
    print(f"Total Leads: {total_leads:,}")
    print(f"Hot Leads (A/A+ Priority): {hot_leads_count:,}")
    print(f"Podiatrist Groups: {podiatrist_count:,}")
    print(f"Wound Care Groups: {wound_care_count:,}")
    print(f"Mohs Surgery Groups: {mohs_count:,}")
    print(f"ZIP Codes Covered: {unique_zips:,}")
    print(f"Regions: {len(regions_data)}")
    print("\n✅ Web dashboard data updated successfully!")
    print("Ready for AWS Amplify deployment!")

if __name__ == "__main__":
    quick_update() 