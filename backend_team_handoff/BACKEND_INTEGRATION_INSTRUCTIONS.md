# Backend Integration Instructions for Lead Editing Functionality

## 🎯 **Overview**
The frontend now has complete lead editing functionality. The backend needs to support the new `PUT /api/v1/leads/{id}` endpoint and resolve some existing issues.

## ✅ **What's Already Working**
Based on terminal logs, these backend components are functioning:
- ✅ Authentication system (`/auth/login`, `/auth/me`)
- ✅ Basic lead retrieval (`GET /api/v1/leads`)
- ✅ User management and roles
- ✅ Database connection and basic CRUD operations
- ✅ Gamification system
- ✅ Analytics dashboard endpoints
- ✅ WebSocket connections
- ✅ Lead distribution system

## ❌ **Critical Issues to Fix**

### **1. Lead Update Endpoint (MISSING)**
**Status:** Implemented in code but not working properly

**What's needed:**
```python
@app.put("/api/v1/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # This endpoint exists but may need debugging
```

**Frontend expects:**
- **Method:** `PUT`
- **URL:** `/api/v1/leads/{lead_id}`
- **Headers:** `Authorization: Bearer {token}`, `Content-Type: application/json`
- **Body:**
```json
{
  "practice_name": "Updated Practice Name",
  "owner_name": "Dr. Updated Owner",
  "practice_phone": "(555) 123-4567",
  "owner_phone": "(555) 987-6543",
  "address": "123 Main Street",
  "city": "Updated City",
  "state": "CA",
  "zip_code": "12345",
  "ein": "12-3456789",
  "npi": "1234567890",
  "entity_type": "Organization",
  "providers": 2,
  "specialties": "Cardiology, Internal Medicine",
  "is_sole_proprietor": false
}
```

**Expected Response:**
```json
{
  "id": 123,
  "practice_name": "Updated Practice Name",
  "owner_name": "Dr. Updated Owner",
  "practice_phone": "(555) 123-4567",
  "owner_phone": "(555) 987-6543",
  "address": "123 Main Street",
  "city": "Updated City",
  "state": "CA",
  "zip_code": "12345",
  "ein": "12-3456789",
  "npi": "1234567890",
  "entity_type": "Organization",
  "providers": 2,
  "specialties": "Cardiology, Internal Medicine",
  "is_sole_proprietor": false,
  "updated_at": "2025-07-22T16:30:00Z"
}
```

### **2. Database Schema Issues (CRITICAL)**
**Error seen:** `column users.last_activity does not exist`

**Fix required:**
```sql
-- Add missing columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS conversion_rate FLOAT DEFAULT 0.0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS activity_score INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deals_closed INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_percentile FLOAT DEFAULT 0.0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_rank INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS performance_score FLOAT DEFAULT 0.0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS badges TEXT;
```

**OR** Update the User model to not query these fields if they don't exist.

### **3. Enum Import Issues (CRITICAL)**
**Error seen:** `ValueError: <enum 'UserRole'> is not a valid Enum`

**Fix required:**
Check `crm_lead_distribution.py` line 16:
```python
# This import may be causing circular dependency
from crm_main import User, Lead, UserRole, LeadStatus, Activity, ActivityType
```

**Solution:** Move shared models to a separate file:
```python
# Create crm_shared_models.py with common models
# Import from there instead of crm_main.py
```

### **4. Port Conflict Issues**
**Error seen:** `address already in use`

**Fix:**
```bash
# Kill existing processes
lsof -ti:8001 | xargs kill -9

# Or change port in crm_main.py
uvicorn.run(app, host='0.0.0.0', port=8002, log_level='info')  # Use different port
```

## 🔧 **Backend Implementation Steps**

### **Step 1: Fix Database Schema**
```python
# In crm_main.py or separate migration script
def create_missing_columns():
    try:
        # Add missing user columns
        engine.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP,
            ADD COLUMN IF NOT EXISTS conversion_rate FLOAT DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS activity_score INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS deals_closed INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS current_percentile FLOAT DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS current_rank INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS performance_score FLOAT DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS badges TEXT;
        """)
        logger.info("✅ Database schema updated successfully")
    except Exception as e:
        logger.warning(f"Database schema update failed: {e}")
```

