#!/bin/bash

# Cura Genesis CRM - AWS RDS PostgreSQL Setup Script
# This script creates and configures AWS RDS PostgreSQL for production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up AWS RDS PostgreSQL for Cura Genesis CRM${NC}"
echo "============================================================"

# Configuration variables
DB_INSTANCE_ID="cura-genesis-crm-db"
DB_NAME="cura_genesis_crm"
DB_USERNAME="crmuser"
DB_PASSWORD="CuraGenesis2024!SecurePassword"
DB_INSTANCE_CLASS="db.t3.micro"
ALLOCATED_STORAGE="20"
ENGINE_VERSION="14.9"
SECURITY_GROUP_NAME="cura-genesis-crm-sg"

# Get AWS region and account ID
AWS_REGION=$(aws configure get region)
if [ -z "$AWS_REGION" ]; then
    echo -e "${RED}❌ AWS region not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}📍 Using AWS Region: $AWS_REGION${NC}"
echo -e "${GREEN}🔑 AWS Account ID: $AWS_ACCOUNT_ID${NC}"

# Function to check if resource exists
check_db_exists() {
    aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID 2>/dev/null | grep -q "DBInstanceIdentifier"
}

# Function to check if security group exists
check_sg_exists() {
    aws ec2 describe-security-groups --group-names $SECURITY_GROUP_NAME 2>/dev/null | grep -q "GroupName"
}

echo ""
echo -e "${YELLOW}🔍 Checking existing resources...${NC}"

# Check if database already exists
if check_db_exists; then
    echo -e "${YELLOW}⚠️ Database $DB_INSTANCE_ID already exists${NC}"
    DB_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --query 'DBInstances[0].Endpoint.Address' --output text)
    echo -e "${GREEN}📊 Database endpoint: $DB_ENDPOINT${NC}"
else
    echo -e "${BLUE}📝 Creating new RDS PostgreSQL database...${NC}"
    
    # Get default VPC and subnets
    DEFAULT_VPC=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
    if [ "$DEFAULT_VPC" = "None" ]; then
        echo -e "${RED}❌ No default VPC found. Please create a VPC first.${NC}"
        exit 1
    fi
    
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$DEFAULT_VPC" --query 'Subnets[].SubnetId' --output text)
    SUBNET_ARRAY=($SUBNET_IDS)
    
    if [ ${#SUBNET_ARRAY[@]} -lt 2 ]; then
        echo -e "${RED}❌ Need at least 2 subnets for RDS. Found ${#SUBNET_ARRAY[@]}${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}🌐 Using VPC: $DEFAULT_VPC${NC}"
    echo -e "${GREEN}🔗 Using subnets: ${SUBNET_ARRAY[0]} ${SUBNET_ARRAY[1]}${NC}"
    
    # Create DB subnet group
    echo -e "${BLUE}📡 Creating DB subnet group...${NC}"
    aws rds create-db-subnet-group \
        --db-subnet-group-name cura-genesis-subnet-group \
        --db-subnet-group-description "Subnet group for Cura Genesis CRM" \
        --subnet-ids ${SUBNET_ARRAY[0]} ${SUBNET_ARRAY[1]} \
        --tags Key=Project,Value=CuraGenesisCRM Key=Environment,Value=Production
    
    # Create security group if it doesn't exist
    if ! check_sg_exists; then
        echo -e "${BLUE}🔒 Creating security group...${NC}"
        SECURITY_GROUP_ID=$(aws ec2 create-security-group \
            --group-name $SECURITY_GROUP_NAME \
            --description "Security group for Cura Genesis CRM Database" \
            --vpc-id $DEFAULT_VPC \
            --query 'GroupId' --output text)
        
        # Add rules for PostgreSQL access
        aws ec2 authorize-security-group-ingress \
            --group-id $SECURITY_GROUP_ID \
            --protocol tcp \
            --port 5432 \
            --cidr 0.0.0.0/0
            
        echo -e "${GREEN}🔒 Security group created: $SECURITY_GROUP_ID${NC}"
    else
        SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --group-names $SECURITY_GROUP_NAME --query 'SecurityGroups[0].GroupId' --output text)
        echo -e "${GREEN}🔒 Using existing security group: $SECURITY_GROUP_ID${NC}"
    fi
    
    # Create RDS instance
    echo -e "${BLUE}🗄️ Creating RDS PostgreSQL instance...${NC}"
    echo -e "${YELLOW}⏳ This will take 5-10 minutes...${NC}"
    
    aws rds create-db-instance \
        --db-instance-identifier $DB_INSTANCE_ID \
        --db-instance-class $DB_INSTANCE_CLASS \
        --engine postgres \
        --engine-version $ENGINE_VERSION \
        --master-username $DB_USERNAME \
        --master-user-password $DB_PASSWORD \
        --allocated-storage $ALLOCATED_STORAGE \
        --db-name $DB_NAME \
        --db-subnet-group-name cura-genesis-subnet-group \
        --vpc-security-group-ids $SECURITY_GROUP_ID \
        --backup-retention-period 7 \
        --storage-encrypted \
        --deletion-protection \
        --enable-performance-insights \
        --tags Key=Project,Value=CuraGenesisCRM Key=Environment,Value=Production
    
    # Wait for database to be available
    echo -e "${YELLOW}⏳ Waiting for database to become available...${NC}"
    aws rds wait db-instance-available --db-instance-identifier $DB_INSTANCE_ID
    
    # Get the endpoint
    DB_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --query 'DBInstances[0].Endpoint.Address' --output text)
    echo -e "${GREEN}✅ Database created successfully!${NC}"
    echo -e "${GREEN}📊 Database endpoint: $DB_ENDPOINT${NC}"
