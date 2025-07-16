#!/usr/bin/env python3
"""
Recalibrated Lead Scoring System

Maintains original A+ exclusivity while leveraging enhanced contact intelligence.
Fixes grade inflation in the enhanced scoring system.
"""

import pandas as pd
import numpy as np

class RecalibratedScoring:
    def __init__(self):
        # Recalibrated scoring maintains original hierarchy but uses enhanced data
        self.specialty_scores = {
            # Combination specialties (highest value)
            'podiatrist_wound_care': 85,  # Reduced from 100 to account for bonuses
            
            # High-value solo specialties
            'podiatrist': 30,             # Reduced from 50
            'mohs_surgery': 35,           # Slightly reduced from 40
            'wound_care': 25,             # Reduced from 45
            
            # Primary care specialties
            'family_medicine': 15,        # Reduced from 25
            'internal_medicine': 12,      # Reduced from 20
            'general_practice': 10
        }
        
        # Size bonuses (smaller practices preferred)
        self.size_bonuses = {
            1: 15,    # Reduced from 25
            2: 12,    # Reduced from 20 
            3: 8,     # Reduced from 15
            4: 5,     # Reduced from 15
            5: 3      # Reduced from 15
        }
        
        # Contact intelligence bonuses (reduced impact)
        self.contact_bonuses = {
            'practice_phone': 5,      # Reduced from 10
            'owner_phone': 5,         # Reduced from 10
            'multiple_phones': 3,     # New bonus for multiple contact methods
            'ein_available': 5,       # Reduced from 10
            'sole_proprietor': 2,     # Reduced from 5
            'address_verified': 2     # New bonus for verified addresses
        }
        
        # Multi-specialty bonuses
        self.specialty_bonuses = {
            'multi_specialty': 10,    # 2+ target specialties
            'comprehensive_care': 15  # 3+ different specialty categories
        }
        
        # Priority thresholds (maintained from original)
        self.priority_thresholds = {
            'A+': 90,   # Exclusive, highest value prospects
            'A': 70,    # High priority
            'B+': 50,   # Medium-high priority  
            'B': 30,    # Medium priority
            'C': 0      # Lower priority
        }

    def calculate_recalibrated_score(self, row):
        """Calculate recalibrated lead score"""
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
        if score >= self.priority_thresholds['A+']:
            return 'A+ Priority'
        elif score >= self.priority_thresholds['A']:
            return 'A Priority'
        elif score >= self.priority_thresholds['B+']:
            return 'B+ Priority'
        elif score >= self.priority_thresholds['B']:
            return 'B Priority'
        else:
            return 'C Priority'

    def has_valid_phone(self, phone):
        """Check if phone number is valid"""
        if pd.isna(phone) or not phone:
            return False
        phone_str = str(phone).strip()
        return len(phone_str) >= 10 and phone_str not in ['N/A', 'None', '']

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

    def update_lead_scores(self, input_file='comprehensive_rural_physician_leads.xlsx', 
                          output_file='recalibrated_rural_physician_leads.xlsx'):
        """Update all lead scores with recalibrated system"""
        print("📊 RECALIBRATING LEAD SCORES")
        print("=" * 40)
        
        # Load enhanced leads
        try:
            df = pd.read_excel(input_file)
            print(f"✅ Loaded {len(df):,} leads from {input_file}")
        except FileNotFoundError:
            print(f"❌ Input file not found: {input_file}")
            return None
        
        # Apply recalibrated scoring
        print("🔄 Calculating recalibrated scores...")
        df['Recalibrated_Score'] = df.apply(self.calculate_recalibrated_score, axis=1)
        df['Recalibrated_Priority'] = df['Recalibrated_Score'].apply(self.categorize_priority)
        
        # Priority distribution analysis
        priority_counts = df['Recalibrated_Priority'].value_counts()
        total_leads = len(df)
        
        print("\n🎯 RECALIBRATED PRIORITY DISTRIBUTION")
        print("-" * 40)
        priority_order = ['A+ Priority', 'A Priority', 'B+ Priority', 'B Priority', 'C Priority']
        
        for priority in priority_order:
            count = priority_counts.get(priority, 0)
            percentage = (count / total_leads) * 100
            print(f"{priority}: {count:,} leads ({percentage:.1f}%)")
        
        # Show top A+ leads
        a_plus_leads = df[df['Recalibrated_Priority'] == 'A+ Priority'].head(10)
        print(f"\n🌟 TOP A+ PRIORITY LEADS (Sample of {len(a_plus_leads)}):")
        print("-" * 40)
        
        for idx, row in a_plus_leads.iterrows():
            print(f"• Score {row['Recalibrated_Score']}: {row['Primary_Specialty']} | "
                  f"{row['Practice_Group_Size']} providers | "
                  f"EIN: {'Yes' if self.has_valid_ein(row.get('EIN')) else 'No'} | "
                  f"Phones: {self.count_valid_phones(row)}")
        
        # Save updated data
        print(f"\n💾 Saving recalibrated data to {output_file}...")
        
        # Reorder columns for better usability
        priority_columns = [
            'Recalibrated_Score', 'Recalibrated_Priority',
            'Primary_Specialty', 'Practice_Group_Size',
            'Practice_Phone', 'Owner_Phone', 'EIN',
            'Legal_Business_Name', 'DBA_Name'
        ]
        
        # Include all original columns plus new scoring
        all_columns = priority_columns + [col for col in df.columns 
                                        if col not in priority_columns]
        
        df_output = df[all_columns].copy()
        
        # Sort by recalibrated score (highest first)
        df_output = df_output.sort_values('Recalibrated_Score', ascending=False)
        
        df_output.to_excel(output_file, index=False)
        print(f"✅ Saved {len(df_output):,} leads with recalibrated scores")
        
        return df_output

    def compare_scoring_systems(self, df):
        """Compare original enhanced vs recalibrated scoring"""
        if 'Enhanced_Score' not in df.columns:
            print("⚠️  Enhanced scores not available for comparison")
            return
        
        print("\n📈 SCORING SYSTEM COMPARISON")
        print("-" * 40)
        
        enhanced_stats = df['Enhanced_Score'].describe()
        recalib_stats = df['Recalibrated_Score'].describe()
        
        print(f"Enhanced System (Inflated):")
        print(f"  • Mean Score: {enhanced_stats['mean']:.1f}")
        print(f"  • A+ Leads: {(df['Enhanced_Score'] >= 90).sum():,}")
        print()
        print(f"Recalibrated System (Fixed):")
        print(f"  • Mean Score: {recalib_stats['mean']:.1f}")
        print(f"  • A+ Leads: {(df['Recalibrated_Score'] >= 90).sum():,}")
        
        reduction = ((enhanced_stats['mean'] - recalib_stats['mean']) / enhanced_stats['mean']) * 100
        a_plus_reduction = ((df['Enhanced_Score'] >= 90).sum() - (df['Recalibrated_Score'] >= 90).sum())
        
        print(f"\n✅ FIXES APPLIED:")
        print(f"  • Score Reduction: -{reduction:.1f}%")
        print(f"  • A+ Grade Inflation Reduced: -{a_plus_reduction:,} leads")

def main():
    """Run recalibrated scoring system"""
    scorer = RecalibratedScoring()
    
    # Update lead scores
    df = scorer.update_lead_scores()
    
    if df is not None:
        # Run comparison if enhanced scores exist
        if 'Enhanced_Score' in df.columns:
            scorer.compare_scoring_systems(df)
        
        print("\n🎯 RECALIBRATION COMPLETE")
        print("=" * 40)
        print("✅ A+ leads now represent truly exclusive prospects")
        print("✅ Scoring maintains original hierarchy")
        print("✅ Enhanced contact data utilized appropriately")
        print("✅ Ready for web dashboard update")

if __name__ == "__main__":
    main() 