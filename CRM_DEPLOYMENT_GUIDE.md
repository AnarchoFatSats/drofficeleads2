# 🚀 Cura Genesis CRM - Complete Deployment Guide

## 📋 System Overview

The Cura Genesis CRM is a comprehensive customer relationship management system specifically designed for medical device sales teams. It preserves your existing sophisticated lead scoring algorithms while adding advanced CRM functionality, gamification, and real-time features.

## 🏗️ Architecture

### Backend Components
- **FastAPI Application** (`crm_main.py`) - Core API server
- **PostgreSQL Database** - Data persistence with sophisticated schema
- **Redis** - Caching and real-time features
- **Celery** - Background task processing
- **WebSocket Support** - Real-time notifications

### Frontend Components  
- **React + TypeScript** - Modern, responsive web interface
- **Material-UI** - Professional healthcare-themed design
- **Redux Toolkit** - State management
- **Socket.IO** - Real-time updates

### Key Features Implemented
✅ **Authentication & Role-Based Access Control**
- JWT-based authentication
- Admin, Manager, and Agent roles
- Session management and security

✅ **Lead Management with Preserved Scoring**
- All existing NPPES lead data migrated
- Medicare allograft scoring preserved
- Rural verification maintained
- Overlooked opportunity scoring intact

✅ **Gamification System**
- Points for activities (calls, emails, demos, sales)
- Badges and achievements
- Leaderboards (daily, weekly, monthly)
- Real-time point notifications

✅ **7-Day Lead Recycling**
- Automatic lead recycling after 7 business days
- Configurable rules by lead priority
- Activity tracking for recycling decisions
- Notification system for recycled leads

✅ **Real-Time Features**
- WebSocket connections for live updates
- Push notifications for new leads
- Activity tracking and points awarded
- Lead assignment notifications

✅ **Professional Healthcare UI**
- Clean, medical industry-appropriate design
- Responsive design for all devices
- Intuitive navigation and workflows
- Advanced data tables and charts

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+

### Step 1: Backend Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Set up environment variables
cp crm_config.env .env
# Edit .env with your database credentials and settings

# 3. Set up PostgreSQL database
# Create database: cura_genesis_crm
psql -U postgres -c "CREATE DATABASE cura_genesis_crm;"

# 4. Run database schema
psql -U postgres -d cura_genesis_crm -f crm_database_schema.sql

# 5. Migrate existing leads (optional)
python migrate_leads_to_crm.py

# 6. Start Redis server
redis-server

# 7. Start Celery workers (in separate terminal)
celery -A crm_realtime worker --loglevel=info

# 8. Start FastAPI server
python crm_main.py
```

### Step 2: Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node.js dependencies
npm install

# 3. Start development server
npm start
```

### Step 3: Quick Setup Script (Alternative)

```bash
# Run the automated setup script
chmod +x setup_crm.sh
./setup_crm.sh
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/cura_genesis_crm

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379/0

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

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@curagenesis.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@curagenesis.com
```

## 👥 Default User Accounts

After running the migration script, you'll have these default accounts:

### Admin Account
- **Email:** admin@curagenesis.com
- **Password:** admin123
- **Role:** Admin (full system access)

### Sample Agent Accounts
- **Email:** agent1@curagenesis.com
- **Password:** admin123
- **Role:** Agent (Territory 1 - Northeast)

- **Email:** agent2@curagenesis.com  
- **Password:** admin123
- **Role:** Agent (Territory 2 - Southeast)

- **Email:** agent3@curagenesis.com
- **Password:** admin123
- **Role:** Agent (Territory 3 - Midwest)

- **Email:** agent4@curagenesis.com
- **Password:** admin123
- **Role:** Agent (Territory 4 - Southwest)

- **Email:** agent5@curagenesis.com
- **Password:** admin123
- **Role:** Agent (Territory 5 - West)

## 🎮 Gamification System

### Point Values
- **First Contact:** 10 points
- **Call Connected:** 15 points
- **Email Sent:** 3 points
- **Meeting Scheduled:** 25 points
- **Lead Qualified:** 30 points
- **Demo Scheduled:** 50 points
- **Proposal Sent:** 75 points
- **Deal Closed:** 200 points

### Badges Available
- **First Blood** - Close your first deal
- **Speed Demon** - Contact lead within 1 hour
- **Closer** - Close 3 deals in a month
- **Lead Hunter** - Make 50 calls in a week
- **Territory King** - Top performer in territory

### Leaderboards
- Daily, weekly, and monthly rankings
- Territory-based competitions
- Real-time point updates

## 🔄 Lead Recycling Rules

