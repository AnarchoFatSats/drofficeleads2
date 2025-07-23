#!/usr/bin/env python3
"""
Migration script to add team hierarchy support to CRM database
Adds manager_id column to users table
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_team_hierarchy():
    """Add team hierarchy support"""
    
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
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user
        )
    else:
        conn = psycopg2.connect(database_url)
    
    cursor = conn.cursor()
    
    try:
        print("🔄 Starting team hierarchy migration...")
        
        # Check if manager_id column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='manager_id'
        """)
        
        if cursor.fetchone():
            print("✅ manager_id column already exists - skipping migration")
            return
        
        # Add manager_id column
        print("📊 Adding manager_id column to users table...")
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN manager_id INTEGER REFERENCES users(id)
        """)
        
        # Add index for performance
        print("📈 Adding index on manager_id...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_manager_id ON users(manager_id)
        """)
        
        # Commit the changes
        conn.commit()
        print("✅ Team hierarchy migration completed successfully!")
        
        # Show current user stats
        cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
        user_stats = cursor.fetchall()
        
        print("\n📊 Current user distribution:")
        for role, count in user_stats:
            print(f"  {role}: {count} users")
            
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        raise
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate_team_hierarchy() 