fi

# Create production environment file
echo ""
echo -e "${BLUE}📝 Creating production environment configuration...${NC}"

cat > .env.production << EOF
# Cura Genesis CRM - Production Environment Configuration
# Generated on $(date)

# ===================================================================
# DATABASE CONFIGURATION (AWS RDS)
# ===================================================================
DATABASE_URL=postgresql://$DB_USERNAME:$DB_PASSWORD@$DB_ENDPOINT:5432/$DB_NAME
DATABASE_ECHO=false

# ===================================================================
# SECURITY & AUTHENTICATION
# ===================================================================
SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===================================================================
# APPLICATION SETTINGS
# ===================================================================
APP_NAME=Cura Genesis CRM
APP_VERSION=1.0.0
DEBUG=false
API_V1_STR=/api/v1

# Frontend URL for CORS (your Amplify domain)
FRONTEND_URL=https://main.dqp56q5wifuh9.amplifyapp.com

# ===================================================================
# LEAD PROCESSING & SCORING
# ===================================================================
LEAD_SCORING_ALGORITHM=medicare_allograft
ENABLE_REAL_TIME_SCORING=true

# ===================================================================
# GAMIFICATION SETTINGS
# ===================================================================
ENABLE_GAMIFICATION=true
POINTS_FIRST_CONTACT=10
POINTS_QUALIFIED_LEAD=25
POINTS_DEMO_SCHEDULED=50
POINTS_PROPOSAL_SENT=75
POINTS_SALE_CLOSED=200

# ===================================================================
# LEAD RECYCLING SYSTEM
# ===================================================================
RECYCLING_ENABLED=true
RECYCLING_DAYS_DEFAULT=7
MIN_CONTACT_ATTEMPTS=3
AUTO_RECYCLING_ENABLED=true

# ===================================================================
# REAL-TIME FEATURES
# ===================================================================
ENABLE_WEBSOCKETS=true
ENABLE_PUSH_NOTIFICATIONS=true

# ===================================================================
# LOGGING
# ===================================================================
LOG_LEVEL=INFO
ENABLE_SQL_LOGGING=false

# ===================================================================
# MONITORING & ANALYTICS
# ===================================================================
ENABLE_ANALYTICS=true
ANALYTICS_RETENTION_DAYS=365

# ===================================================================
# RATE LIMITING
# ===================================================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# ===================================================================
# AWS CONFIGURATION
# ===================================================================
AWS_REGION=$AWS_REGION
RDS_ENDPOINT=$DB_ENDPOINT

EOF

echo -e "${GREEN}📝 Production environment file created: .env.production${NC}"

# Test database connection
echo ""
echo -e "${BLUE}🔍 Testing database connection...${NC}"

# Install psycopg2 if not present
if ! python -c "import psycopg2" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing psycopg2-binary...${NC}"
    pip install psycopg2-binary
fi

# Test connection with Python
python << EOF
import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="$DB_ENDPOINT",
        database="$DB_NAME", 
        user="$DB_USERNAME",
        password="$DB_PASSWORD",
        port=5432,
        connect_timeout=10
    )
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"✅ Database connection successful!")
    print(f"📊 PostgreSQL version: {version}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database connection test passed!${NC}"
else
    echo -e "${RED}❌ Database connection test failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 AWS RDS PostgreSQL setup completed successfully!${NC}"
echo "============================================================"
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Apply database schema: python setup_database.py --production"
echo "2. Test API endpoints with new database"
echo "3. Deploy backend to AWS ECS or Amplify"
echo ""
echo -e "${BLUE}📊 Database Details:${NC}"
echo "• Instance ID: $DB_INSTANCE_ID"
echo "• Endpoint: $DB_ENDPOINT"
echo "• Database: $DB_NAME"
echo "• Username: $DB_USERNAME"
echo "• Environment file: .env.production"
echo ""
echo -e "${YELLOW}🔒 Security Note:${NC}"
echo "The database password is: $DB_PASSWORD"
echo "Store this securely and consider changing it after initial setup."
echo ""
echo -e "${GREEN}✅ Ready to proceed with backend integration!${NC}" 