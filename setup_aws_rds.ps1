# Cura Genesis CRM - AWS RDS PostgreSQL Setup Script (PowerShell)
# This script creates and configures AWS RDS PostgreSQL for production

param(
    [switch]$Force,
    [string]$DbPassword = "CuraGenesis2024!SecurePassword"
)

# Configuration variables
$DB_INSTANCE_ID = "cura-genesis-crm-db"
$DB_NAME = "cura_genesis_crm"
$DB_USERNAME = "crmuser"
$DB_INSTANCE_CLASS = "db.t3.micro"
$ALLOCATED_STORAGE = "20"
$ENGINE_VERSION = "14.9"
$SECURITY_GROUP_NAME = "cura-genesis-crm-sg"

Write-Host "🚀 Setting up AWS RDS PostgreSQL for Cura Genesis CRM" -ForegroundColor Blue
Write-Host "============================================================"

# Get AWS region and account ID
try {
    $AWS_REGION = aws configure get region
    if (-not $AWS_REGION) {
        Write-Host "❌ AWS region not configured. Please run 'aws configure' first." -ForegroundColor Red
        exit 1
    }
    
    $AWS_ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
    Write-Host "📍 Using AWS Region: $AWS_REGION" -ForegroundColor Green
    Write-Host "🔑 AWS Account ID: $AWS_ACCOUNT_ID" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to get AWS configuration. Please ensure AWS CLI is configured." -ForegroundColor Red
    exit 1
}

