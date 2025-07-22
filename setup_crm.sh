#!/bin/bash

# Cura Genesis CRM Setup Script
# Sets up PostgreSQL database, installs dependencies, and initializes the CRM system

set -e  # Exit on any error

echo "🚀 Cura Genesis CRM Setup"
echo "========================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
    print_info "Detected macOS platform"
elif [[ "$OSTYPE" == "linux"* ]]; then
    PLATFORM="linux"
    print_info "Detected Linux platform"
else
    print_error "Unsupported platform: $OSTYPE"
    exit 1
fi

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Python 3.8+
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_status "pip3 found"
    else
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check if PostgreSQL is available
    if command -v psql &> /dev/null; then
        print_status "PostgreSQL client found"
    else
        print_warning "PostgreSQL client not found - will need to install"
        install_postgresql
    fi
    
    # Check if Redis is available
    if command -v redis-cli &> /dev/null; then
        print_status "Redis client found"
    else
        print_warning "Redis not found - will need to install"
        install_redis
    fi
}

# Install PostgreSQL
install_postgresql() {
    print_info "Installing PostgreSQL..."
    
    if [[ "$PLATFORM" == "macos" ]]; then
        if command -v brew &> /dev/null; then
            brew install postgresql
            brew services start postgresql
        else
            print_error "Homebrew not found. Please install PostgreSQL manually."
            exit 1
        fi
    elif [[ "$PLATFORM" == "linux" ]]; then
        sudo apt-get update
        sudo apt-get install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    fi
    
    print_status "PostgreSQL installed"
}

# Install Redis
install_redis() {
    print_info "Installing Redis..."
    
    if [[ "$PLATFORM" == "macos" ]]; then
        if command -v brew &> /dev/null; then
            brew install redis
            brew services start redis
        else
            print_error "Homebrew not found. Please install Redis manually."
            exit 1
        fi
    elif [[ "$PLATFORM" == "linux" ]]; then
        sudo apt-get update
        sudo apt-get install -y redis-server
        sudo systemctl start redis-server
        sudo systemctl enable redis-server
    fi
    
    print_status "Redis installed"
}

# Setup Python environment
setup_python_env() {
    print_info "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_status "Python dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Setup database
setup_database() {
    print_info "Setting up database..."
    
    # Read database configuration
    echo "Database Configuration:"
    read -p "Enter PostgreSQL username (default: postgres): " DB_USER
    DB_USER=${DB_USER:-postgres}
    
    read -p "Enter PostgreSQL password: " -s DB_PASSWORD
    echo
    
    read -p "Enter database name (default: cura_genesis_crm): " DB_NAME
    DB_NAME=${DB_NAME:-cura_genesis_crm}
    
    read -p "Enter database host (default: localhost): " DB_HOST
    DB_HOST=${DB_HOST:-localhost}
    
    read -p "Enter database port (default: 5432): " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    
    # Create database if it doesn't exist
    export PGPASSWORD=$DB_PASSWORD
    
    if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        print_warning "Database $DB_NAME already exists"
    else
        createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME
        print_status "Database $DB_NAME created"
    fi
    
    # Run database schema
    if [ -f "crm_database_schema.sql" ]; then
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f crm_database_schema.sql
        print_status "Database schema created"
    else
        print_error "Database schema file not found"
        exit 1
    fi
    
    # Create .env file
    cat > .env << EOF
# Cura Genesis CRM Environment Configuration
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
DEBUG=false
REDIS_URL=redis://localhost:6379/0
FRONTEND_URL=http://localhost:3000

# Gamification
ENABLE_GAMIFICATION=true
POINTS_FIRST_CONTACT=10
POINTS_QUALIFIED_LEAD=25
POINTS_DEMO_SCHEDULED=50
POINTS_PROPOSAL_SENT=75
POINTS_SALE_CLOSED=200

# Lead Recycling
RECYCLING_ENABLED=true
RECYCLING_DAYS_DEFAULT=7
MIN_CONTACT_ATTEMPTS=3

# Email (update with your SMTP settings)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@curagenesis.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@curagenesis.com
EOF
    
    print_status "Environment configuration created (.env)"
    unset PGPASSWORD
}

# Migrate existing leads
migrate_leads() {
    print_info "Migrating existing leads..."
    
    if [ -f "web/data/hot_leads.json" ]; then
        print_info "Found existing leads data"
        read -p "Do you want to migrate existing leads to the CRM? (y/N): " MIGRATE
        
        if [[ $MIGRATE =~ ^[Yy]$ ]]; then
            source venv/bin/activate
            source .env
            python migrate_leads_to_crm.py
            print_status "Lead migration completed"
        fi
    else
        print_warning "No existing leads data found (web/data/hot_leads.json)"
    fi
}

# Create directories
create_directories() {
    print_info "Creating directories..."
    
    mkdir -p logs
    mkdir -p uploads
    mkdir -p temp
    
    print_status "Directories created"
}

# Final setup
final_setup() {
    print_info "Final setup steps..."
    
    # Create systemd service file for Linux
    if [[ "$PLATFORM" == "linux" ]]; then
        cat > cura-genesis-crm.service << EOF
[Unit]
Description=Cura Genesis CRM
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python crm_main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
        print_status "Systemd service file created (cura-genesis-crm.service)"
    fi
    
    # Create startup scripts
    cat > start_crm.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Cura Genesis CRM..."

# Activate virtual environment
source venv/bin/activate

# Load environment variables
source .env

# Start the CRM server
python crm_main.py
EOF
    
    chmod +x start_crm.sh
    print_status "Startup script created (start_crm.sh)"
    
    # Create development script
    cat > start_dev.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Cura Genesis CRM (Development Mode)..."

# Activate virtual environment
source venv/bin/activate

# Load environment variables
source .env

# Set debug mode
export DEBUG=true

# Start with auto-reload
uvicorn crm_main:app --host 0.0.0.0 --port 8000 --reload
EOF
    
    chmod +x start_dev.sh
    print_status "Development script created (start_dev.sh)"
}

# Main setup function
main() {
    echo "This script will set up the Cura Genesis CRM system."
    echo "It will install dependencies, set up the database, and migrate your existing leads."
    echo
    
    read -p "Do you want to continue? (y/N): " CONFIRM
    if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    echo
    print_info "Starting Cura Genesis CRM setup..."
    
    # Run setup steps
    check_prerequisites
    setup_python_env
    create_directories
    setup_database
    migrate_leads
    final_setup
    
    echo
    print_status "🎉 Cura Genesis CRM setup completed!"
    echo
    echo "Next steps:"
    echo "1. Review and update the .env file with your settings"
    echo "2. Start the CRM server: ./start_crm.sh"
    echo "3. Access the web interface at: http://localhost:8000"
    echo "4. Login with admin@curagenesis.com / admin123"
    echo
    echo "For development mode with auto-reload: ./start_dev.sh"
    echo
    echo "Default agent logins:"
    echo "• agent1@curagenesis.com / admin123"
    echo "• agent2@curagenesis.com / admin123"
    echo "• agent3@curagenesis.com / admin123"
    echo "• agent4@curagenesis.com / admin123"
    echo "• agent5@curagenesis.com / admin123"
    echo
}

# Run main function
main "$@" 