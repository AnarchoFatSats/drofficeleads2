#!/usr/bin/env python3
"""
Create web-friendly data exports for AWS Amplify deployment
"""

import pandas as pd
import json
import os
from datetime import datetime

def create_web_data():
    print("🌐 Creating web-friendly data exports...")
    
    # Create web directory
    os.makedirs('web', exist_ok=True)
    os.makedirs('web/data', exist_ok=True)
    
    # Load the main dataset
    df = pd.read_csv('rural_physician_groups.csv')
    
    # Create high-priority leads for immediate display
    hot_leads = []
    
    # Podiatrist + Wound Care (highest priority)
    pod_wound = df[
        df['Specialties'].str.contains('Podiatrist', na=False) & 
        df['Specialties'].str.contains('Wound Care', na=False)
    ]
    
    # Multi-specialty Podiatrist groups
    pod_multi = df[
        df['Specialties'].str.contains('Podiatrist', na=False) & 
        (df['Specialty_Count'] >= 3) &
        ~df.index.isin(pod_wound.index)
    ]
    
    # Multi-specialty Wound Care groups
    wound_multi = df[
        df['Specialties'].str.contains('Wound Care', na=False) & 
        (df['Specialty_Count'] >= 3) &
        ~df.index.isin(pod_wound.index) &
        ~df.index.isin(pod_multi.index)
    ]
    
    # Mohs Surgery specialists
    mohs = df[df['Specialties'].str.contains('Mohs Surgery', na=False)]
    
    # Combine and format for web
    priority_groups = [
        ('A+ Priority', 'Podiatrist + Wound Care', pod_wound),
        ('A Priority', 'Multi-Specialty Podiatrist', pod_multi), 
        ('B Priority', 'Multi-Specialty Wound Care', wound_multi),
        ('B Priority', 'Mohs Surgery Specialists', mohs)
    ]
    
    for priority, category, group_df in priority_groups:
        for _, row in group_df.head(20).iterrows():  # Limit for web performance
            lead = {
                'id': len(hot_leads) + 1,
                'priority': priority,
                'category': category,
                'providers': int(row['Provider_Count']),
                'specialties': row['Specialties'],
                'phone': clean_phone(row.get('Phone_Number', '')),
                'address': clean_address(row.get('Practice_Address', '')),
                'zip': str(row.get('ZIP_Code', '')),
                'population': int(row.get('TotalPopulation', 0)) if pd.notna(row.get('TotalPopulation')) else 0,
                'score': calculate_web_score(row)
            }
            hot_leads.append(lead)
    
    # Sort by score
    hot_leads.sort(key=lambda x: x['score'], reverse=True)
    
    # Create summary statistics
    summary = {
        'total_leads': len(df),
        'hot_leads': len(hot_leads),
        'podiatrist_groups': len(df[df['Specialties'].str.contains('Podiatrist', na=False)]),
        'wound_care_groups': len(df[df['Specialties'].str.contains('Wound Care', na=False)]),
        'mohs_groups': len(df[df['Specialties'].str.contains('Mohs Surgery', na=False)]),
        'zip_codes_covered': df['ZIP_Code'].nunique(),
        'avg_population': int(df['TotalPopulation'].mean()) if df['TotalPopulation'].notna().any() else 0,
        'last_updated': datetime.now().isoformat()
    }
    
    # Create regional breakdown
    regions = {}
    for _, row in df.head(1000).iterrows():  # Sample for performance
        addr = str(row.get('Practice_Address', ''))
        import re
        state_match = re.search(r'\b([A-Z]{2})\b', addr)
        if state_match:
            state = state_match.group(1)
            if state not in regions:
                regions[state] = {'count': 0, 'leads': []}
            regions[state]['count'] += 1
    
    # Save data files
    with open('web/data/hot_leads.json', 'w') as f:
        json.dump(hot_leads, f, indent=2)
    
    with open('web/data/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    with open('web/data/regions.json', 'w') as f:
        json.dump(regions, f, indent=2)
    
    print(f"✅ Created web data files:")
    print(f"   • hot_leads.json: {len(hot_leads)} priority leads")
    print(f"   • summary.json: Key metrics")
    print(f"   • regions.json: Geographic data")

def clean_phone(phone):
    if pd.isna(phone) or phone == '':
        return ''
    import re
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return str(phone)

def clean_address(address):
    if pd.isna(address):
        return ''
    # Simplify address for web display
    addr = str(address).replace(' SUITE', ', Suite').replace(' STE', ', Ste')
    return addr[:100] + '...' if len(addr) > 100 else addr

def calculate_web_score(row):
    """Calculate a simple 1-100 score for web display"""
    specialties = str(row['Specialties']).lower()
    providers = row['Provider_Count']
    
    if 'podiatrist' in specialties and 'wound care' in specialties:
        base = 95
    elif 'podiatrist' in specialties and row['Specialty_Count'] >= 3:
        base = 85
    elif 'wound care' in specialties and row['Specialty_Count'] >= 3:
        base = 75
    elif 'mohs surgery' in specialties:
        base = 70
    else:
        base = 50
    
    # Adjust for group size
    size_bonus = min(providers * 2, 10)
    return min(base + size_bonus, 100)

if __name__ == "__main__":
    create_web_data() 