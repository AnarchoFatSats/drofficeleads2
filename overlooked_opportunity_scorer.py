#!/usr/bin/env python3
"""
Overlooked Opportunity Scorer - "The Crumbs Strategy"

Targets practices that big companies ignore:
- Small independent practices (1-5 physicians)
- Underserved small cities/towns  
- Medicare-dense but non-metro locations
- High relationship-building potential
- Clusterable for territory dominance

Strategy: Build your network where big pharma doesn't go
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional, Set
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OverlookedOpportunityScorer:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        
        # Big Company Avoidance Indicators (Higher = More Overlooked)
        self.metro_avoidance_bonus = {
            # Major metros that big companies saturate (LOWER scores)
            'NEW YORK': 0, 'LOS ANGELES': 0, 'CHICAGO': 0, 'HOUSTON': 0,
            'PHILADELPHIA': 0, 'PHOENIX': 0, 'SAN ANTONIO': 0, 'SAN DIEGO': 0,
            'DALLAS': 0, 'SAN JOSE': 0, 'AUSTIN': 0, 'JACKSONVILLE': 0,
            'FORT WORTH': 0, 'COLUMBUS': 0, 'CHARLOTTE': 0, 'INDIANAPOLIS': 0,
            'SAN FRANCISCO': 0, 'SEATTLE': 0, 'DENVER': 0, 'WASHINGTON': 0,
            'BOSTON': 0, 'NASHVILLE': 0, 'BALTIMORE': 0, 'OKLAHOMA CITY': 0,
            'LOUISVILLE': 0, 'PORTLAND': 0, 'LAS VEGAS': 0, 'MILWAUKEE': 0,
            'ALBUQUERQUE': 0, 'TUCSON': 0, 'FRESNO': 0, 'SACRAMENTO': 0,
            'MESA': 0, 'KANSAS CITY': 0, 'ATLANTA': 0, 'LONG BEACH': 0,
            'COLORADO SPRINGS': 0, 'RALEIGH': 0, 'MIAMI': 0, 'VIRGINIA BEACH': 0,
            'OMAHA': 0, 'OAKLAND': 0, 'MINNEAPOLIS': 0, 'TULSA': 0,
            'ARLINGTON': 0, 'TAMPA': 0, 'NEW ORLEANS': 0, 'WICHITA': 0,
            'CLEVELAND': 0, 'BAKERSFIELD': 0, 'AURORA': 0, 'ANAHEIM': 0,
            'HONOLULU': 0, 'SANTA ANA': 0, 'CORPUS CHRISTI': 0, 'RIVERSIDE': 0,
            'LEXINGTON': 0, 'STOCKTON': 0, 'ST. LOUIS': 0, 'SAINT PAUL': 0,
            'HENDERSON': 0, 'BUFFALO': 0, 'NORFOLK': 0, 'LINCOLN': 0,
            'PLANO': 0, 'ST. PETERSBURG': 0, 'JERSEY CITY': 0, 'GREENSBORO': 0,
            'CHANDLER': 0, 'BIRMINGHAM': 0, 'ANCHORAGE': 0, 'CHULA VISTA': 0
        }
        
        # Small City Sweet Spots (15K-100K population = Overlooked Goldmines)
        self.small_city_bonus = 25  # Big companies find these "inefficient"
        
        # Allograft Specialty Priority (Medicare + Wound Care Focus)
        self.allograft_specialty_scores = {
            # TOP TIER: Perfect Allograft Targets
            'Wound Care - Physician Specialist': 40,     # Ultimate target
            'Wound Care - Physician': 40,                # Ultimate target
            'Podiatrist': 35,                           # Diabetic foot ulcers (huge Medicare market)
            'Surgery - Plastic/Reconstructive': 35,     # Burn reconstruction
            'Surgery - General': 30,                    # Wound complications
            
            # HIGH VALUE: Medicare-Dense Specialties
            'Endocrinology - Diabetes': 30,            # Direct diabetes → wound pipeline
            'Vascular Surgery': 30,                    # Circulation → wound healing
            'Geriatric Medicine': 25,                  # Aging population
            'Infectious Disease': 25,                  # Wound infections
            'Dermatology - Mohs Surgery': 25,          # Skin cancer wounds
            
            # SUPPORTING: Primary Care (High Volume)
            'Family Medicine': 20,                     # Managing diabetic patients
            'Internal Medicine': 20,                   # Chronic disease management
            'General Practice': 18,                    # General Medicare population
            'Cardiovascular Disease': 20,              # Poor circulation
            'Nephrology': 18,                          # Diabetic complications
            
            # LOWER PRIORITY
            'Dermatology - General': 15,
            'Orthopaedic Surgery': 15,
            'Wound Care - Nurse': 35,                  # High priority but different approach
            'Wound Care - Physical Therapist': 30
        }
        
        # Practice Size Sweet Spot (Big companies prefer larger practices)
        self.practice_size_scores = {
            1: 20,    # Solo practices = Maximum overlooked opportunity
            2: 18,    # 2-person = High opportunity  
            3: 15,    # 3-person = Good opportunity
            4: 10,    # 4-person = Moderate opportunity
            5: 8,     # 5-person = Lower opportunity
            6: 5,     # 6+ = Big company territory
            7: 3,
            8: 1,
            9: 0,
            10: 0     # 10+ providers = Big company focus
        }

    def load_comprehensive_leads(self) -> pd.DataFrame:
        """Load the existing comprehensive leads"""
        leads_file = self.base_dir / 'comprehensive_rural_physician_leads.xlsx'
        
        if not leads_file.exists():
            logger.error(f"Comprehensive leads file not found: {leads_file}")
            return pd.DataFrame()
        
        try:
            df = pd.read_excel(leads_file)
            logger.info(f"Loaded {len(df):,} comprehensive leads for re-scoring")
            return df
        except Exception as e:
            logger.error(f"Error loading comprehensive leads: {e}")
            return pd.DataFrame()

    def calculate_metro_avoidance_score(self, city: str, state: str) -> int:
        """Calculate how much big companies avoid this location"""
        if pd.isna(city):
            return 15  # Unknown = moderate opportunity
        
        city_upper = str(city).upper().strip()
        
        # Major metros = 0 points (saturated by big companies)
        if city_upper in self.metro_avoidance_bonus:
            return 0
        
        # State capitals often over-served
        state_capitals = {
            'ALBANY', 'ANNAPOLIS', 'ATLANTA', 'AUGUSTA', 'AUSTIN', 'BATON ROUGE',
            'BISMARCK', 'BOISE', 'BOSTON', 'CHEYENNE', 'COLUMBIA', 'COLUMBUS',
            'CONCORD', 'DENVER', 'DES MOINES', 'DOVER', 'FRANKFORT', 'HARRISBURG',
            'HARTFORD', 'HELENA', 'HONOLULU', 'INDIANAPOLIS', 'JACKSON', 'JEFFERSON CITY',
            'JUNEAU', 'LANSING', 'LINCOLN', 'LITTLE ROCK', 'MADISON', 'MONTGOMERY',
            'MONTPELIER', 'NASHVILLE', 'OKLAHOMA CITY', 'OLYMPIA', 'PHOENIX',
            'PIERRE', 'PROVIDENCE', 'RALEIGH', 'RICHMOND', 'SACRAMENTO', 'SAINT PAUL',
            'SALEM', 'SALT LAKE CITY', 'SANTA FE', 'SPRINGFIELD', 'TALLAHASSEE',
            'TOPEKA', 'TRENTON'
        }
        
        if city_upper in state_capitals:
            return 8  # State capitals = moderately served
        
        # Small cities = overlooked goldmines
        if len(city_upper) <= 15:  # Heuristic for smaller cities
            return 25  # High overlooked opportunity
        
        return 15  # Default moderate opportunity

    def calculate_overlooked_opportunity_score(self, row: pd.Series) -> Dict[str, int]:
        """Calculate comprehensive overlooked opportunity score"""
        
        # 1. METRO AVOIDANCE SCORE (25 points max)
        metro_score = self.calculate_metro_avoidance_score(
            row.get('Practice_City', ''), 
            row.get('Practice_State', '')
        )
        
        # 2. ALLOGRAFT SPECIALTY SCORE (40 points max)
        primary_specialty = row.get('Primary_Specialty', '')
        specialty_score = self.allograft_specialty_scores.get(primary_specialty, 5)
        
        # 3. PRACTICE SIZE ADVANTAGE (20 points max)
        practice_size = row.get('Practice_Size', 1)
        if pd.isna(practice_size):
            practice_size = 1
        size_score = self.practice_size_scores.get(int(practice_size), 0)
        
        # 4. INDEPENDENT PRACTICE BONUS (15 points max)
        # Already filtered for independent practices, so full bonus
        independent_score = 15
        
        # 5. MULTI-SPECIALTY BONUS (relationship building opportunity)
        all_specialties = str(row.get('All_Specialties', ''))
        specialty_count = len([s for s in all_specialties.split(' | ') if s.strip()])
        
        if specialty_count >= 3:
            multi_specialty_bonus = 10  # Comprehensive care = relationship gold
        elif specialty_count >= 2:
            multi_specialty_bonus = 5   # Multi-specialty bonus
        else:
            multi_specialty_bonus = 0
        
        # 6. CONTACT QUALITY BONUS (easier to reach)
        contact_bonus = 0
        if pd.notna(row.get('Practice_Phone', '')):
            contact_bonus += 3
        if pd.notna(row.get('Multiple_Phones', '')) and row.get('Multiple_Phones', False):
            contact_bonus += 2
        
        # TOTAL OVERLOOKED OPPORTUNITY SCORE
        total_score = (metro_score + specialty_score + size_score + 
                      independent_score + multi_specialty_bonus + contact_bonus)
        
        return {
            'Overlooked_Opportunity_Score': min(total_score, 100),  # Cap at 100
            'Metro_Avoidance_Score': metro_score,
            'Allograft_Specialty_Score': specialty_score,
            'Practice_Size_Advantage': size_score,
            'Independent_Practice_Bonus': independent_score,
            'Multi_Specialty_Bonus': multi_specialty_bonus,
            'Contact_Quality_Bonus': contact_bonus,
            'Big_Company_Blindness': 'HIGH' if total_score >= 75 else 'MEDIUM' if total_score >= 50 else 'LOW'
        }

    def enhance_with_opportunity_intelligence(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add overlooked opportunity intelligence to leads"""
        logger.info(f"Calculating overlooked opportunity scores for {len(df):,} leads...")
        
        enhanced_leads = []
        
        for idx, row in df.iterrows():
            if idx % 10000 == 0:
                logger.info(f"Processed {idx:,} leads...")
            
            # Calculate opportunity scores
            opportunity_scores = self.calculate_overlooked_opportunity_score(row)
            
            # Build enhanced lead record
            enhanced_lead = row.to_dict()
            enhanced_lead.update(opportunity_scores)
            
            # Add strategic categorization
            enhanced_lead['Strategic_Category'] = self.get_strategic_category(
                opportunity_scores['Overlooked_Opportunity_Score'],
                row.get('Primary_Specialty', '')
            )
            
            # Add territory clustering hints
            enhanced_lead['Territory_Cluster'] = f"{row.get('Practice_State', 'XX')}-{str(row.get('Practice_City', 'Unknown'))[:3].upper()}"
            
            enhanced_leads.append(enhanced_lead)
        
        enhanced_df = pd.DataFrame(enhanced_leads)
        logger.info(f"Enhanced {len(enhanced_df):,} leads with opportunity intelligence")
        
        return enhanced_df

    def get_strategic_category(self, score: int, specialty: str) -> str:
        """Categorize leads by strategic value"""
        if score >= 85:
            return "🏆 GOLDMINE" if 'Wound Care' in specialty or 'Podiatrist' in specialty else "🏆 PLATINUM"
        elif score >= 70:
            return "💎 HIGH VALUE" if 'Wound Care' in specialty or 'Podiatrist' in specialty else "💎 GOLD"
        elif score >= 55:
            return "⭐ GOOD OPPORTUNITY" if any(x in specialty for x in ['Family Medicine', 'Internal Medicine']) else "⭐ SILVER"
        elif score >= 40:
            return "✅ VIABLE TARGET"
        else:
            return "📋 CONSIDER"

    def generate_territory_analysis(self, df: pd.DataFrame) -> Dict:
        """Analyze territorial opportunities"""
        logger.info("Generating territorial opportunity analysis...")
        
        # Group by state and city for clustering analysis
        state_analysis = df.groupby('Practice_State').agg({
            'Overlooked_Opportunity_Score': ['count', 'mean', 'max'],
            'Allograft_Specialty_Score': 'mean',
            'Metro_Avoidance_Score': 'mean'
        }).round(1)
        
        # Top overlooked markets (state level)
        top_states = state_analysis.sort_values(
            ('Overlooked_Opportunity_Score', 'mean'), 
            ascending=False
        ).head(15)
        
        # City clustering opportunities
        city_clusters = df.groupby(['Practice_State', 'Practice_City']).agg({
            'Overlooked_Opportunity_Score': ['count', 'mean'],
            'Strategic_Category': lambda x: x.mode().iloc[0] if len(x) > 0 else 'Unknown'
        }).round(1)
        
        city_clusters = city_clusters[
            city_clusters[('Overlooked_Opportunity_Score', 'count')] >= 3  # 3+ prospects per city
        ].sort_values(
            ('Overlooked_Opportunity_Score', 'mean'), 
            ascending=False
        ).head(25)
        
        return {
            'top_states': top_states,
            'city_clusters': city_clusters,
            'total_goldmines': len(df[df['Strategic_Category'].str.contains('GOLDMINE', na=False)]),
            'total_high_value': len(df[df['Strategic_Category'].str.contains('HIGH VALUE', na=False)])
        }

    def run_opportunity_analysis(self) -> pd.DataFrame:
        """Run complete overlooked opportunity analysis"""
        logger.info("🎯 STARTING OVERLOOKED OPPORTUNITY ANALYSIS")
        logger.info("Strategy: Target practices big companies ignore")
        
        # Load comprehensive leads
        df = self.load_comprehensive_leads()
        if len(df) == 0:
            logger.error("No leads to analyze")
            return pd.DataFrame()
        
        # Enhance with opportunity intelligence
        enhanced_df = self.enhance_with_opportunity_intelligence(df)
        
        # Sort by overlooked opportunity score
        enhanced_df = enhanced_df.sort_values('Overlooked_Opportunity_Score', ascending=False)
        
        # Generate territorial analysis
        territory_analysis = self.generate_territory_analysis(enhanced_df)
        
        # Print summary
        self.print_opportunity_summary(enhanced_df, territory_analysis)
        
        # Save results
        output_file = 'overlooked_opportunity_goldmines.xlsx'
        enhanced_df.to_excel(output_file, index=False)
        logger.info(f"✅ Saved overlooked opportunity analysis to {output_file}")
        
        return enhanced_df

    def print_opportunity_summary(self, df: pd.DataFrame, territory_analysis: Dict):
        """Print comprehensive opportunity summary"""
        logger.info("\n" + "="*80)
        logger.info("🏆 OVERLOOKED OPPORTUNITY GOLDMINES - 'THE CRUMBS STRATEGY'")
        logger.info("="*80)
        
        # Overall stats
        logger.info(f"Total Overlooked Opportunities: {len(df):,}")
        
        # Strategic categories
        logger.info(f"\n🎯 Strategic Categories:")
        category_counts = df['Strategic_Category'].value_counts()
        for category, count in category_counts.items():
            pct = count/len(df)*100
            logger.info(f"  {category}: {count:,} ({pct:.1f}%)")
        
        # Score distribution
        score_ranges = [
            (85, 100, "🏆 GOLDMINES"),
            (70, 84, "💎 HIGH VALUE"),
            (55, 69, "⭐ GOOD OPPORTUNITY"),
            (40, 54, "✅ VIABLE"),
            (0, 39, "📋 CONSIDER")
        ]
        
        logger.info(f"\n📊 Opportunity Distribution:")
        for min_score, max_score, label in score_ranges:
            count = len(df[df['Overlooked_Opportunity_Score'].between(min_score, max_score)])
            if count > 0:
                pct = count/len(df)*100
                logger.info(f"  {label}: {count:,} ({pct:.1f}%)")
        
        # Top specialties in goldmines
        goldmines = df[df['Overlooked_Opportunity_Score'] >= 75]
        if len(goldmines) > 0:
            logger.info(f"\n🏆 Top Specialties in Goldmines ({len(goldmines):,} total):")
            top_goldmine_specialties = goldmines['Primary_Specialty'].value_counts().head(10)
            for specialty, count in top_goldmine_specialties.items():
                avg_score = goldmines[goldmines['Primary_Specialty'] == specialty]['Overlooked_Opportunity_Score'].mean()
                logger.info(f"  {specialty}: {count:,} (Avg Score: {avg_score:.1f})")
        
        # Territory opportunities
        logger.info(f"\n🗺️ Top Territory Opportunities:")
        logger.info(f"  States with highest overlooked potential:")
        for state, data in territory_analysis['top_states'].head(10).iterrows():
            count = int(data[('Overlooked_Opportunity_Score', 'count')])
            avg_score = data[('Overlooked_Opportunity_Score', 'mean')]
            logger.info(f"    {state}: {count:,} prospects (Avg Score: {avg_score:.1f})")
        
        # Sample top prospects
        logger.info(f"\n🌟 TOP 20 OVERLOOKED GOLDMINES:")
        top_prospects = df.head(20)
        for idx, row in top_prospects.iterrows():
            score = row['Overlooked_Opportunity_Score']
            specialty = row['Primary_Specialty']
            city = row.get('Practice_City', 'Unknown')
            state = row.get('Practice_State', 'XX')
            category = row['Strategic_Category']
            logger.info(f"• Score: {score} | {specialty} | {city}, {state} | {category}")

if __name__ == "__main__":
    scorer = OverlookedOpportunityScorer()
    results_df = scorer.run_opportunity_analysis()
    
    if len(results_df) > 0:
        logger.info(f"\n🎯 SUCCESS: Identified {len(results_df):,} overlooked opportunities")
        logger.info("Focus on goldmines and high-value prospects for maximum ROI")
        logger.info("Build territories in clustered markets for efficiency")
    else:
        logger.error("❌ No opportunities identified") 