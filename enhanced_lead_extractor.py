#!/usr/bin/env python3
"""
Enhanced Lead Extractor - Maximum Contact Intelligence

Extracts comprehensive lead data including:
- Multiple phone numbers (practice, mailing, authorized official)
- Complete practice names and legal business names
- Detailed owner/authorized official information
- Full business addresses and contact details
- Business structure and ownership data
- EINs, licensing, and credential information

Target: Small rural physician groups with maximum actionable data
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedLeadExtractor:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        
        # Target specialty taxonomy codes
        self.target_taxonomies = {
            '213E00000X': 'Podiatrist',
            '207ND0900X': 'Dermatology - Mohs Surgery', 
            '163WW0000X': 'Wound Care - Nurse',
            '2251C2600X': 'Wound Care - Physical Therapist',  
            '261QH0600X': 'Wound Care - Clinic',
            '207Q00000X': 'Family Medicine',
            '208D00000X': 'General Practice',
            '207R00000X': 'Internal Medicine',
            '207XX0004X': 'Wound Care - Physician',
            '207XX0005X': 'Wound Care - Physician Specialist'
        }
        
        # Hospital/health system exclusion indicators
        self.hospital_indicators = [
            'HOSPITAL', 'HEALTH SYSTEM', 'MEDICAL CENTER', 'HEALTHCARE SYSTEM',
            'REGIONAL MEDICAL', 'MERCY', 'BAPTIST', 'METHODIST', 'PRESBYTERIAN',
            'SAINT ', 'ST ', 'UNIVERSITY', 'CLINIC NETWORK', 'HEALTHCARE NETWORK'
        ]
    
    def safe_str(self, value) -> str:
        """Safely convert value to string, handling NaN"""
        if pd.isna(value) or value is None:
            return ''
        return str(value).strip()

    def extract_comprehensive_lead_data(self, chunk_file: str) -> pd.DataFrame:
        """Extract maximum lead intelligence from NPPES chunk"""
        logger.info(f"Processing chunk: {chunk_file}")
        
        try:
            # Read NPPES chunk
            df = pd.read_csv(chunk_file, dtype=str, low_memory=False)
            logger.info(f"Loaded {len(df):,} records from {chunk_file}")
            
            # Filter for target specialties
            target_providers = self.filter_target_specialties(df)
            logger.info(f"Found {len(target_providers):,} target specialty providers")
            
            if target_providers.empty:
                return pd.DataFrame()
            
            # Extract comprehensive lead data
            leads = self.build_comprehensive_leads(target_providers)
            logger.info(f"Extracted {len(leads):,} comprehensive leads")
            
            return leads
            
        except Exception as e:
            logger.error(f"Error processing {chunk_file}: {e}")
            return pd.DataFrame()

    def filter_target_specialties(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter for target specialties with comprehensive data"""
        
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

    def build_comprehensive_leads(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build comprehensive lead records with maximum contact intelligence"""
        
        leads = []
        
        for _, row in df.iterrows():
            # Extract all specialties for this provider
            specialties = self.extract_all_specialties(row)
            
            # Build comprehensive lead record
            lead = {
                # Basic Provider Info
                'NPI': self.safe_str(row.get('NPI', '')),
                'Entity_Type': 'Individual' if row.get('Entity Type Code') == '1' else 'Organization',
                
                # Provider Names (Individual)
                'Provider_First_Name': self.safe_str(row.get('Provider First Name', '')),
                'Provider_Last_Name': self.safe_str(row.get('Provider Last Name (Legal Name)', '')),
                'Provider_Middle_Name': self.safe_str(row.get('Provider Middle Name', '')),
                'Provider_Name_Prefix': self.safe_str(row.get('Provider Name Prefix Text', '')),
                'Provider_Name_Suffix': self.safe_str(row.get('Provider Name Suffix Text', '')),
                'Provider_Credentials': self.safe_str(row.get('Provider Credential Text', '')),
                
                # Practice/Organization Names
                'Legal_Business_Name': self.safe_str(row.get('Provider Organization Name (Legal Business Name)', '')),
                'Other_Organization_Name': self.safe_str(row.get('Provider Other Organization Name', '')),
                'DBA_Name': self.determine_practice_name(row),
                
                # Primary Contact Phone Numbers
                'Practice_Phone': self.clean_phone(row.get('Provider Business Practice Location Address Telephone Number', '')),
                'Mailing_Phone': self.clean_phone(row.get('Provider Business Mailing Address Telephone Number', '')),
                'Primary_Phone': self.get_primary_phone(row),
                
                # Fax Numbers
                'Practice_Fax': self.clean_phone(row.get('Provider Business Practice Location Address Fax Number', '')),
                'Mailing_Fax': self.clean_phone(row.get('Provider Business Mailing Address Fax Number', '')),
                
                # Practice Location Address
                'Practice_Address_Line1': row.get('Provider First Line Business Practice Location Address', ''),
                'Practice_Address_Line2': row.get('Provider Second Line Business Practice Location Address', ''),
                'Practice_City': row.get('Provider Business Practice Location Address City Name', ''),
                'Practice_State': row.get('Provider Business Practice Location Address State Name', ''),
                'Practice_ZIP': row.get('Provider Business Practice Location Address Postal Code', ''),
                'Practice_Country': row.get('Provider Business Practice Location Address Country Code (If outside U.S.)', ''),
                
                # Mailing Address (if different)
                'Mailing_Address_Line1': row.get('Provider First Line Business Mailing Address', ''),
                'Mailing_Address_Line2': row.get('Provider Second Line Business Mailing Address', ''),
                'Mailing_City': row.get('Provider Business Mailing Address City Name', ''),
                'Mailing_State': row.get('Provider Business Mailing Address State Name', ''),
                'Mailing_ZIP': row.get('Provider Business Mailing Address Postal Code', ''),
                'Mailing_Country': row.get('Provider Business Mailing Address Country Code (If outside U.S.)', ''),
                
                # Owner/Authorized Official Information
                'Owner_First_Name': row.get('Authorized Official First Name', ''),
                'Owner_Last_Name': row.get('Authorized Official Last Name', ''),
                'Owner_Middle_Name': row.get('Authorized Official Middle Name', ''),
                'Owner_Name_Prefix': row.get('Authorized Official Name Prefix Text', ''),
                'Owner_Name_Suffix': row.get('Authorized Official Name Suffix Text', ''),
                'Owner_Title': row.get('Authorized Official Title or Position', ''),
                'Owner_Credentials': row.get('Authorized Official Credential Text', ''),
                'Owner_Phone': self.clean_phone(row.get('Authorized Official Telephone Number', '')),
                'Owner_Full_Name': self.build_full_name(
                    self.safe_str(row.get('Authorized Official First Name', '')),
                    self.safe_str(row.get('Authorized Official Last Name', '')),
                    self.safe_str(row.get('Authorized Official Middle Name', '')),
                    self.safe_str(row.get('Authorized Official Name Prefix Text', '')),
                    self.safe_str(row.get('Authorized Official Name Suffix Text', ''))
                ),
                
                # Business Structure & Legal Info
                'Is_Sole_Proprietor': row.get('Is Sole Proprietor', ''),
                'Is_Organization_Subpart': row.get('Is Organization Subpart', ''),
                'Parent_Organization': row.get('Parent Organization LBN', ''),
                'Parent_TIN': row.get('Parent Organization TIN', ''),
                'EIN': row.get('Employer Identification Number (EIN)', ''),
                
                # Specialties & Licensing
                'Primary_Specialty': specialties[0] if specialties else '',
                'All_Specialties': ' | '.join(specialties),
                'Specialty_Count': len(specialties),
                'Primary_Taxonomy_Code': self.get_primary_taxonomy(row),
                
                # License Information
                'Primary_License_Number': row.get('Provider License Number_1', ''),
                'Primary_License_State': row.get('Provider License Number State Code_1', ''),
                
                # Administrative Dates
                'Enumeration_Date': row.get('Provider Enumeration Date', ''),
                'Last_Update_Date': row.get('Last Update Date', ''),
                'Certification_Date': row.get('Certification Date', ''),
                
                # Provider Demographics
                'Gender': row.get('Provider Sex Code', ''),
                
                # Data Quality Indicators
                'Has_Practice_Phone': 'Yes' if self.clean_phone(row.get('Provider Business Practice Location Address Telephone Number', '')) else 'No',
                'Has_Owner_Phone': 'Yes' if self.clean_phone(row.get('Authorized Official Telephone Number', '')) else 'No',
                'Has_Multiple_Phones': self.count_available_phones(row),
                'Address_Match': 'Same' if self.addresses_match(row) else 'Different',
                
                # ZIP Code for rural matching
                'ZIP_Code': self.extract_zip_code(row.get('Provider Business Practice Location Address Postal Code', ''))
            }
            
            leads.append(lead)
        
        return pd.DataFrame(leads)

    def extract_all_specialties(self, row) -> List[str]:
        """Extract all specialties for a provider"""
        specialties = []
        
        taxonomy_cols = [col for col in row.index if 'Healthcare Provider Taxonomy Code_' in col]
        
        for col in taxonomy_cols:
            taxonomy_code = row.get(col, '')
            if pd.notna(taxonomy_code) and taxonomy_code in self.target_taxonomies:
                specialty = self.target_taxonomies[taxonomy_code]
                if specialty not in specialties:
                    specialties.append(specialty)
        
        return specialties

    def determine_practice_name(self, row) -> str:
        """Determine the best practice name to use"""
        legal_name = self.safe_str(row.get('Provider Organization Name (Legal Business Name)', ''))
        other_name = self.safe_str(row.get('Provider Other Organization Name', ''))
        
        # For individuals, use provider name
        if row.get('Entity Type Code') == '1':
            first = self.safe_str(row.get('Provider First Name', ''))
            last = self.safe_str(row.get('Provider Last Name (Legal Name)', ''))
            credentials = self.safe_str(row.get('Provider Credential Text', ''))
            
            if first and last:
                name = f"{first} {last}"
                if credentials:
                    name += f", {credentials}"
                return name
        
        # For organizations, prefer other name over legal name if available
        if other_name:
            return other_name
        elif legal_name:
            return legal_name
        
        return ''

    def clean_phone(self, phone: str) -> str:
        """Clean and format phone number"""
        if pd.isna(phone) or not phone:
            return ''
        
        # Remove all non-digits
        digits = re.sub(r'\D', '', str(phone))
        
        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        elif len(digits) > 0:
            return digits  # Return digits if not standard format
        
        return ''

    def get_primary_phone(self, row) -> str:
        """Get the best primary phone number"""
        practice_phone = self.clean_phone(row.get('Provider Business Practice Location Address Telephone Number', ''))
        owner_phone = self.clean_phone(row.get('Authorized Official Telephone Number', ''))
        mailing_phone = self.clean_phone(row.get('Provider Business Mailing Address Telephone Number', ''))
        
        # Prefer practice phone, then owner phone, then mailing phone
        return practice_phone or owner_phone or mailing_phone

    def count_available_phones(self, row) -> int:
        """Count how many phone numbers are available"""
        phones = [
            self.clean_phone(row.get('Provider Business Practice Location Address Telephone Number', '')),
            self.clean_phone(row.get('Authorized Official Telephone Number', '')),
            self.clean_phone(row.get('Provider Business Mailing Address Telephone Number', ''))
        ]
        return len([p for p in phones if p])

    def addresses_match(self, row) -> bool:
        """Check if mailing and practice addresses match"""
        practice_addr = (
            row.get('Provider First Line Business Practice Location Address', '') +
            row.get('Provider Business Practice Location Address City Name', '') +
            row.get('Provider Business Practice Location Address State Name', '') +
            row.get('Provider Business Practice Location Address Postal Code', '')
        ).replace(' ', '').upper()
        
        mailing_addr = (
            row.get('Provider First Line Business Mailing Address', '') +
            row.get('Provider Business Mailing Address City Name', '') +
            row.get('Provider Business Mailing Address State Name', '') +
            row.get('Provider Business Mailing Address Postal Code', '')
        ).replace(' ', '').upper()
        
        return practice_addr == mailing_addr

    def build_full_name(self, first: str, last: str, middle: str = '', prefix: str = '', suffix: str = '') -> str:
        """Build full formatted name"""
        parts = []
        
        if prefix:
            parts.append(prefix)
        if first:
            parts.append(first)
        if middle:
            parts.append(middle)
        if last:
            parts.append(last)
        if suffix:
            parts.append(suffix)
        
        return ' '.join(parts).strip()

    def get_primary_taxonomy(self, row) -> str:
        """Get the primary taxonomy code"""
        return row.get('Healthcare Provider Taxonomy Code_1', '')

    def extract_zip_code(self, postal_code: str) -> str:
        """Extract 5-digit ZIP code"""
        if pd.isna(postal_code) or not postal_code:
            return ''
        
        # Extract first 5 digits
        digits = re.sub(r'\D', '', str(postal_code))
        return digits[:5] if len(digits) >= 5 else digits

    def load_rural_zips(self) -> set:
        """Load rural ZIP codes from RUCA data"""
        try:
            ruca_file = self.base_dir / "RUCA2010zipcode.csv"
            if not ruca_file.exists():
                logger.warning("RUCA file not found, will process all ZIPs")
                return set()
            
            ruca_df = pd.read_csv(ruca_file)
            # Rural codes: 4-10
            rural_df = ruca_df[ruca_df['RUCA2'].between(4, 10)]
            # Handle the quoted column name
            zip_col = "'ZIP_CODE'" if "'ZIP_CODE'" in ruca_df.columns else 'ZIP_CODE'
            rural_zips = set(rural_df[zip_col].astype(str).str.strip("'").str.zfill(5))
            logger.info(f"Loaded {len(rural_zips):,} rural ZIP codes")
            return rural_zips
            
        except Exception as e:
            logger.error(f"Error loading RUCA data: {e}")
            return set()

    def process_all_chunks(self) -> pd.DataFrame:
        """Process all NPPES chunks and extract comprehensive leads"""
        chunk_dir = self.base_dir / "npidata_pfile_20050523-20250713_split"
        
        if not chunk_dir.exists():
            logger.error(f"Chunk directory not found: {chunk_dir}")
            return pd.DataFrame()
        
        # Load rural ZIP codes
        rural_zips = self.load_rural_zips()
        
        all_leads = []
        chunk_files = sorted(list(chunk_dir.glob("*.csv")))
        
        logger.info(f"Processing {len(chunk_files)} chunk files")
        
        for i, chunk_file in enumerate(chunk_files, 1):
            logger.info(f"Processing chunk {i}/{len(chunk_files)}: {chunk_file.name}")
            
            chunk_leads = self.extract_comprehensive_lead_data(chunk_file)
            
            if not chunk_leads.empty:
                # Filter for rural ZIPs if RUCA data available
                if rural_zips:
                    rural_mask = chunk_leads['ZIP_Code'].isin(rural_zips)
                    chunk_leads = chunk_leads[rural_mask]
                    logger.info(f"Found {len(chunk_leads):,} rural leads in chunk {i}")
                
                all_leads.append(chunk_leads)
        
        if not all_leads:
            logger.warning("No leads found")
            return pd.DataFrame()
        
        # Combine all leads
        final_leads = pd.concat(all_leads, ignore_index=True)
        
        # Group by practice/owner for small practice identification
        final_leads = self.identify_practice_groups(final_leads)
        
        logger.info(f"Total comprehensive leads extracted: {len(final_leads):,}")
        return final_leads

    def identify_practice_groups(self, leads_df: pd.DataFrame) -> pd.DataFrame:
        """Group providers by practice and identify small groups (1-5 providers)"""
        
        # Create grouping key based on owner + address
        leads_df['Practice_Group_Key'] = (
            leads_df['Owner_Full_Name'].fillna('') + '|' +
            leads_df['Practice_Address_Line1'].fillna('') + '|' +
            leads_df['Practice_ZIP'].fillna('')
        )
        
        # Count providers per group
        group_counts = leads_df['Practice_Group_Key'].value_counts()
        small_groups = group_counts[group_counts <= 5].index
        
        # Filter for small groups only
        small_practice_leads = leads_df[leads_df['Practice_Group_Key'].isin(small_groups)].copy()
        
        # Add group size information
        small_practice_leads['Practice_Group_Size'] = small_practice_leads['Practice_Group_Key'].map(group_counts)
        
        # Remove the temporary grouping key
        small_practice_leads = small_practice_leads.drop('Practice_Group_Key', axis=1)
        
        return small_practice_leads

    def save_comprehensive_leads(self, leads_df: pd.DataFrame, filename: str = "comprehensive_rural_physician_leads.xlsx"):
        """Save comprehensive leads to Excel with multiple tabs"""
        
        output_file = self.base_dir / filename
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # All leads
            leads_df.to_excel(writer, sheet_name='All_Comprehensive_Leads', index=False)
            
            # Leads with owner phone numbers
            owner_phone_leads = leads_df[leads_df['Has_Owner_Phone'] == 'Yes']
            owner_phone_leads.to_excel(writer, sheet_name='Leads_With_Owner_Phone', index=False)
            
            # High-value specialties
            podiatry_leads = leads_df[leads_df['All_Specialties'].str.contains('Podiatrist', na=False)]
            if not podiatry_leads.empty:
                podiatry_leads.to_excel(writer, sheet_name='Podiatrist_Leads', index=False)
            
            wound_care_leads = leads_df[leads_df['All_Specialties'].str.contains('Wound Care', na=False)]
            if not wound_care_leads.empty:
                wound_care_leads.to_excel(writer, sheet_name='Wound_Care_Leads', index=False)
            
            mohs_leads = leads_df[leads_df['All_Specialties'].str.contains('Mohs Surgery', na=False)]
            if not mohs_leads.empty:
                mohs_leads.to_excel(writer, sheet_name='Mohs_Surgery_Leads', index=False)
            
            # Solo practitioners
            solo_leads = leads_df[leads_df['Practice_Group_Size'] == 1]
            solo_leads.to_excel(writer, sheet_name='Solo_Practitioners', index=False)
            
            # Multi-provider small groups
            small_groups = leads_df[leads_df['Practice_Group_Size'].between(2, 5)]
            if not small_groups.empty:
                small_groups.to_excel(writer, sheet_name='Small_Group_Practices', index=False)
        
        logger.info(f"Comprehensive leads saved to: {output_file}")
        
        # Print summary
        self.print_comprehensive_summary(leads_df)

    def print_comprehensive_summary(self, leads_df: pd.DataFrame):
        """Print comprehensive lead summary"""
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE RURAL PHYSICIAN LEADS SUMMARY")
        print(f"{'='*60}")
        
        print(f"Total Leads: {len(leads_df):,}")
        print(f"Leads with Owner Phone: {len(leads_df[leads_df['Has_Owner_Phone'] == 'Yes']):,}")
        print(f"Leads with Practice Phone: {len(leads_df[leads_df['Has_Practice_Phone'] == 'Yes']):,}")
        print(f"Leads with Multiple Phones: {len(leads_df[leads_df['Has_Multiple_Phones'] >= 2]):,}")
        
        print(f"\nBy Practice Size:")
        size_counts = leads_df['Practice_Group_Size'].value_counts().sort_index()
        for size, count in size_counts.items():
            print(f"  {size} provider(s): {count:,} leads")
        
        print(f"\nBy Specialty:")
        specialty_counts = {}
        for specialties in leads_df['All_Specialties']:
            if pd.notna(specialties):
                for specialty in specialties.split(' | '):
                    specialty_counts[specialty] = specialty_counts.get(specialty, 0) + 1
        
        for specialty, count in sorted(specialty_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {specialty}: {count:,}")
        
        print(f"\nData Quality:")
        print(f"  EIN Available: {len(leads_df[leads_df['EIN'].notna() & (leads_df['EIN'] != '')]):,}")
        print(f"  Sole Proprietors: {len(leads_df[leads_df['Is_Sole_Proprietor'] == 'Y']):,}")
        print(f"  Practice ≠ Mailing Address: {len(leads_df[leads_df['Address_Match'] == 'Different']):,}")

def main():
    """Main execution"""
    extractor = EnhancedLeadExtractor()
    
    print("Starting comprehensive lead extraction...")
    leads_df = extractor.process_all_chunks()
    
    if not leads_df.empty:
        extractor.save_comprehensive_leads(leads_df)
        print(f"\n✅ Successfully extracted {len(leads_df):,} comprehensive leads!")
    else:
        print("❌ No leads found")

if __name__ == "__main__":
    main() 