### Default Rules by Priority
- **A+ Priority:** 7 days, 3 contact attempts minimum
- **A Priority:** 7 days, 3 contact attempts minimum
- **B+ Priority:** 10 days, 2 contact attempts minimum
- **B Priority:** 14 days, 2 contact attempts minimum
- **C Priority:** 21 days, 1 contact attempt minimum

### Recycling Process
1. Lead assigned to agent automatically sets recycling timer
2. System checks daily for eligible leads
3. Leads meeting criteria are automatically recycled
4. Previous agent and managers are notified
5. Lead returns to general pool for reassignment

## 📊 Lead Scoring (Preserved)

Your existing sophisticated lead scoring is fully preserved:

### Medicare Allograft Scoring
- Specialty-based scoring maintained
- Rural ZIP code verification
- Provider type filtering

### Overlooked Opportunity Scoring  
- Historical performance analysis
- Market opportunity identification
- Competitive advantage scoring

### Priority Assignment
- A+ Priority: Score 90-100
- A Priority: Score 80-89
- B+ Priority: Score 70-79
- B Priority: Score 60-69
- C Priority: Score below 60

## 🔧 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/logout` - User logout

### Leads
- `GET /api/v1/leads` - Get leads with filters
- `GET /api/v1/leads/{id}` - Get lead details
- `PUT /api/v1/leads/{id}` - Update lead
- `POST /api/v1/leads/{id}/assign` - Assign lead

### Activities
- `GET /api/v1/activities` - Get activities
- `POST /api/v1/activities` - Create activity
- `PUT /api/v1/activities/{id}` - Update activity

### Gamification
- `GET /api/v1/gamification/leaderboard` - Get leaderboard
- `GET /api/v1/gamification/points/{user_id}` - Get user points
- `GET /api/v1/gamification/badges/{user_id}` - Get user badges

### Notifications
- `GET /api/v1/notifications` - Get notifications
- `PUT /api/v1/notifications/{id}/read` - Mark as read

## 🚀 Production Deployment

### Using Docker (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Production Setup

```bash
# 1. Set up production database
# 2. Configure environment variables for production
# 3. Set up SSL certificates
# 4. Configure reverse proxy (nginx)
# 5. Set up monitoring (optional)
# 6. Configure backup strategy
```

### AWS Deployment

```bash
# 1. Set up RDS PostgreSQL instance
# 2. Set up ElastiCache Redis instance
# 3. Deploy backend to ECS or EC2
# 4. Deploy frontend to S3 + CloudFront
# 5. Configure Route 53 for domain
```

## 📈 Monitoring & Analytics

### Built-in Metrics
- User activity tracking
- Lead conversion rates
- Response time analytics
- Gamification engagement metrics

### Health Check Endpoints
- `GET /health` - Basic health check
- `GET /api/v1/system/status` - Detailed system status

## 🔐 Security Features

### Authentication Security
- JWT tokens with expiration
- Password strength requirements
- Account lockout after failed attempts
- Session management

### Data Security
- SQL injection prevention
- XSS protection
- CORS configuration
- Input validation and sanitization

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check PostgreSQL service
   sudo systemctl status postgresql
   
   # Check connection string in .env
   ```

2. **Redis Connection Failed**
   ```bash
   # Start Redis service
   redis-server
   
   # Check Redis status
   redis-cli ping
   ```

3. **WebSocket Connection Issues**
   ```bash
   # Check if port 8000 is available
   netstat -tulpn | grep 8000
   ```

4. **Migration Issues**
   ```bash
   # Check if hot_leads.json exists
   ls -la web/data/hot_leads.json
   
   # Run migration with debug
   python migrate_leads_to_crm.py --debug
   ```

## 📞 Support & Maintenance

### Regular Tasks
- Database backups (daily)
- Log rotation
- Performance monitoring
- Security updates

### Backup Strategy
```bash
# Database backup
pg_dump cura_genesis_crm > backup_$(date +%Y%m%d).sql

# Redis backup
redis-cli BGSAVE
```

## 🎯 Next Steps & Enhancements

### Immediate Improvements
1. Email integration (SMTP configuration)
2. Calendar integration (Google Calendar)
3. Phone system integration (Twilio)
4. Advanced reporting dashboards

### Future Enhancements
1. Mobile app development
2. AI-powered lead scoring
3. Advanced analytics and forecasting
4. Integration with existing CRM systems

## 📄 License & Support

This CRM system preserves and enhances your existing lead generation investment while providing a modern, scalable platform for your sales team.

For technical support or customization requests, refer to the documentation or contact your development team.

---

**🎉 Congratulations!** Your Cura Genesis CRM is now ready to supercharge your medical device sales with advanced lead management, gamification, and real-time features while preserving all your valuable lead scoring algorithms! 