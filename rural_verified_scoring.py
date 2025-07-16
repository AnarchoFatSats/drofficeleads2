#!/usr/bin/env python3
"""
Rural-Verified Lead Scoring System

Ensures that ONLY rural leads can receive high priority scores (A+ and A).
Combines the recalibrated scoring logic with mandatory rural verification.

Key Features:
- Rural verification is a HARD REQUIREMENT for A+ and A scores
- Non-rural leads are automatically capped at B+ maximum
- Uses RUCA codes 4-10 for rural classification
- Maintains all other scoring logic from recalibrated system
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuralVerifiedScoring:
    def __init__(self):
        # Load rural ZIP codes on initialization
        self.rural_zips = self.load_rural_zips()
        
        # Recalibrated scoring (same as recalibrated_scoring.py)
        self.specialty_scores = {
            # Combination specialties (highest value)
            'podiatrist_wound_care': 85,  
            
            # High-value solo specialties
            'podiatrist': 30,             
            'mohs_surgery': 35,           
            'wound_care': 25,             
            
            # Primary care specialties
            'family_medicine': 15,        
            'internal_medicine': 12,      
            'general_practice': 10
        }
        
        # Size bonuses (smaller practices preferred)
        self.size_bonuses = {
            1: 15, 2: 12, 3: 8, 4: 5, 5: 3
        }
        
        # Contact intelligence bonuses (reduced impact)
        self.contact_bonuses = {
            'practice_phone': 5,
            'owner_phone': 5,
            'multiple_phones': 3,
            'ein_available': 5,
            'sole_proprietor': 2,
            'address_verified': 2
        }
        
        # Multi-specialty bonuses
        self.specialty_bonuses = {
            'multi_specialty': 10,
            'comprehensive_care': 15
        }
        
        # Rural-verified priority thresholds
        self.priority_thresholds = {
            'A+': 90,   # RURAL ONLY - Exclusive, highest value prospects
            'A': 70,    # RURAL ONLY - High priority
            'B+': 50,   # Available to non-rural (capped for non-rural)
            'B': 30,    # Medium priority
            'C': 0      # Lower priority
        }

    def load_rural_zips(self) -> set:
        """Load rural ZIP codes from RUCA data"""
        try:
            ruca_file = Path("RUCA2010zipcode.csv")
            if not ruca_file.exists():
                logger.warning("⚠️  RUCA file not found - using fallback rural detection")
                return set()
            
            ruca_df = pd.read_csv(ruca_file)
            
            # Debug: Print column names to see what we're working with
            logger.info(f"RUCA columns: {list(ruca_df.columns)}")
            
            # Handle the quoted column name issue more robustly
            zip_col = None
            for col in ruca_df.columns:
                if 'ZIP_CODE' in col:
                    zip_col = col
                    break
            
            if zip_col is None:
                logger.error("No ZIP_CODE column found in RUCA data")
                return set()
            
            # Rural codes: 4-10 (rural/small town)
            rural_df = ruca_df[ruca_df['RUCA2'].between(4, 10)]
            rural_zips = set(rural_df[zip_col].astype(str).str.strip("'\"").str.zfill(5))
            
            logger.info(f"✅ Loaded {len(rural_zips):,} rural ZIP codes from RUCA data")
            return rural_zips
            
        except Exception as e:
            logger.error(f"❌ Error loading RUCA data: {e}")
            return set()

    def is_rural_zip(self, zip_code) -> bool:
        """Verify if ZIP code is rural based on RUCA data"""
        # Handle NaN/None/empty values
        if pd.isna(zip_code) or not zip_code:
            return False
        
        # Convert to string and clean
        zip_str = str(zip_code).strip()
        if not zip_str or zip_str in ['nan', 'None', '']:
            return False
        
        if not self.rural_zips:
            # Fallback: Basic rural detection (rough approximation)
            if len(zip_str) < 5:
                return False
            # Exclude major urban ZIP prefixes
            urban_prefixes = ['100', '101', '102', '103', '104', '200', '201', '900', '901', '902']
            return zip_str[:3] not in urban_prefixes
        
        # Extract 5-digit ZIP
        zip5 = zip_str[:5].zfill(5) if len(zip_str) >= 5 else zip_str.zfill(5)
        return zip5 in self.rural_zips

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

    def calculate_base_score(self, row):
        """Calculate base score using recalibrated algorithm"""
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
        
        # Contact intelligence bonuses
        if self.has_valid_phone(row.get('Practice_Phone')):
            score += self.contact_bonuses['practice_phone']
        
        if self.has_valid_phone(row.get('Owner_Phone')):
            score += self.contact_bonuses['owner_phone']
        
        phone_count = self.count_valid_phones(row)
        if phone_count >= 2:
            score += self.contact_bonuses['multiple_phones']
        
        if self.has_valid_ein(row.get('EIN')):
            score += self.contact_bonuses['ein_available']
        
        if str(row.get('Business_Structure', '')).lower() == 'sole proprietor':
            score += self.contact_bonuses['sole_proprietor']
        
        if row.get('Address_Match') == 'Different':
            score += self.contact_bonuses['address_verified']
        
        return score

    def calculate_rural_verified_score(self, row):
        """Calculate score with mandatory rural verification"""
        # First, verify rural location
        zip_code = row.get('ZIP_Code', '')
        is_rural = self.is_rural_zip(zip_code)
        
        # Calculate base score
        base_score = self.calculate_base_score(row)
        
        # Apply rural verification rules
        if not is_rural:
            # Non-rural leads are capped at B+ level (max 50 points)
            final_score = min(base_score, 49)  # Just under B+ threshold
            rural_status = 'NON_RURAL'
        else:
            # Rural leads get full scoring
            final_score = base_score
            rural_status = 'RURAL'
        
        return final_score, rural_status

    def assign_priority_grade(self, score, rural_status):
        """Assign priority grade with rural verification"""
        if rural_status == 'NON_RURAL':
            # Non-rural leads cannot get A+ or A grades
            if score >= self.priority_thresholds['B+']:
                return 'B+'
            elif score >= self.priority_thresholds['B']:
                return 'B'
            else:
                return 'C'
        else:
            # Rural leads get full priority scale
            if score >= self.priority_thresholds['A+']:
                return 'A+'
            elif score >= self.priority_thresholds['A']:
                return 'A'
            elif score >= self.priority_thresholds['B+']:
                return 'B+'
            elif score >= self.priority_thresholds['B']:
                return 'B'
            else:
                return 'C'

    def score_leads(self, df):
        """Score all leads with rural verification"""
        logger.info(f"Scoring {len(df):,} leads with rural verification...")
        
        results = []
        rural_count = 0
        non_rural_count = 0
        
        for idx, row in df.iterrows():
            score, rural_status = self.calculate_rural_verified_score(row)
            priority = self.assign_priority_grade(score, rural_status)
            
            if rural_status == 'RURAL':
                rural_count += 1
            else:
                non_rural_count += 1
            
            results.append({
                'Lead_ID': idx,
                'Score': score,
                'Priority': priority,
                'Rural_Status': rural_status,
                'ZIP_Code': row.get('ZIP_Code', ''),
                'Primary_Specialty': row.get('Primary_Specialty', ''),
                'Practice_Group_Size': row.get('Practice_Group_Size', 1)
            })
        
        results_df = pd.DataFrame(results)
        
        # Log summary
        logger.info("📊 RURAL VERIFICATION SUMMARY")
        logger.info(f"✅ Rural leads: {rural_count:,} ({rural_count/len(df)*100:.1f}%)")
        logger.info(f"⚠️  Non-rural leads: {non_rural_count:,} ({non_rural_count/len(df)*100:.1f}%)")
        
        # Priority distribution for rural vs non-rural
        rural_priorities = results_df[results_df['Rural_Status'] == 'RURAL']['Priority'].value_counts()
        non_rural_priorities = results_df[results_df['Rural_Status'] == 'NON_RURAL']['Priority'].value_counts()
        
        logger.info("\n🏆 RURAL LEAD PRIORITIES:")
        for priority, count in rural_priorities.sort_index().items():
            logger.info(f"   {priority}: {count:,} leads")
        
        if len(non_rural_priorities) > 0:
            logger.info("\n⚠️  NON-RURAL LEAD PRIORITIES (Capped):")
            for priority, count in non_rural_priorities.sort_index().items():
                logger.info(f"   {priority}: {count:,} leads")
        
        return results_df

    def update_original_dataset(self, df, scores_df):
        """Update original dataset with rural-verified scores"""
        # Merge scores back into original dataset
        df_scored = df.copy()
        df_scored = df_scored.merge(
            scores_df[['Lead_ID', 'Score', 'Priority', 'Rural_Status']], 
            left_index=True, 
            right_on='Lead_ID', 
            how='left'
        )
        
        # Drop the Lead_ID column (it's just the index)
        df_scored = df_scored.drop('Lead_ID', axis=1)
        
        return df_scored

def main():
    """Test the rural-verified scoring system"""
    scorer = RuralVerifiedScoring()
    
    # Load the comprehensive leads dataset
    try:
        df = pd.read_excel('comprehensive_rural_physician_leads.xlsx')
        logger.info(f"Loaded {len(df):,} leads for rural verification scoring")
        
        # Score all leads
        scores_df = scorer.score_leads(df)
        
        # Update original dataset
        df_final = scorer.update_original_dataset(df, scores_df)
        
        # Save results
        output_file = 'rural_verified_scored_leads.xlsx'
        df_final.to_excel(output_file, index=False)
        logger.info(f"✅ Saved rural-verified scores to {output_file}")
        
        # Show A+ examples
        a_plus_leads = df_final[df_final['Priority'] == 'A+']
        if len(a_plus_leads) > 0:
            logger.info(f"\n🌟 A+ RURAL LEADS (Exclusive): {len(a_plus_leads):,}")
            for idx, row in a_plus_leads.head(10).iterrows():
                logger.info(f"• {row['Primary_Specialty']} | Size: {row['Practice_Group_Size']} | ZIP: {row['ZIP_Code']} | Score: {row['Score']}")
        
        return df_final
        
    except FileNotFoundError:
        logger.error("❌ comprehensive_rural_physician_leads.xlsx not found")
        return None

if __name__ == "__main__":
    main() 