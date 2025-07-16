#!/usr/bin/env python3
"""
Quick Web Dashboard Update
Efficiently updates web dashboard with comprehensive lead details including practice names and owner info
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

def format_phone(phone):
    """Format phone number for display"""
    if not phone or len(phone) < 10:
        return phone
    # Format as (XXX) XXX-XXXX
    return f"({phone[:3]}) {phone[3:6]}-{phone[6:10]}"

def get_best_practice_name(row):
    """Get the best available practice name"""
    # Priority: Legal Business Name > DBA Name > Other Organization Name
    legal_name = row.get('Legal_Business_Name', '')
    dba_name = row.get('DBA_Name', '')
    other_name = row.get('Other_Organization_Name', '')
    
    if pd.notna(legal_name) and str(legal_name).strip():
        return str(legal_name).strip()
    elif pd.notna(dba_name) and str(dba_name).strip():
        return str(dba_name).strip()
    elif pd.notna(other_name) and str(other_name).strip():
        return str(other_name).strip()
    else:
        # Individual provider name
        first = str(row.get('Provider_First_Name', '')).strip()
        last = str(row.get('Provider_Last_Name', '')).strip()
        if first and last:
            return f"{first} {last}"
        return "Practice Name Not Available"

def get_owner_info(row):
    """Get owner/contact information"""
    owner_name = row.get('Owner_Full_Name', '')
    if pd.notna(owner_name) and str(owner_name).strip():
        return str(owner_name).strip()
    
    # Try individual provider name if no owner
    first = str(row.get('Provider_First_Name', '')).strip()
    last = str(row.get('Provider_Last_Name', '')).strip()
    if first and last:
        credentials = str(row.get('Provider_Credentials', '')).strip()
        name = f"{first} {last}"
        if credentials:
            name += f", {credentials}"
        return name
    
    return "Contact Not Available"

def quick_update():
    """Quick update of web dashboard data with comprehensive lead details"""
    print("Reading comprehensive leads data (this may take a moment)...")
    
    # Read the comprehensive leads data
    df = pd.read_excel('comprehensive_rural_physician_leads.xlsx')
    print(f"Loaded {len(df):,} leads")
    
    # Quick calculations for summary
    total_leads = len(df)
    
    # Count specialties
    df['Primary_Specialty'] = df['Primary_Specialty'].astype(str)
    podiatrist_count = df['Primary_Specialty'].str.contains('Podiatrist', na=False).sum()
    wound_care_count = df['Primary_Specialty'].str.contains('Wound Care', na=False).sum()
    mohs_count = df['Primary_Specialty'].str.contains('Mohs', na=False).sum()
    
    # Clean phone numbers
    df['Clean_Practice_Phone'] = df['Practice_Phone'].apply(clean_phone)
    df['Clean_Owner_Phone'] = df['Owner_Phone'].apply(clean_phone)
    df['Clean_Primary_Phone'] = df['Primary_Phone'].apply(clean_phone)
    
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
    
    # EIN bonus (indicates established business)
    df.loc[df['EIN'].notna(), 'Score'] += 5
    
    hot_leads_count = (df['Score'] >= 75).sum()  # Lowered threshold since we're seeing 75s
    unique_zips = df['Practice_ZIP'].nunique()
    
    # Update summary.json
    summary_data = {
        "total_leads": total_leads,
        "hot_leads": int(hot_leads_count),
        "podiatrist_groups": int(podiatrist_count),
        "wound_care_groups": int(wound_care_count),
        "mohs_groups": int(mohs_count),
        "zip_codes_covered": int(unique_zips),
        "avg_population": 16903,
        "last_updated": datetime.now().isoformat()
    }
    
    with open('web/data/summary.json', 'w') as f:
        json.dump(summary_data, f, indent=2)
    print("✅ Updated summary.json")
    
    # Create comprehensive hot leads data (top 100 leads)
    hot_leads_df = df.nlargest(100, 'Score')
    hot_leads_data = []
    
    for idx, row in hot_leads_df.iterrows():
        # Get best available phones
        practice_phone = row['Clean_Practice_Phone']
        owner_phone = row['Clean_Owner_Phone'] 
        primary_phone = row['Clean_Primary_Phone']
        
        # Priority: Practice Phone > Owner Phone > Primary Phone
        best_phone = practice_phone or owner_phone or primary_phone or 'N/A'
        
        # Get practice name
        practice_name = get_best_practice_name(row)
        
        # Get owner/contact info
        owner_info = get_owner_info(row)
        
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
        for field in ['Practice_Address_Line1', 'Practice_City', 'Practice_State']:
            if pd.notna(row.get(field)):
                address_parts.append(str(row[field]))
        address = ', '.join(address_parts) if address_parts else 'N/A'
        
        # Get EIN for business info
        ein = str(row.get('EIN', '')).strip() if pd.notna(row.get('EIN')) else None
        
        lead_data = {
            "id": len(hot_leads_data) + 1,
            "priority": priority,
            "category": category,
            "practice_name": practice_name,
            "owner_name": owner_info,
            "providers": int(row.get('Practice_Group_Size', 1)),
            "specialties": str(row.get('Primary_Specialty', 'N/A')),
            "practice_phone": format_phone(practice_phone) if practice_phone else None,
            "owner_phone": format_phone(owner_phone) if owner_phone else None,
            "best_phone": format_phone(best_phone) if best_phone != 'N/A' else 'N/A',
            "address": address,
            "zip": str(row.get('Practice_ZIP', 'N/A')),
            "ein": ein,
            "entity_type": str(row.get('Entity_Type', 'N/A')),
            "is_sole_proprietor": str(row.get('Is_Sole_Proprietor', 'N/A')),
            "population": 16903,
            "score": int(score),
            "npi": str(row.get('NPI', 'N/A'))
        }
        hot_leads_data.append(lead_data)
    
    with open('web/data/hot_leads.json', 'w') as f:
        json.dump(hot_leads_data, f, indent=2)
    print(f"✅ Updated hot_leads.json with {len(hot_leads_data)} comprehensive leads")
    
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
    print("COMPREHENSIVE WEB DASHBOARD UPDATE SUMMARY")
    print("="*60)
    print(f"Total Leads: {total_leads:,}")
    print(f"Hot Leads (Score ≥75): {hot_leads_count:,}")
    print(f"Podiatrist Groups: {podiatrist_count:,}")
    print(f"Wound Care Groups: {wound_care_count:,}")
    print(f"Mohs Surgery Groups: {mohs_count:,}")
    print(f"ZIP Codes Covered: {unique_zips:,}")
    print(f"Regions: {len(regions_data)}")
    print("\nNew Lead Data Includes:")
    print("✅ Practice Names (Legal/DBA/Organization)")
    print("✅ Owner/Contact Information") 
    print("✅ Multiple Phone Numbers (Practice/Owner)")
    print("✅ EIN & Business Entity Type")
    print("✅ NPI Numbers")
    print("✅ Sole Proprietor Status")
    print("\n✅ Web dashboard data updated successfully!")
    print("Ready for AWS Amplify deployment!")

if __name__ == "__main__":
    quick_update() 