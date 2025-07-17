#!/usr/bin/env python3
"""
Debug Medicare Allograft Filtering
Understand why leads are being filtered out
"""

import pandas as pd
from pathlib import Path
import logging
from medicare_allograft_lead_extractor import MedicareAllografLeadExtractor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_filtering():
    """Debug what's happening in the filtering process"""
    extractor = MedicareAllografLeadExtractor()
    
    # Load rural ZIP codes
    rural_zips = extractor.load_rural_zip_codes()
    logger.info(f"Loaded {len(rural_zips):,} rural ZIP codes")
    
    # Find first chunk file
    chunk_dir = Path('npidata_pfile_20050523-20250713_split')
    chunk_files = sorted(list(chunk_dir.glob("*.csv")))
    first_chunk = chunk_files[0]
    
    # Read chunk
    df = pd.read_csv(first_chunk, dtype=str, low_memory=False)
    logger.info(f"Loaded {len(df):,} total records")
    
    # Filter for target specialties
    specialty_mask = pd.Series(False, index=df.index)
    for i in range(1, 16):
        taxonomy_col = f'Healthcare Provider Taxonomy Code_{i}'
        if taxonomy_col in df.columns:
            specialty_mask |= df[taxonomy_col].isin(extractor.target_taxonomies.keys())
    
    target_df = df[specialty_mask].copy()
    logger.info(f"Found {len(target_df):,} target specialty providers")
    
    if len(target_df) == 0:
        logger.error("No target specialty providers found")
        return
    
    # Analyze filtering steps
    logger.info(f"\n{'='*60}")
    logger.info("FILTERING ANALYSIS")
    logger.info(f"{'='*60}")
    
    # Step 1: Check specialties
    step1_count = len(target_df)
    logger.info(f"Step 1 - Target specialties: {step1_count:,}")
    
    # Show top specialties found
    all_specialties = []
    for idx, row in target_df.head(1000).iterrows():  # Sample first 1000
        specialties = extractor.extract_specialties(row)
        all_specialties.extend(specialties)
    
    from collections import Counter
    specialty_counts = Counter(all_specialties)
    logger.info("Top specialties found (sample):")
    for specialty, count in specialty_counts.most_common(10):
        score = extractor.medicare_allograft_scores.get(specialty, 0)
        logger.info(f"  {specialty}: {count} instances (Score: {score})")
    
    # Step 2: Check independent practices
    independent_mask = target_df.apply(extractor.is_independent_practice, axis=1)
    independent_df = target_df[independent_mask]
    step2_count = len(independent_df)
    logger.info(f"\nStep 2 - Independent practices: {step2_count:,} ({step2_count/step1_count*100:.1f}% of target specialties)")
    
    if step2_count < step1_count:
        hospital_count = step1_count - step2_count
        logger.info(f"  Filtered out {hospital_count:,} hospital-affiliated providers")
    
    # Step 3: Check rural ZIP codes
    if len(independent_df) > 0:
        zip_codes = independent_df['Provider Business Practice Location Address Postal Code'].fillna('').astype(str).str[:5]
        rural_mask = zip_codes.isin(rural_zips)
        rural_df = independent_df[rural_mask]
        step3_count = len(rural_df)
        
        logger.info(f"\nStep 3 - Rural locations: {step3_count:,} ({step3_count/step2_count*100:.1f}% of independent practices)")
        
        if step3_count == 0:
            logger.warning("🚨 NO RURAL PROVIDERS FOUND!")
            logger.info("Let's analyze ZIP code distribution...")
            
            # Analyze ZIP codes
            unique_zips = zip_codes.value_counts().head(20)
            logger.info(f"\nTop ZIP codes in data (first 20):")
            for zip_code, count in unique_zips.items():
                is_rural = zip_code in rural_zips
                rural_status = "🏞️ RURAL" if is_rural else "🏙️ NON-RURAL"
                logger.info(f"  {zip_code}: {count} providers - {rural_status}")
            
            logger.info(f"\nTotal unique ZIP codes in data: {len(zip_codes.unique()):,}")
            rural_in_data = len([z for z in zip_codes.unique() if z in rural_zips])
            logger.info(f"Rural ZIP codes in data: {rural_in_data:,}")
            
        else:
            logger.info(f"✅ Found {step3_count:,} rural providers")
            
            # Show sample rural providers
            sample_rural = rural_df.head(10)
            logger.info(f"\nSample rural providers:")
            for idx, row in sample_rural.iterrows():
                specialties = extractor.extract_specialties(row)
                primary = max(specialties, key=lambda x: extractor.medicare_allograft_scores.get(x, 0)) if specialties else "Unknown"
                city = row.get('Provider Business Practice Location Address City Name', '')
                state = row.get('Provider Business Practice Location Address State Name', '')
                zip_code = str(row.get('Provider Business Practice Location Address Postal Code', ''))[:5]
                logger.info(f"  {primary} | {city}, {state} {zip_code}")
    
    # Alternative: Test with non-rural filter to see what we'd get
    logger.info(f"\n{'='*60}")
    logger.info("ALTERNATIVE: NON-RURAL ANALYSIS")
    logger.info(f"{'='*60}")
    
    if len(independent_df) > 0:
        # Process first 100 independent practices (regardless of rural status)
        sample_df = independent_df.head(100)
        sample_leads = []
        
        for idx, row in sample_df.iterrows():
            specialties = extractor.extract_specialties(row)
            if not specialties:
                continue
            
            zip_code = str(row.get('Provider Business Practice Location Address Postal Code', ''))[:5]
            is_rural = zip_code in rural_zips
            
            primary_specialty = max(specialties, key=lambda x: extractor.medicare_allograft_scores.get(x, 0))
            medicare_score = extractor.calculate_medicare_allograft_score(specialties, is_rural, 1)
            
            sample_leads.append({
                'Primary_Specialty': primary_specialty,
                'Medicare_Score': medicare_score,
                'Is_Rural': is_rural,
                'ZIP_Code': zip_code,
                'City': row.get('Provider Business Practice Location Address City Name', ''),
                'State': row.get('Provider Business Practice Location Address State Name', ''),
                'All_Specialties': ' | '.join(specialties)
            })
        
        if sample_leads:
            sample_df_leads = pd.DataFrame(sample_leads)
            rural_sample = len(sample_df_leads[sample_df_leads['Is_Rural'] == True])
            non_rural_sample = len(sample_df_leads[sample_df_leads['Is_Rural'] == False])
            
            logger.info(f"Sample of 100 independent practices:")
            logger.info(f"  Rural: {rural_sample} ({rural_sample/len(sample_df_leads)*100:.1f}%)")
            logger.info(f"  Non-rural: {non_rural_sample} ({non_rural_sample/len(sample_df_leads)*100:.1f}%)")
            
            if rural_sample > 0:
                logger.info(f"\nTop rural prospects in sample:")
                rural_prospects = sample_df_leads[sample_df_leads['Is_Rural'] == True].sort_values('Medicare_Score', ascending=False)
                for idx, row in rural_prospects.head(5).iterrows():
                    logger.info(f"  Score: {row['Medicare_Score']} | {row['Primary_Specialty']} | {row['City']}, {row['State']}")

if __name__ == "__main__":
    debug_filtering() 