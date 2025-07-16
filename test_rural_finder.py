#!/usr/bin/env python3
"""
Test version of Rural Physician Finder - processes just one chunk for testing
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestRuralPhysicianFinder:
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
        
        # Hospital/health system indicators
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
        """Load rural ZIP codes from manual file or RUCA data"""
        try:
            # Try manual rural zips first
            manual_file = self.base_dir / "manual_rural_zips.csv"
            if manual_file.exists():
                df = pd.read_csv(manual_file)
                rural_zips = set(df['ZIP_CODE'].astype(str).str.zfill(5))
                logger.info(f"Loaded {len(rural_zips)} rural ZIP codes from manual file")
                return rural_zips
            
            # Fall back to RUCA Excel file if exists
            ruca_file = self.base_dir / "ruca2010zipcode.xlsx"
            if ruca_file.exists():
                df = pd.read_excel(ruca_file)
                rural_df = df[df['RUCA2010'] >= 4]
                rural_zips = set(rural_df['ZIP_CODE'].astype(str).str.zfill(5))
                logger.info(f"Loaded {len(rural_zips)} rural ZIP codes from RUCA data")
                return rural_zips
                
            logger.warning("No rural ZIP file found. Using fallback logic.")
            return set()
        except Exception as e:
            logger.error(f"Error loading rural ZIP data: {e}")
            return set()
    
    def _is_likely_independent(self, org_name: str, authorized_official: str = "") -> bool:
        """Determine if organization is likely independent"""
        if not org_name:
            return True  # Individual providers
            
        org_name_lower = org_name.lower()
        
        # Check for hospital/health system indicators
        for indicator in self.hospital_indicators:
            if indicator in org_name_lower:
                return False
                
        # These are GOOD indicators for independent practices
        independent_indicators = [
            'family practice', 'medical group', 'clinic', 'associates',
            'internal medicine', 'pediatrics', 'dermatology', 'primary care'
        ]
        
        has_independent = any(ind in org_name_lower for ind in independent_indicators)
        return has_independent or len(org_name) < 50  # Short names often independent
    
    def _is_rural_zip(self, zip_code: str) -> bool:
        """Check if ZIP code is rural"""
        if not self.rural_zips:
            # Fallback logic for very basic rural detection
            return len(zip_code) >= 5 and zip_code[:3] not in ['100', '101', '102', '103', '104']
            
        zip5 = zip_code[:5] if len(zip_code) >= 5 else zip_code
        return zip5 in self.rural_zips
    
    def test_single_chunk(self) -> pd.DataFrame:
        """Test processing on a single chunk"""
        split_dir = self.base_dir / "npidata_pfile_20050523-20250713_split"
        
        if not split_dir.exists():
            logger.error(f"Split directory not found: {split_dir}")
            return pd.DataFrame()
        
        chunk_files = list(split_dir.glob("*.csv"))
        if not chunk_files:
            logger.error("No chunk files found")
            return pd.DataFrame()
        
        # Process just the first chunk
        test_file = chunk_files[0]
        logger.info(f"Testing with file: {test_file.name}")
        
        try:
            # Read a small sample first
            sample_df = pd.read_csv(test_file, nrows=1000, low_memory=False)
            logger.info(f"Sample loaded with {len(sample_df)} rows and {len(sample_df.columns)} columns")
            
            # Check what taxonomy columns exist
            taxonomy_cols = [col for col in sample_df.columns if 'Healthcare Provider Taxonomy Code_' in col]
            logger.info(f"Found taxonomy columns: {taxonomy_cols}")
            
            # Filter for target specialties
            target_mask = pd.Series(False, index=sample_df.index)
            for tax_col in taxonomy_cols:
                target_mask |= sample_df[tax_col].isin(self.target_taxonomies.keys())
            
            filtered_df = sample_df[target_mask].copy()
            logger.info(f"Found {len(filtered_df)} providers with target specialties")
            
            # Process each row
            results = []
            for idx, row in filtered_df.iterrows():
                # Get ZIP code
                zip_code = row.get('Provider Business Practice Location Address Postal Code', '')
                if not zip_code:
                    zip_code = row.get('Provider Business Mailing Address Postal Code', '')
                zip_code = str(zip_code).strip()[:5] if zip_code else ''
                
                # Check if rural
                is_rural = self._is_rural_zip(zip_code)
                
                # Get organization info
                org_name = row.get('Provider Organization Name (Legal Business Name)', '')
                
                # Check if independent
                authorized_official = f"{row.get('Authorized Official First Name', '')} {row.get('Authorized Official Last Name', '')}"
                is_independent = self._is_likely_independent(org_name, authorized_official)
                
                # Get taxonomy codes
                taxonomy_codes = []
                for tax_col in taxonomy_cols:
                    tax_code = row.get(tax_col, '')
                    if tax_code and tax_code in self.target_taxonomies:
                        taxonomy_codes.append(tax_code)
                
                # Create result record
                result = {
                    'NPI': row.get('NPI', ''),
                    'Organization_Name': org_name,
                    'Provider_Name': f"{row.get('Provider First Name', '')} {row.get('Provider Last Name (Legal Name)', '')}",
                    'ZIP_Code': zip_code,
                    'Is_Rural': is_rural,
                    'Is_Independent': is_independent,
                    'Phone': row.get('Provider Business Practice Location Address Telephone Number', ''),
                    'Authorized_Official': authorized_official.strip(),
                    'Primary_Specialty': self.target_taxonomies.get(taxonomy_codes[0], '') if taxonomy_codes else '',
                    'All_Specialties': '|'.join([self.target_taxonomies.get(tax, '') for tax in taxonomy_codes]),
                    'Meets_Criteria': is_rural and is_independent and len(taxonomy_codes) > 0
                }
                
                results.append(result)
            
            result_df = pd.DataFrame(results)
            logger.info(f"Processed {len(result_df)} total providers")
            
            # Show summary
            if len(result_df) > 0:
                rural_count = result_df['Is_Rural'].sum()
                independent_count = result_df['Is_Independent'].sum()
                meets_criteria = result_df['Meets_Criteria'].sum()
                
                logger.info(f"Rural providers: {rural_count}")
                logger.info(f"Independent providers: {independent_count}")
                logger.info(f"Meets all criteria: {meets_criteria}")
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error processing test chunk: {e}")
            return pd.DataFrame()

def main():
    """Test the pipeline"""
    print("Testing Rural Physician Finder")
    print("=" * 40)
    
    finder = TestRuralPhysicianFinder()
    
    # Test single chunk
    test_results = finder.test_single_chunk()
    
    if test_results.empty:
        print("No results from test - check logs for issues")
    else:
        print(f"\nTest Results Summary:")
        print(f"Total providers processed: {len(test_results)}")
        print(f"Rural providers: {test_results['Is_Rural'].sum()}")
        print(f"Independent providers: {test_results['Is_Independent'].sum()}")
        print(f"Providers meeting all criteria: {test_results['Meets_Criteria'].sum()}")
        
        # Show some examples
        qualifying = test_results[test_results['Meets_Criteria'] == True]
        if len(qualifying) > 0:
            print(f"\nExample qualifying providers:")
            for idx, row in qualifying.head(5).iterrows():
                print(f"• {row['Provider_Name']} - {row['Primary_Specialty']}")
                print(f"  Org: {row['Organization_Name']}")
                print(f"  ZIP: {row['ZIP_Code']}, Phone: {row['Phone']}")
                print()
        
        # Save test results
        test_results.to_csv('test_results.csv', index=False)
        print(f"Saved test results to test_results.csv")

if __name__ == "__main__":
    main() 