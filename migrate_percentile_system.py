#!/usr/bin/env python3
"""
Migration script to add percentile/rank system to existing CRM database
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_to_percentile_system():
    """Add new columns for percentile/rank system"""
    
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
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user
        )
        
        cursor = conn.cursor()
        
        print("🔄 Migrating database to percentile/rank system...")
        
        # Add new columns to users table
        migration_sql = """
        -- Add new performance metric columns
        ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP WITH TIME ZONE;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS conversion_rate FLOAT DEFAULT 0.0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS activity_score INTEGER DEFAULT 0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS deals_closed INTEGER DEFAULT 0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS current_percentile FLOAT DEFAULT 0.0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS current_rank INTEGER DEFAULT 0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS performance_score FLOAT DEFAULT 0.0;
        
        -- Remove old points/level columns (keep them for now for data preservation)
        -- ALTER TABLE users DROP COLUMN IF EXISTS total_points;
        -- ALTER TABLE users DROP COLUMN IF EXISTS level;
        
        -- Initialize new metrics based on existing data
        UPDATE users SET 
            conversion_rate = 0.0,
            activity_score = COALESCE(total_points, 0),  -- Use old points as activity score base
            deals_closed = 0,
            current_percentile = 50.0,  -- Start everyone at 50th percentile
            current_rank = 1,
            performance_score = 0.0,
            last_activity = NOW()
        WHERE conversion_rate IS NULL;
        
        -- Drop old achievement tables if they exist
        DROP TABLE IF EXISTS user_achievements CASCADE;
        DROP TABLE IF EXISTS achievements CASCADE;
        """
        
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✅ Database migration completed successfully!")
        print("📊 New columns added: conversion_rate, activity_score, deals_closed, current_percentile, current_rank, performance_score, last_activity")
        
        # Show updated table structure
        cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Updated users table structure:")
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_to_percentile_system()
    if success:
        print("\n🚀 Ready to restart CRM with percentile/rank system!")
    else:
        print("\n💥 Migration failed - please check the errors above") 