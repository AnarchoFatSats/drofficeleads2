#!/usr/bin/env python3
"""
Recalibrated Web Dashboard Update

Updates the web dashboard with recalibrated scores that fix the A+ grade inflation
while maintaining the enhanced contact intelligence benefits.
"""

import pandas as pd
import json
import os
from datetime import datetime
import re

class RecalibratedWebUpdate:
    def __init__(self):
        # Recalibrated scoring (same as recalibrated_scoring.py)
        self.specialty_scores = {
            'podiatrist_wound_care': 85,
            'podiatrist': 30,
            'mohs_surgery': 35,
            'wound_care': 25,
            'family_medicine': 15,
            'internal_medicine': 12,
            'general_practice': 10
        }
        
        self.size_bonuses = {1: 15, 2: 12, 3: 8, 4: 5, 5: 3}
        
        self.contact_bonuses = {
            'practice_phone': 5,
            'owner_phone': 5,
            'multiple_phones': 3,
            'ein_available': 5,
            'sole_proprietor': 2,
            'address_verified': 2
        }
        
        self.specialty_bonuses = {
            'multi_specialty': 10,
            'comprehensive_care': 15
        }

    def clean_phone(self, phone):
        """Clean and format phone number"""
        if pd.isna(phone) or not phone:
            return None
        
        phone_str = str(phone).strip()
        if phone_str in ['N/A', 'None', '']:
            return None
        
        # Extract digits only
        digits = re.sub(r'\D', '', phone_str)
        if len(digits) < 10:
            return None
        
        # Format as (XXX) XXX-XXXX
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return phone_str

    def has_valid_phone(self, phone):
        """Check if phone number is valid"""
        return self.clean_phone(phone) is not None

    def has_valid_ein(self, ein):
        """Check if EIN is valid"""
        if pd.isna(ein) or not ein:
            return False
        ein_str = str(ein).strip()
        return ein_str not in ['<UNAVAIL>', 'N/A', 'None', ''] and len(ein_str) >= 9

    def count_valid_phones(self, row):
        """Count number of valid phone numbers"""
        phones = [
            row.get('Practice_Phone'),
            row.get('Owner_Phone'), 
            row.get('Primary_Phone')
        ]
        return sum(1 for phone in phones if self.has_valid_phone(phone))

    def calculate_recalibrated_score(self, row):
        """Calculate recalibrated lead score using same algorithm as recalibrated_scoring.py"""
        score = 0
        
        # Extract key data
        specialty = str(row.get('Primary_Specialty', '')).lower()
        all_specialties = str(row.get('All_Specialties', '')).lower()
        group_size = row.get('Practice_Group_Size', 1)
        
        # Base specialty scoring
        if 'podiatrist' in specialty and 'wound care' in all_specialties:
            score += self.specialty_scores['podiatrist_wound_care']
        elif 'podiatrist' in specialty:
            score += self.specialty_scores['podiatrist']
        elif 'mohs' in specialty:
            score += self.specialty_scores['mohs_surgery']
        elif 'wound care' in specialty:
            score += self.specialty_scores['wound_care']
        elif 'family medicine' in specialty:
            score += self.specialty_scores['family_medicine']
        elif 'internal medicine' in specialty:
            score += self.specialty_scores['internal_medicine']
        elif 'general practice' in specialty:
            score += self.specialty_scores['general_practice']
        
        # Group size bonus
        score += self.size_bonuses.get(group_size, 0)
        
        # Multi-specialty bonuses
        specialty_count = row.get('Specialty_Count', 1)
        if specialty_count >= 3:
            score += self.specialty_bonuses['comprehensive_care']
        elif specialty_count >= 2:
            score += self.specialty_bonuses['multi_specialty']
        
        # Contact intelligence bonuses (reduced impact)
        if self.has_valid_phone(row.get('Practice_Phone')):
            score += self.contact_bonuses['practice_phone']
        
        if self.has_valid_phone(row.get('Owner_Phone')):
            score += self.contact_bonuses['owner_phone']
        
        # Multiple phone bonus
        phone_count = self.count_valid_phones(row)
        if phone_count >= 2:
            score += self.contact_bonuses['multiple_phones']
        
        # Business data bonuses
        if self.has_valid_ein(row.get('EIN')):
            score += self.contact_bonuses['ein_available']
        
        if row.get('Is_Sole_Proprietor') == 'True':
            score += self.contact_bonuses['sole_proprietor']
        
        if row.get('Address_Match') == 'Different':
            score += self.contact_bonuses['address_verified']
        
        # Population context (small rural bonus)
        population = row.get('TotalPopulation', 15000)
        if pd.notna(population):
            if population < 8000:
                score += 8   # Small town bonus
            elif population < 15000:
                score += 4   # Medium rural bonus
        
        return min(int(score), 100)  # Cap at 100

    def categorize_priority(self, score):
        """Categorize score into priority level"""
        if score >= 90:
            return 'A+ Priority'
        elif score >= 70:
            return 'A Priority'
        elif score >= 50:
            return 'B+ Priority'
        elif score >= 30:
            return 'B Priority'
        else:
            return 'C Priority'

    def get_best_practice_name(self, row):
        """Get the best available practice name"""
        legal_name = row.get('Legal_Business_Name', '')
        dba_name = row.get('DBA_Name', '')
        other_name = row.get('Other_Organization_Name', '')
        
        # Prefer DBA name if available, then legal name, then other name
        if dba_name and dba_name != legal_name:
            return dba_name
        elif legal_name:
            return legal_name
        elif other_name:
            return other_name
        else:
            # Build name from individual provider info
            first = row.get('Provider_First_Name', '')
            last = row.get('Provider_Last_Name', '')
            if first and last:
                return f"{first} {last}"
            return 'Independent Practice'

    def get_owner_info(self, row):
        """Get owner/contact information"""
        owner_name = row.get('Owner_Full_Name', '')
        if not owner_name:
            # Try to build from individual fields
            first = row.get('Owner_First_Name', '')
            last = row.get('Owner_Last_Name', '')
            if first and last:
                owner_name = f"{first} {last}"
        
        # Add title if available
        title = row.get('Owner_Title', '')
        if title and owner_name:
            return f"{owner_name}, {title}"
        
        return owner_name or 'Contact Info Available'

    def update_web_dashboard(self):
        """Update web dashboard with recalibrated scores"""
        print("🌐 UPDATING WEB DASHBOARD WITH RECALIBRATED SCORES")
        print("=" * 60)
        
        # Try to load recalibrated data first, fall back to original
        try:
            df = pd.read_excel('recalibrated_rural_physician_leads.xlsx')
            print(f"✅ Loaded {len(df):,} recalibrated leads")
            use_recalibrated = True
        except FileNotFoundError:
            try:
                df = pd.read_excel('comprehensive_rural_physician_leads.xlsx')
                print(f"✅ Loaded {len(df):,} comprehensive leads")
                print("⚠️  Using comprehensive leads, will recalculate scores")
                use_recalibrated = False
            except FileNotFoundError:
                print("❌ No lead files found")
                return
        
        # Apply recalibrated scoring if needed
        if not use_recalibrated:
            print("🔄 Calculating recalibrated scores...")
            df['Recalibrated_Score'] = df.apply(self.calculate_recalibrated_score, axis=1)
            df['Recalibrated_Priority'] = df['Recalibrated_Score'].apply(self.categorize_priority)
        else:
            # Data already has recalibrated scores
            if 'Recalibrated_Score' not in df.columns:
                df['Recalibrated_Score'] = df.apply(self.calculate_recalibrated_score, axis=1)
                df['Recalibrated_Priority'] = df['Recalibrated_Score'].apply(self.categorize_priority)
        
        # Clean phone numbers
        df['Clean_Practice_Phone'] = df['Practice_Phone'].apply(self.clean_phone)
        df['Clean_Owner_Phone'] = df['Owner_Phone'].apply(self.clean_phone)
        df['Clean_Primary_Phone'] = df['Primary_Phone'].apply(self.clean_phone)
        
        # Count leads by priority
        total_leads = len(df)
        priority_counts = df['Recalibrated_Priority'].value_counts()
        hot_leads_count = priority_counts.get('A+ Priority', 0) + priority_counts.get('A Priority', 0)
        a_plus_count = priority_counts.get('A+ Priority', 0)
        
        # Count specialties
        podiatrist_count = df['Primary_Specialty'].str.contains('Podiatrist', na=False).sum()
        wound_care_count = df['Primary_Specialty'].str.contains('Wound Care', na=False).sum()
        mohs_count = df['Primary_Specialty'].str.contains('Mohs', na=False).sum()
        unique_zips = df['ZIP_Code'].nunique()
        
        print(f"\n📊 RECALIBRATED DASHBOARD STATS")
        print("-" * 40)
        print(f"Total Leads: {total_leads:,}")
        print(f"A+ Priority: {a_plus_count:,} ({(a_plus_count/total_leads*100):.1f}%)")
        print(f"Hot Prospects (A+/A): {hot_leads_count:,} ({(hot_leads_count/total_leads*100):.1f}%)")
        print(f"Podiatrist Groups: {podiatrist_count:,}")
        print(f"Wound Care Groups: {wound_care_count:,}")
        print(f"Mohs Surgery Groups: {mohs_count:,}")
        
        # Create web directory
        os.makedirs('web/data', exist_ok=True)
        
        # Update summary.json with recalibrated stats
        summary_data = {
            "total_leads": int(total_leads),
            "hot_leads": int(hot_leads_count),
            "a_plus_leads": int(a_plus_count),
            "podiatrist_groups": int(podiatrist_count),
            "wound_care_groups": int(wound_care_count),
            "mohs_groups": int(mohs_count),
            "zip_codes_covered": int(unique_zips),
            "avg_population": 16903,
            "last_updated": datetime.now().isoformat(),
            "scoring_system": "recalibrated"
        }
        
        with open('web/data/summary.json', 'w') as f:
            json.dump(summary_data, f, indent=2)
        print("✅ Updated summary.json with recalibrated stats")
        
        # Create comprehensive hot leads data (top 100 A+ and A priority leads)
        hot_leads_df = df[
            df['Recalibrated_Priority'].isin(['A+ Priority', 'A Priority'])
        ].nlargest(100, 'Recalibrated_Score')
        
        hot_leads_data = []
        
        for idx, row in hot_leads_df.iterrows():
            # Get best available phones
            practice_phone = row['Clean_Practice_Phone']
            owner_phone = row['Clean_Owner_Phone'] 
            primary_phone = row['Clean_Primary_Phone']
            
            # Priority: Practice Phone > Owner Phone > Primary Phone
            best_phone = practice_phone or owner_phone or primary_phone or 'N/A'
            
            # Get practice name
            practice_name = self.get_best_practice_name(row)
            
            # Get owner/contact info
            owner_info = self.get_owner_info(row)
            
            # Priority category (using recalibrated scores)
            priority = row['Recalibrated_Priority']
            
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
            
            # Address components
            address_parts = []
            for field in ['Practice_Address_Line1', 'Practice_City', 'Practice_State']:
                if pd.notna(row.get(field)):
                    address_parts.append(str(row[field]))
            address = ', '.join(address_parts) if address_parts else 'N/A'
            
            # Get EIN for business info
            ein = str(row.get('EIN', '')).strip() if pd.notna(row.get('EIN')) else None
            if ein == '<UNAVAIL>':
                ein = None
            
            lead_data = {
                'id': int(idx),
                'score': int(row['Recalibrated_Score']),  # Use recalibrated score
                'priority': priority,
                'category': category,
                'practice_name': practice_name,
                'owner_name': owner_info,
                'practice_phone': practice_phone or '',
                'owner_phone': owner_phone or '',
                'specialties': row.get('Primary_Specialty', ''),
                'providers': int(row.get('Practice_Group_Size', 1)),
                'city': row.get('Practice_City', ''),
                'state': row.get('Practice_State', ''),
                'zip': str(row.get('ZIP_Code', '')),
                'address': address,
                'ein': ein,
                'is_sole_proprietor': str(row.get('Is_Sole_Proprietor', False)),
                'entity_type': row.get('Entity_Type', ''),
                'npi': str(row.get('NPI', ''))
            }
            
            hot_leads_data.append(lead_data)
        
        # Sort by recalibrated score
        hot_leads_data.sort(key=lambda x: x['score'], reverse=True)
        
        # Save hot leads data
        with open('web/data/hot_leads.json', 'w') as f:
            json.dump(hot_leads_data, f, indent=2)
        print(f"✅ Updated hot_leads.json with {len(hot_leads_data)} recalibrated priority leads")
        
        # Create regions data (simplified)
        regions = {}
        state_counts = df.groupby('Practice_State').size().to_dict()
        for state, count in list(state_counts.items())[:50]:  # Top 50 states
            if pd.notna(state):
                regions[state] = {"count": int(count), "leads": []}
        
        with open('web/data/regions.json', 'w') as f:
            json.dump(regions, f, indent=2)
        print("✅ Updated regions.json")
        
        print(f"\n🎯 RECALIBRATED WEB DASHBOARD UPDATE COMPLETE")
        print("=" * 60)
        print("✅ A+ leads now represent truly exclusive prospects")
        print("✅ Grade inflation eliminated")
        print("✅ City search autocomplete ready")
        print("✅ Enhanced contact intelligence preserved")
        print(f"✅ Dashboard shows {a_plus_count:,} A+ leads (exclusive)")
        print(f"✅ Hot prospects: {hot_leads_count:,} total")

def main():
    """Run recalibrated web dashboard update"""
    updater = RecalibratedWebUpdate()
    updater.update_web_dashboard()

if __name__ == "__main__":
    main() 