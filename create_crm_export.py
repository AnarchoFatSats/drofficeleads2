#!/usr/bin/env python3
"""
Create CRM-Ready Rural Physician Leads Export

Formats the analysis results into a comprehensive CRM spreadsheet with:
- Lead scoring and prioritization
- Complete contact information
- Market demographics and sizing
- Geographic clustering for territory planning
- Lead source tracking and notes
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path

class CRMLeadProcessor:
    def __init__(self):
        self.priority_weights = {
            'podiatrist_wound_care': 100,  # Highest value
            'podiatrist_multi': 80,        # High value  
            'wound_care_multi': 70,        # Medium-high value
            'mohs_surgery': 60,            # Special value
            'podiatrist_solo': 40,         # Medium value
            'wound_care_solo': 35,         # Medium-low value
            'primary_care_multi': 25,      # Lower value
            'primary_care_solo': 15        # Lowest value
        }
        
    def load_and_enrich_data(self, filename='rural_physician_groups.csv'):
        """Load results and add CRM-specific enrichments"""
        print("📊 Loading and enriching lead data...")
        
        # Load base results
        df = pd.read_csv(filename)
        
        # Add CRM fields
        df['Lead_ID'] = df.index + 1
        df['Date_Added'] = datetime.now().strftime('%Y-%m-%d')
        df['Lead_Source'] = 'NPPES Rural Analysis 2025'
        df['Lead_Status'] = 'New'
        df['Assigned_Rep'] = ''
        df['Last_Contact_Date'] = ''
        df['Next_Follow_Up'] = ''
        df['Notes'] = ''
        
        # Calculate lead scores
        df['Lead_Score'] = df.apply(self.calculate_lead_score, axis=1)
        df['Priority_Category'] = df.apply(self.categorize_lead, axis=1)
        
        # Parse and clean contact information
        df = self.parse_contact_info(df)
        
        # Add geographic clustering
        df = self.add_geographic_clusters(df)
        
        # Add market sizing
        df = self.add_market_context(df)
        
        return df
    
    def calculate_lead_score(self, row):
        """Calculate numeric lead score based on specialties and group size"""
        specialties = str(row['Specialties']).lower()
        provider_count = row['Provider_Count']
        population = row.get('TotalPopulation', 0)
        
        base_score = 0
        
        # Specialty-based scoring
        if 'podiatrist' in specialties and 'wound care' in specialties:
            base_score = self.priority_weights['podiatrist_wound_care']
        elif 'podiatrist' in specialties and row['Specialty_Count'] >= 3:
            base_score = self.priority_weights['podiatrist_multi']
        elif 'wound care' in specialties and row['Specialty_Count'] >= 3:
            base_score = self.priority_weights['wound_care_multi']
        elif 'mohs surgery' in specialties:
            base_score = self.priority_weights['mohs_surgery']
        elif 'podiatrist' in specialties:
            base_score = self.priority_weights['podiatrist_solo']
        elif 'wound care' in specialties:
            base_score = self.priority_weights['wound_care_solo']
        elif row['Specialty_Count'] >= 3:
            base_score = self.priority_weights['primary_care_multi']
        else:
            base_score = self.priority_weights['primary_care_solo']
        
        # Size multiplier (prefer smaller, more manageable groups)
        size_multiplier = {1: 1.0, 2: 1.1, 3: 1.2, 4: 1.1, 5: 1.0}.get(provider_count, 0.9)
        
        # Population bonus (prefer underserved areas)
        if pd.notna(population):
            if population < 10000:
                pop_bonus = 10  # Small town bonus
            elif population < 25000:
                pop_bonus = 5   # Medium town bonus
            else:
                pop_bonus = 0
        else:
            pop_bonus = 0
            
        final_score = int(base_score * size_multiplier + pop_bonus)
        return min(final_score, 100)  # Cap at 100
    
    def categorize_lead(self, row):
        """Assign priority category based on lead score"""
        score = row['Lead_Score']
        if score >= 90:
            return 'A+ Hot Lead'
        elif score >= 70:
            return 'A High Priority'
        elif score >= 50:
            return 'B Medium Priority'
        elif score >= 30:
            return 'C Low Priority'
        else:
            return 'D Nurture'
    
    def parse_contact_info(self, df):
        """Parse and clean contact information"""
        print("📞 Parsing contact information...")
        
        # Clean phone numbers
        df['Phone_Clean'] = df['Phone_Number'].fillna('').astype(str).apply(self.format_phone)
        
        # Parse addresses
        address_parts = df['Practice_Address'].fillna('').apply(self.parse_address)
        df['Street_Address'] = [addr['street'] for addr in address_parts]
        df['City'] = [addr['city'] for addr in address_parts]
        df['State'] = [addr['state'] for addr in address_parts] 
        df['ZIP'] = df['ZIP_Code']
        
        # Format organization name
        df['Company_Name'] = df['Organization_Name'].fillna('Independent Practice')
        
        # Contact person (from Authorized Official)
        df['Contact_First'] = df['Contact_First_Name'].fillna('')
        df['Contact_Last'] = df['Contact_Last_Name'].fillna('')
        df['Contact_Full'] = (df['Contact_First'] + ' ' + df['Contact_Last']).str.strip()
        df['Contact_Title'] = df['Contact_Title'].fillna('Practice Manager')
        
        return df
    
    def format_phone(self, phone):
        """Format phone number consistently"""
        if pd.isna(phone) or phone == '' or phone == 'nan':
            return ''
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', str(phone))
        
        # Format as (XXX) XXX-XXXX if we have 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone  # Return original if can't parse
    
    def parse_address(self, address_str):
        """Parse address string into components"""
        if pd.isna(address_str) or address_str == '':
            return {'street': '', 'city': '', 'state': ''}
        
        parts = str(address_str).strip().split(' ')
        
        # Find ZIP code to separate city from street
        zip_pattern = r'\b\d{5}\b'
        zip_match = re.search(zip_pattern, address_str)
        
        if zip_match and len(parts) >= 3:
            zip_pos = zip_match.start()
            before_zip = address_str[:zip_pos].strip()
            parts = before_zip.split(' ')
            
            if len(parts) >= 2:
                # Last 1-2 words before ZIP are likely the city
                if len(parts) >= 3:
                    city = ' '.join(parts[-2:]) if parts[-1].isupper() else parts[-1]
                    street = ' '.join(parts[:-2 if city == ' '.join(parts[-2:]) else -1])
                else:
                    city = parts[-1]
                    street = ' '.join(parts[:-1])
                
                # Try to extract state (usually 2 letters after city)
                state_match = re.search(r'\b([A-Z]{2})\b', address_str[zip_pos:])
                state = state_match.group(1) if state_match else ''
                
                return {'street': street, 'city': city, 'state': state}
        
        # Fallback: just return the whole string as street
        return {'street': address_str, 'city': '', 'state': ''}
    
    def add_geographic_clusters(self, df):
        """Add geographic clustering for territory planning"""
        print("🗺️  Adding geographic clusters...")
        
        # Group by state for basic clustering
        df['Territory'] = df['State'].fillna('Unknown')
        
        # Add region classification
        state_regions = {
            'ME': 'Northeast', 'NH': 'Northeast', 'VT': 'Northeast', 'MA': 'Northeast',
            'RI': 'Northeast', 'CT': 'Northeast', 'NY': 'Northeast', 'NJ': 'Northeast', 'PA': 'Northeast',
            'OH': 'Midwest', 'IN': 'Midwest', 'IL': 'Midwest', 'MI': 'Midwest', 'WI': 'Midwest',
            'MN': 'Midwest', 'IA': 'Midwest', 'MO': 'Midwest', 'ND': 'Midwest', 'SD': 'Midwest',
            'NE': 'Midwest', 'KS': 'Midwest',
            'DE': 'South', 'MD': 'South', 'DC': 'South', 'VA': 'South', 'WV': 'South',
            'KY': 'South', 'TN': 'South', 'NC': 'South', 'SC': 'South', 'GA': 'South',
            'FL': 'South', 'AL': 'South', 'MS': 'South', 'AR': 'South', 'LA': 'South',
            'OK': 'South', 'TX': 'South',
            'MT': 'West', 'WY': 'West', 'CO': 'West', 'NM': 'West', 'ID': 'West',
            'UT': 'West', 'NV': 'West', 'AZ': 'West', 'WA': 'West', 'OR': 'West',
            'CA': 'West', 'AK': 'West', 'HI': 'West'
        }
        
        df['Region'] = df['State'].map(state_regions).fillna('Unknown')
        
        return df
    
    def add_market_context(self, df):
        """Add market sizing and demographic context"""
        print("📈 Adding market context...")
        
        # Market size categories based on population
        def categorize_market(pop):
            if pd.isna(pop):
                return 'Unknown'
            elif pop < 5000:
                return 'Small Town (<5K)'
            elif pop < 15000:
                return 'Medium Town (5K-15K)'
            elif pop < 35000:
                return 'Large Town (15K-35K)'
            else:
                return 'Small City (35K+)'
        
        df['Market_Size'] = df['TotalPopulation'].apply(categorize_market)
        
        # Calculate potential annual revenue estimate
        df['Est_Annual_Revenue'] = df.apply(self.estimate_revenue_potential, axis=1)
        
        return df
    
    def estimate_revenue_potential(self, row):
        """Estimate potential annual revenue based on group characteristics"""
        base_revenue = {
            'A+ Hot Lead': 50000,
            'A High Priority': 35000,
            'B Medium Priority': 20000,
            'C Low Priority': 10000,
            'D Nurture': 5000
        }
        
        # Base on priority category
        estimate = base_revenue.get(row['Priority_Category'], 10000)
        
        # Adjust for provider count
        provider_multiplier = min(row['Provider_Count'] * 0.3 + 0.7, 2.0)
        estimate *= provider_multiplier
        
        # Adjust for market size
        pop = row.get('TotalPopulation', 15000)
        if pd.notna(pop):
            if pop > 25000:
                estimate *= 1.2  # Larger market bonus
            elif pop < 8000:
                estimate *= 0.8  # Smaller market adjustment
        
        return int(estimate)
    
    def create_crm_export(self, df, filename='rural_physician_leads_crm.xlsx'):
        """Create comprehensive CRM export"""
        print("📋 Creating CRM export...")
        
        # Define CRM column mapping
        crm_columns = {
            'Lead_ID': 'Lead ID',
            'Priority_Category': 'Priority',
            'Lead_Score': 'Score',
            'Company_Name': 'Company',
            'Contact_Full': 'Contact Name',
            'Contact_Title': 'Title',
            'Phone_Clean': 'Phone',
            'Street_Address': 'Street',
            'City': 'City',
            'State': 'State', 
            'ZIP': 'ZIP',
            'Provider_Count': 'Providers',
            'Specialties': 'Specialties',
            'Market_Size': 'Market Size',
            'TotalPopulation': 'Population',
            'Est_Annual_Revenue': 'Est. Revenue',
            'Region': 'Region',
            'Territory': 'Territory',
            'Lead_Source': 'Source',
            'Date_Added': 'Date Added',
            'Lead_Status': 'Status',
            'Assigned_Rep': 'Assigned Rep',
            'Last_Contact_Date': 'Last Contact',
            'Next_Follow_Up': 'Follow Up',
            'Notes': 'Notes'
        }
        
        # Create CRM-ready dataframe
        crm_df = df[list(crm_columns.keys())].copy()
        crm_df = crm_df.rename(columns=crm_columns)
        
        # Sort by priority and score
        crm_df = crm_df.sort_values(['Score', 'Providers'], ascending=[False, False])
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Main leads sheet
            crm_df.to_excel(writer, sheet_name='All Leads', index=False)
            
            # Priority segments
            hot_leads = crm_df[crm_df['Priority'].isin(['A+ Hot Lead', 'A High Priority'])]
            hot_leads.to_excel(writer, sheet_name='Hot Leads', index=False)
            
            # By specialty
            podiatrist_leads = crm_df[crm_df['Specialties'].str.contains('Podiatrist', na=False)]
            podiatrist_leads.to_excel(writer, sheet_name='Podiatrist Groups', index=False)
            
            wound_care_leads = crm_df[crm_df['Specialties'].str.contains('Wound Care', na=False)]
            wound_care_leads.to_excel(writer, sheet_name='Wound Care Groups', index=False)
            
            mohs_leads = crm_df[crm_df['Specialties'].str.contains('Mohs', na=False)]
            mohs_leads.to_excel(writer, sheet_name='Mohs Surgery Groups', index=False)
            
            # By region for territory planning
            for region in ['Northeast', 'South', 'Midwest', 'West']:
                region_leads = crm_df[crm_df['Region'] == region]
                if len(region_leads) > 0:
                    region_leads.to_excel(writer, sheet_name=f'{region} Territory', index=False)
            
            # Summary dashboard
            self.create_summary_dashboard(crm_df, writer)
        
        print(f"✅ CRM export created: {filename}")
        return filename
    
    def create_summary_dashboard(self, df, writer):
        """Create summary dashboard sheet"""
        summary_data = []
        
        # Overall statistics
        summary_data.append(['LEAD SUMMARY', ''])
        summary_data.append(['Total Leads', len(df)])
        summary_data.append(['Hot Leads (A+/A)', len(df[df['Priority'].isin(['A+ Hot Lead', 'A High Priority'])])])
        summary_data.append(['Total Est. Revenue', f"${df['Est. Revenue'].sum():,}"])
        summary_data.append(['Avg Score', f"{df['Score'].mean():.1f}"])
        summary_data.append(['', ''])
        
        # By priority
        summary_data.append(['BY PRIORITY', ''])
        priority_counts = df['Priority'].value_counts()
        for priority, count in priority_counts.items():
            summary_data.append([priority, count])
        summary_data.append(['', ''])
        
        # By region
        summary_data.append(['BY REGION', ''])
        region_counts = df['Region'].value_counts()
        for region, count in region_counts.items():
            summary_data.append([region, count])
        summary_data.append(['', ''])
        
        # By specialty
        summary_data.append(['BY SPECIALTY', ''])
        summary_data.append(['Podiatrist Groups', len(df[df['Specialties'].str.contains('Podiatrist', na=False)])])
        summary_data.append(['Wound Care Groups', len(df[df['Specialties'].str.contains('Wound Care', na=False)])])
        summary_data.append(['Mohs Surgery Groups', len(df[df['Specialties'].str.contains('Mohs', na=False)])])
        
        # Create summary dataframe
        summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name='Dashboard', index=False)

def main():
    processor = CRMLeadProcessor()
    
    print("🚀 Creating comprehensive CRM export...")
    print("=" * 50)
    
    # Load and process data
    df = processor.load_and_enrich_data()
    
    # Create CRM export
    filename = processor.create_crm_export(df)
    
    # Print summary
    print(f"\n📊 FINAL RESULTS")
    print("=" * 30)
    print(f"Total Leads: {len(df):,}")
    print(f"Hot Leads (A+/A): {len(df[df['Priority_Category'].isin(['A+ Hot Lead', 'A High Priority'])]):,}")
    print(f"Total Est. Revenue: ${df['Est_Annual_Revenue'].sum():,}")
    print(f"Territories Covered: {df['Region'].nunique()} regions")
    print(f"States Covered: {df['State'].nunique()} states")
    
    print(f"\n✅ CRM file created: {filename}")
    print("📋 Sheets included:")
    print("  • All Leads - Complete dataset")
    print("  • Hot Leads - Priority A+/A only")
    print("  • Specialty sheets - By target specialty")
    print("  • Territory sheets - By geographic region")
    print("  • Dashboard - Summary statistics")

if __name__ == "__main__":
    main() 