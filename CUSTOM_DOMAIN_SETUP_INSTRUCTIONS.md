# VantagePoint CRM - Custom Domain Setup Instructions

## 🎯 OBJECTIVE
Set up **api.vantagepointcrm.com** as the custom domain for the VantagePoint CRM backend API.

---

## ✅ FRONTEND CONFIGURATION UPDATED

### **📋 Files Updated (11 total):**
- `web/config.js`
- `aws_deploy/index.html`
- `aws_deploy/index_simple.html` 
- `aws_deploy/login.html`
- `aws_deploy/debug_send_docs.html`
- `backend_team_handoff/aws_deploy/index.html`
- `backend_team_handoff/aws_deploy/login.html`
- `backend_team_handoff/PACKAGE_SUMMARY.json`
- `crm_enhanced_dashboard_v2.html`
- `crm_production_dashboard.html`
- `debug_send_docs.html`

### **🔄 URL Change:**
- **OLD**: `https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod`
- **NEW**: `https://api.vantagepointcrm.com`

---

## 🛠 AWS INFRASTRUCTURE SETUP REQUIRED

### **Step 1: Request SSL Certificate**
```bash
aws acm request-certificate \
    --domain-name api.vantagepointcrm.com \
    --subject-alternative-names vantagepointcrm.com *.vantagepointcrm.com \
    --validation-method DNS \
    --region us-east-1
```

### **Step 2: Validate Certificate**
1. Go to AWS Certificate Manager (ACM) console
2. Find the pending certificate for `api.vantagepointcrm.com`
3. Click "Create records in Route 53" (since you have a hosted zone)
4. Wait for validation to complete (5-10 minutes)

### **Step 3: Create Custom Domain in API Gateway**
```bash
aws apigateway create-domain-name \
    --domain-name api.vantagepointcrm.com \
    --certificate-arn arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT-ID \
    --endpoint-configuration types=EDGE \
    --region us-east-1
```

### **Step 4: Create Base Path Mapping**
```bash
aws apigateway create-base-path-mapping \
    --domain-name api.vantagepointcrm.com \
    --rest-api-id blyqk7itsc \
    --stage prod \
    --region us-east-1
```

### **Step 5: Get CloudFront Distribution Domain**
```bash
aws apigateway get-domain-name \
    --domain-name api.vantagepointcrm.com \
    --region us-east-1
```
**Note the `distributionDomainName` value for DNS setup.**

---

## 📝 DNS RECORDS FOR ROUTE 53

### **Required CNAME Record:**
```
Name: api.vantagepointcrm.com
Type: CNAME  
Value: [CloudFront Distribution Domain from Step 5]
TTL: 300
```

### **Example:**
```
Name: api.vantagepointcrm.com
Type: CNAME
Value: d1a2b3c4d5e6f7.cloudfront.net
TTL: 300
```

---

## 🧪 TESTING THE SETUP

### **1. Test SSL Certificate:**
```bash
curl -I https://api.vantagepointcrm.com/health
```

### **2. Test API Endpoint:**
```bash
curl https://api.vantagepointcrm.com/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "service": "VantagePoint CRM API",
  "leads_count": 20,
  "users_count": 3,
  "version": "2.0.0"
}
```

### **3. Test Authentication:**
```bash
curl -X POST https://api.vantagepointcrm.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

---

## 🚀 FRONTEND DEPLOYMENT

### **After DNS Propagation (15-30 minutes):**

1. **Test locally:**
   ```bash
   cd aws_deploy
   python -m http.server 8000
   # Open http://localhost:8000
   ```

2. **Deploy to AWS Amplify:**
   - Frontend will now use `https://api.vantagepointcrm.com`
   - All API calls will go through the custom domain
   - SSL certificate ensures secure HTTPS communication

3. **Update main domain:**
   - Frontend: `https://vantagepointcrm.com` (Amplify)
   - Backend API: `https://api.vantagepointcrm.com` (Custom Domain)

---

## 🔧 AUTOMATED SETUP SCRIPT

### **Run the automated setup:**
```bash
python setup_custom_domain.py
```

This script will:
1. Request SSL certificate
2. Create custom domain in API Gateway
3. Set up base path mapping
4. Provide DNS record information
5. Verify the setup

---

## 📊 CONFIGURATION VERIFICATION

### **Check Updated Files:**
```bash
# Verify web/config.js
grep "api.vantagepointcrm.com" web/config.js

# Verify aws_deploy files  
grep "api.vantagepointcrm.com" aws_deploy/index.html
```

### **Expected in web/config.js:**
```javascript
const CONFIG = {
    API_BASE_URL: 'https://api.vantagepointcrm.com',
    // ...
};
```

---

## 🎯 FINAL ARCHITECTURE

### **Production URLs:**
- **Frontend**: `https://vantagepointcrm.com` (AWS Amplify)
- **Backend API**: `https://api.vantagepointcrm.com` (Custom Domain → API Gateway → Lambda)

### **API Endpoints:**
- Health: `https://api.vantagepointcrm.com/health`
- Login: `https://api.vantagepointcrm.com/api/v1/auth/login`
- Leads: `https://api.vantagepointcrm.com/api/v1/leads`
- Summary: `https://api.vantagepointcrm.com/api/v1/summary`

---

## ⚠️ IMPORTANT NOTES

1. **DNS Propagation**: Allow 15-30 minutes for DNS changes to propagate globally
2. **Certificate Validation**: Must be completed before custom domain creation
3. **HTTPS Only**: The custom domain will only work with HTTPS (SSL certificate required)
4. **CloudFront Edge**: API Gateway uses CloudFront edge locations for global performance

---

## 🆘 TROUBLESHOOTING

### **Common Issues:**

1. **Certificate Validation Failed:**
   - Check Route 53 records were created correctly
   - Wait for full validation (up to 30 minutes)

2. **DNS Not Resolving:**
   - Verify CNAME record points to correct CloudFront domain
   - Check TTL and wait for propagation

3. **403 Forbidden:**
   - Verify base path mapping is created correctly
   - Check API Gateway deployment status

4. **SSL Errors:**
   - Ensure certificate covers the domain
   - Verify certificate is in us-east-1 region

---

## 🎉 SUCCESS CRITERIA

✅ **Certificate validated in ACM**  
✅ **Custom domain created in API Gateway**  
✅ **CNAME record added to Route 53**  
✅ **API responding at https://api.vantagepointcrm.com/health**  
✅ **Frontend configuration updated**  
✅ **Authentication working with custom domain**

---

**🚀 Once complete, VantagePoint CRM will be fully operational with professional custom domain!** 