#!/usr/bin/env python3
"""
Rural Physician Group Finder

Identifies small physician groups (1-5 clinicians) that are:
1. Independently owned (not hospital/health system affiliated) 
2. Located in rural ZIP codes
3. Include Podiatry, Wound Care, Mohs Surgery, or Primary Care providers
4. Provides owner/contact information when available

Uses NPPES data + additional datasets as available.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import openpyxl
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RuralPhysicianFinder:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.target_taxonomies = {
            '213E00000X': 'Podiatrist',
            '207ND0900X': 'Dermatology - Mohs Surgery', 
            '163WW0000X': 'Wound Care - Nurse',
            '2251C2600X': 'Wound Care - Physical Therapist',
            '261QH0600X': 'Wound Care - Clinic',
            '207Q00000X': 'Family Medicine',
            '208D00000X': 'General Practice',
            '207QA0000X': 'Family Medicine - Adolescent Medicine',
            '207QB0002X': 'Family Medicine - Obstetrics',
            '207QG0300X': 'Family Medicine - Geriatric Medicine'
        }
        
        # Hospital/health system indicators (common names to filter out)
        self.hospital_indicators = [
            'hospital', 'health system', 'medical center', 'healthcare system',
            'regional medical', 'memorial', 'saint ', 'st ', 'st.', 'kaiser',
            'cleveland clinic', 'mayo clinic', 'johns hopkins', 'mount sinai',
            'cedars-sinai', 'mass general', 'brigham', 'presbyterian',
            'methodist', 'baptist', 'catholic', 'adventist', 'mercy',
            'university medical', 'veterans affairs', 'va medical'
        ]
        
        # Load rural ZIP codes
        self.rural_zips = self._load_rural_zips()
        
    def _load_rural_zips(self) -> set:
        """Load rural ZIP codes from RUCA data"""
        try:
            # Try to read the RUCA Excel file
            ruca_file = self.base_dir / "ruca2010zipcode.xlsx"
            if ruca_file.exists():
                df = pd.read_excel(ruca_file)
                # RUCA codes 4-10 are considered rural/small town
                rural_df = df[df['RUCA2010'] >= 4]
                rural_zips = set(rural_df['ZIP_CODE'].astype(str).str.zfill(5))
                logger.info(f"Loaded {len(rural_zips)} rural ZIP codes from RUCA data")
                return rural_zips
            else:
                logger.warning("RUCA file not found. Will create placeholder rural filter.")
                return set()
        except Exception as e:
            logger.error(f"Error loading RUCA data: {e}")
            return set()
    
    def _is_likely_independent(self, org_name: str, authorized_official: str = "") -> bool:
        """
        Determine if organization is likely independent (not hospital/health system)
        """
        if not org_name:
            return True  # Individual providers
            
        org_name_lower = org_name.lower()
        
        # Check for hospital/health system indicators
        for indicator in self.hospital_indicators:
            if indicator in org_name_lower:
                return False
                
        # Additional patterns that suggest health system affiliation
        health_system_patterns = [
            'llc', 'inc', 'incorporated', 'corporation', 'corp',
            'associates', 'partners', 'group', 'clinic', 'practice',
            'medical associates', 'family practice', 'internal medicine'
        ]
        
        # These are actually GOOD indicators for independent practices
        independent_indicators = [
            'family practice', 'medical group', 'clinic', 'associates',
            'internal medicine', 'pediatrics', 'dermatology'
        ]
        
        # Has independent indicators but no hospital indicators = likely independent
        has_independent = any(ind in org_name_lower for ind in independent_indicators)
        
        return has_independent or len(org_name) < 50  # Short names often independent
    
    def _is_target_specialty(self, taxonomy_codes: List[str]) -> bool:
        """Check if any taxonomy codes match our target specialties"""
        return any(code in self.target_taxonomies for code in taxonomy_codes if code)
    
    def _is_rural_zip(self, zip_code: str) -> bool:
        """Check if ZIP code is rural based on RUCA data"""
        if not self.rural_zips:
            # Fallback: assume certain ZIP patterns are more rural
            # This is a rough approximation
            return len(zip_code) >= 5 and zip_code[:3] not in ['100', '101', '102', '103', '104']
            
        zip5 = zip_code[:5] if len(zip_code) >= 5 else zip_code
        return zip5 in self.rural_zips
    
    def process_nppes_chunk(self, chunk_file: Path) -> pd.DataFrame:
        """Process a single NPPES CSV chunk"""
        logger.info(f"Processing {chunk_file.name}")
        
        try:
            # Read chunk with specific columns of interest
            columns_of_interest = [
                'NPI', 'Entity Type Code', 'Provider Organization Name (Legal Business Name)',
                'Provider Last Name (Legal Name)', 'Provider First Name', 
                'Provider Business Practice Location Address Postal Code',
                'Provider Business Mailing Address Postal Code',
                'Authorized Official Last Name', 'Authorized Official First Name',
                'Authorized Official Title or Position',
                'Provider Business Practice Location Address Telephone Number',
                'Healthcare Provider Taxonomy Code_1', 'Healthcare Provider Taxonomy Code_2',
                'Healthcare Provider Taxonomy Code_3', 'Healthcare Provider Taxonomy Code_4',
                'Healthcare Provider Taxonomy Code_5'
            ]
            
            # Read in chunks to handle large files
            chunk_dfs = []
            for df_chunk in pd.read_csv(chunk_file, chunksize=10000, low_memory=False):
                # Filter for our target taxonomies first
                taxonomy_cols = [col for col in df_chunk.columns if 'Healthcare Provider Taxonomy Code_' in col]
                
                # Create mask for target specialties
                target_mask = pd.Series(False, index=df_chunk.index)
                for tax_col in taxonomy_cols:
                    if tax_col in df_chunk.columns:
                        target_mask |= df_chunk[tax_col].isin(self.target_taxonomies.keys())
                
                # Filter chunk
                filtered_chunk = df_chunk[target_mask].copy()
                
                if len(filtered_chunk) > 0:
                    chunk_dfs.append(filtered_chunk)
            
            if not chunk_dfs:
                return pd.DataFrame()
                
            df = pd.concat(chunk_dfs, ignore_index=True)
            
            # Additional filtering
            results = []
            
            for _, row in df.iterrows():
                # Get ZIP code (prefer practice location, fall back to mailing)
                zip_code = row.get('Provider Business Practice Location Address Postal Code', '')
                if not zip_code:
                    zip_code = row.get('Provider Business Mailing Address Postal Code', '')
                
                zip_code = str(zip_code).strip()[:5] if zip_code else ''
                
                # Skip if not rural
                if not self._is_rural_zip(zip_code):
                    continue
                
                # Get organization info
                org_name = row.get('Provider Organization Name (Legal Business Name)', '')
                
                # Check if likely independent
                authorized_official = f"{row.get('Authorized Official First Name', '')} {row.get('Authorized Official Last Name', '')}"
                if not self._is_likely_independent(org_name, authorized_official):
                    continue
                
                # Get taxonomy codes
                taxonomy_codes = []
                for i in range(1, 6):
                    tax_code = row.get(f'Healthcare Provider Taxonomy Code_{i}', '')
                    if tax_code:
                        taxonomy_codes.append(tax_code)
                
                # Build result record
                result = {
                    'NPI': row.get('NPI', ''),
                    'Entity_Type': row.get('Entity Type Code', ''),
                    'Organization_Name': org_name,
                    'Provider_Last_Name': row.get('Provider Last Name (Legal Name)', ''),
                    'Provider_First_Name': row.get('Provider First Name', ''),
                    'ZIP_Code': zip_code,
                    'Phone': row.get('Provider Business Practice Location Address Telephone Number', ''),
                    'Authorized_Official_Name': authorized_official.strip(),
                    'Authorized_Official_Title': row.get('Authorized Official Title or Position', ''),
                    'Primary_Taxonomy': taxonomy_codes[0] if taxonomy_codes else '',
                    'Primary_Specialty': self.target_taxonomies.get(taxonomy_codes[0], '') if taxonomy_codes else '',
                    'All_Taxonomies': '|'.join(taxonomy_codes),
                    'All_Specialties': '|'.join([self.target_taxonomies.get(tax, tax) for tax in taxonomy_codes if tax in self.target_taxonomies])
                }
                
                results.append(result)
            
            result_df = pd.DataFrame(results)
            logger.info(f"Found {len(result_df)} potential rural providers in {chunk_file.name}")
            return result_df
            
        except Exception as e:
            logger.error(f"Error processing {chunk_file}: {e}")
            return pd.DataFrame()
    
    def find_small_groups(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify small groups (1-5 providers) from the filtered data"""
        if df.empty:
            return df
            
        # Group by organization name and ZIP to identify practice groups
        # Use a combination of org name, ZIP, and phone for grouping
        df['Group_Key'] = df['Organization_Name'].fillna('') + '|' + df['ZIP_Code'] + '|' + df['Phone'].fillna('')
        
        # Count providers per group
        group_counts = df.groupby('Group_Key').size()
        small_groups = group_counts[(group_counts >= 1) & (group_counts <= 5)]
        
        # Filter to only small groups
        small_group_providers = df[df['Group_Key'].isin(small_groups.index)].copy()
        
        # Add group size info
        small_group_providers['Group_Size'] = small_group_providers['Group_Key'].map(group_counts)
        
        # Sort by group, then by provider name
        small_group_providers = small_group_providers.sort_values([
            'Group_Key', 'Provider_Last_Name', 'Provider_First_Name'
        ])
        
        return small_group_providers
    
    def create_call_list(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create a call list with contact information"""
        if df.empty:
            return df
            
        # Create summary by group
        call_list = []
        
        for group_key, group_df in df.groupby('Group_Key'):
            # Get group information
            first_record = group_df.iloc[0]
            
            # Aggregate specialties
            all_specialties = set()
            for _, row in group_df.iterrows():
                specialties = row['All_Specialties'].split('|') if row['All_Specialties'] else []
                all_specialties.update([s for s in specialties if s])
            
            # Contact info - prefer authorized official, fall back to first provider
            contact_name = first_record['Authorized_Official_Name']
            contact_title = first_record['Authorized_Official_Title']
            
            if not contact_name.strip():
                contact_name = f"{first_record['Provider_First_Name']} {first_record['Provider_Last_Name']}"
                contact_title = "Provider"
            
            call_record = {
                'Organization_Name': first_record['Organization_Name'],
                'Group_Size': len(group_df),
                'ZIP_Code': first_record['ZIP_Code'],
                'Phone': first_record['Phone'],
                'Contact_Name': contact_name,
                'Contact_Title': contact_title,
                'Specialties': ', '.join(sorted(all_specialties)),
                'Provider_Names': '; '.join([f"{row['Provider_First_Name']} {row['Provider_Last_Name']}" 
                                           for _, row in group_df.iterrows()]),
                'NPIs': '; '.join([str(row['NPI']) for _, row in group_df.iterrows()])
            }
            
            call_list.append(call_record)
        
        call_list_df = pd.DataFrame(call_list)
        
        # Sort by specialties (prioritize our key specialties)
        priority_specialties = ['Podiatrist', 'Dermatology - Mohs Surgery', 'Wound Care']
        
        def specialty_priority(specialties):
            for i, priority_spec in enumerate(priority_specialties):
                if priority_spec in specialties:
                    return i
            return len(priority_specialties)
        
        call_list_df['Priority'] = call_list_df['Specialties'].apply(specialty_priority)
        call_list_df = call_list_df.sort_values(['Priority', 'Organization_Name'])
        
        return call_list_df.drop('Priority', axis=1)
    
    def process_all_chunks(self) -> pd.DataFrame:
        """Process all NPPES chunks and combine results"""
        split_dir = self.base_dir / "npidata_pfile_20050523-20250713_split"
        
        if not split_dir.exists():
            logger.error(f"Split directory not found: {split_dir}")
            return pd.DataFrame()
        
        chunk_files = list(split_dir.glob("*.csv"))
        logger.info(f"Found {len(chunk_files)} chunk files to process")
        
        all_results = []
        
        for chunk_file in chunk_files:
            chunk_result = self.process_nppes_chunk(chunk_file)
            if not chunk_result.empty:
                all_results.append(chunk_result)
        
        if not all_results:
            logger.warning("No results found in any chunks")
            return pd.DataFrame()
        
        # Combine all results
        combined_df = pd.concat(all_results, ignore_index=True)
        logger.info(f"Total providers found: {len(combined_df)}")
        
        # Remove duplicates (same NPI)
        combined_df = combined_df.drop_duplicates(subset=['NPI'])
        logger.info(f"Unique providers after deduplication: {len(combined_df)}")
        
        return combined_df
    
    def run_analysis(self) -> Dict[str, pd.DataFrame]:
        """Run the complete analysis"""
        logger.info("Starting rural physician group analysis...")
        
        # Process all NPPES data
        all_providers = self.process_all_chunks()
        
        if all_providers.empty:
            logger.warning("No providers found matching criteria")
            return {'providers': pd.DataFrame(), 'small_groups': pd.DataFrame(), 'call_list': pd.DataFrame()}
        
        # Find small groups
        small_groups = self.find_small_groups(all_providers)
        logger.info(f"Providers in small groups (1-5): {len(small_groups)}")
        
        # Create call list
        call_list = self.create_call_list(small_groups)
        logger.info(f"Total practice groups to contact: {len(call_list)}")
        
        return {
            'providers': all_providers,
            'small_groups': small_groups, 
            'call_list': call_list
        }
    
    def save_results(self, results: Dict[str, pd.DataFrame], output_dir: str = "results"):
        """Save results to CSV files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        for name, df in results.items():
            if not df.empty:
                filename = output_path / f"rural_physicians_{name}.csv"
                df.to_csv(filename, index=False)
                logger.info(f"Saved {len(df)} records to {filename}")

def main():
    """Main execution function"""
    finder = RuralPhysicianFinder()
    
    # Run the analysis
    results = finder.run_analysis()
    
    # Save results
    finder.save_results(results)
    
    # Print summary
    print("\n" + "="*60)
    print("RURAL PHYSICIAN GROUP ANALYSIS SUMMARY")
    print("="*60)
    
    if results['call_list'].empty:
        print("No qualifying physician groups found.")
        print("\nThis could be due to:")
        print("- Very restrictive filtering criteria")
        print("- Limited rural ZIP code data")
        print("- Most providers being part of large health systems")
        print("\nConsider:")
        print("1. Expanding geographic criteria")
        print("2. Adding more specialty taxonomy codes")
        print("3. Getting complete DAC file for better group size detection")
    else:
        call_list = results['call_list']
        print(f"Found {len(call_list)} small physician groups to contact")
        print(f"Total providers: {results['small_groups']['Group_Size'].sum()}")
        print(f"Average group size: {results['small_groups']['Group_Size'].mean():.1f}")
        
        print("\nTop 10 Groups to Contact:")
        print("-" * 60)
        for _, row in call_list.head(10).iterrows():
            print(f"• {row['Organization_Name']}")
            print(f"  Contact: {row['Contact_Name']} ({row['Contact_Title']})")
            print(f"  Phone: {row['Phone']}")
            print(f"  Specialties: {row['Specialties']}")
            print(f"  Group Size: {row['Group_Size']} providers")
            print(f"  ZIP: {row['ZIP_Code']}")
            print()

if __name__ == "__main__":
    main() 