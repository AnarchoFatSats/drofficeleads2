# Frontend Requirements: Agent Lead Creation

## 🎯 **Current Issue**
**Agents CANNOT create new leads** - only view and edit existing ones.

## 📊 **Current Frontend Capabilities**
✅ **Working Functions:**
- View leads in comprehensive table
- Edit existing leads (full modal interface)
- Filter and search leads 
- Add notes and dispositions
- Export lead data to CSV

❌ **Missing Function:**
- **Create/Add new leads** - NO interface exists

## 🔧 **Required Frontend Changes**

### **1. Add "Create Lead" Button**
**Location:** Near the export buttons in `web/index.html`
```html
<button class="btn-create" onclick="openCreateLeadModal()">
    <i class="fas fa-plus"></i> Create New Lead
</button>
```

### **2. Create Lead Modal Interface**
**New functionality needed in existing files:**

**`web/lead-edit-modal.js`:**
- Add `createNewLead()` method to existing `LeadEditModal` class
- Modify existing modal to work for both edit and create modes
- Clear validation to handle empty forms for new leads

**`web/script.js`:**
- Add `openCreateLeadModal()` function
- Add API call to `POST /api/v1/leads` endpoint
- Handle success/error responses for lead creation

### **3. API Integration Required**
**Frontend needs to call:**
```javascript
POST /api/v1/leads
Headers: {
    'Authorization': 'Bearer {token}',
    'Content-Type': 'application/json'
}
Body: {
    "company_name": "Practice Name",
    "contact_name": "Dr. Name", 
    "phone": "555-1234",
    "email": "email@example.com",
    "specialty": "Cardiology",
    "location": "City, State"
}
```

## 🚨 **Backend Requirements** 
**⚠️ BACKEND TEAM NEEDED:**

### **Missing Backend Endpoint:**
- **`POST /api/v1/leads`** - Does not exist or not working
- Last test showed "Internal server error" on authentication

### **Backend Tasks:**
1. ✅ **Fix authentication** - Currently returning 500 errors  
2. ❌ **Add/Fix POST /api/v1/leads endpoint**
3. ❌ **Test endpoint with valid JWT token**
4. ❌ **Ensure agents have permission to create leads**

## 📋 **Implementation Priority**
1. **FIRST:** Backend team fixes POST endpoint
2. **SECOND:** Frontend team adds Create Lead button & modal
3. **THIRD:** Test end-to-end functionality

## ✅ **Success Criteria**
- Agent clicks "Create New Lead" button
- Modal opens with empty form
- Agent fills in lead details
- Lead saves successfully to backend
- New lead appears in leads table
- Agent can immediately edit the new lead

---
**Status:** Waiting for backend team to fix POST /api/v1/leads endpoint 