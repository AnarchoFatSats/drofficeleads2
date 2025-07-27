#!/usr/bin/env python3
"""
Automated Lead Management System
Intelligent lead replenishment based on inventory levels, team performance, and conversion data
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
import requests
import time

# Import our CRM models and services
import sys
sys.path.append('.')
from crm_main import User, Lead, LeadStatus, Base, Activity, ActivityType
from smart_lead_injection_api import APISmartLeadInjection

# Production database configuration
DATABASE_URL = "postgresql://crmuser:CuraGenesis2024%21SecurePassword@cura-genesis-crm-db.c6ds4c4qok1n.us-east-1.rds.amazonaws.com:5432/cura_genesis_crm"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_lead_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedLeadManager:
    """Intelligent automated lead replenishment system"""
    
    def __init__(self, crm_api_url="http://localhost:8006", config_file=None):
        self.crm_api_url = crm_api_url
        self.engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()
        
        # Load configuration
        self.config = self.load_configuration(config_file)
        
        # Track upload history
        self.upload_history = self.load_upload_history()
        
        logger.info("🤖 Automated Lead Manager initialized")
        
    def load_configuration(self, config_file=None):
        """Load automation configuration from file or use defaults"""
        default_config = {
            # Lead inventory thresholds
            'min_total_leads': 50,        # Trigger replenishment when total leads < 50
            'target_total_leads': 150,    # Replenish to this level
            'min_priority_leads': {       # Minimum leads per priority
                'A+': 10,
                'A': 30,
                'B': 20
            },
            
            # Performance-based adjustments
            'high_conversion_threshold': 0.15,  # 15%+ conversion = upload more A+ leads
            'low_conversion_threshold': 0.05,   # <5% conversion = focus on A/B leads
            
            # Upload batching
            'max_upload_per_run': 100,    # Don't upload more than 100 at once
            'min_upload_batch': 25,       # Always upload at least 25 when triggered
            
            # Safety controls
            'max_daily_uploads': 500,     # Don't upload more than 500 leads per day
            'min_time_between_uploads': 3600,  # Wait 1 hour between uploads (seconds)
            
            # Source file management
            'source_files': [
                'web/data/hot_leads.json',
                # Can add more source files as they become available
            ],
            'used_leads_tracking': 'uploaded_leads_tracking.json'
        }
        
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                
                # Merge file config with defaults
                config = default_config.copy()
                
                # Map JSON structure to internal config
                if 'lead_inventory_thresholds' in file_config:
                    config['min_total_leads'] = file_config['lead_inventory_thresholds'].get('min_total_leads', config['min_total_leads'])
                    config['target_total_leads'] = file_config['lead_inventory_thresholds'].get('target_total_leads', config['target_total_leads'])
                    config['min_priority_leads'] = file_config['lead_inventory_thresholds'].get('min_priority_leads', config['min_priority_leads'])
                
                if 'performance_thresholds' in file_config:
                    config['high_conversion_threshold'] = file_config['performance_thresholds'].get('high_conversion_threshold', config['high_conversion_threshold'])
                    config['low_conversion_threshold'] = file_config['performance_thresholds'].get('low_conversion_threshold', config['low_conversion_threshold'])
                
                if 'upload_controls' in file_config:
                    config['max_upload_per_run'] = file_config['upload_controls'].get('max_upload_per_run', config['max_upload_per_run'])
                    config['min_upload_batch'] = file_config['upload_controls'].get('min_upload_batch', config['min_upload_batch'])
                    config['max_daily_uploads'] = file_config['upload_controls'].get('max_daily_uploads', config['max_daily_uploads'])
                    hours = file_config['upload_controls'].get('min_time_between_uploads_hours', config['min_time_between_uploads']/3600)
                    config['min_time_between_uploads'] = int(hours * 3600)
                
                if 'source_management' in file_config:
                    config['source_files'] = file_config['source_management'].get('source_files', config['source_files'])
                
                logger.info(f"📋 Loaded configuration from {config_file}")
                return config
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to load config file {config_file}: {e}")
                logger.info("📋 Using default configuration")
        
        return default_config
    
    def load_upload_history(self) -> Dict:
        """Load tracking of previously uploaded leads"""
        try:
            with open(self.config['used_leads_tracking'], 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'uploaded_npis': set(),
                'daily_upload_count': 0,
                'last_upload_date': None,
                'last_upload_time': 0
            }
    
    def save_upload_history(self):
        """Save upload tracking data"""
        # Convert set to list for JSON serialization
        history_to_save = self.upload_history.copy()
        history_to_save['uploaded_npis'] = list(self.upload_history['uploaded_npis'])
        
        with open(self.config['used_leads_tracking'], 'w') as f:
            json.dump(history_to_save, f, indent=2, default=str)
    
    def get_current_lead_metrics(self) -> Dict:
        """Get comprehensive lead inventory and performance metrics"""
        try:
            # Basic lead counts
            total_leads = self.db.query(Lead).count()
            available_leads = self.db.query(Lead).filter(
                Lead.status.in_([LeadStatus.NEW, LeadStatus.RECYCLED])
            ).count()
            
            # Priority distribution
            priority_counts = {}
            for priority in ['A+', 'A', 'B', 'C']:
                count = self.db.query(Lead).filter(
                    Lead.priority == priority,
                    Lead.status.in_([LeadStatus.NEW, LeadStatus.RECYCLED])
                ).count()
                priority_counts[priority] = count
            
            # Performance metrics (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            # Conversion rates by priority
            conversion_rates = {}
            for priority in ['A+', 'A', 'B']:
                total_worked = self.db.query(Lead).filter(
                    Lead.priority == priority,
                    Lead.created_at >= thirty_days_ago,
                    Lead.status != LeadStatus.NEW
                ).count()
                
                converted = self.db.query(Lead).filter(
                    Lead.priority == priority,
                    Lead.created_at >= thirty_days_ago,
                    Lead.status == LeadStatus.CLOSED_WON
                ).count()
                
                conversion_rates[priority] = converted / total_worked if total_worked > 0 else 0
            
            # Agent activity
            active_agents = self.db.query(User).filter(
                User.role == 'agent',
                User.is_active == True
            ).count()
            
            return {
                'total_leads': total_leads,
                'available_leads': available_leads,
                'priority_counts': priority_counts,
                'conversion_rates': conversion_rates,
                'active_agents': active_agents,
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting lead metrics: {e}")
            return {}
    
    def calculate_upload_strategy(self, metrics: Dict) -> Dict:
        """Determine what leads to upload based on current metrics and performance"""
        strategy = {
            'should_upload': False,
            'priority_targets': {},
            'total_target': 0,
            'reasoning': []
        }
        
        # Check if upload is needed
        if metrics['total_leads'] < self.config['min_total_leads']:
            strategy['should_upload'] = True
            strategy['reasoning'].append(f"Total leads ({metrics['total_leads']}) below minimum ({self.config['min_total_leads']})")
            
            # Set default targets to reach minimum levels
            target_total = self.config['target_total_leads'] - metrics['total_leads']
            target_total = min(target_total, self.config['max_upload_per_run'])
            
            # Distribute targets across priorities
            priority_ratio = {'A+': 0.2, 'A': 0.5, 'B': 0.3}  # Default distribution
            for priority, ratio in priority_ratio.items():
                strategy['priority_targets'][priority] = int(target_total * ratio)
        
        # Check priority-specific minimums (override general targets if higher)
        for priority, min_count in self.config['min_priority_leads'].items():
            current_count = metrics['priority_counts'].get(priority, 0)
            if current_count < min_count:
                strategy['should_upload'] = True
                needed = min_count - current_count + 5  # Add buffer
                # Use the higher of calculated target or minimum needed
                strategy['priority_targets'][priority] = max(
                    strategy['priority_targets'].get(priority, 0), 
                    needed
                )
                strategy['reasoning'].append(f"{priority} priority has {current_count}, need {min_count} minimum")
        
        # Performance-based adjustments
        if strategy['should_upload']:
            for priority, rate in metrics['conversion_rates'].items():
                if rate >= self.config['high_conversion_threshold']:
                    # High conversion - upload more of this priority
                    current_target = strategy['priority_targets'].get(priority, 0)
                    bonus = min(20, int(current_target * 0.5))  # 50% bonus, max 20
                    strategy['priority_targets'][priority] = current_target + bonus
                    strategy['reasoning'].append(f"{priority} has high conversion ({rate:.1%}) - adding {bonus} bonus leads")
        
        # Calculate total target
        strategy['total_target'] = sum(strategy['priority_targets'].values())
        
        # Apply safety limits
        if strategy['total_target'] > self.config['max_upload_per_run']:
            strategy['total_target'] = self.config['max_upload_per_run']
            strategy['reasoning'].append(f"Capped at max upload limit ({self.config['max_upload_per_run']})")
        
        return strategy
    
    def check_safety_constraints(self) -> Tuple[bool, str]:
        """Check if it's safe to upload more leads"""
        now = time.time()
        
        # Check time since last upload
        if (now - self.upload_history.get('last_upload_time', 0)) < self.config['min_time_between_uploads']:
            time_left = self.config['min_time_between_uploads'] - (now - self.upload_history.get('last_upload_time', 0))
            return False, f"Must wait {time_left/60:.1f} more minutes between uploads"
        
        # Check daily upload limit
        today = datetime.utcnow().date()
        if str(today) == self.upload_history.get('last_upload_date'):
            if self.upload_history.get('daily_upload_count', 0) >= self.config['max_daily_uploads']:
                return False, f"Daily upload limit reached ({self.config['max_daily_uploads']})"
        
        return True, "Safety checks passed"
    
    def load_available_leads(self) -> List[Dict]:
        """Load leads from source files that haven't been uploaded yet"""
        available_leads = []
        uploaded_npis = set(self.upload_history.get('uploaded_npis', []))
        
        for source_file in self.config['source_files']:
            try:
                with open(source_file, 'r') as f:
                    leads = json.load(f)
                
                # Filter out already uploaded leads
                new_leads = [
                    lead for lead in leads 
                    if lead.get('npi') and lead.get('npi') not in uploaded_npis
                ]
                
                available_leads.extend(new_leads)
                logger.info(f"Loaded {len(new_leads)} new leads from {source_file}")
                
            except Exception as e:
                logger.error(f"Error loading {source_file}: {e}")
        
        return available_leads
    
    def select_leads_for_upload(self, available_leads: List[Dict], strategy: Dict) -> List[Dict]:
        """Select specific leads based on upload strategy"""
        selected_leads = []
        
        # Group available leads by priority
        leads_by_priority = {}
        for lead in available_leads:
            score = lead.get('score', 0)
            if score >= 90:
                priority = 'A+'
            elif score >= 75:
                priority = 'A'
            elif score >= 60:
                priority = 'B'
            else:
                priority = 'C'
            
            if priority not in leads_by_priority:
                leads_by_priority[priority] = []
            leads_by_priority[priority].append(lead)
        
        # Sort each priority by score (highest first)
        for priority in leads_by_priority:
            leads_by_priority[priority].sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Select leads according to strategy
        for priority, target_count in strategy['priority_targets'].items():
            if priority in leads_by_priority:
                selected = leads_by_priority[priority][:target_count]
                selected_leads.extend(selected)
                logger.info(f"Selected {len(selected)} {priority} priority leads (target: {target_count})")
        
        return selected_leads
    
    def execute_automated_upload(self, selected_leads: List[Dict]) -> bool:
        """Execute the automated lead upload"""
        try:
            # Use the proven API injection system
            injector = APISmartLeadInjection(self.crm_api_url)
            
            if not injector.authenticate():
                logger.error("Failed to authenticate with CRM API")
                return False
            
            # Transform leads for API
            api_leads = [injector.transform_lead_for_api(lead) for lead in selected_leads]
            
            # Upload in batches
            total_uploaded = 0
            total_duplicates = 0
            total_errors = 0
            
            batch_size = 50
            for i in range(0, len(api_leads), batch_size):
                batch = api_leads[i:i + batch_size]
                
                uploaded, duplicates, errors = injector.upload_lead_batch(batch)
                total_uploaded += uploaded
                total_duplicates += duplicates
                total_errors += errors
                
                logger.info(f"Automated batch {i//batch_size + 1}: {uploaded} uploaded, {duplicates} duplicates, {errors} errors")
                
                # Brief pause between batches
                time.sleep(2)
            
            # Update tracking
            uploaded_npis = [lead.get('npi') for lead in selected_leads if lead.get('npi')]
            self.upload_history['uploaded_npis'].update(uploaded_npis)
            
            today = datetime.utcnow().date()
            if str(today) != self.upload_history.get('last_upload_date'):
                self.upload_history['daily_upload_count'] = 0
            
            self.upload_history['daily_upload_count'] += total_uploaded
            self.upload_history['last_upload_date'] = str(today)
            self.upload_history['last_upload_time'] = time.time()
            
            self.save_upload_history()
            
            logger.info(f"🎉 Automated upload complete: {total_uploaded} leads uploaded, {total_duplicates} duplicates, {total_errors} errors")
            return True
            
        except Exception as e:
            logger.error(f"Automated upload failed: {e}")
            return False
    
    def run_automation_cycle(self):
        """Execute one complete automation cycle"""
        logger.info("🔄 Starting automated lead management cycle")
        
        try:
            # Get current metrics
            metrics = self.get_current_lead_metrics()
            if not metrics:
                logger.error("Failed to get lead metrics")
                return
            
            logger.info(f"📊 Current metrics: {metrics['total_leads']} total, {metrics['available_leads']} available")
            
            # Calculate upload strategy
            strategy = self.calculate_upload_strategy(metrics)
            
            if not strategy['should_upload']:
                logger.info("✅ Lead levels sufficient, no upload needed")
                return
            
            logger.info(f"🎯 Upload strategy: {strategy['reasoning']}")
            logger.info(f"📈 Targets: {strategy['priority_targets']}")
            
            # Check safety constraints
            safe, reason = self.check_safety_constraints()
            if not safe:
                logger.warning(f"⚠️ Upload blocked: {reason}")
                return
            
            # Load available leads
            available_leads = self.load_available_leads()
            if not available_leads:
                logger.warning("⚠️ No new leads available for upload")
                return
            
            logger.info(f"📁 Found {len(available_leads)} available leads")
            
            # Select leads for upload
            selected_leads = self.select_leads_for_upload(available_leads, strategy)
            if not selected_leads:
                logger.warning("⚠️ No leads selected for upload")
                return
            
            logger.info(f"🎯 Selected {len(selected_leads)} leads for automated upload")
            
            # Execute upload
            success = self.execute_automated_upload(selected_leads)
            
            if success:
                logger.info("🎉 Automated lead management cycle completed successfully")
            else:
                logger.error("❌ Automated upload failed")
                
        except Exception as e:
            logger.error(f"Automation cycle failed: {e}")
            import traceback
            traceback.print_exc()
    
    def start_continuous_monitoring(self, check_interval_minutes=30):
        """Start continuous monitoring with periodic checks"""
        logger.info(f"🚀 Starting continuous lead monitoring (checks every {check_interval_minutes} minutes)")
        
        while True:
            try:
                self.run_automation_cycle()
                
                # Wait for next check
                logger.info(f"😴 Sleeping for {check_interval_minutes} minutes...")
                time.sleep(check_interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Continuous monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Lead Management System')
    parser.add_argument('--mode', choices=['once', 'continuous'], default='once',
                       help='Run once or start continuous monitoring')
    parser.add_argument('--interval', type=int, default=30,
                       help='Check interval in minutes for continuous mode')
    parser.add_argument('--config', type=str, 
                       help='Configuration file path (JSON format)')
    
    args = parser.parse_args()
    
    manager = AutomatedLeadManager(config_file=args.config)
    
    if args.mode == 'once':
        logger.info("Running single automation cycle...")
        manager.run_automation_cycle()
    else:
        logger.info("Starting continuous monitoring...")
        manager.start_continuous_monitoring(args.interval)

if __name__ == "__main__":
    main() 