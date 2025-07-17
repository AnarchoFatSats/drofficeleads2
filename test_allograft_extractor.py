#!/usr/bin/env python3
"""
Test Medicare Allograft Lead Extractor (Single Chunk)
Validate targeting of allograft wound care patches for Medicare populations
"""

import pandas as pd
from pathlib import Path
import logging
from medicare_allograft_lead_extractor import MedicareAllografLeadExtractor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_single_chunk():
    """Test extractor on first chunk"""
    extractor = MedicareAllografLeadExtractor()
    
    # Load rural ZIP codes
    rural_zips = extractor.load_rural_zip_codes()
    logger.info(f"Loaded {len(rural_zips):,} rural ZIP codes")
    
    # Find first chunk file
    chunk_dir = Path('npidata_pfile_20050523-20250713_split')
    chunk_files = sorted(list(chunk_dir.glob("*.csv")))
    
    if not chunk_files:
        logger.error("No chunk files found")
        return
    
    first_chunk = chunk_files[0]
    logger.info(f"Testing with chunk: {first_chunk.name}")
    
    # Process first chunk
    leads_df = extractor.process_nppes_chunk(first_chunk, rural_zips, 1)
    
    if len(leads_df) == 0:
        logger.warning("No leads found in test chunk")
        return
    
    logger.info(f"\n{'='*80}")
    logger.info(f"MEDICARE ALLOGRAFT TEST RESULTS (Single Chunk)")
    logger.info(f"{'='*80}")
    logger.info(f"Total leads: {len(leads_df):,}")
    
    # Score distribution
    score_ranges = [
        (90, 100, "A+"),
        (80, 89, "A"),
        (70, 79, "B+"),
        (60, 69, "B"),
        (0, 59, "C")
    ]
    
    for min_score, max_score, grade in score_ranges:
        count = len(leads_df[leads_df['Medicare_Allograft_Score'].between(min_score, max_score)])
        if count > 0:
            pct = count/len(leads_df)*100
            logger.info(f"  {grade} ({min_score}-{max_score}): {count:,} leads ({pct:.1f}%)")
    
    # Top specialties
    logger.info(f"\nTop Target Specialties:")
    specialty_counts = leads_df['Primary_Specialty'].value_counts()
    for specialty, count in specialty_counts.head(10).items():
        score = extractor.medicare_allograft_scores.get(specialty, 0)
        pct = count/len(leads_df)*100
        logger.info(f"  {specialty}: {count:,} ({pct:.1f}%) - Base Score: {score}")
    
    # Target categories
    logger.info(f"\nTarget Categories:")
    category_counts = leads_df['Target_Category'].value_counts()
    for category, count in category_counts.items():
        pct = count/len(leads_df)*100
        logger.info(f"  {category}: {count:,} ({pct:.1f}%)")
    
    # Geographic distribution
    logger.info(f"\nGeographic Distribution:")
    state_counts = leads_df['State'].value_counts().head(10)
    for state, count in state_counts.items():
        rural_count = len(leads_df[(leads_df['State'] == state) & (leads_df['Is_Rural'] == True)])
        pct = count/len(leads_df)*100
        logger.info(f"  {state}: {count:,} ({pct:.1f}%) - Rural: {rural_count:,}")
    
    # Show top prospects
    top_leads = leads_df.head(15)
    logger.info(f"\n🌟 TOP 15 MEDICARE ALLOGRAFT PROSPECTS:")
    for idx, row in top_leads.iterrows():
        rural_indicator = "🏞️" if row['Is_Rural'] else "🏙️"
        logger.info(f"• {rural_indicator} Score: {row['Medicare_Allograft_Score']} | {row['Primary_Specialty']} | {row['City']}, {row['State']} | {row['Target_Category']}")
    
    # Special combinations
    multi_specialty = leads_df[leads_df['Specialty_Count'] >= 2]
    if len(multi_specialty) > 0:
        logger.info(f"\n🔥 Multi-Specialty Practices ({len(multi_specialty):,} total):")
        top_multi = multi_specialty.head(10)
        for idx, row in top_multi.iterrows():
            logger.info(f"• Score: {row['Medicare_Allograft_Score']} | {row['All_Specialties']} | {row['City']}, {row['State']}")
    
    # Save test results
    test_output = 'test_medicare_allograft_leads.xlsx'
    leads_df.to_excel(test_output, index=False)
    logger.info(f"\n✅ Test results saved to {test_output}")
    
    return leads_df

if __name__ == "__main__":
    test_single_chunk() 