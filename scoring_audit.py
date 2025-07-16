#!/usr/bin/env python3
"""
Scoring Audit - Compare Original vs Enhanced Lead Scoring

Analyzes the dramatic increase in A+ leads and provides recommendations
for recalibrating the enhanced scoring system.
"""

import pandas as pd
import numpy as np
from pathlib import Path

class ScoringAudit:
    def __init__(self):
        # Original scoring weights (from create_crm_export.py)
        self.original_weights = {
            'podiatrist_wound_care': 100,  # Highest value
            'podiatrist_multi': 80,        # High value  
            'wound_care_multi': 70,        # Medium-high value
            'mohs_surgery': 60,            # Special value
            'podiatrist_solo': 40,         # Medium value
            'wound_care_solo': 35,         # Medium-low value
            'primary_care_multi': 25,      # Lower value
            'primary_care_solo': 15        # Lowest value
        }
        
        # Original thresholds
        self.original_thresholds = {
            'A+ Hot Lead': 90,
            'A High Priority': 70,
            'B Medium Priority': 50,
            'C Low Priority': 30,
            'D Nurture': 0
        }

    def calculate_original_score(self, row):
        """Calculate score using original methodology"""
        specialties = str(row.get('Primary_Specialty', '')).lower()
        provider_count = row.get('Practice_Group_Size', 1)
        population = row.get('TotalPopulation', 15000)
        
        # Determine specialty category
        specialty_count = 1  # Simplified for audit
        if 'podiatrist' in specialties and 'wound care' in specialties:
            base_score = self.original_weights['podiatrist_wound_care']
        elif 'podiatrist' in specialties and specialty_count >= 3:
            base_score = self.original_weights['podiatrist_multi']
        elif 'wound care' in specialties and specialty_count >= 3:
            base_score = self.original_weights['wound_care_multi']
        elif 'mohs' in specialties:
            base_score = self.original_weights['mohs_surgery']
        elif 'podiatrist' in specialties:
            base_score = self.original_weights['podiatrist_solo']
        elif 'wound care' in specialties:
            base_score = self.original_weights['wound_care_solo']
        elif specialty_count >= 3:
            base_score = self.original_weights['primary_care_multi']
        else:
            base_score = self.original_weights['primary_care_solo']
        
        # Size multiplier (prefer smaller, more manageable groups)
        size_multiplier = {1: 1.0, 2: 1.1, 3: 1.2, 4: 1.1, 5: 1.0}.get(provider_count, 0.9)
        
        # Population bonus (prefer underserved areas)
        if pd.notna(population):
            if population < 10000:
                pop_bonus = 10  # Small town bonus
            elif population < 25000:
                pop_bonus = 5   # Medium town bonus
            else:
                pop_bonus = 0
        else:
            pop_bonus = 0
            
        final_score = int(base_score * size_multiplier + pop_bonus)
        return min(final_score, 100)  # Cap at 100

    def calculate_enhanced_score(self, row):
        """Calculate score using enhanced methodology (from quick_web_update.py)"""
        specialties = str(row.get('Primary_Specialty', '')).lower()
        score = 0
        
        # Base specialty scoring (increased values)
        if 'podiatrist' in specialties:
            score += 50
        if 'wound care' in specialties:
            score += 45
        if 'mohs' in specialties:
            score += 40
        if 'family medicine' in specialties:
            score += 25
        if 'internal medicine' in specialties:
            score += 20
        
        # Group size bonus (smaller is better for targeting)
        group_size = row.get('Practice_Group_Size', 1)
        if group_size == 1:
            score += 25
        elif group_size == 2:
            score += 20
        elif 3 <= group_size <= 5:
            score += 15
        
        # Phone availability bonus
        practice_phone = row.get('Practice_Phone', '')
        owner_phone = row.get('Owner_Phone', '')
        if pd.notna(practice_phone) and practice_phone:
            score += 10
        if pd.notna(owner_phone) and owner_phone:
            score += 10
        
        # EIN bonus (indicates established business)
        ein = row.get('EIN', '')
        if pd.notna(ein) and ein and ein != '<UNAVAIL>':
            score += 10
        
        # Sole proprietor bonus (easier to contact decision maker)
        is_sole_prop = row.get('Is_Sole_Proprietor', False)
        if is_sole_prop:
            score += 5
        
        return min(score, 100)

    def categorize_score(self, score, system='original'):
        """Categorize score into priority levels"""
        if system == 'original':
            thresholds = self.original_thresholds
        else:
            # Enhanced system uses same thresholds but different scoring
            thresholds = self.original_thresholds
            
        if score >= thresholds['A+ Hot Lead']:
            return 'A+ Priority'
        elif score >= thresholds['A High Priority']:
            return 'A Priority'
        elif score >= thresholds['B Medium Priority']:
            return 'B+ Priority'
        elif score >= thresholds['C Low Priority']:
            return 'B Priority'
        else:
            return 'C Priority'

    def run_audit(self):
        """Run comprehensive scoring audit"""
        print("🔍 SCORING SYSTEM AUDIT")
        print("=" * 50)
        
        # Load enhanced leads data
        try:
            df = pd.read_excel('comprehensive_rural_physician_leads.xlsx')
            print(f"✅ Loaded {len(df):,} enhanced leads")
        except FileNotFoundError:
            print("❌ Enhanced leads file not found")
            return
        
        # Sample for performance (first 10,000 records)
        sample_size = min(10000, len(df))
        df_sample = df.head(sample_size).copy()
        print(f"📊 Analyzing sample of {sample_size:,} leads")
        print()
        
        # Calculate both scoring systems
        df_sample['Original_Score'] = df_sample.apply(self.calculate_original_score, axis=1)
        df_sample['Enhanced_Score'] = df_sample.apply(self.calculate_enhanced_score, axis=1)
        
        df_sample['Original_Priority'] = df_sample['Original_Score'].apply(
            lambda x: self.categorize_score(x, 'original')
        )
        df_sample['Enhanced_Priority'] = df_sample['Enhanced_Score'].apply(
            lambda x: self.categorize_score(x, 'enhanced')
        )
        
        # Score distribution analysis
        print("📈 SCORE DISTRIBUTION COMPARISON")
        print("-" * 40)
        
        orig_stats = df_sample['Original_Score'].describe()
        enh_stats = df_sample['Enhanced_Score'].describe()
        
        print(f"Original System:")
        print(f"  • Mean Score: {orig_stats['mean']:.1f}")
        print(f"  • Median Score: {orig_stats['50%']:.1f}")
        print(f"  • Max Score: {orig_stats['max']:.1f}")
        print()
        print(f"Enhanced System:")
        print(f"  • Mean Score: {enh_stats['mean']:.1f}")
        print(f"  • Median Score: {enh_stats['50%']:.1f}")
        print(f"  • Max Score: {enh_stats['max']:.1f}")
        print()
        
        score_increase = ((enh_stats['mean'] - orig_stats['mean']) / orig_stats['mean']) * 100
        print(f"🚨 Average Score Increase: +{score_increase:.1f}%")
        print()
        
        # Priority distribution comparison
        print("🎯 PRIORITY DISTRIBUTION COMPARISON")
        print("-" * 40)
        
        orig_counts = df_sample['Original_Priority'].value_counts()
        enh_counts = df_sample['Enhanced_Priority'].value_counts()
        
        priority_order = ['A+ Priority', 'A Priority', 'B+ Priority', 'B Priority', 'C Priority']
        
        for priority in priority_order:
            orig_count = orig_counts.get(priority, 0)
            enh_count = enh_counts.get(priority, 0)
            orig_pct = (orig_count / len(df_sample)) * 100
            enh_pct = (enh_count / len(df_sample)) * 100
            
            change = ((enh_count - orig_count) / max(orig_count, 1)) * 100
            print(f"{priority}:")
            print(f"  • Original: {orig_count:,} ({orig_pct:.1f}%)")
            print(f"  • Enhanced: {enh_count:,} ({enh_pct:.1f}%)")
            print(f"  • Change: {change:+.0f}%")
            print()
        
        # Specific examples of score inflation
        print("🔍 SCORE INFLATION EXAMPLES")
        print("-" * 40)
        
        # Find leads that moved from B/C to A+
        score_jumpers = df_sample[
            (df_sample['Original_Priority'].isin(['B+ Priority', 'B Priority', 'C Priority'])) &
            (df_sample['Enhanced_Priority'] == 'A+ Priority')
        ].head(5)
        
        for idx, row in score_jumpers.iterrows():
            print(f"Example {idx+1}:")
            print(f"  • Specialty: {row['Primary_Specialty']}")
            print(f"  • Group Size: {row['Practice_Group_Size']} providers")
            print(f"  • Original Score: {row['Original_Score']} ({row['Original_Priority']})")
            print(f"  • Enhanced Score: {row['Enhanced_Score']} ({row['Enhanced_Priority']})")
            print(f"  • Has EIN: {pd.notna(row.get('EIN')) and row.get('EIN') != '<UNAVAIL>'}")
            print(f"  • Has Practice Phone: {pd.notna(row.get('Practice_Phone'))}")
            print(f"  • Has Owner Phone: {pd.notna(row.get('Owner_Phone'))}")
            print()
        
        # Recommendations
        print("💡 SCORING RECALIBRATION RECOMMENDATIONS")
        print("-" * 40)
        print("1. **Reduce Base Specialty Scores**: Current values too high")
        print("   • Podiatrist: 50 → 30 points")
        print("   • Wound Care: 45 → 25 points")
        print("   • Mohs Surgery: 40 → 35 points")
        print()
        print("2. **Reduce Data Availability Bonuses**: Having data ≠ better prospect")
        print("   • Phone bonuses: 10 → 5 points each")
        print("   • EIN bonus: 10 → 5 points")
        print("   • Sole proprietor: 5 → 3 points")
        print()
        print("3. **Maintain Original Priority Thresholds**:")
        print("   • A+ Priority: ≥90 points (exclusive)")
        print("   • A Priority: 70-89 points")
        print("   • B+ Priority: 50-69 points")
        print()
        print("4. **Implement Specialty Combinations**:")
        print("   • Podiatrist + Wound Care: 80 base points")
        print("   • Multi-specialty groups: +10 bonus")
        print()
        
        return df_sample

if __name__ == "__main__":
    auditor = ScoringAudit()
    results = auditor.run_audit() 