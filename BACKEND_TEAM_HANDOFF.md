# Backend Team Handoff - Cura Genesis CRM

## 🚨 URGENT PRODUCTION ISSUES

### **Lambda Backend (Production)**
- **URL**: `https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod`
- **Status**: ❌ Returning 500 "Internal server error"
- **Issue**: Pydantic validation errors with `previous_agents` field
- **Files**: `lambda_crm_with_email_field.py`, `lambda_crm_send_docs_fixed.py`
- **Function**: `cura-genesis-crm-api` (AWS Lambda)

### **AWS ECS Deployment**
- **Status**: ❌ Failed after 6+ hours
- **Issue**: CloudFormation timeout/failure
- **Files**: `aws-ecs-deployment.yml`, `deploy_to_aws.sh`
- **Stack**: `cura-genesis-crm` (us-east-1)

### **Local Backend**
- **Status**: ❌ Database connection issues
- **Issue**: PostgreSQL timeout, Pydantic schema errors
- **File**: `crm_main.py`
- **Error**: `psycopg2.OperationalError: server closed connection`

## 🎯 REQUIREMENTS

### **Core CRM Features Needed**
1. **User Management**: Admin/Manager/Agent roles
2. **Lead Management**: 101 leads, 20 per agent distribution
3. **Lead Operations**: Status updates, notes, assignment
4. **Email Integration**: PTAN/EIN fields, "Send Docs" API
5. **Remote Access**: Agents work from anywhere (not local)

### **API Endpoints Required**
```
✅ POST /api/v1/auth/login
✅ GET /api/v1/auth/me
❌ GET /api/v1/leads (500 error)
❌ PUT /api/v1/leads/{id} (500 error)
❌ POST /api/v1/leads/{id}/notes
❌ POST /api/v1/leads/{id}/send-docs
❌ POST /api/v1/team/create-user
```

## 🔧 SPECIFIC FIXES NEEDED

### **1. Pydantic Schema Fix**
**File**: Lambda functions
**Error**: 
```
{'type': 'list_type', 'loc': ('response', X, 'previous_agents'), 'msg': 'Input should be a valid list', 'input': '[]'}
```
**Fix**: Convert string `'[]'` to actual list `[]` in database or Pydantic model

### **2. Database Schema**
**Issue**: `previous_agents` field type mismatch
**Current**: String `'[]'` 
**Needed**: JSON/List type
**Migration**: Convert existing data from string to JSON

### **3. Lambda Deployment**
**Current Package**: `lambda_working_crm.zip`
**Status**: Deployed but returning 500
**Need**: Debug Lambda logs, fix validation errors

### **4. ECS Alternative**
**If Lambda can't be fixed**: Deploy full FastAPI app to ECS
**Files**: `crm_main.py`, `docker-compose.yml`, `aws-ecs-deployment.yml`
**Status**: CloudFormation deployment failed

## 📁 KEY FILES

### **Backend Code**
- `crm_main.py` - Full FastAPI application
- `lambda_crm_with_email_field.py` - Current Lambda version
- `lambda_crm_send_docs_fixed.py` - Alternative Lambda

### **Database**
- **PostgreSQL**: `cura-genesis-crm-db.c6ds4c4qok1n.us-east-1.rds.amazonaws.com`
- **Database**: `cura_genesis_crm`
- **Leads**: 101 high-scoring leads in database
- **Schema Issue**: `previous_agents` field type

### **Frontend (Ready)**
- `aws_deploy/index.html` - Simplified frontend
- `aws_deploy/login.html` - Login page
- **Deployed**: AWS Amplify
- **Status**: ✅ Ready, waiting for working backend

### **Deployment**
- `aws-ecs-deployment.yml` - ECS CloudFormation
- `deploy_to_aws.sh` - Deployment script
- `amplify.yml` - Frontend deployment config

## 🎯 SUCCESS CRITERIA

### **MVP Requirements**
1. **Production backend** accessible remotely (not localhost)
2. **Agent login** with 20 leads assigned per agent
3. **Lead editing** with email, PTAN, EIN fields
4. **Send Docs** integration working
5. **Admin user creation** for team management

### **Technical Requirements**
- **No local dependencies** - pure cloud solution
- **Database persistence** - leads survive restarts
- **Auto-scaling** - handle multiple agents
- **Security** - JWT auth, role-based permissions

## 🚀 RECOMMENDED APPROACH

### **Option A: Fix Lambda** (Fastest)
1. Debug Pydantic validation in Lambda logs
2. Fix `previous_agents` schema conversion
3. Deploy working Lambda version

### **Option B: ECS Deployment** (Most Robust)
1. Fix CloudFormation template issues
2. Deploy full FastAPI app to ECS
3. Configure load balancer for remote access

### **Option C: Alternative Cloud** (Backup)
- Deploy to Heroku, DigitalOcean, or other platform
- Use managed database service
- Skip AWS complexity

## 📞 IMMEDIATE ACTIONS

1. **Assign backend engineer** to debug Lambda 500 errors
2. **Check AWS logs** for specific error details
3. **Test database schema** fixes for `previous_agents`
4. **Provide timeline** for production deployment

---

**Current Status**: Both Lambda and ECS deployments failed. Frontend ready. Database has data. Need backend engineering expertise to resolve infrastructure issues.

**Priority**: HIGH - Agents need remote access ASAP 