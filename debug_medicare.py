#!/usr/bin/env python3
"""
Debug Medicare Extractor
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_error():
    """Debug the string concatenation error"""
    
    # Test Medicare taxonomy codes
    target_taxonomies = {
        '213E00000X': 'Podiatrist',
        '207ND0900X': 'Dermatology - Mohs Surgery', 
        '207RE0101X': 'Endocrinology - Diabetes',
        '208G00000X': 'Vascular Surgery',
        '207Q00000X': 'Family Medicine',
    }
    
    # Load first chunk
    chunk_file = Path("npidata_pfile_20050523-20250713_split/npidata_pfile_20050523-20250713_part_001.csv")
    
    try:
        # Read small sample
        df = pd.read_csv(chunk_file, dtype=str, low_memory=False, nrows=1000)
        logger.info(f"Loaded {len(df)} sample records")
        
        # Check for target specialties
        specialty_mask = pd.Series(False, index=df.index)
        taxonomy_cols = [col for col in df.columns if 'Healthcare Provider Taxonomy Code_' in col]
        
        for col in taxonomy_cols:
            if col in df.columns:
                specialty_mask |= df[col].isin(target_taxonomies.keys())
        
        target_df = df[specialty_mask].copy()
        logger.info(f"Found {len(target_df)} target specialty providers in sample")
        
        if len(target_df) == 0:
            logger.warning("No target specialties found in sample")
            return
        
        # Test processing first few rows
        for idx, row in target_df.head(3).iterrows():
            try:
                logger.info(f"Processing row {idx}...")
                
                # Extract specialties
                specialties = []
                for col in taxonomy_cols:
                    taxonomy_code = row.get(col, '')
                    if pd.notna(taxonomy_code) and str(taxonomy_code).strip() and taxonomy_code in target_taxonomies:
                        specialty = target_taxonomies[taxonomy_code]
                        if specialty and specialty not in specialties:
                            specialties.append(str(specialty))
                
                logger.info(f"  Specialties found: {specialties}")
                
                if not specialties:
                    logger.info(f"  No valid specialties for row {idx}")
                    continue
                
                # Test the join operation that's failing
                try:
                    specialty_string = ' | '.join([str(s) for s in specialties if s])
                    logger.info(f"  Specialty string: {specialty_string}")
                except Exception as e:
                    logger.error(f"  Error joining specialties: {e}")
                    logger.error(f"  Specialties list: {specialties}")
                    logger.error(f"  Specialties types: {[type(s) for s in specialties]}")
                    
                # Test primary specialty selection
                try:
                    medicare_priority_scores = {
                        'Podiatrist': 50,
                        'Endocrinology - Diabetes': 45,
                        'Vascular Surgery': 40,
                        'Dermatology - Mohs Surgery': 35,
                        'Family Medicine': 25,
                    }
                    
                    primary_specialty = max(specialties, key=lambda x: medicare_priority_scores.get(x, 0))
                    logger.info(f"  Primary specialty: {primary_specialty}")
                    
                except Exception as e:
                    logger.error(f"  Error finding primary specialty: {e}")
                
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                
        logger.info("Debug completed")
        
    except Exception as e:
        logger.error(f"Debug error: {e}")

if __name__ == "__main__":
    debug_error() 