# Function to check if database exists
function Test-DatabaseExists {
    try {
        $result = aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# Function to check if security group exists
function Test-SecurityGroupExists {
    try {
        $result = aws ec2 describe-security-groups --group-names $SECURITY_GROUP_NAME 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

Write-Host ""
Write-Host "🔍 Checking existing resources..." -ForegroundColor Yellow

# Check if database already exists
if (Test-DatabaseExists) {
    Write-Host "⚠️ Database $DB_INSTANCE_ID already exists" -ForegroundColor Yellow
    $DB_ENDPOINT = aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --query 'DBInstances[0].Endpoint.Address' --output text
    Write-Host "📊 Database endpoint: $DB_ENDPOINT" -ForegroundColor Green
}
else {
    Write-Host "📝 Creating new RDS PostgreSQL database..." -ForegroundColor Blue
    
    # Get default VPC and subnets
    $DEFAULT_VPC = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text
    if ($DEFAULT_VPC -eq "None" -or -not $DEFAULT_VPC) {
        Write-Host "❌ No default VPC found. Please create a VPC first." -ForegroundColor Red
        exit 1
    }
    
    $SUBNET_IDS = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$DEFAULT_VPC" --query 'Subnets[].SubnetId' --output text
    $SUBNET_ARRAY = $SUBNET_IDS -split '\s+'
    
    if ($SUBNET_ARRAY.Count -lt 2) {
        Write-Host "❌ Need at least 2 subnets for RDS. Found $($SUBNET_ARRAY.Count)" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "🌐 Using VPC: $DEFAULT_VPC" -ForegroundColor Green
    Write-Host "🔗 Using subnets: $($SUBNET_ARRAY[0]) $($SUBNET_ARRAY[1])" -ForegroundColor Green
    
    # Create DB subnet group
    Write-Host "📡 Creating DB subnet group..." -ForegroundColor Blue
    try {
        aws rds create-db-subnet-group `
            --db-subnet-group-name cura-genesis-subnet-group `
            --db-subnet-group-description "Subnet group for Cura Genesis CRM" `
            --subnet-ids $SUBNET_ARRAY[0] $SUBNET_ARRAY[1] `
            --tags Key=Project,Value=CuraGenesisCRM Key=Environment,Value=Production
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️ Subnet group may already exist, continuing..." -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "⚠️ Error creating subnet group, may already exist" -ForegroundColor Yellow
    }
    
    # Create security group if it doesn't exist
    if (-not (Test-SecurityGroupExists)) {
        Write-Host "🔒 Creating security group..." -ForegroundColor Blue
        $SECURITY_GROUP_ID = aws ec2 create-security-group `
            --group-name $SECURITY_GROUP_NAME `
            --description "Security group for Cura Genesis CRM Database" `
            --vpc-id $DEFAULT_VPC `
            --query 'GroupId' --output text
        
        # Add rules for PostgreSQL access
        aws ec2 authorize-security-group-ingress `
            --group-id $SECURITY_GROUP_ID `
            --protocol tcp `
            --port 5432 `
            --cidr 0.0.0.0/0
            
        Write-Host "🔒 Security group created: $SECURITY_GROUP_ID" -ForegroundColor Green
    }
    else {
        $SECURITY_GROUP_ID = aws ec2 describe-security-groups --group-names $SECURITY_GROUP_NAME --query 'SecurityGroups[0].GroupId' --output text
        Write-Host "🔒 Using existing security group: $SECURITY_GROUP_ID" -ForegroundColor Green
    }
    
    # Create RDS instance
    Write-Host "🗄️ Creating RDS PostgreSQL instance..." -ForegroundColor Blue
    Write-Host "⏳ This will take 5-10 minutes..." -ForegroundColor Yellow
    
    aws rds create-db-instance `
        --db-instance-identifier $DB_INSTANCE_ID `
        --db-instance-class $DB_INSTANCE_CLASS `
        --engine postgres `
        --engine-version $ENGINE_VERSION `
        --master-username $DB_USERNAME `
        --master-user-password $DbPassword `
        --allocated-storage $ALLOCATED_STORAGE `
        --db-name $DB_NAME `
        --db-subnet-group-name cura-genesis-subnet-group `
        --vpc-security-group-ids $SECURITY_GROUP_ID `
        --backup-retention-period 7 `
        --storage-encrypted `
        --deletion-protection `
        --enable-performance-insights `
        --tags Key=Project,Value=CuraGenesisCRM Key=Environment,Value=Production
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create RDS instance" -ForegroundColor Red
        exit 1
    }
    
    # Wait for database to be available
    Write-Host "⏳ Waiting for database to become available..." -ForegroundColor Yellow
    aws rds wait db-instance-available --db-instance-identifier $DB_INSTANCE_ID
    
    # Get the endpoint
    $DB_ENDPOINT = aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --query 'DBInstances[0].Endpoint.Address' --output text
    Write-Host "✅ Database created successfully!" -ForegroundColor Green
    Write-Host "📊 Database endpoint: $DB_ENDPOINT" -ForegroundColor Green
}

# Create production environment file
Write-Host ""
Write-Host "📝 Creating production environment configuration..." -ForegroundColor Blue

# Generate a secure secret key
$bytes = [System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)
$SECRET_KEY = [System.Convert]::ToHexString($bytes).ToLower()

$envContent = @"
# Cura Genesis CRM - Production Environment Configuration
# Generated on $(Get-Date)

# ===================================================================
# DATABASE CONFIGURATION (AWS RDS)
# ===================================================================
DATABASE_URL=postgresql://$DB_USERNAME`:$DbPassword@$DB_ENDPOINT`:5432/$DB_NAME
DATABASE_ECHO=false

# ===================================================================
# SECURITY & AUTHENTICATION
# ===================================================================
SECRET_KEY=$SECRET_KEY
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
"@

$envContent | Out-File -FilePath ".env.production" -Encoding UTF8
Write-Host "📝 Production environment file created: .env.production" -ForegroundColor Green

# Test database connection
Write-Host ""
Write-Host "🔍 Testing database connection..." -ForegroundColor Blue

# Install psycopg2 if not present
try {
    python -c "import psycopg2" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "📦 Installing psycopg2-binary..." -ForegroundColor Yellow
        pip install psycopg2-binary
    }
}
catch {
    Write-Host "📦 Installing psycopg2-binary..." -ForegroundColor Yellow
    pip install psycopg2-binary
}

# Test connection with Python
$pythonScript = @"
import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="$DB_ENDPOINT",
        database="$DB_NAME", 
        user="$DB_USERNAME",
        password="$DbPassword",
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
"@

$pythonScript | python
$connectionTest = $LASTEXITCODE

if ($connectionTest -eq 0) {
    Write-Host "✅ Database connection test passed!" -ForegroundColor Green
}
else {
    Write-Host "❌ Database connection test failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 AWS RDS PostgreSQL setup completed successfully!" -ForegroundColor Green
Write-Host "============================================================"
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Apply database schema: python setup_database.py --production"
Write-Host "2. Test API endpoints with new database"
Write-Host "3. Deploy backend to AWS ECS or Amplify"
Write-Host ""
Write-Host "📊 Database Details:" -ForegroundColor Blue
Write-Host "• Instance ID: $DB_INSTANCE_ID"
Write-Host "• Endpoint: $DB_ENDPOINT"
Write-Host "• Database: $DB_NAME"
Write-Host "• Username: $DB_USERNAME"
Write-Host "• Environment file: .env.production"
Write-Host ""
Write-Host "🔒 Security Note:" -ForegroundColor Yellow
Write-Host "The database password is: $DbPassword"
Write-Host "Store this securely and consider changing it after initial setup."
Write-Host ""
Write-Host "✅ Ready to proceed with backend integration!" -ForegroundColor Green 