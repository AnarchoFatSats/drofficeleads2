#!/usr/bin/env python3
"""
Prospect Guidelines Validator

Verifies that the enhanced dataset still follows the original prospect guidelines:
1. Small rural practices (1-5 providers) ✓
2. Target specialties ✓ 
3. Rural RUCA codes (4-10) ✓
4. Hospital exclusion ❓
5. Independent practice filtering ❓
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re

class ProspectGuidelinesValidator:
    def __init__(self):
        self.hospital_indicators = [
            'HOSPITAL', 'HEALTH SYSTEM', 'MEDICAL CENTER', 'HEALTHCARE SYSTEM',
            'REGIONAL MEDICAL', 'MERCY', 'BAPTIST', 'METHODIST', 'PRESBYTERIAN',
            'SAINT ', 'ST ', 'UNIVERSITY', 'CLINIC NETWORK', 'HEALTHCARE NETWORK',
            'KAISER', 'CLEVELAND CLINIC', 'MAYO CLINIC', 'JOHNS HOPKINS',
            'MOUNT SINAI', 'CEDARS-SINAI', 'MASS GENERAL', 'BRIGHAM',
            'CATHOLIC', 'ADVENTIST', 'VETERANS AFFAIRS', 'VA MEDICAL'
        ]
        
        self.target_specialties = {
            'Podiatrist', 'Dermatology - Mohs Surgery', 'Wound Care - Nurse',
            'Wound Care - Physical Therapist', 'Wound Care - Clinic',
            'Family Medicine', 'General Practice', 'Internal Medicine',
            'Wound Care - Physician', 'Wound Care - Physician Specialist'
        }

    def load_rural_zips(self):
        """Load rural ZIP codes from RUCA data"""
        try:
            ruca_file = Path("RUCA2010zipcode.csv")
            if not ruca_file.exists():
                print("⚠️  RUCA file not found - cannot validate rural criteria")
                return set()
            
            ruca_df = pd.read_csv(ruca_file)
            # Rural codes: 4-10
            rural_df = ruca_df[ruca_df['RUCA2'].between(4, 10)]
            # Handle the quoted column name
            zip_col = "'ZIP_CODE'" if "'ZIP_CODE'" in ruca_df.columns else 'ZIP_CODE'
            rural_zips = set(rural_df[zip_col].astype(str).str.strip("'").str.zfill(5))
            print(f"✅ Loaded {len(rural_zips):,} rural ZIP codes")
            return rural_zips
            
        except Exception as e:
            print(f"❌ Error loading RUCA data: {e}")
            return set()

    def is_likely_hospital_affiliated(self, org_name, dba_name='', owner_name=''):
        """Check if organization appears to be hospital affiliated"""
        if not org_name:
            return False
            
        # Combine all name fields for checking
        all_names = f"{org_name} {dba_name} {owner_name}".upper()
        
        # Check for hospital indicators
        for indicator in self.hospital_indicators:
            if indicator in all_names:
                return True
                
        # Additional patterns that suggest hospital affiliation
        hospital_patterns = [
            r'\b\w+\s+REGIONAL\b',  # "Something Regional"
            r'\b\w+\s+MEMORIAL\b',  # "Something Memorial" 
            r'HEALTH\s+CENTER',     # "Health Center"
            r'MEDICAL\s+GROUP',     # "Medical Group" (often hospital owned)
            r'PHYSICIAN\s+GROUP',   # "Physician Group" (often hospital owned)
            r'\bHHS\b',             # Health & Hospital Systems
            r'\bIHN\b',             # Integrated Healthcare Network
        ]
        
        for pattern in hospital_patterns:
            if re.search(pattern, all_names):
                return True
                
        return False

    def validate_enhanced_dataset(self, filename='comprehensive_rural_physician_leads.xlsx'):
        """Validate enhanced dataset against original guidelines"""
        print("🔍 PROSPECT GUIDELINES VALIDATION")
        print("=" * 50)
        
        # Load enhanced dataset
        try:
            df = pd.read_excel(filename)
            print(f"✅ Loaded {len(df):,} enhanced leads")
        except FileNotFoundError:
            print(f"❌ Enhanced leads file not found: {filename}")
            return
        
        print("\n📋 VALIDATING CORE REQUIREMENTS")
        print("-" * 40)
        
        # 1. Practice Size Validation (1-5 providers)
        valid_sizes = df['Practice_Group_Size'].between(1, 5)
        print(f"✅ Practice Size (1-5 providers): {valid_sizes.sum():,}/{len(df):,} ({(valid_sizes.sum()/len(df)*100):.1f}%)")
        
        invalid_sizes = df[~valid_sizes]
        if len(invalid_sizes) > 0:
            print(f"⚠️  Found {len(invalid_sizes)} practices with >5 providers")
            size_counts = invalid_sizes['Practice_Group_Size'].value_counts().head()
            for size, count in size_counts.items():
                print(f"   • {size} providers: {count} practices")
        
        # 2. Target Specialty Validation
        has_target_specialty = df['Primary_Specialty'].isin(self.target_specialties)
        print(f"✅ Target Specialties: {has_target_specialty.sum():,}/{len(df):,} ({(has_target_specialty.sum()/len(df)*100):.1f}%)")
        
        # Show specialty breakdown
        specialty_counts = df['Primary_Specialty'].value_counts().head(10)
        print("   Top specialties:")
        for specialty, count in specialty_counts.items():
            indicator = "✓" if specialty in self.target_specialties else "❌"
            print(f"   {indicator} {specialty}: {count:,}")
        
        # 3. Rural ZIP Code Validation
        rural_zips = self.load_rural_zips()
        if rural_zips:
            df['ZIP_5'] = df['ZIP_Code'].astype(str).str[:5].str.zfill(5)
            is_rural = df['ZIP_5'].isin(rural_zips)
            print(f"✅ Rural ZIP Codes: {is_rural.sum():,}/{len(df):,} ({(is_rural.sum()/len(df)*100):.1f}%)")
            
            if not is_rural.all():
                non_rural_count = (~is_rural).sum()
                print(f"⚠️  Found {non_rural_count} leads in non-rural ZIP codes")
        
        # 4. Hospital Affiliation Check
        print("\n🏥 HOSPITAL AFFILIATION ANALYSIS")
        print("-" * 40)
        
        hospital_flags = df.apply(lambda row: self.is_likely_hospital_affiliated(
            row.get('Legal_Business_Name', ''),
            row.get('DBA_Name', ''),
            row.get('Owner_Full_Name', '')
        ), axis=1)
        
        hospital_count = hospital_flags.sum()
        independent_count = len(df) - hospital_count
        
        print(f"✅ Independent Practices: {independent_count:,} ({(independent_count/len(df)*100):.1f}%)")
        print(f"⚠️  Possible Hospital Affiliated: {hospital_count:,} ({(hospital_count/len(df)*100):.1f}%)")
        
        if hospital_count > 0:
            print("\n📋 HOSPITAL AFFILIATION EXAMPLES:")
            hospital_examples = df[hospital_flags].head(10)
            for idx, row in hospital_examples.iterrows():
                print(f"• {row.get('Legal_Business_Name', 'N/A')}")
                if row.get('DBA_Name'):
                    print(f"  DBA: {row.get('DBA_Name')}")
                print(f"  Owner: {row.get('Owner_Full_Name', 'N/A')}")
                print()
        
        # 5. Data Quality Assessment
        print("📊 DATA QUALITY ASSESSMENT")
        print("-" * 40)
        
        # Phone coverage
        has_practice_phone = df['Practice_Phone'].notna() & (df['Practice_Phone'] != '')
        has_owner_phone = df['Owner_Phone'].notna() & (df['Owner_Phone'] != '')
        has_any_phone = has_practice_phone | has_owner_phone
        
        print(f"📞 Phone Coverage:")
        print(f"   • Practice Phone: {has_practice_phone.sum():,} ({(has_practice_phone.sum()/len(df)*100):.1f}%)")
        print(f"   • Owner Phone: {has_owner_phone.sum():,} ({(has_owner_phone.sum()/len(df)*100):.1f}%)")
        print(f"   • Any Phone: {has_any_phone.sum():,} ({(has_any_phone.sum()/len(df)*100):.1f}%)")
        
        # EIN coverage
        has_ein = df['EIN'].notna() & (df['EIN'] != '<UNAVAIL>') & (df['EIN'] != '')
        print(f"🏢 Business Data:")
        print(f"   • EIN Available: {has_ein.sum():,} ({(has_ein.sum()/len(df)*100):.1f}%)")
        
        # Address verification
        address_verified = df['Address_Match'] == 'Different'
        print(f"📍 Address Verification:")
        print(f"   • Practice ≠ Mailing: {address_verified.sum():,} ({(address_verified.sum()/len(df)*100):.1f}%)")
        
        # 6. Completeness Score
        print("\n🎯 LEAD COMPLETENESS ANALYSIS")
        print("-" * 40)
        
        # Calculate completeness score for each lead
        df['Completeness_Score'] = 0
        df.loc[has_practice_phone, 'Completeness_Score'] += 25
        df.loc[has_owner_phone, 'Completeness_Score'] += 20
        df.loc[has_ein, 'Completeness_Score'] += 20
        df.loc[address_verified, 'Completeness_Score'] += 15
        df.loc[df['Owner_Full_Name'].notna() & (df['Owner_Full_Name'] != ''), 'Completeness_Score'] += 10
        df.loc[df['Owner_Title'].notna() & (df['Owner_Title'] != ''), 'Completeness_Score'] += 10
        
        completeness_stats = df['Completeness_Score'].describe()
        print(f"Completeness Score Distribution:")
        print(f"   • Mean: {completeness_stats['mean']:.1f}/100")
        print(f"   • Median: {completeness_stats['50%']:.1f}/100")
        print(f"   • High Quality (≥80): {(df['Completeness_Score'] >= 80).sum():,} leads")
        print(f"   • Medium Quality (≥60): {(df['Completeness_Score'] >= 60).sum():,} leads")
        print(f"   • Basic Quality (≥40): {(df['Completeness_Score'] >= 40).sum():,} leads")
        
        # 7. Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("-" * 40)
        
        if hospital_count > len(df) * 0.05:  # More than 5% hospital affiliated
            print("🔧 FILTERING IMPROVEMENT NEEDED:")
            print(f"   • {hospital_count:,} leads appear hospital-affiliated")
            print("   • Consider strengthening hospital exclusion filters")
            print("   • Review organization names and ownership patterns")
            print()
        
        if not is_rural.all() and rural_zips:
            print("🗺️  GEOGRAPHIC FILTERING:")
            print(f"   • {(~is_rural).sum():,} leads in non-rural areas")
            print("   • Verify RUCA code filtering is working correctly")
            print()
        
        if has_any_phone.sum() < len(df) * 0.95:  # Less than 95% phone coverage
            print("📞 CONTACT INTELLIGENCE:")
            phone_gap = len(df) - has_any_phone.sum()
            print(f"   • {phone_gap:,} leads missing phone numbers")
            print("   • Consider additional phone data sources")
            print()
        
        print("✅ VALIDATION COMPLETE")
        print("Enhanced dataset maintains core prospect guidelines")
        
        return df

def main():
    """Run prospect guidelines validation"""
    validator = ProspectGuidelinesValidator()
    df = validator.validate_enhanced_dataset()

if __name__ == "__main__":
    main() 