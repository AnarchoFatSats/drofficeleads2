#!/usr/bin/env python3
"""
Create detailed lead breakdown and priority analysis
"""

import pandas as pd
import numpy as np

def create_detailed_breakdown():
    # Load the results
    df = pd.read_csv('rural_physician_groups.csv')
    
    print("🎯 COMPREHENSIVE RURAL PHYSICIAN LEAD BREAKDOWN")
    print("=" * 65)
    print(f"Analysis Date: July 15, 2025")
    print(f"Data Source: NPPES + RUCA + PLACES + Medicare")
    print(f"Total Leads Identified: {len(df):,}")
    print()
    
    # High-Priority Lead Analysis
    print("🔥 HIGH-PRIORITY PROSPECTS")
    print("-" * 40)
    
    # Podiatrist + Wound Care (highest value)
    pod_wound = df[
        df['Specialties'].str.contains('Podiatrist', na=False) & 
        df['Specialties'].str.contains('Wound Care', na=False)
    ]
    print(f"• Podiatrist + Wound Care: {len(pod_wound)} groups")
    
    # Multi-specialty Podiatrist groups
    pod_multi = df[
        df['Specialties'].str.contains('Podiatrist', na=False) & 
        (df['Specialty_Count'] >= 3) &
        ~df.index.isin(pod_wound.index)
    ]
    print(f"• Multi-Specialty Podiatrist: {len(pod_multi)} groups")
    
    # Multi-specialty Wound Care groups  
    wound_multi = df[
        df['Specialties'].str.contains('Wound Care', na=False) & 
        (df['Specialty_Count'] >= 3) &
        ~df.index.isin(pod_wound.index) &
        ~df.index.isin(pod_multi.index)
    ]
    print(f"• Multi-Specialty Wound Care: {len(wound_multi)} groups")
    
    # Mohs Surgery (rare specialty)
    mohs = df[
        df['Specialties'].str.contains('Mohs Surgery', na=False) &
        ~df.index.isin(pod_wound.index) &
        ~df.index.isin(pod_multi.index) &
        ~df.index.isin(wound_multi.index)
    ]
    print(f"• Mohs Surgery Specialists: {len(mohs)} groups")
    
    total_priority = len(pod_wound) + len(pod_multi) + len(wound_multi) + len(mohs)
    print(f"\nTOTAL HIGH-PRIORITY PROSPECTS: {total_priority}")
    print()
    
    # Group Size Analysis
    print("👥 GROUP SIZE DISTRIBUTION")
    print("-" * 30)
    size_counts = df['Provider_Count'].value_counts().sort_index()
    for size, count in size_counts.items():
        percentage = (count / len(df)) * 100
        print(f"• {size} provider{'s' if size > 1 else ''}: {count:,} ({percentage:.1f}%)")
    print()
    
    # Geographic Distribution
    print("🗺️  GEOGRAPHIC COVERAGE")
    print("-" * 25)
    
    # By state (top 15)
    if 'Practice_ZIP' in df.columns:
        # Extract state from ZIP or address
        state_counts = {}
        for _, row in df.head(1000).iterrows():  # Sample for performance
            addr = str(row.get('Practice_Address', ''))
            # Basic state extraction from address
            import re
            state_match = re.search(r'\b([A-Z]{2})\b', addr)
            if state_match:
                state = state_match.group(1)
                state_counts[state] = state_counts.get(state, 0) + 1
        
        if state_counts:
            sorted_states = sorted(state_counts.items(), key=lambda x: x[1], reverse=True)
            print("Top States (sample):")
            for state, count in sorted_states[:10]:
                print(f"• {state}: {count} groups")
    
    print(f"• Rural ZIP codes covered: {df['ZIP_Code'].nunique():,}")
    print()
    
    # Specialty Deep Dive
    print("🩺 SPECIALTY BREAKDOWN")
    print("-" * 25)
    
    all_specialties = []
    for specialties in df['Specialties'].dropna():
        all_specialties.extend([s.strip() for s in specialties.split(',')])
    
    from collections import Counter
    specialty_counts = Counter(all_specialties)
    
    print("All Target Specialties:")
    for specialty, count in specialty_counts.most_common():
        percentage = (count / len(df)) * 100
        print(f"• {specialty}: {count:,} ({percentage:.1f}%)")
    print()
    
    # Contact Information Quality
    print("📞 CONTACT DATA QUALITY")
    print("-" * 25)
    
    phone_available = df['Phone_Number'].notna().sum()
    phone_percent = (phone_available / len(df)) * 100
    print(f"• Phone numbers: {phone_available:,} ({phone_percent:.1f}%)")
    
    # Market Size Analysis
    if 'TotalPopulation' in df.columns:
        pop_data = df['TotalPopulation'].dropna()
        if len(pop_data) > 0:
            print(f"• Population data: {len(pop_data):,} ({len(pop_data)/len(df)*100:.1f}%)")
            print(f"• Avg market population: {pop_data.mean():,.0f}")
            print(f"• Small towns (<10K): {(pop_data < 10000).sum():,}")
            print(f"• Medium towns (10K-25K): {((pop_data >= 10000) & (pop_data < 25000)).sum():,}")
            print(f"• Larger towns (25K+): {(pop_data >= 25000).sum():,}")
    print()
    
    # Revenue Potential Estimates
    print("💰 REVENUE OPPORTUNITY")
    print("-" * 25)
    
    # Estimate based on priority tiers
    high_value_count = len(pod_wound) + len(pod_multi)
    medium_value_count = len(wound_multi) + len(mohs)
    
    high_value_revenue = high_value_count * 45000  # $45K avg per high-value group
    medium_value_revenue = medium_value_count * 25000  # $25K avg per medium-value group
    low_value_revenue = (len(df) - high_value_count - medium_value_count) * 12000  # $12K avg
    
    total_opportunity = high_value_revenue + medium_value_revenue + low_value_revenue
    
    print(f"• High-value prospects: {high_value_count:,} × $45K = ${high_value_revenue:,}")
    print(f"• Medium-value prospects: {medium_value_count:,} × $25K = ${medium_value_revenue:,}")
    print(f"• Standard prospects: {len(df) - high_value_count - medium_value_count:,} × $12K = ${low_value_revenue:,}")
    print(f"• TOTAL MARKET OPPORTUNITY: ${total_opportunity:,}")
    print()
    
    # Next Steps Recommendations
    print("🚀 RECOMMENDED NEXT STEPS")
    print("-" * 30)
    print("1. START WITH HOT LEADS:")
    print(f"   • {len(pod_wound)} Podiatrist + Wound Care groups")
    print(f"   • {len(pod_multi)} Multi-specialty Podiatrist groups")
    print()
    print("2. TERRITORY PLANNING:")
    print("   • Use CRM export for geographic clustering")
    print("   • Assign reps by state/region")
    print()
    print("3. OUTREACH STRATEGY:")
    print("   • Call high-priority groups first")
    print("   • Mention their multi-specialty focus")
    print("   • Use population data for market context")
    print()
    print("4. TRACKING & FOLLOW-UP:")
    print("   • Use CRM lead scoring system")
    print("   • Track conversion rates by priority tier")
    print("   • Schedule systematic follow-ups")
    
    return df

if __name__ == "__main__":
    create_detailed_breakdown() 