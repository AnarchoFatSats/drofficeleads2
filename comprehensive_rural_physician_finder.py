#!/usr/bin/env python3
"""
Comprehensive Rural Physician Group Finder

Uses complete dataset to identify small physician groups (1-5 clinicians) that are:
1. Independently owned (not hospital/health system affiliated) 
2. Located in rural ZIP codes (RUCA codes 4-10)
3. Include Podiatry, Wound Care, Mohs Surgery, or Primary Care providers
4. Provides detailed owner/contact information and market context

Data Sources:
- NPPES: Provider directory with specialties and ownership
- RUCA: Rural-urban classification  
- PLACES: Health demographics by ZIP/county
- Medicare: Market size indicators
- ZIP-Tract: Geographic mappings
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import openpyxl
from typing import Dict, List, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveRuralPhysicianFinder:
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
        
        # Hospital/health system indicators (to exclude)
        self.hospital_indicators = [
            'hospital', 'health system', 'medical center', 'health center',
            'healthcare system', 'regional medical', 'medical group',
            'physician group', 'clinic network', 'health network'
        ]
        
    def load_ruca_data(self) -> pd.DataFrame:
        """Load rural-urban classification codes"""
        logger.info("Loading RUCA rural classification data...")
        
        try:
            ruca_df = pd.read_csv(self.base_dir / "RUCA2010zipcode.csv")
            
            # Handle quoted column names and clean data
            ruca_df.columns = ruca_df.columns.str.replace("'", "").str.replace('"', '')
            
            # Clean ZIP codes (remove quotes if present) 
            if 'ZIP_CODE' in ruca_df.columns:
                ruca_df['ZIP_CODE'] = ruca_df['ZIP_CODE'].astype(str).str.replace("'", "").str.replace('"', '').str.zfill(5)
            elif 'ZCTA5CE10' in ruca_df.columns:
                ruca_df = ruca_df.rename(columns={'ZCTA5CE10': 'ZIP_CODE'})
                ruca_df['ZIP_CODE'] = ruca_df['ZIP_CODE'].astype(str).str.replace("'", "").str.replace('"', '').str.zfill(5)
            
            # Define rural areas (RUCA codes 4-10 are rural/small town)
            rural_zips = ruca_df[ruca_df['RUCA2'].isin([4, 5, 6, 7, 8, 9, 10])]['ZIP_CODE'].unique()
            logger.info(f"Identified {len(rural_zips):,} rural ZIP codes")
            
            return ruca_df, set(rural_zips)
            
        except Exception as e:
            logger.error(f"Error loading RUCA data: {e}")
            return pd.DataFrame(), set()
    
    def load_places_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load PLACES health demographic data"""
        logger.info("Loading PLACES health demographic data...")
        
        try:
            # Load ZIP code level data
            places_zip = pd.read_csv(self.base_dir / "PLACES__ZCTA_Data__GIS_Friendly_Format___2022_release.csv")
            places_zip['ZIP_CODE'] = places_zip['ZCTA5'].astype(str).str.zfill(5)
            
            # Load county level data  
            places_county = pd.read_csv(self.base_dir / "PLACES__County_Data__GIS_Friendly_Format___2020_release.csv")
            
            logger.info(f"Loaded PLACES data: {len(places_zip):,} ZIPs, {len(places_county):,} counties")
            return places_zip, places_county
            
        except Exception as e:
            logger.error(f"Error loading PLACES data: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def load_medicare_data(self) -> pd.DataFrame:
        """Load Medicare enrollment data for market sizing"""
        logger.info("Loading Medicare enrollment data...")
        
        try:
            medicare_file = self.base_dir / "Medicare Monthly Enrollment/2025-03/Medicare Monthly Enrollment Data_March 2025.csv"
            medicare_df = pd.read_csv(medicare_file)
            
            # Filter to county-level data
            county_data = medicare_df[medicare_df['BENE_GEO_LVL'] == 'County'].copy()
            logger.info(f"Loaded Medicare data for {len(county_data):,} counties")
            
            return county_data
            
        except Exception as e:
            logger.error(f"Error loading Medicare data: {e}")
            return pd.DataFrame()
    
    def process_nppes_chunk(self, chunk_file: Path, rural_zips: set, chunk_num: int) -> pd.DataFrame:
        """Process a single NPPES chunk file"""
        logger.info(f"Processing NPPES chunk {chunk_num}: {chunk_file.name}")
        
        try:
            # Read chunk
            df = pd.read_csv(chunk_file, dtype=str, low_memory=False)
            logger.info(f"Loaded {len(df):,} records from chunk {chunk_num}")
            
            # Clean practice ZIP codes
            df['Practice_ZIP'] = df['Provider Business Practice Location Address Postal Code'].astype(str).str[:5].str.zfill(5)
            
            # Filter to rural ZIP codes
            rural_providers = df[df['Practice_ZIP'].isin(rural_zips)].copy()
            logger.info(f"Found {len(rural_providers):,} providers in rural areas")
            
            if len(rural_providers) == 0:
                return pd.DataFrame()
            
            # Filter to target specialties
            target_providers = []
            for i in range(1, 16):  # Check all 15 taxonomy code fields
                col = f'Healthcare Provider Taxonomy Code_{i}'
                if col in rural_providers.columns:
                    specialty_matches = rural_providers[
                        rural_providers[col].isin(self.target_taxonomies.keys())
                    ].copy()
                    
                    if len(specialty_matches) > 0:
                        specialty_matches['Primary_Taxonomy'] = specialty_matches[col]
                        specialty_matches['Specialty_Name'] = specialty_matches[col].map(self.target_taxonomies)
                        target_providers.append(specialty_matches)
            
            if not target_providers:
                return pd.DataFrame()
            
            # Combine all specialty matches
            final_providers = pd.concat(target_providers, ignore_index=True).drop_duplicates(subset=['NPI'])
            logger.info(f"Found {len(final_providers):,} providers with target specialties")
            
            # Group by organization to identify small groups
            org_groups = self.identify_small_groups(final_providers)
            
            return org_groups
            
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_num}: {e}")
            return pd.DataFrame()
    
    def identify_small_groups(self, providers_df: pd.DataFrame) -> pd.DataFrame:
        """Identify small physician groups (1-5 providers)"""
        logger.info("Identifying small physician groups...")
        
        # Define grouping criteria - multiple ways to identify same organization
        grouping_cols = []
        
        # Use organization name if available
        if 'Provider Organization Name (Legal Business Name)' in providers_df.columns:
            providers_df['Org_Name_Clean'] = providers_df['Provider Organization Name (Legal Business Name)'].fillna('').str.upper().str.strip()
            grouping_cols.append('Org_Name_Clean')
        
        # Use EIN (Employer Identification Number)
        if 'Employer Identification Number (EIN)' in providers_df.columns:
            providers_df['EIN_Clean'] = providers_df['Employer Identification Number (EIN)'].fillna('').str.strip()
            grouping_cols.append('EIN_Clean')
        
        # Use practice address as grouping criteria  
        providers_df['Practice_Address'] = (
            providers_df['Provider First Line Business Practice Location Address'].fillna('').str.upper() + ' ' +
            providers_df['Provider Business Practice Location Address City Name'].fillna('').str.upper() + ' ' +
            providers_df['Practice_ZIP']
        ).str.strip()
        grouping_cols.append('Practice_Address')
        
        # Group providers
        if not grouping_cols:
            logger.warning("No grouping columns available")
            return pd.DataFrame()
        
        # Create composite group key
        providers_df['Group_Key'] = providers_df[grouping_cols].fillna('').apply(
            lambda x: '|'.join(x.astype(str)), axis=1
        )
        
        # Count providers per group
        group_counts = providers_df.groupby('Group_Key').agg({
            'NPI': 'count',
            'Provider Organization Name (Legal Business Name)': 'first',
            'Employer Identification Number (EIN)': 'first',
            'Practice_Address': 'first',
            'Specialty_Name': lambda x: ', '.join(x.unique()),
            'Authorized Official Last Name': 'first',
            'Authorized Official First Name': 'first',
            'Authorized Official Title or Position': 'first',
            'Provider Business Practice Location Address Telephone Number': 'first',
            'Practice_ZIP': 'first'
        }).reset_index()
        
        group_counts.columns = [
            'Group_Key', 'Provider_Count', 'Organization_Name', 'EIN', 'Practice_Address',
            'Specialties', 'Contact_Last_Name', 'Contact_First_Name', 'Contact_Title',
            'Phone_Number', 'ZIP_Code'
        ]
        
        # Filter to small groups (1-5 providers)
        small_groups = group_counts[
            (group_counts['Provider_Count'] >= 1) & 
            (group_counts['Provider_Count'] <= 5)
        ].copy()
        
        # Filter out likely hospital-affiliated groups
        small_groups = self.filter_independent_groups(small_groups)
        
        logger.info(f"Identified {len(small_groups):,} small, independent groups")
        return small_groups
    
    def filter_independent_groups(self, groups_df: pd.DataFrame) -> pd.DataFrame:
        """Filter out hospital/health system affiliated groups"""
        logger.info("Filtering for independent ownership...")
        
        # Check organization names for hospital indicators
        org_name_mask = groups_df['Organization_Name'].fillna('').str.lower().apply(
            lambda x: not any(indicator in x for indicator in self.hospital_indicators)
        )
        
        # Check practice addresses for hospital indicators  
        address_mask = groups_df['Practice_Address'].fillna('').str.lower().apply(
            lambda x: not any(indicator in x for indicator in self.hospital_indicators)
        )
        
        independent_groups = groups_df[org_name_mask & address_mask].copy()
        
        logger.info(f"After filtering: {len(independent_groups):,} independent groups remain")
        return independent_groups
    
    def enrich_with_demographics(self, groups_df: pd.DataFrame, places_zip: pd.DataFrame, 
                               places_county: pd.DataFrame, medicare_df: pd.DataFrame) -> pd.DataFrame:
        """Enrich results with demographic and market data"""
        logger.info("Enriching with demographic and market data...")
        
        # Merge with PLACES ZIP data
        enriched = groups_df.merge(
            places_zip[['ZIP_CODE', 'TotalPopulation', 'DIABETES_CrudePrev', 'OBESITY_CrudePrev']],
            left_on='ZIP_Code', right_on='ZIP_CODE', how='left'
        )
        
        # Add Medicare beneficiary counts (by county)
        # This would require ZIP to county mapping - for now, add placeholder
        enriched['Medicare_Market_Size'] = 'TBD'
        
        logger.info("Demographic enrichment complete")
        return enriched
    
    def run_analysis(self) -> pd.DataFrame:
        """Run the complete analysis pipeline"""
        logger.info("Starting comprehensive rural physician analysis...")
        
        # Load reference data
        ruca_df, rural_zips = self.load_ruca_data()
        places_zip, places_county = self.load_places_data() 
        medicare_df = self.load_medicare_data()
        
        if len(rural_zips) == 0:
            logger.error("No rural ZIP codes loaded - cannot proceed")
            return pd.DataFrame()
        
        # Process all NPPES chunks
        all_groups = []
        chunk_dir = self.base_dir / "npidata_pfile_20050523-20250713_split"
        
        if not chunk_dir.exists():
            logger.error(f"NPPES split directory not found: {chunk_dir}")
            return pd.DataFrame()
        
        chunk_files = sorted(list(chunk_dir.glob("*.csv")))
        logger.info(f"Found {len(chunk_files)} NPPES chunk files to process")
        
        for i, chunk_file in enumerate(chunk_files, 1):  # Process ALL chunks
            chunk_groups = self.process_nppes_chunk(chunk_file, rural_zips, i)
            if len(chunk_groups) > 0:
                all_groups.append(chunk_groups)
        
        if not all_groups:
            logger.warning("No qualifying groups found")
            return pd.DataFrame()
        
        # Combine all results
        final_results = pd.concat(all_groups, ignore_index=True)
        
        # Remove duplicates across chunks
        final_results = final_results.drop_duplicates(subset=['Group_Key'])
        
        # Enrich with demographic data
        final_results = self.enrich_with_demographics(final_results, places_zip, places_county, medicare_df)
        
        # Sort by relevance (multiple specialties, smaller groups first)
        final_results['Specialty_Count'] = final_results['Specialties'].str.count(',') + 1
        final_results = final_results.sort_values(['Specialty_Count', 'Provider_Count'], ascending=[False, True])
        
        logger.info(f"Analysis complete! Found {len(final_results):,} qualifying physician groups")
        
        return final_results
    
    def save_results(self, results_df: pd.DataFrame, filename: str = "rural_physician_groups.csv"):
        """Save results to CSV file"""
        output_file = self.base_dir / filename
        results_df.to_csv(output_file, index=False)
        logger.info(f"Results saved to: {output_file}")
        
        # Also save a summary
        summary_file = self.base_dir / "analysis_summary.txt"
        with open(summary_file, 'w') as f:
            f.write("Rural Physician Group Analysis Summary\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total qualifying groups found: {len(results_df):,}\n")
            f.write(f"Groups by size:\n")
            size_counts = results_df['Provider_Count'].value_counts().sort_index()
            for size, count in size_counts.items():
                f.write(f"  {size} provider(s): {count:,} groups\n")
            
            f.write(f"\nSpecialty distribution:\n")
            all_specialties = []
            for specialties in results_df['Specialties'].dropna():
                all_specialties.extend([s.strip() for s in specialties.split(',')])
            
            from collections import Counter
            specialty_counts = Counter(all_specialties)
            for specialty, count in specialty_counts.most_common():
                f.write(f"  {specialty}: {count:,} groups\n")
        
        logger.info(f"Summary saved to: {summary_file}")

if __name__ == "__main__":
    finder = ComprehensiveRuralPhysicianFinder()
    results = finder.run_analysis()
    
    if len(results) > 0:
        finder.save_results(results)
        print(f"\n✅ Analysis complete! Found {len(results):,} qualifying physician groups.")
        print(f"📊 Results saved to: rural_physician_groups.csv")
        print(f"📋 Summary saved to: analysis_summary.txt")
        
        # Show preview
        print(f"\n📋 Preview of top results:")
        print(results[['Organization_Name', 'Provider_Count', 'Specialties', 'ZIP_Code', 'Phone_Number']].head(10).to_string(index=False))
    else:
        print("❌ No qualifying groups found. Check the logs for details.") 