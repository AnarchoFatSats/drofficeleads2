#!/usr/bin/env python3
"""
Migration script to update users table schema to match crm_main.py User model
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production', override=True)
load_dotenv('.env', override=False)

def get_database_url():
    """Get database URL from environment or default"""
    return os.getenv('DATABASE_URL', 
        'postgresql://crmuser:CuraGenesis2024!SecurePassword@cura-genesis-crm-db.c6ds4c4qok1n.us-east-1.rds.amazonaws.com:5432/cura_genesis_crm'
    )

def migrate_users_table():
    """Migrate the users table to match the new schema"""
    database_url = get_database_url()
    print(f"🔄 Connecting to database...")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("✅ Database connection successful")
            
            # Start a transaction
            trans = conn.begin()
            
            try:
                print("🔄 Applying users table schema migration...")
                
                # Add new required columns
                migration_sql = """
                -- Add username column (required)
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS username VARCHAR(50);
                
                -- Add full_name column
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS full_name VARCHAR(100);
                
                -- Add hashed_password column
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);
                
                -- Add is_active column
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
                
                -- Add last_activity column
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP WITH TIME ZONE;
                
                -- Add team hierarchy
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS manager_id INTEGER REFERENCES users(id);
                
                -- Add performance metrics
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS conversion_rate FLOAT DEFAULT 0.0;
                
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS activity_score INTEGER DEFAULT 0;
                
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS deals_closed INTEGER DEFAULT 0;
                
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS current_percentile FLOAT DEFAULT 0.0;
                
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS current_rank INTEGER DEFAULT 0;
                
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS performance_score FLOAT DEFAULT 0.0;
                
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS badges JSONB;
                
                -- Migrate existing data
                -- Set username from email (before @)
                UPDATE users 
                SET username = split_part(email, '@', 1) 
                WHERE username IS NULL;
                
                -- Set full_name from first_name + last_name
                UPDATE users 
                SET full_name = COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')
                WHERE full_name IS NULL AND (first_name IS NOT NULL OR last_name IS NOT NULL);
                
                -- Copy password_hash to hashed_password
                UPDATE users 
                SET hashed_password = password_hash 
                WHERE hashed_password IS NULL AND password_hash IS NOT NULL;
                
                -- Set default badges
                UPDATE users 
                SET badges = '[]'::jsonb 
                WHERE badges IS NULL;
                
                -- Make username NOT NULL and UNIQUE
                ALTER TABLE users 
                ALTER COLUMN username SET NOT NULL;
                
                -- Add unique constraint on username if it doesn't exist
                DO $$ 
                BEGIN
                    ALTER TABLE users ADD CONSTRAINT users_username_unique UNIQUE (username);
                EXCEPTION 
                    WHEN duplicate_table THEN 
                        NULL; -- Ignore if constraint already exists
                END $$;
                
                -- Make hashed_password NOT NULL
                ALTER TABLE users 
                ALTER COLUMN hashed_password SET NOT NULL;
                """
                
                # Execute migration
                conn.execute(text(migration_sql))
                
                # Commit the transaction
                trans.commit()
                print("✅ Users table migration completed successfully")
                
                # Verify the migration
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    ORDER BY ordinal_position
                """))
                
                print("\n📋 Updated users table structure:")
                for row in result:
                    nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                    print(f"   {row[0]}: {row[1]} ({nullable})")
                
                # Check if we have any users
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                print(f"\n👥 Total users in table: {user_count}")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting users table schema migration...")
    success = migrate_users_table()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("   The users table now matches the crm_main.py User model.")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1) 