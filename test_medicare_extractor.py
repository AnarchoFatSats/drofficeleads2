#!/usr/bin/env python3
"""
Test Medicare-Focused Lead Extractor - One Chunk Only

Quick test to see the quality of Medicare-focused leads
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from medicare_focused_lead_extractor import MedicareFocusedLeadExtractor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_medicare_extraction():
    """Test Medicare extraction on one chunk"""
    extractor = MedicareFocusedLeadExtractor()
    
    # Load rural ZIP codes
    rural_zips = extractor.load_rural_zips()
    
    # Process just the first chunk as a test
    chunk_dir = Path("npidata_pfile_20050523-20250713_split")
    chunk_files = sorted(list(chunk_dir.glob("*.csv")))
    
    if not chunk_files:
        logger.error("No chunk files found")
        return
    
    # Test on first chunk
    test_file = chunk_files[0]
    logger.info(f"🧪 Testing Medicare extraction on: {test_file}")
    
    leads_df = extractor.process_nppes_chunk(test_file, rural_zips, 1)
    
    if len(leads_df) == 0:
        logger.warning("No leads found in test chunk")
        return
    
    # Analyze results
    logger.info(f"\n🎯 MEDICARE-FOCUSED TEST RESULTS")
    logger.info(f"Total leads from one chunk: {len(leads_df):,}")
    
    # Top specialties
    logger.info(f"\n📊 Top Medicare Specialties Found:")
    specialty_counts = leads_df['Primary_Specialty'].value_counts().head(10)
    for specialty, count in specialty_counts.items():
        priority_score = extractor.medicare_priority_scores.get(specialty, 0)
        logger.info(f"  • {specialty}: {count:,} leads (Priority: {priority_score})")
    
    # Score distribution
    logger.info(f"\n🏆 Medicare Lead Score Distribution:")
    score_ranges = [
        (90, 100, "A+ Priority (90-100)"),
        (70, 89, "A Priority (70-89)"),
        (50, 69, "B+ Priority (50-69)"),
        (30, 49, "B Priority (30-49)"),
        (0, 29, "C Priority (0-29)")
    ]
    
    for min_score, max_score, label in score_ranges:
        count = len(leads_df[(leads_df['Medicare_Lead_Score'] >= min_score) & 
                           (leads_df['Medicare_Lead_Score'] <= max_score)])
        percentage = (count / len(leads_df)) * 100
        logger.info(f"  {label}: {count:,} leads ({percentage:.1f}%)")
    
    # Show top 10 prospects
    top_leads = leads_df.nlargest(10, 'Medicare_Lead_Score')
    logger.info(f"\n🌟 TOP 10 MEDICARE WOUND CARE PROSPECTS:")
    for idx, row in top_leads.iterrows():
        logger.info(f"• Score: {row['Medicare_Lead_Score']} | {row['Primary_Specialty']} | "
                   f"Specialties: {row['All_Specialties']} | ZIP: {row['ZIP_Code']}")
    
    # Check for high-value combinations
    combo_leads = leads_df[leads_df['Specialty_Count'] >= 2]
    if len(combo_leads) > 0:
        logger.info(f"\n🎯 Multi-Specialty Medicare Groups: {len(combo_leads):,}")
        
        # Specific high-value combos
        pod_endo = combo_leads[combo_leads['All_Specialties'].str.contains('Podiatrist', na=False) & 
                             combo_leads['All_Specialties'].str.contains('Endocrinology', na=False)]
        if len(pod_endo) > 0:
            logger.info(f"  • Podiatrist + Endocrinology: {len(pod_endo)} (PERFECT for diabetic foot care)")
        
        pod_wound = combo_leads[combo_leads['All_Specialties'].str.contains('Podiatrist', na=False) & 
                              combo_leads['All_Specialties'].str.contains('Wound Care', na=False)]
        if len(pod_wound) > 0:
            logger.info(f"  • Podiatrist + Wound Care: {len(pod_wound)} (Comprehensive foot/wound specialists)")
        
        vasc_wound = combo_leads[combo_leads['All_Specialties'].str.contains('Vascular Surgery', na=False) & 
                               combo_leads['All_Specialties'].str.contains('Wound Care', na=False)]
        if len(vasc_wound) > 0:
            logger.info(f"  • Vascular Surgery + Wound Care: {len(vasc_wound)} (Circulation + healing experts)")
    
    # Save test results
    test_output = 'medicare_test_results.xlsx'
    leads_df.to_excel(test_output, index=False)
    logger.info(f"\n✅ Test results saved to: {test_output}")
    
    return leads_df

if __name__ == "__main__":
    test_medicare_extraction() 