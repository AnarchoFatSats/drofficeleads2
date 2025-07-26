#!/usr/bin/env python3
"""
Cura Genesis CRM Database Setup Script
Supports both local PostgreSQL and AWS RDS environments
"""

import sys
import os
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def print_header():
    """Print setup header"""
    print("🚀 Setting up Cura Genesis CRM Database")
    print("=" * 50)

def check_python_dependencies():
    """Check and install required Python packages"""
    required_packages = [
        'psycopg2-binary',
        'sqlalchemy', 
        'python-dotenv'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✅ {package} is installed")
        except ImportError:
            logger.info(f"📦 Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def load_environment(env_file: str = None):
    """Load environment variables from file"""
    try:
        from dotenv import load_dotenv
        
        if env_file:
            env_path = Path(env_file)
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"✅ Loaded environment from {env_file}")
                return True
            else:
                logger.error(f"❌ Environment file not found: {env_file}")
                return False
        else:
            # Try to find environment file
            for env_name in ['.env.production', '.env', 'crm_config.env']:
                env_path = Path(env_name)
                if env_path.exists():
                    load_dotenv(env_path)
                    logger.info(f"✅ Loaded environment from {env_name}")
                    return True
            
            logger.warning("⚠️ No environment file found, using defaults")
            return False
    except ImportError:
        logger.error("❌ python-dotenv not installed")
        return False

def get_database_url(production: bool = False) -> str:
    """Get database URL from environment or defaults"""
    if production:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            # Check for AWS RDS components
            rds_endpoint = os.getenv('RDS_ENDPOINT')
            if rds_endpoint:
                db_user = os.getenv('DB_USERNAME', 'crmuser')
                db_password = os.getenv('DB_PASSWORD', 'CuraGenesis2024!SecurePassword')
                db_name = os.getenv('DB_NAME', 'cura_genesis_crm')
                db_url = f"postgresql://{db_user}:{db_password}@{rds_endpoint}:5432/{db_name}"
            else:
                db_url = "postgresql://crmuser:CuraGenesis2024!SecurePassword@localhost:5432/cura_genesis_crm"
    else:
        db_url = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/cura_genesis_crm')
    
    return db_url

def test_database_connection(database_url: str) -> bool:
    """Test database connection"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse database URL
        result = urlparse(database_url)
        
        logger.info("🔍 Testing database connection...")
        
        # Test connection
        conn = psycopg2.connect(
            host=result.hostname,
            database=result.path[1:],  # Remove leading /
            user=result.username,
            password=result.password,
            port=result.port or 5432,
            connect_timeout=10
        )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        logger.info(f"✅ Database connection successful!")
        logger.info(f"📊 PostgreSQL version: {version}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def apply_database_schema(database_url: str) -> bool:
    """Apply database schema from SQL file"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        schema_file = Path('crm_database_schema.sql')
        if not schema_file.exists():
            logger.error(f"❌ Schema file not found: {schema_file}")
            return False
        
        logger.info("📋 Applying database schema...")
        
        # Parse database URL
        result = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=result.hostname,
            database=result.path[1:],
            user=result.username,
            password=result.password,
            port=result.port or 5432
        )
        
        # Read and execute schema
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        cursor = conn.cursor()
        cursor.execute(schema_sql)
        conn.commit()
        
        logger.info("✅ Database schema applied successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to apply schema: {e}")
        return False

def run_migrations(database_url: str) -> bool:
    """Run database migrations"""
    try:
        logger.info("🔄 Running database migrations...")
        
        # Check if migration script exists
        migration_script = Path('migrate_percentile_system.py')
        if migration_script.exists():
            # Set DATABASE_URL environment variable for migration script
            env = os.environ.copy()
            env['DATABASE_URL'] = database_url
            
            result = subprocess.run(
                [sys.executable, str(migration_script)],
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("✅ Migrations completed successfully")
                return True
            else:
                logger.error(f"❌ Migration failed: {result.stderr}")
                return False
        else:
            logger.info("ℹ️ No migration script found, skipping...")
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        return False

def create_default_env_file():
    """Create a default .env file if none exists"""
    env_file = Path('.env')
    if not env_file.exists():
        logger.info("📝 Creating default .env file...")
        
        default_env = """# Cura Genesis CRM Environment Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/cura_genesis_crm
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=false
ENABLE_GAMIFICATION=true
RECYCLING_ENABLED=true
"""
        
        with open(env_file, 'w') as f:
            f.write(default_env)
        
        logger.info("✅ Default .env file created")
        logger.warning("⚠️ Please update the DATABASE_URL and SECRET_KEY in .env")

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='Setup Cura Genesis CRM Database')
    parser.add_argument('--production', action='store_true', help='Use production environment settings')
    parser.add_argument('--env-file', help='Specify environment file to use')
    parser.add_argument('--schema-only', action='store_true', help='Only apply schema, skip migrations')
    parser.add_argument('--test-only', action='store_true', help='Only test connection, skip setup')
    
    args = parser.parse_args()
    
    print_header()
    
    # Check dependencies
    logger.info("🔍 Checking dependencies...")
    check_python_dependencies()
    
    # Load environment
    if args.env_file:
        load_environment(args.env_file)
    elif args.production:
        if not load_environment('.env.production'):
            logger.error("❌ Production environment file not found")
            logger.info("💡 Please run the AWS RDS setup script first: bash setup_aws_rds.sh")
            return False
    else:
        load_environment()
        create_default_env_file()
    
    # Get database URL
    database_url = get_database_url(args.production)
    logger.info(f"🔗 Using database URL: {database_url.split('@')[0]}@***")
    
    # Test connection
    if not test_database_connection(database_url):
        if args.production:
            logger.error("💡 Make sure AWS RDS instance is running and accessible")
        else:
            logger.error("💡 Make sure PostgreSQL is installed and running locally")
        return False
    
    if args.test_only:
        logger.info("✅ Connection test completed successfully!")
        return True
    
    # Apply schema
    if not apply_database_schema(database_url):
        return False
    
    # Run migrations (unless schema-only)
    if not args.schema_only:
        if not run_migrations(database_url):
            logger.warning("⚠️ Migrations failed, but schema was applied")
    
    # Success message
    logger.info("")
    logger.info("🎉 Database setup completed successfully!")
    logger.info("=" * 50)
    
    if args.production:
        logger.info("🌟 Production database is ready!")
        logger.info("📋 Next steps:")
        logger.info("   1. Test API endpoints: python crm_main.py")
        logger.info("   2. Deploy backend to AWS")
        logger.info("   3. Update frontend API URLs")
    else:
        logger.info("🧪 Development database is ready!")
        logger.info("📋 Next step: python crm_main.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1) 