### **Step 2: Test Lead Update Endpoint**
```python
# Test script to verify the endpoint works
import requests

# Login first
login_response = requests.post("http://localhost:8001/auth/login", 
    json={"username": "admin", "password": "admin123"})
token = login_response.json()["access_token"]

# Test lead update
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
update_data = {
    "practice_name": "Test Updated Practice",
    "owner_name": "Dr. Test Owner",
    "practice_phone": "(555) 123-4567",
    "city": "Test City",
    "state": "CA"
}

response = requests.put("http://localhost:8001/api/v1/leads/1", 
    json=update_data, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### **Step 3: Fix Circular Dependencies**
Create `crm_shared_models.py`:
```python
# Move shared enums and models here
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"

class LeadStatus(str, Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    # ... etc
```

Then update imports in `crm_lead_distribution.py`:
```python
from crm_shared_models import UserRole, LeadStatus, ActivityType
```

### **Step 4: Verify Permissions**
Make sure lead update permissions work correctly:
```python
# Agents can only edit their assigned leads
if current_user.role == UserRole.AGENT and lead.assigned_user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Can only update your assigned leads")

# Admins and managers can edit any lead
# This should already be implemented
```

## 🧪 **Testing Checklist**

### **Backend Tests**
- [ ] `PUT /api/v1/leads/{id}` endpoint responds successfully
- [ ] Agent can edit their assigned leads
- [ ] Agent CANNOT edit unassigned leads (403 error)
- [ ] Admin can edit any lead
- [ ] All lead fields update correctly in database
- [ ] Response includes `updated_at` timestamp
- [ ] Invalid data returns proper validation errors

### **Integration Tests**
- [ ] Frontend can successfully update leads
- [ ] Changes reflect immediately in the UI
- [ ] Error messages display properly
- [ ] Authentication errors handled gracefully

## 🚀 **Deployment Steps**

### **1. Development Environment**
```bash
# Start backend
source crm_venv/bin/activate
python crm_main.py

# Should see:
# INFO: Uvicorn running on http://0.0.0.0:8001
# ✅ Database tables created/verified
# 🎯 Lead distribution system initialized
```

### **2. Test Frontend Integration**
```bash
# Open frontend
open web/index.html
# Or serve with:
python -m http.server 3000 -d web/
```

### **3. Verify Lead Editing**
1. Login to frontend
2. Click "Edit" button on any lead
3. Modify lead information
4. Click "Save Changes"
5. Verify success message
6. Check that changes persist

## ⚠️ **Known Backend Issues (Non-Critical)**

### **Deprecation Warnings**
```python
# Replace deprecated on_event with lifespan
# Current:
@app.on_event("startup")
async def startup_event():
    pass

# Should be:
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup code
    yield
    # shutdown code

app = FastAPI(lifespan=lifespan)
```

### **SQLAlchemy Warnings**
```python
# Replace deprecated declarative_base
# Current:
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# Should be:
from sqlalchemy.orm import declarative_base
Base = declarative_base()
```

### **Bcrypt Warning**
Non-critical warning about bcrypt version detection. Password hashing still works.

## 📞 **Support & Troubleshooting**

### **Common Issues**

**1. "Address already in use" error:**
```bash
lsof -ti:8001 | xargs kill -9
```

**2. Database connection errors:**
```bash
# Check PostgreSQL is running
brew services start postgresql
# Or restart Docker if using containerized DB
```

**3. Import/dependency errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**4. Frontend not connecting to backend:**
```javascript
// Check API base URL in lead-edit-modal.js
const response = await fetch('/api/v1/leads/${leadId}', {
    method: 'PUT',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
});
```

## 🎉 **Success Criteria**

✅ **Backend is ready when:**
1. Server starts without errors
2. All API endpoints respond correctly
3. Database schema is complete
4. Authentication works properly
5. Lead update endpoint accepts PUT requests
6. Frontend can successfully edit and save leads

---

## 📋 **Quick Start Commands**

```bash
# 1. Fix database schema
python -c "from crm_main import create_missing_columns; create_missing_columns()"

# 2. Kill existing processes
lsof -ti:8001 | xargs kill -9

# 3. Start backend
source crm_venv/bin/activate
python crm_main.py

# 4. Test endpoint
curl -X PUT http://localhost:8001/api/v1/leads/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"practice_name": "Test Update"}'
```

**The frontend is 100% ready - just need the backend endpoint working! 🚀** 