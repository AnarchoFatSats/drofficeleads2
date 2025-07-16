#!/usr/bin/env python3
"""
Helper script to download additional datasets for rural physician analysis.

This script attempts to download:
1. RUCA (Rural-Urban Commuting Area) codes for rural classification
2. CMS Provider Enrollment data (if available)
3. Taxonomy code reference data
"""

import requests
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_ruca_data():
    """Download RUCA ZIP code data from USDA"""
    try:
        # Alternative RUCA data source
        urls = [
            "https://www.ers.usda.gov/webdocs/DataFiles/53241/ruca2010zipcode.xlsx",
            "https://www.ers.usda.gov/webdocs/DataFiles/53241/ruca2010zipcode.csv"
        ]
        
        for url in urls:
            try:
                logger.info(f"Attempting to download RUCA data from {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                filename = url.split('/')[-1]
                with open(filename, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Successfully downloaded {filename}")
                return True
            except Exception as e:
                logger.warning(f"Failed to download from {url}: {e}")
                
        logger.error("Could not download RUCA data from any source")
        return False
        
    except Exception as e:
        logger.error(f"Error downloading RUCA data: {e}")
        return False

def download_taxonomy_codes():
    """Download NUCC taxonomy codes"""
    try:
        url = "https://download.cms.gov/nppes/nucc_taxonomy_25xx.csv"
        logger.info(f"Downloading taxonomy codes from {url}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open("nucc_taxonomy_codes.csv", 'wb') as f:
            f.write(response.content)
        logger.info("Successfully downloaded taxonomy codes")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading taxonomy codes: {e}")
        return False

def create_manual_ruca_subset():
    """Create a manual subset of rural ZIP codes for major rural states"""
    logger.info("Creating manual rural ZIP code list for major rural states...")
    
    # ZIP code ranges that are typically rural (this is a rough approximation)
    rural_zip_ranges = {
        # Montana
        'MT': [(59000, 59999)],
        # North Dakota  
        'ND': [(58000, 58999)],
        # South Dakota
        'SD': [(57000, 57999)],
        # Wyoming
        'WY': [(82000, 83199)],
        # Vermont
        'VT': [(5000, 5999)],
        # Alaska
        'AK': [(99000, 99999)],
        # Rural areas of larger states (sample)
        'RURAL_SAMPLE': [
            (60000, 62999),  # Rural Illinois
            (66000, 67999),  # Rural Kansas  
            (68000, 69199),  # Rural Nebraska
            (70000, 71999),  # Rural Louisiana
            (75000, 76999),  # Rural Texas
            (80000, 81999),  # Rural Colorado
            (83200, 83899),  # Rural Idaho
        ]
    }
    
    rural_zips = set()
    for state, ranges in rural_zip_ranges.items():
        for start, end in ranges:
            for zip_code in range(start, end + 1):
                rural_zips.add(f"{zip_code:05d}")
    
    # Save to CSV
    rural_df = pd.DataFrame({'ZIP_CODE': sorted(rural_zips), 'RUCA2010': 9})
    rural_df.to_csv('manual_rural_zips.csv', index=False)
    logger.info(f"Created manual rural ZIP list with {len(rural_zips)} ZIP codes")
    return True

def get_dac_data_info():
    """Provide information on how to get DAC data"""
    print("\n" + "="*60)
    print("HOW TO GET ADDITIONAL DATA SOURCES")
    print("="*60)
    
    print("\n1. DAC National Downloadable File (Group Practice Info):")
    print("   - Go to: https://download.cms.gov/nppes/")
    print("   - Look for 'DAC_NationalDownloadableFile.csv'")
    print("   - This file contains group practice affiliations")
    print("   - Alternative: Contact CMS directly for current link")
    
    print("\n2. PECOS Provider Enrollment Data:")
    print("   - Go to: https://pecos.cms.hhs.gov/pecos/login.do")
    print("   - May require registration")
    print("   - Contains additional provider ownership information")
    
    print("\n3. State Medical Board Data:")
    print("   - Each state has its own provider database")
    print("   - Often contains practice ownership information")
    print("   - Examples:")
    print("     * Texas: https://www.tmb.state.tx.us/")
    print("     * California: https://www.mbc.ca.gov/")
    print("     * Florida: https://flboardofmedicine.gov/")
    
    print("\n4. Secretary of State Business Registration:")
    print("   - Use practice names from results to look up business entities")
    print("   - Can reveal ownership structure")
    print("   - Each state has online business search tools")

def main():
    """Main function to acquire additional data"""
    print("NPPES Rural Physician Data Acquisition Helper")
    print("=" * 50)
    
    # Try to download RUCA data
    if not download_ruca_data():
        print("\nRUCA data download failed. Creating manual rural ZIP subset...")
        create_manual_ruca_subset()
    
    # Try to download taxonomy codes
    download_taxonomy_codes()
    
    # Provide info on getting other data
    get_dac_data_info()
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Install requirements: pip install -r requirements.txt")
    print("2. Run the analysis: python rural_physician_finder.py")
    print("3. Check results/ directory for output files")
    print("4. Manually acquire additional datasets as needed")

if __name__ == "__main__":
    main() 