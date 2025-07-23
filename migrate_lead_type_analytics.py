#!/usr/bin/env python3
"""
Migration script to add lead type analytics tables to existing CRM database
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_lead_type_analytics():
    """Add lead type analytics tables"""
    
    # Database connection
    database_url = os.getenv('DATABASE_URL', 'postgresql://alexsiegel@localhost:5432/cura_genesis_crm')
    
    # Parse database URL
    if database_url.startswith('postgresql://'):
        conn_parts = database_url.replace('postgresql://', '').split('/')
        conn_info = conn_parts[0].split('@')
        user = conn_info[0]
        host_port = conn_info[1].split(':')
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else '5432'
        database = conn_parts[1]
    else:
        raise ValueError("DATABASE_URL must start with 'postgresql://'")

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user
        )
        cursor = conn.cursor()
        
        print("🚀 Starting lead type analytics migration...")
        
        # Create agent_lead_type_performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_lead_type_performance (
                id SERIAL PRIMARY KEY,
                agent_id INTEGER NOT NULL REFERENCES users(id),
                
                -- Lead Type Categorization
                specialty_category VARCHAR(100),
                priority_level VARCHAR(10),
                state_region VARCHAR(50),
                practice_size VARCHAR(20),
                score_range VARCHAR(20),
                lead_source VARCHAR(50),
                
                -- Performance Metrics
                total_assigned INTEGER DEFAULT 0,
                total_contacted INTEGER DEFAULT 0,
                total_closed_won INTEGER DEFAULT 0,
                total_closed_lost INTEGER DEFAULT 0,
                total_recycled INTEGER DEFAULT 0,
                
                -- Calculated Performance Scores
                contact_rate FLOAT DEFAULT 0.0,
                conversion_rate FLOAT DEFAULT 0.0,
                close_rate FLOAT DEFAULT 0.0,
                avg_days_to_close FLOAT DEFAULT 0.0,
                
                -- Timestamps
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- Create unique constraint on agent + lead type combination
                UNIQUE(agent_id, specialty_category, priority_level, state_region, practice_size, score_range, lead_source)
            );
        """)
        
        print("✅ Created agent_lead_type_performance table")
        
        # Create lead_type_analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_type_analytics (
                id SERIAL PRIMARY KEY,
                
                -- Lead Type Categorization
                specialty_category VARCHAR(100),
                priority_level VARCHAR(10),
                state_region VARCHAR(50),
                practice_size VARCHAR(20),
                score_range VARCHAR(20),
                lead_source VARCHAR(50),
                
                -- Aggregate Metrics
                total_leads INTEGER DEFAULT 0,
                total_contacted INTEGER DEFAULT 0,
                total_closed_won INTEGER DEFAULT 0,
                total_closed_lost INTEGER DEFAULT 0,
                
                -- Performance Metrics
                overall_contact_rate FLOAT DEFAULT 0.0,
                overall_conversion_rate FLOAT DEFAULT 0.0,
                overall_close_rate FLOAT DEFAULT 0.0,
                avg_deal_value FLOAT DEFAULT 0.0,
                
                -- Top Performers for this lead type
                best_agent_id INTEGER REFERENCES users(id),
                best_agent_conversion_rate FLOAT DEFAULT 0.0,
                
                -- Update tracking
                last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- Create unique constraint on lead type combination
                UNIQUE(specialty_category, priority_level, state_region, practice_size, score_range, lead_source)
            );
        """)
        
        print("✅ Created lead_type_analytics table")
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_performance_agent_id 
            ON agent_lead_type_performance(agent_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_performance_specialty 
            ON agent_lead_type_performance(specialty_category);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_performance_conversion 
            ON agent_lead_type_performance(conversion_rate DESC);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lead_analytics_specialty 
            ON lead_type_analytics(specialty_category);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lead_analytics_conversion 
            ON lead_type_analytics(overall_conversion_rate DESC);
        """)
        
        print("✅ Created performance indexes")
        
        # Commit the transaction
        conn.commit()
        print("🎯 Lead type analytics migration completed successfully!")
        
        # Display summary
        cursor.execute("SELECT COUNT(*) FROM agent_lead_type_performance")
        perf_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lead_type_analytics")
        analytics_count = cursor.fetchone()[0]
        
        print(f"\n📊 Database Summary:")
        print(f"  - Agent performance records: {perf_count}")
        print(f"  - Lead type analytics records: {analytics_count}")
        print(f"\n🚀 Ready for lead type analytics and smart assignment!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_lead_type_analytics() 