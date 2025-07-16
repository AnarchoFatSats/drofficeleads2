#!/usr/bin/env python3
"""
Create a prioritized contact list from rural physician analysis results
"""

import pandas as pd
import re

def create_priority_contact_list():
    # Load results
    results = pd.read_csv('rural_physician_groups.csv')
    
    print("🎯 PRIORITY RURAL PHYSICIAN GROUPS FOR OUTREACH")
    print("=" * 60)
    print(f"Total Groups Found: {len(results):,}")
    print()
    
    # Priority 1: Multi-specialty groups with Podiatrist + Wound Care
    priority1 = results[
        results['Specialties'].str.contains('Podiatrist', na=False) & 
        results['Specialties'].str.contains('Wound Care', na=False)
    ].copy()
    
    # Priority 2: Groups with Podiatrist + multiple other target specialties  
    priority2 = results[
        results['Specialties'].str.contains('Podiatrist', na=False) & 
        (results['Specialty_Count'] >= 3) &
        ~results.index.isin(priority1.index)
    ].copy()
    
    # Priority 3: Groups with Wound Care + multiple specialties
    priority3 = results[
        results['Specialties'].str.contains('Wound Care', na=False) & 
        (results['Specialty_Count'] >= 3) &
        ~results.index.isin(priority1.index) &
        ~results.index.isin(priority2.index)
    ].copy()
    
    # Priority 4: Mohs Surgery groups
    priority4 = results[
        results['Specialties'].str.contains('Mohs Surgery', na=False) &
        ~results.index.isin(priority1.index) &
        ~results.index.isin(priority2.index) &
        ~results.index.isin(priority3.index)
    ].copy()
    
    priorities = [
        ("🥇 HIGHEST PRIORITY: Podiatrist + Wound Care", priority1),
        ("🥈 HIGH PRIORITY: Podiatrist + Multi-Specialty", priority2),
        ("🥉 MEDIUM PRIORITY: Wound Care + Multi-Specialty", priority3),
        ("⭐ SPECIAL: Mohs Surgery Groups", priority4)
    ]
    
    for title, df in priorities:
        if len(df) == 0:
            continue
            
        print(f"\n{title}")
        print(f"Found {len(df)} groups")
        print("-" * 50)
        
        for idx, row in df.head(10).iterrows():
            # Extract contact info
            phone = row['Phone_Number'] if pd.notna(row['Phone_Number']) else 'No phone listed'
            zip_code = row['ZIP_Code']
            provider_count = row['Provider_Count']
            specialties = row['Specialties']
            
            # Parse address from Practice_Address field
            address = row['Practice_Address'] if pd.notna(row['Practice_Address']) else 'Address not available'
            
            # Clean up address format
            if isinstance(address, str):
                address_parts = address.split(' ')
                if len(address_parts) > 2:
                    # Format as: Street, City ZIP
                    try:
                        # Find ZIP in address to split city
                        zip_match = re.search(r'\b\d{5}\b', address)
                        if zip_match:
                            zip_pos = zip_match.start()
                            street_city = address[:zip_pos].strip()
                            # Split street and city better
                            parts = street_city.split(' ')
                            if len(parts) > 3:
                                street = ' '.join(parts[:-1])  
                                city = parts[-1]
                                address = f"{street}, {city} {zip_code}"
                    except:
                        pass
            
            print(f"📍 {address}")
            print(f"📞 {phone}")
            print(f"👥 {provider_count} provider{'s' if provider_count > 1 else ''}")
            print(f"🩺 {specialties}")
            
            # Add population context
            if pd.notna(row['TotalPopulation']):
                pop = int(row['TotalPopulation'])
                print(f"🏘️  Population: {pop:,}")
            
            print()
    
    # Summary statistics
    total_priority = len(priority1) + len(priority2) + len(priority3) + len(priority4)
    print(f"\n📊 OUTREACH SUMMARY")
    print("=" * 30)
    print(f"🎯 High-value prospects: {total_priority:,}")
    print(f"📞 Total contacts available: {results['Phone_Number'].notna().sum():,}")
    print(f"🌾 Rural markets covered: {results['ZIP_Code'].nunique():,} ZIP codes")

if __name__ == "__main__":
    create_priority_contact_list() 