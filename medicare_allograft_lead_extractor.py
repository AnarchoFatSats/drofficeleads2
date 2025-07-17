#!/usr/bin/env python3
"""
Medicare-Focused Allograft Wound Care Lead Extractor

Targeting: Allograft wound care patches for Medicare-dense populations (65+)
Focus: Rural private practices (1-5 physicians) serving Medicare wound care patients

Priority Scoring:
1. Wound Care Centers/Specialists (Highest)
2. Burn Centers (Independent only)  
3. Podiatry (High Medicare volume - diabetic foot care)
4. Medicare-focused specialties (Endocrinology, Vascular Surgery, etc.)

Research Basis: $28-97B Medicare wound care market, 16.4% of beneficiaries have wounds
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional, Set
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MedicareAllografLeadExtractor:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        
        # Medicare Allograft Wound Care Target Taxonomies
        self.target_taxonomies = {
            # TIER 1: WOUND CARE SPECIALISTS (Highest Priority)
            '207XX0004X': 'Wound Care - Physician',              # 100 points base
            '207XX0005X': 'Wound Care - Physician Specialist',   # 100 points base  
            '261QH0600X': 'Wound Care - Clinic',                 # 95 points base
            '163WW0000X': 'Wound Care - Nurse',                  # 90 points base
            '2251C2600X': 'Wound Care - Physical Therapist',     # 85 points base
            
            # TIER 2: BURN CENTERS & SPECIALIZED SURGERY (Second Priority)
            '2086S0122X': 'Surgery - Plastic/Reconstructive',    # 95 points (burn reconstruction)
            '208600000X': 'Surgery - General',                   # 90 points (burn treatment)
            '208G00000X': 'Vascular Surgery',                    # 85 points (circulation/wound healing)
            
            # TIER 3: PODIATRY (High Medicare Volume)
            '213E00000X': 'Podiatrist',                          # 85 points (diabetic foot ulcers)
            '213EG0000X': 'Podiatrist - General',                # 80 points
            '213ES0103X': 'Podiatrist - Sports Medicine',        # 75 points
            
            # TIER 4: MEDICARE-DENSE SPECIALTIES  
            '207RE0101X': 'Endocrinology - Diabetes',            # 80 points (diabetic wounds)
            '207RG0300X': 'Endocrinology - General',             # 75 points
            '207QG0300X': 'Geriatric Medicine',                  # 80 points (aging population)
            '207RI0200X': 'Infectious Disease',                  # 75 points (wound infections)
            '207RN0300X': 'Nephrology',                          # 70 points (diabetic kidney disease)
            '207RC0000X': 'Cardiovascular Disease',              # 70 points (circulation issues)
            
            # TIER 5: DERMATOLOGY (Skin-related)
            '207ND0900X': 'Dermatology - Mohs Surgery',          # 75 points (skin cancer → wounds)
            '207N00000X': 'Dermatology - General',               # 65 points
            
            # TIER 6: PRIMARY CARE (Managing Chronic Conditions)
            '207Q00000X': 'Family Medicine',                     # 60 points (managing diabetics)
            '207R00000X': 'Internal Medicine',                   # 60 points (chronic diseases)
            '208D00000X': 'General Practice',                    # 55 points
            
            # TIER 7: ORTHOPEDIC (Diabetic foot complications)
            '207X00000X': 'Orthopaedic Surgery',                 # 55 points (bone infections)
            '207XS0114X': 'Orthopaedic Surgery - Hand',          # 60 points (hand wounds)
            '207XX0801X': 'Orthopaedic Surgery - Trauma',        # 65 points (trauma wounds)
        }
        
        # Medicare Allograft Priority Scoring (Based on wound care likelihood + Medicare density)
        self.medicare_allograft_scores = {
            # TIER 1: WOUND CARE SPECIALISTS (Highest conversion potential)
            'Wound Care - Physician Specialist': 100,            # Perfect target
            'Wound Care - Physician': 100,                       # Perfect target
            'Wound Care - Clinic': 95,                           # Perfect target
            'Wound Care - Nurse': 90,                            # High volume
            'Wound Care - Physical Therapist': 85,               # Supportive care
            
            # TIER 2: BURN CENTERS & SURGICAL SPECIALISTS
            'Surgery - Plastic/Reconstructive': 95,              # Burn reconstruction, wound closure
            'Surgery - General': 90,                             # Burn treatment, wound complications
            'Vascular Surgery': 85,                              # Circulation → wound healing
            
            # TIER 3: PODIATRY (Massive Medicare diabetic foot market)
            'Podiatrist': 85,                                    # Diabetic foot ulcers (huge Medicare market)
            'Podiatrist - General': 80,                          # General foot care
            'Podiatrist - Sports Medicine': 75,                  # Active seniors
            
            # TIER 4: MEDICARE-DENSE SPECIALTIES
            'Endocrinology - Diabetes': 80,                      # Direct diabetes → wound pipeline
            'Geriatric Medicine': 80,                            # Aging population, multiple comorbidities
            'Endocrinology - General': 75,                       # Diabetes management
            'Infectious Disease': 75,                            # Wound infections, antibiotic management
            'Dermatology - Mohs Surgery': 75,                    # Skin cancer → surgical wounds
            'Nephrology': 70,                                    # Diabetic kidney disease
            'Cardiovascular Disease': 70,                        # Poor circulation
            
            # TIER 5: DERMATOLOGY & ORTHOPEDIC
            'Dermatology - General': 65,                         # Skin conditions
            'Orthopaedic Surgery - Trauma': 65,                  # Trauma wounds
            'Orthopaedic Surgery - Hand': 60,                    # Hand injuries/wounds
            
            # TIER 6: PRIMARY CARE (Lower priority but high volume)
            'Family Medicine': 60,                               # Managing diabetic patients
            'Internal Medicine': 60,                             # Chronic disease management
            'General Practice': 55,                              # General Medicare population
            'Orthopaedic Surgery': 55,                           # General bone/joint issues
        }
        
        # Rural ZIP codes for targeting (loaded separately)
        self.rural_zip_codes: Set[str] = set()
        
        # Hospital/health system exclusion patterns (independent practices only)
        self.hospital_exclusions = [
            'HOSPITAL', 'HEALTH SYSTEM', 'MEDICAL CENTER', 'HEALTHCARE SYSTEM',
            'REGIONAL MEDICAL', 'MERCY', 'BAPTIST', 'METHODIST', 'PRESBYTERIAN',
            'SAINT ', 'ST ', 'UNIVERSITY', 'CLINIC NETWORK', 'HEALTHCARE NETWORK',
            'KAISER', 'CLEVELAND CLINIC', 'MAYO CLINIC', 'JOHNS HOPKINS',
            'MOUNT SINAI', 'CEDARS-SINAI', 'MASS GENERAL', 'BRIGHAM',
            'CATHOLIC', 'ADVENTIST', 'VETERANS AFFAIRS', 'VA MEDICAL',
            'COMMUNITY HEALTH', 'REGIONAL HEALTH', 'HEALTH PARTNERS'
        ]

    def load_rural_zip_codes(self) -> Set[str]:
        """Load rural ZIP codes from RUCA data"""
        try:
            ruca_file = self.base_dir / 'RUCA2010zipcode.csv'
            if not ruca_file.exists():
                logger.warning(f"RUCA file not found: {ruca_file}")
                return set()
            
            # Load RUCA data
            ruca_df = pd.read_csv(ruca_file)
            logger.info(f"Loaded RUCA data: {len(ruca_df):,} ZIP codes")
            
            # Handle potential column name variations
            zip_col = None
            for col in ruca_df.columns:
                if 'ZIP' in col.upper() or 'ZIPCODE' in col.upper():
                    zip_col = col
                    break
            
            if zip_col is None:
                logger.error("No ZIP code column found in RUCA data")
                return set()
            
            # RUCA codes 4-10 are rural/small town
            # Focus on codes 4-10 for rural targeting
            if 'RUCA2' in ruca_df.columns:
                rural_df = ruca_df[ruca_df['RUCA2'].between(4, 10)]
            else:
                # Fallback: assume all are potential rural if no RUCA2 column
                rural_df = ruca_df
            
            rural_zips = set(rural_df[zip_col].astype(str).str.zfill(5))
            logger.info(f"Loaded {len(rural_zips):,} rural ZIP codes")
            return rural_zips
            
        except Exception as e:
            logger.error(f"Error loading rural ZIP codes: {e}")
            return set()

    def extract_specialties(self, row: pd.Series) -> List[str]:
        """Extract all Medicare-relevant specialties from provider row"""
        specialties = []
        
        # Check all taxonomy fields
        for i in range(1, 16):  # Healthcare Taxonomy Code_1 through _15
            taxonomy_col = f'Healthcare Provider Taxonomy Code_{i}'
            if taxonomy_col in row and pd.notna(row[taxonomy_col]):
                taxonomy_code = str(row[taxonomy_col]).strip()
                if taxonomy_code in self.target_taxonomies:
                    specialty = self.target_taxonomies[taxonomy_code]
                    if specialty not in specialties:
                        specialties.append(specialty)
        
        return specialties

    def is_independent_practice(self, row: pd.Series) -> bool:
        """Check if practice is independent (not hospital-affiliated)"""
        # Check organization name
        org_name = str(row.get('Provider Organization Name (Legal Business Name)', '')).upper()
        
        for exclusion in self.hospital_exclusions:
            if exclusion in org_name:
                return False
        
        return True

    def calculate_medicare_allograft_score(self, specialties: List[str], 
                                         is_rural: bool, 
                                         group_size: int = 1) -> int:
        """Calculate Medicare allograft wound care lead score"""
        if not specialties:
            return 0
        
        # Base score from highest priority specialty
        specialty_scores = [self.medicare_allograft_scores.get(spec, 0) for spec in specialties]
        base_score = max(specialty_scores) if specialty_scores else 0
        
        # Multi-specialty bonuses (comprehensive wound care)
        if len(specialties) >= 3:
            base_score += 25  # Comprehensive care bonus
        elif len(specialties) >= 2:
            base_score += 15  # Multi-specialty bonus
        
        # SPECIAL COMBINATION BONUSES for allograft wound care
        specialty_set = set(specialties)
        
        # ULTIMATE COMBINATIONS (Medicare wound care powerhouses)
        if {'Podiatrist', 'Endocrinology - Diabetes', 'Wound Care - Physician Specialist'}.issubset(specialty_set):
            base_score += 40  # Perfect diabetic wound care team
        elif {'Wound Care - Physician', 'Surgery - Plastic/Reconstructive'}.issubset(specialty_set):
            base_score += 35  # Advanced wound reconstruction
        elif {'Vascular Surgery', 'Wound Care - Physician Specialist'}.issubset(specialty_set):
            base_score += 35  # Circulation + wound healing expertise
        
        # HIGH-VALUE COMBINATIONS
        elif {'Podiatrist', 'Endocrinology - Diabetes'}.issubset(specialty_set):
            base_score += 30  # Diabetic foot specialists
        elif {'Wound Care - Physician', 'Infectious Disease'}.issubset(specialty_set):
            base_score += 30  # Wound infection specialists
        elif {'Geriatric Medicine', 'Wound Care - Physician'}.issubset(specialty_set):
            base_score += 25  # Aging population specialists
        elif {'Surgery - General', 'Wound Care - Physician'}.issubset(specialty_set):
            base_score += 25  # Surgical wound complications
        
        # RURAL BONUS (higher Medicare reimbursement, less competition)
        if is_rural:
            base_score += 20  # Rural Medicare advantage
        
        # PRACTICE SIZE BONUS (easier to target smaller practices)
        size_bonuses = {1: 15, 2: 12, 3: 8, 4: 5, 5: 3}
        base_score += size_bonuses.get(group_size, 0)
        
        # BURN CENTER BONUS (independent only)
        if any('Surgery - Plastic' in spec or 'Surgery - General' in spec for spec in specialties):
            if is_rural:  # Independent rural surgical practices
                base_score += 15  # Burn center potential
        
        return min(base_score, 100)  # Cap at 100

    def clean_phone(self, phone: str) -> str:
        """Clean and format phone number"""
        if pd.isna(phone):
            return ''
        
        # Remove non-digits
        digits = re.sub(r'\D', '', str(phone))
        
        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return str(phone)

    def build_full_name(self, first: str, last: str, middle: str = '', 
                       prefix: str = '', suffix: str = '') -> str:
        """Build full provider name"""
        name_parts = []
        
        if prefix and pd.notna(prefix):
            name_parts.append(str(prefix))
        if first and pd.notna(first):
            name_parts.append(str(first))
        if middle and pd.notna(middle):
            name_parts.append(str(middle))
        if last and pd.notna(last):
            name_parts.append(str(last))
        if suffix and pd.notna(suffix):
            name_parts.append(str(suffix))
        
        return ' '.join(name_parts)

    def build_address(self, address1: str, address2: str = '', 
                     city: str = '', state: str = '', zip_code: str = '') -> str:
        """Build full address"""
        address_parts = []
        
        if address1 and pd.notna(address1):
            address_parts.append(str(address1))
        if address2 and pd.notna(address2):
            address_parts.append(str(address2))
        
        city_state_zip = []
        if city and pd.notna(city):
            city_state_zip.append(str(city))
        if state and pd.notna(state):
            city_state_zip.append(str(state))
        if zip_code and pd.notna(zip_code):
            city_state_zip.append(str(zip_code))
        
        if city_state_zip:
            address_parts.append(', '.join(city_state_zip))
        
        return ', '.join(address_parts)

    def process_nppes_chunk(self, chunk_file: Path, rural_zips: Set[str], chunk_num: int) -> pd.DataFrame:
        """Process a single NPPES chunk file"""
        logger.info(f"Processing chunk {chunk_num}: {chunk_file.name}")
        
        try:
            # Read chunk
            df = pd.read_csv(chunk_file, dtype=str, low_memory=False)
            logger.info(f"Loaded {len(df):,} records from {chunk_file.name}")
            
            # Filter for target specialties
            specialty_mask = pd.Series(False, index=df.index)
            
            for i in range(1, 16):
                taxonomy_col = f'Healthcare Provider Taxonomy Code_{i}'
                if taxonomy_col in df.columns:
                    specialty_mask |= df[taxonomy_col].isin(self.target_taxonomies.keys())
            
            target_df = df[specialty_mask].copy()
            logger.info(f"Found {len(target_df):,} target specialty providers")
            
            if len(target_df) == 0:
                return pd.DataFrame()
            
            # Build comprehensive leads
            leads = []
            
            for idx, row in target_df.iterrows():
                # Extract specialties
                specialties = self.extract_specialties(row)
                if not specialties:
                    continue
                
                # Check if independent practice
                if not self.is_independent_practice(row):
                    continue
                
                # Get ZIP code and check if rural
                zip_code = str(row.get('Provider Business Practice Location Address Postal Code', ''))[:5]
                is_rural = zip_code in rural_zips
                
                # Filter for rural locations if we have rural data
                if rural_zips and not is_rural:
                    continue
                
                # Calculate Medicare allograft score
                primary_specialty = max(specialties, key=lambda x: self.medicare_allograft_scores.get(x, 0))
                medicare_score = self.calculate_medicare_allograft_score(specialties, is_rural, 1)
                
                # Build lead record
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
                    'Practice_Address': self.build_address(
                        row.get('Provider First Line Business Practice Location Address', ''),
                        row.get('Provider Second Line Business Practice Location Address', ''),
                        row.get('Provider Business Practice Location Address City Name', ''),
                        row.get('Provider Business Practice Location Address State Name', ''),
                        zip_code
                    ),
                    
                    # Geographic
                    'City': row.get('Provider Business Practice Location Address City Name', ''),
                    'State': row.get('Provider Business Practice Location Address State Name', ''),
                    'ZIP_Code': zip_code,
                    'Is_Rural': is_rural,
                    
                    # Medicare Allograft Scoring
                    'Primary_Specialty': primary_specialty,
                    'All_Specialties': ' | '.join(specialties),
                    'Specialty_Count': len(specialties),
                    'Medicare_Allograft_Score': medicare_score,
                    'Base_Priority_Score': self.medicare_allograft_scores.get(primary_specialty, 0),
                    
                    # Contact Information
                    'Practice_Phone': self.clean_phone(row.get('Provider Business Practice Location Address Telephone Number', '')),
                    'Practice_Fax': self.clean_phone(row.get('Provider Business Practice Location Address Fax Number', '')),
                    
                    # Targeting Intelligence
                    'Target_Category': self.get_target_category(primary_specialty),
                    'Medicare_Density_Score': self.get_medicare_density_score(primary_specialty),
                    'Wound_Care_Likelihood': self.get_wound_care_likelihood(specialties)
                }
                
                leads.append(lead)
            
            results_df = pd.DataFrame(leads)
            
            if len(results_df) > 0:
                logger.info(f"Extracted {len(results_df):,} Medicare allograft leads from chunk {chunk_num}")
                
                # Show top specialties for this chunk
                top_specialties = results_df['Primary_Specialty'].value_counts().head(5)
                for specialty, count in top_specialties.items():
                    score = self.medicare_allograft_scores.get(specialty, 0)
                    logger.info(f"  {specialty}: {count} leads (Score: {score})")
            
            return results_df
            
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_file}: {e}")
            return pd.DataFrame()

    def get_target_category(self, specialty: str) -> str:
        """Get target category for specialty"""
        if 'Wound Care' in specialty:
            return 'Wound Care Specialist'
        elif specialty in ['Surgery - Plastic/Reconstructive', 'Surgery - General']:
            return 'Burn Center Potential'
        elif 'Podiatrist' in specialty:
            return 'Podiatry (High Medicare Volume)'
        elif specialty in ['Endocrinology - Diabetes', 'Geriatric Medicine']:
            return 'Medicare-Dense Specialty'
        else:
            return 'Supporting Specialty'

    def get_medicare_density_score(self, specialty: str) -> int:
        """Get Medicare patient density score for specialty"""
        medicare_density = {
            'Geriatric Medicine': 95,
            'Podiatrist': 90,
            'Endocrinology - Diabetes': 85,
            'Wound Care - Physician Specialist': 80,
            'Cardiovascular Disease': 80,
            'Nephrology': 75,
            'Family Medicine': 70,
            'Internal Medicine': 70
        }
        return medicare_density.get(specialty, 50)

    def get_wound_care_likelihood(self, specialties: List[str]) -> int:
        """Calculate likelihood of seeing wound care patients"""
        wound_likelihood = {
            'Wound Care - Physician Specialist': 100,
            'Wound Care - Physician': 100,
            'Podiatrist': 85,
            'Surgery - Plastic/Reconstructive': 80,
            'Endocrinology - Diabetes': 75,
            'Vascular Surgery': 75,
            'Surgery - General': 70,
            'Infectious Disease': 65,
            'Dermatology - Mohs Surgery': 60
        }
        
        max_likelihood = max([wound_likelihood.get(spec, 30) for spec in specialties], default=30)
        return max_likelihood

    def run_full_extraction(self) -> pd.DataFrame:
        """Run full Medicare allograft lead extraction"""
        logger.info("🎯 STARTING MEDICARE ALLOGRAFT WOUND CARE EXTRACTION")
        
        # Load rural ZIP codes
        rural_zips = self.load_rural_zip_codes()
        self.rural_zip_codes = rural_zips
        
        # Process all NPPES chunks
        chunk_dir = self.base_dir / 'npidata_pfile_20050523-20250713_split'
        
        if not chunk_dir.exists():
            logger.error(f"NPPES split directory not found: {chunk_dir}")
            return pd.DataFrame()
        
        chunk_files = sorted(list(chunk_dir.glob("*.csv")))
        total_chunks = len(chunk_files)
        logger.info(f"Found {total_chunks} NPPES chunk files to process")
        
        all_leads = []
        
        for i, chunk_file in enumerate(chunk_files, 1):
            logger.info(f"Processing chunk {i}/{total_chunks}: {chunk_file.name}")
            chunk_leads = self.process_nppes_chunk(chunk_file, rural_zips, i)
            
            if len(chunk_leads) > 0:
                all_leads.append(chunk_leads)
        
        if not all_leads:
            logger.warning("❌ No leads found")
            return pd.DataFrame()
        
        # Combine all results
        final_leads = pd.concat(all_leads, ignore_index=True)
        
        # Remove duplicates
        final_leads = final_leads.drop_duplicates(subset=['NPI'])
        
        # Sort by Medicare allograft score (highest first)
        final_leads = final_leads.sort_values('Medicare_Allograft_Score', ascending=False)
        
        logger.info(f"🎯 MEDICARE ALLOGRAFT EXTRACTION COMPLETE")
        logger.info(f"Total leads extracted: {len(final_leads):,}")
        
        # Enhanced summary reporting
        self.print_extraction_summary(final_leads)
        
        return final_leads

    def print_extraction_summary(self, leads_df: pd.DataFrame):
        """Print comprehensive extraction summary"""
        if len(leads_df) == 0:
            return
        
        logger.info("\n" + "="*80)
        logger.info("MEDICARE ALLOGRAFT WOUND CARE LEADS SUMMARY")
        logger.info("="*80)
        
        # Overall stats
        logger.info(f"Total Leads: {len(leads_df):,}")
        rural_count = len(leads_df[leads_df['Is_Rural'] == True])
        logger.info(f"Rural Locations: {rural_count:,} ({rural_count/len(leads_df)*100:.1f}%)")
        
        # Score distribution
        a_plus = len(leads_df[leads_df['Medicare_Allograft_Score'] >= 90])
        a_grade = len(leads_df[leads_df['Medicare_Allograft_Score'].between(80, 89)])
        b_plus = len(leads_df[leads_df['Medicare_Allograft_Score'].between(70, 79)])
        
        logger.info(f"\nScore Distribution:")
        logger.info(f"  A+ (90-100): {a_plus:,} leads ({a_plus/len(leads_df)*100:.1f}%)")
        logger.info(f"  A  (80-89):  {a_grade:,} leads ({a_grade/len(leads_df)*100:.1f}%)")
        logger.info(f"  B+ (70-79):  {b_plus:,} leads ({b_plus/len(leads_df)*100:.1f}%)")
        
        # Top specialties
        logger.info(f"\nTop Target Specialties:")
        specialty_counts = leads_df['Primary_Specialty'].value_counts()
        for specialty, count in specialty_counts.head(10).items():
            score = self.medicare_allograft_scores.get(specialty, 0)
            pct = count/len(leads_df)*100
            logger.info(f"  {specialty}: {count:,} ({pct:.1f}%) - Priority: {score}")
        
        # Target categories
        logger.info(f"\nTarget Categories:")
        category_counts = leads_df['Target_Category'].value_counts()
        for category, count in category_counts.items():
            pct = count/len(leads_df)*100
            logger.info(f"  {category}: {count:,} ({pct:.1f}%)")
        
        # Top states
        logger.info(f"\nTop States:")
        state_counts = leads_df['State'].value_counts().head(10)
        for state, count in state_counts.items():
            rural_in_state = len(leads_df[(leads_df['State'] == state) & (leads_df['Is_Rural'] == True)])
            pct = count/len(leads_df)*100
            logger.info(f"  {state}: {count:,} ({pct:.1f}%) - Rural: {rural_in_state:,}")

if __name__ == "__main__":
    extractor = MedicareAllografLeadExtractor()
    leads_df = extractor.run_full_extraction()
    
    if len(leads_df) > 0:
        # Save results
        output_file = 'medicare_allograft_wound_care_leads.xlsx'
        leads_df.to_excel(output_file, index=False)
        logger.info(f"✅ Saved Medicare allograft leads to {output_file}")
        
        # Show top prospects
        top_leads = leads_df.head(25)
        logger.info(f"\n🌟 TOP 25 MEDICARE ALLOGRAFT WOUND CARE PROSPECTS:")
        for idx, row in top_leads.iterrows():
            logger.info(f"• Score: {row['Medicare_Allograft_Score']} | {row['Primary_Specialty']} | {row['City']}, {row['State']} | {row['All_Specialties']}")
    else:
        logger.error("❌ No Medicare allograft leads extracted") 