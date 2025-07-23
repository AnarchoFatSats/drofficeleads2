# 🚀 **CURA GENESIS CRM - PRODUCTION BACKEND GUIDE**

## ✅ **PRODUCTION CODE STATUS**

**✅ SYNTAX CLEAN** - All code compiles without errors  
**✅ MODELS COMPLETE** - Database models are production-ready  
**✅ API ENDPOINTS** - Full CRUD operations implemented  
**✅ ROLE-BASED ACCESS** - Security properly implemented  
**✅ NEW FEATURE** - Lead creation API added  

---

## 🔧 **BACKEND SETUP INSTRUCTIONS**

### **1. Environment Setup**
```bash
# Navigate to project directory
cd /Users/alexsiegel/Downloads/NPPES_Data_Dissemination_July_2025_V2

# Activate virtual environment
source crm_venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt
```

### **2. Database Setup**
```bash
# Ensure PostgreSQL is running
brew services start postgresql@14

# Create database (if not exists)
createdb cura_genesis_crm

# Run migrations/setup
python migrate_leads_to_crm.py
```

### **3. Start Backend Server**
```bash
# Start CRM backend
python crm_main.py

# Server will run on: http://localhost:8001
```

---

## 🌐 **NEW API ENDPOINTS FOR LEAD MANAGEMENT**

### **Create Single Lead**
```bash
POST /api/v1/leads
Authorization: Bearer <token>
Content-Type: application/json

{
  "practice_name": "Downtown Medical Center",
  "owner_name": "Dr. John Smith",
  "practice_phone": "(555) 123-4567",
  "specialties": "Cardiology, Interventional Cardiology",
  "city": "New York",
  "state": "NY",
  "zip_code": "10001",
  "npi": "1234567890",
  "ein": "12-3456789",
  "estimated_deal_value": 250000
}
```

### **Bulk Import Leads (Admin/Manager Only)**
```bash
POST /api/v1/leads/bulk
Authorization: Bearer <token>
Content-Type: application/json

[
  {
    "practice_name": "North Medical Group",
    "owner_name": "Dr. Sarah Johnson",
    "specialties": "Nephrology",
    "city": "Boston",
    "state": "MA"
  },
  {
    "practice_name": "West Coast Cardiology",
    "owner_name": "Dr. Mike Chen",
    "specialties": "Cardiology",
    "city": "Los Angeles", 
    "state": "CA"
  }
]
```

### **Get Leads (Role-Based)**
```bash
# Agents see only their assigned leads
GET /api/v1/leads
Authorization: Bearer <agent_token>

# Admins see all leads
GET /api/v1/leads?show_all=true
Authorization: Bearer <admin_token>
```

---

## 🔐 **AUTHENTICATION & ACCESS**

### **Login**
```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

### **Default Accounts**
- **Admin**: `admin` / `admin123` (Full system access)
- **Agent**: `agent1` / `admin123` (Limited to assigned leads)
- **Manager**: `manager` / `admin123` (Team oversight)

---

## 📊 **MONITORING & HEALTH CHECKS**

### **Health Check Endpoint**
```bash
GET /health

# Returns comprehensive system status:
{
  "status": "healthy",
  "timestamp": "2025-07-22T22:30:45.123456",
  "version": "1.0.0",
  "database": "connected",
  "database_stats": {
    "total_leads": 150,
    "total_users": 8,
    "active_agents": 5
  },
  "redis": "connected",
  "lead_scoring": "active",
  "lead_distribution": "active",
  "distribution_stats": {
    "total_leads": 150,
    "assigned_leads": 100,
    "available_leads": 50,
    "active_agents": 5,
    "distribution_health": "Good"
  },
  "features": {
    "lead_creation_api": true,
    "bulk_import": true,
    "role_based_access": true,
    "gamification": true,
    "auto_recycling": true,
    "real_time_updates": true
  }
}
```

---

## 🎯 **LEAD DISTRIBUTION SYSTEM**

### **How It Works**
1. **Agent Capacity**: Each agent gets exactly 20 leads
2. **Auto-Assignment**: New leads automatically distributed
3. **24-Hour Rule**: Inactive leads recycled after 24 hours
4. **7-Day Max**: Forced recycling after 7 days
5. **Disposition Tracking**: All status changes monitored

### **Distribution API**
```bash
# Force redistribution (Admin only)
POST /api/v1/distribution/redistribute
Authorization: Bearer <admin_token>

# Check distribution stats
GET /api/v1/distribution/stats
Authorization: Bearer <token>

# Trigger recycling check
POST /api/v1/distribution/recycle-check
Authorization: Bearer <admin_token>
```

---

## 🎮 **GAMIFICATION SYSTEM**

### **Point Values**
- **Call Connected**: 15 points
- **Lead Qualified**: 30 points  
- **Demo Scheduled**: 50 points
- **Deal Closed**: 200 points

### **Leaderboard API**
```bash
GET /api/v1/gamification/leaderboard
Authorization: Bearer <token>

# Returns top performers with scores
```

---

## 🔧 **PRODUCTION DEPLOYMENT**

### **Environment Variables**
```bash
# Required for production
DATABASE_URL=postgresql://user:pass@host:port/dbname
SECRET_KEY=your-super-secret-production-key
REDIS_URL=redis://host:port/db
DEBUG=false
```

### **Security Considerations**
1. **Change default passwords** before production
2. **Update SECRET_KEY** with strong random value
3. **Configure CORS** for your domain only
4. **Set up SSL/TLS** for all API endpoints
5. **Enable rate limiting** for API endpoints

### **Monitoring Setup**
```bash
# Add to your monitoring system
GET /health

# Monitor these endpoints:
- Database connectivity
- Redis status
- Lead distribution health
- Active agent count
```

---

## 🚀 **WHAT'S READY FOR PRODUCTION**

✅ **Complete Lead Management**
- ✅ Create leads via API
- ✅ Bulk import (up to 1000 leads)
- ✅ Automatic lead distribution
- ✅ Role-based access control
- ✅ Lead recycling system

✅ **User Management**
- ✅ JWT authentication
- ✅ Role-based permissions (Admin/Manager/Agent)
- ✅ Secure password hashing

✅ **Activity Tracking**
- ✅ All agent interactions logged
- ✅ Timestamps on every action
- ✅ Contact attempt counting
- ✅ Disposition tracking

✅ **Gamification**
- ✅ Point system for activities
- ✅ Real-time leaderboards
- ✅ Performance-based competition

✅ **Analytics & Reporting**
- ✅ Conversion rate tracking
- ✅ Agent performance metrics
- ✅ System health monitoring

✅ **Real-Time Features**
- ✅ WebSocket notifications
- ✅ Live lead distribution
- ✅ Instant point updates

---

## 📞 **NEXT STEPS**

1. **Test API Endpoints** - Use the examples above
2. **Configure Production Settings** - Update environment variables
3. **Set Up Monitoring** - Use the `/health` endpoint
4. **Deploy to Production** - Use your preferred hosting platform
5. **Train Your Team** - Show agents the competition features

Your CRM is **production-ready** with comprehensive lead management, role-based access, and competitive gamification! 🚀 