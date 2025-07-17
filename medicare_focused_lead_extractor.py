#!/usr/bin/env python3
"""
Medicare-Focused Lead Extractor for Wound Care Campaign

Targets specialties that serve Medicare patients (65+) with wound care needs in rural areas.
Focus on chronic conditions, diabetes, circulation issues, and age-related wound healing challenges.

Enhanced Specialty Targeting:
- Existing: Podiatry, Wound Care, Mohs Surgery, Primary Care
- NEW Medicare-Focused: Endocrinology, Vascular Surgery, Infectious Disease, Geriatric Medicine

Campaign Focus: Rural Medicare wound care market with less competition, higher reimbursement
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MedicareFocusedLeadExtractor:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        
        # Enhanced Medicare-focused taxonomy codes
        self.target_taxonomies = {
            # Core Wound Care Specialties
            '213E00000X': 'Podiatrist',
            '207ND0900X': 'Dermatology - Mohs Surgery', 
            '163WW0000X': 'Wound Care - Nurse',
            '2251C2600X': 'Wound Care - Physical Therapist',  
            '261QH0600X': 'Wound Care - Clinic',
            '207XX0004X': 'Wound Care - Physician',
            '207XX0005X': 'Wound Care - Physician Specialist',
            
            # Primary Care (Managing Diabetic/Chronic Patients)
            '207Q00000X': 'Family Medicine',
            '208D00000X': 'General Practice',
            '207R00000X': 'Internal Medicine',
            
            # NEW Medicare-Focused Specialties
            '207RE0101X': 'Endocrinology - Diabetes',           # Diabetic foot ulcers, massive Medicare market
            '207RG0300X': 'Endocrinology - General',            # Diabetes management, wound healing
            '208G00000X': 'Vascular Surgery',                   # Circulation problems → chronic wounds
            '207RI0200X': 'Infectious Disease',                 # Wound infections, rural access issues
            '207QG0300X': 'Geriatric Medicine',                 # Aging population, wound care needs
            '207RN0300X': 'Nephrology',                         # Diabetic kidney disease → wound issues
            '207RC0000X': 'Cardiovascular Disease',             # Poor circulation → wound healing
            '207RP1001X': 'Pulmonary Disease',                  # COPD patients with healing issues
            
            # Surgical Specialties (Wound Complications)
            '208600000X': 'Surgery - General',                  # Wound complications, surgical site infections
            '2086S0122X': 'Surgery - Plastic/Reconstructive',   # Wound reconstruction, complex healing
            '207X00000X': 'Orthopaedic Surgery'                 # Diabetic foot complications, bone infections
        }
        
        # Medicare specialty priority scoring
        self.medicare_priority_scores = {
            # Highest Priority: Direct Wound Care + Medicare Population
            'Podiatrist': 50,                                   # Diabetic foot care, high Medicare volume
            'Endocrinology - Diabetes': 45,                     # Direct diabetes → wound care pipeline
            'Wound Care - Physician Specialist': 45,
            'Wound Care - Physician': 40,
            'Vascular Surgery': 40,                             # Circulation → wound healing
            
            # High Priority: Medicare Conditions Leading to Wounds
            'Geriatric Medicine': 35,                           # Aging population, multiple comorbidities
            'Infectious Disease': 35,                           # Wound infections, antibiotic management
            'Dermatology - Mohs Surgery': 35,                   # Skin cancer → wounds in Medicare age
            'Endocrinology - General': 30,
            'Nephrology': 30,                                   # Diabetic kidney disease
            
            # Medium Priority: Primary Care Managing Chronic Conditions
            'Family Medicine': 25,                              # Managing diabetic patients
            'Internal Medicine': 25,                            # Chronic disease management
            'Cardiovascular Disease': 25,                       # Poor circulation
            
            # Support Specialties
            'Surgery - General': 20,                            # Wound complications
            'Surgery - Plastic/Reconstructive': 20,             # Complex wound reconstruction
            'Wound Care - Nurse': 20,
            'General Practice': 15,
            'Orthopaedic Surgery': 15,                          # Diabetic foot complications
            'Wound Care - Clinic': 15,
            'Pulmonary Disease': 10,
            'Wound Care - Physical Therapist': 10
        }
        
        # Hospital/health system exclusion indicators
        self.hospital_indicators = [
            'HOSPITAL', 'HEALTH SYSTEM', 'MEDICAL CENTER', 'HEALTHCARE SYSTEM',
            'REGIONAL MEDICAL', 'MERCY', 'BAPTIST', 'METHODIST', 'PRESBYTERIAN',
            'SAINT ', 'ST ', 'UNIVERSITY', 'CLINIC NETWORK', 'HEALTHCARE NETWORK',
            'KAISER', 'CLEVELAND CLINIC', 'MAYO CLINIC', 'JOHNS HOPKINS',
            'MOUNT SINAI', 'CEDARS-SINAI', 'MASS GENERAL', 'BRIGHAM',
            'CATHOLIC', 'ADVENTIST', 'VETERANS AFFAIRS', 'VA MEDICAL'
        ]

    def load_rural_zips(self) -> set:
        """Load rural ZIP codes from RUCA data"""
        try:
            ruca_file = self.base_dir / "RUCA2010zipcode.csv"
            if not ruca_file.exists():
                logger.warning("⚠️  RUCA file not found - using fallback rural detection")
                return set()
            
            ruca_df = pd.read_csv(ruca_file)
            logger.info(f"RUCA columns: {list(ruca_df.columns)}")
            
            # Rural codes: 4-10 (rural/small town)
            rural_df = ruca_df[ruca_df['RUCA2'].between(4, 10)]
            
            # Handle the quoted column name - check actual column names
            zip_col = None
            for col in ruca_df.columns:
                if 'ZIP' in col.upper():
                    zip_col = col
                    break
            
            if zip_col is None:
                logger.error("Could not find ZIP code column in RUCA data")
                return set()
            
            # Clean the ZIP codes (remove quotes and pad to 5 digits)
            rural_zips = set(rural_df[zip_col].astype(str).str.strip("'\"").str.zfill(5))
            
            logger.info(f"✅ Loaded {len(rural_zips):,} rural ZIP codes from RUCA data")
            return rural_zips
            
        except Exception as e:
            logger.error(f"Error loading RUCA data: {e}")
            return set()

    def filter_target_specialties(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter for Medicare-focused target specialties"""
        
        # Create specialty match mask
        specialty_mask = pd.Series(False, index=df.index)
        
        # Check all taxonomy code columns
        taxonomy_cols = [col for col in df.columns if 'Healthcare Provider Taxonomy Code_' in col]
        
        for col in taxonomy_cols:
            if col in df.columns:
                specialty_mask |= df[col].isin(self.target_taxonomies.keys())
        
        target_df = df[specialty_mask].copy()
        
        # Filter out hospital/health system affiliated providers
        if 'Provider Organization Name (Legal Business Name)' in target_df.columns:
            org_name = target_df['Provider Organization Name (Legal Business Name)'].fillna('').str.upper()
            hospital_mask = pd.Series(False, index=target_df.index)
            
            for indicator in self.hospital_indicators:
                hospital_mask |= org_name.str.contains(indicator, na=False)
            
            target_df = target_df[~hospital_mask]
        
        return target_df

    def calculate_medicare_score(self, specialties: List[str], group_size: int = 1) -> int:
        """Calculate Medicare-focused lead score"""
        base_score = 0
        
        # Get highest priority specialty score
        specialty_scores = [self.medicare_priority_scores.get(spec, 0) for spec in specialties]
        if specialty_scores:
            base_score = max(specialty_scores)
        
        # Multi-specialty bonus (especially valuable for Medicare)
        if len(specialties) >= 3:
            base_score += 20  # Comprehensive care bonus
        elif len(specialties) >= 2:
            base_score += 10  # Multi-specialty bonus
        
        # Special combination bonuses for Medicare wound care
        specialty_set = set(specialties)
        
        # Ultimate combination: Podiatrist + Endocrinology + Wound Care
        if {'Podiatrist', 'Endocrinology - Diabetes', 'Wound Care - Physician Specialist'}.issubset(specialty_set):
            base_score += 30  # Medicare wound care powerhouse
        
        # High-value combinations
        elif {'Podiatrist', 'Endocrinology - Diabetes'}.issubset(specialty_set):
            base_score += 25  # Diabetic foot care specialists
        elif {'Podiatrist', 'Wound Care - Physician Specialist'}.issubset(specialty_set):
            base_score += 25  # Comprehensive foot/wound care
        elif {'Vascular Surgery', 'Wound Care - Physician'}.issubset(specialty_set):
            base_score += 25  # Circulation + wound healing
        elif {'Geriatric Medicine', 'Wound Care - Physician'}.issubset(specialty_set):
            base_score += 20  # Aging population wound specialists
        
        # Group size preference (smaller = easier to target)
        size_bonus = {1: 15, 2: 12, 3: 8, 4: 5, 5: 3}.get(group_size, 0)
        base_score += size_bonus
        
        return min(base_score, 100)  # Cap at 100

    def build_comprehensive_leads(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build comprehensive Medicare-focused leads"""
        logger.info(f"Building comprehensive Medicare-focused leads from {len(df):,} providers...")
        
        leads = []
        
        for idx, row in df.iterrows():
            # Extract all specialties
            specialties = self.extract_all_specialties(row)
            
            if not specialties:
                continue
            
            # Get primary specialty (highest scoring)
            primary_specialty = max(specialties, key=lambda x: self.medicare_priority_scores.get(x, 0))
            
            # Practice group size (default to 1 for individual providers)
            group_size = 1  # Enhanced later via grouping logic
            
            # Calculate Medicare-focused score
            medicare_score = self.calculate_medicare_score(specialties, group_size)
            
            # Build comprehensive lead record
            lead = {
                # Core Identity
                'NPI': row.get('NPI', ''),
                'Provider_Name': self.build_full_name(
                    row.get('Provider First Name', ''),
                    row.get('Provider Last Name (Legal Name)', ''),
                    row.get('Provider Middle Name', ''),
                    row.get('Provider Name Prefix Text', ''),
                    row.get('Provider Name Suffix Text', '')
                ),
                
                # Practice Information
                'Practice_Name': row.get('Provider Organization Name (Legal Business Name)', ''),
                'Legal_Business_Name': row.get('Provider Organization Name (Legal Business Name)', ''),
                'DBA_Name': row.get('Provider Other Organization Name', ''),
                
                # Medicare-Focused Specialty Data
                'Primary_Specialty': str(primary_specialty) if primary_specialty else '',
                'Medicare_Priority_Score': self.medicare_priority_scores.get(primary_specialty, 0),
                'All_Specialties': ' | '.join([str(s) for s in specialties if s]),
                'Specialty_Count': len(specialties),
                'Medicare_Lead_Score': medicare_score,
                
                # Contact Intelligence (Multiple Phones)
                'Practice_Phone': self.clean_phone(row.get('Provider Business Practice Location Address Telephone Number', '')),
                'Practice_Fax': self.clean_phone(row.get('Provider Business Practice Location Address Fax Number', '')),
                'Owner_Phone': self.clean_phone(row.get('Authorized Official Telephone Number', '')),
                'Primary_Phone': self.clean_phone(row.get('Provider Business Practice Location Address Telephone Number', '')),
                
                # Owner/Contact Information
                'Owner_Name': self.build_full_name(
                    row.get('Authorized Official First Name', ''),
                    row.get('Authorized Official Last Name', ''),
                    row.get('Authorized Official Middle Name', ''),
                    row.get('Authorized Official Name Prefix Text', ''),
                    row.get('Authorized Official Name Suffix Text', '')
                ),
                'Owner_Title': row.get('Authorized Official Title or Position', ''),
                'Owner_Credential': row.get('Authorized Official Credential Text', ''),
                
                # Business Structure
                'Entity_Type': 'Individual' if row.get('Entity Type Code') == '1' else 'Organization',
                'Entity_Type_Code': row.get('Entity Type Code', ''),
                'EIN': row.get('Employer Identification Number (EIN)', ''),
                'Is_Sole_Proprietor': row.get('Is Sole Proprietor', ''),
                
                # Address Information
                'Practice_Address': self.build_full_address(
                    row.get('Provider Business Practice Location Address Line 1', ''),
                    row.get('Provider Business Practice Location Address Line 2', ''),
                    row.get('Provider Business Practice Location Address City Name', ''),
                    row.get('Provider Business Practice Location Address State Name', ''),
                    row.get('Provider Business Practice Location Address Postal Code', '')
                ),
                'Mailing_Address': self.build_full_address(
                    row.get('Provider Business Mailing Address Line 1', ''),
                    row.get('Provider Business Mailing Address Line 2', ''),
                    row.get('Provider Business Mailing Address City Name', ''),
                    row.get('Provider Business Mailing Address State Name', ''),
                    row.get('Provider Business Mailing Address Postal Code', '')
                ),
                'ZIP_Code': self.extract_zip_code(row.get('Provider Business Practice Location Address Postal Code', '')),
                'State': row.get('Provider Business Practice Location Address State Name', ''),
                'City': row.get('Provider Business Practice Location Address City Name', ''),
                
                # Professional Data
                'Enumeration_Date': row.get('Provider Enumeration Date', ''),
                'Last_Update_Date': row.get('Last Update Date', ''),
                'Certification_Date': row.get('Certification Date', ''),
                'Gender': row.get('Provider Gender Code', ''),
                
                # Data Quality Indicators
                'Has_Practice_Phone': 'Yes' if self.clean_phone(row.get('Provider Business Practice Location Address Telephone Number', '')) else 'No',
                'Has_Owner_Phone': 'Yes' if self.clean_phone(row.get('Authorized Official Telephone Number', '')) else 'No',
                'Has_Multiple_Phones': self.count_available_phones(row),
                'Address_Match': 'Same' if self.addresses_match(row) else 'Different',
                'Practice_Group_Size': group_size  # Will be enhanced later
            }
            
            leads.append(lead)
        
        leads_df = pd.DataFrame(leads)
        logger.info(f"✅ Built {len(leads_df):,} comprehensive Medicare-focused leads")
        
        return leads_df

    def extract_all_specialties(self, row) -> List[str]:
        """Extract all Medicare-relevant specialties for a provider"""
        specialties = []
        
        taxonomy_cols = [col for col in row.index if 'Healthcare Provider Taxonomy Code_' in col]
        
        for col in taxonomy_cols:
            taxonomy_code = row.get(col, '')
            if pd.notna(taxonomy_code) and str(taxonomy_code).strip() and taxonomy_code in self.target_taxonomies:
                specialty = self.target_taxonomies[taxonomy_code]
                if specialty and specialty not in specialties:
                    specialties.append(str(specialty))  # Ensure string
        
        return specialties

    def clean_phone(self, phone: str) -> str:
        """Clean and format phone number"""
        if pd.isna(phone) or not phone:
            return ''
        
        # Remove all non-digits
        digits = re.sub(r'\D', '', str(phone))
        
        # Must be 10 digits for US phone number
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return digits if digits else ''

    def count_available_phones(self, row) -> str:
        """Count available phone numbers"""
        phones = [
            self.clean_phone(row.get('Provider Business Practice Location Address Telephone Number', '')),
            self.clean_phone(row.get('Authorized Official Telephone Number', '')),
            self.clean_phone(row.get('Provider Business Practice Location Address Fax Number', ''))
        ]
        
        valid_phones = [p for p in phones if p]
        return f"{len(valid_phones)} phones available"

    def addresses_match(self, row) -> bool:
        """Check if practice and mailing addresses match"""
        practice_addr = f"{row.get('Provider Business Practice Location Address Line 1', '')} {row.get('Provider Business Practice Location Address City Name', '')}".strip()
        mailing_addr = f"{row.get('Provider Business Mailing Address Line 1', '')} {row.get('Provider Business Mailing Address City Name', '')}".strip()
        
        return practice_addr.lower() == mailing_addr.lower() if practice_addr and mailing_addr else False

    def build_full_name(self, first: str, last: str, middle: str = '', prefix: str = '', suffix: str = '') -> str:
        """Build full formatted name"""
        parts = []
        
        # Safely convert all inputs to strings and filter out empty/None values
        for part in [prefix, first, middle, last, suffix]:
            if part and pd.notna(part) and str(part).strip():
                parts.append(str(part).strip())
        
        return ' '.join(parts)

    def build_full_address(self, line1: str, line2: str, city: str, state: str, zip_code: str) -> str:
        """Build full formatted address"""
        parts = []
        
        # Safely handle address components
        if line1 and pd.notna(line1) and str(line1).strip():
            parts.append(str(line1).strip())
        if line2 and pd.notna(line2) and str(line2).strip():
            parts.append(str(line2).strip())
        if city and state and pd.notna(city) and pd.notna(state):
            city_str = str(city).strip()
            state_str = str(state).strip()
            if city_str and state_str:
                parts.append(f"{city_str}, {state_str}")
        if zip_code and pd.notna(zip_code):
            zip_clean = self.extract_zip_code(str(zip_code))
            if zip_clean:
                parts.append(zip_clean)
        
        return ', '.join(parts)

    def extract_zip_code(self, postal_code: str) -> str:
        """Extract 5-digit ZIP code"""
        if pd.isna(postal_code) or not postal_code:
            return ''
        
        # Extract first 5 digits
        digits = re.sub(r'\D', '', str(postal_code))
        return digits[:5] if len(digits) >= 5 else digits

    def process_nppes_chunk(self, chunk_file: Path, rural_zips: set, chunk_num: int) -> pd.DataFrame:
        """Process a single NPPES chunk file with Medicare focus"""
        logger.info(f"Processing chunk {chunk_num}/21: {chunk_file.name}")
        logger.info(f"Processing chunk: {chunk_file}")
        
        try:
            # Read NPPES chunk
            df = pd.read_csv(chunk_file, dtype=str, low_memory=False)
            logger.info(f"Loaded {len(df):,} records from {chunk_file}")
            
            # Filter to target specialties
            target_df = self.filter_target_specialties(df)
            
            if len(target_df) == 0:
                return pd.DataFrame()
            
            logger.info(f"Found {len(target_df):,} target specialty providers")
            
            # Filter to rural ZIP codes if available
            if rural_zips:
                target_df['ZIP'] = target_df['Provider Business Practice Location Address Postal Code'].astype(str).str[:5].str.zfill(5)
                target_df = target_df[target_df['ZIP'].isin(rural_zips)]
                logger.info(f"Filtered to {len(target_df):,} rural providers")
            
            if len(target_df) == 0:
                return pd.DataFrame()
            
            # Build comprehensive leads
            leads_df = self.build_comprehensive_leads(target_df)
            
            logger.info(f"Extracted {len(leads_df):,} comprehensive leads")
            return leads_df
            
        except Exception as e:
            logger.error(f"Error processing {chunk_file}: {e}")
            return pd.DataFrame()

    def run_extraction(self) -> pd.DataFrame:
        """Run the complete Medicare-focused lead extraction"""
        logger.info("🏥 Starting Medicare-focused rural physician lead extraction...")
        
        # Load rural ZIP codes
        rural_zips = self.load_rural_zips()
        
        # Process all NPPES chunks
        all_leads = []
        chunk_dir = self.base_dir / "npidata_pfile_20050523-20250713_split"
        
        if not chunk_dir.exists():
            logger.error(f"NPPES split directory not found: {chunk_dir}")
            return pd.DataFrame()
        
        chunk_files = sorted(list(chunk_dir.glob("*.csv")))
        logger.info(f"Found {len(chunk_files)} NPPES chunk files to process")
        
        for i, chunk_file in enumerate(chunk_files, 1):
            chunk_leads = self.process_nppes_chunk(chunk_file, rural_zips, i)
            if len(chunk_leads) > 0:
                all_leads.append(chunk_leads)
        
        if not all_leads:
            logger.warning("No leads found")
            return pd.DataFrame()
        
        # Combine all results
        final_leads = pd.concat(all_leads, ignore_index=True)
        
        # Remove duplicates
        final_leads = final_leads.drop_duplicates(subset=['NPI'])
        
        # Sort by Medicare score (highest first)
        final_leads = final_leads.sort_values('Medicare_Lead_Score', ascending=False)
        
        logger.info(f"🎯 MEDICARE-FOCUSED EXTRACTION COMPLETE")
        logger.info(f"Total leads extracted: {len(final_leads):,}")
        
        # Summary by specialty
        specialty_counts = final_leads['Primary_Specialty'].value_counts()
        logger.info("📊 Specialty breakdown:")
        for specialty, count in specialty_counts.head(10).items():
            score = self.medicare_priority_scores.get(specialty, 0)
            logger.info(f"  {specialty}: {count:,} leads (Priority Score: {score})")
        
        return final_leads

if __name__ == "__main__":
    extractor = MedicareFocusedLeadExtractor()
    leads_df = extractor.run_extraction()
    
    if len(leads_df) > 0:
        # Save results
        output_file = 'medicare_focused_rural_leads.xlsx'
        leads_df.to_excel(output_file, index=False)
        logger.info(f"✅ Saved Medicare-focused leads to {output_file}")
        
        # Show top priorities
        top_leads = leads_df.head(20)
        logger.info(f"\n🌟 TOP 20 MEDICARE WOUND CARE PROSPECTS:")
        for idx, row in top_leads.iterrows():
            logger.info(f"• {row['Primary_Specialty']} | Score: {row['Medicare_Lead_Score']} | {row['All_Specialties']} | {row['ZIP_Code']}")
    else:
        logger.error("❌ No leads extracted") 