# 🤖 Automated Lead Replenishment System

## **OVERVIEW**

Your CRM now has intelligent, automated lead replenishment that monitors lead levels and automatically uploads new leads when inventory runs low. No more manual lead management!

---

## **🎯 HOW IT WORKS**

### **Smart Monitoring**
- **Real-time Analysis:** Continuously monitors total leads and priority distribution
- **Performance Tracking:** Analyzes conversion rates by priority (A+, A, B)
- **Intelligent Triggers:** Automatically detects when lead levels fall below thresholds

### **Strategic Upload Planning**
- **Priority-Based:** Focuses on A+ leads when conversion rates are high
- **Balanced Distribution:** Maintains optimal mix of lead priorities
- **Performance Adaptive:** Adjusts strategy based on team performance

### **Safety & Control**
- **Duplicate Protection:** Never creates duplicate leads
- **Rate Limiting:** Respects daily upload limits and timing constraints
- **Source Tracking:** Remembers which leads have been uploaded

---

## **⚙️ CONFIGURATION**

### **Default Thresholds** (`automation_config.json`)
```json
{
  "lead_inventory_thresholds": {
    "min_total_leads": 50,      // Trigger replenishment
    "target_total_leads": 150,  // Target inventory level
    "min_priority_leads": {
      "A+": 10,  // Minimum A+ leads
      "A": 30,   // Minimum A leads  
      "B": 20    // Minimum B leads
    }
  },
  
  "upload_controls": {
    "max_upload_per_run": 100,        // Safety limit per cycle
    "max_daily_uploads": 500,         // Daily upload limit
    "min_time_between_uploads_hours": 1  // Cooldown period
  }
}
```

### **Demo Configuration** (`demo_automation_config.json`)
- **Higher thresholds** to trigger uploads for demonstration
- **Faster cycles** for testing (1-minute intervals)
- **Smaller batches** for controlled testing

---

## **🚀 USAGE**

### **Single Check**
```bash
source crm_venv/bin/activate
python automated_lead_manager.py --mode once
```

### **Continuous Monitoring** (Recommended for Production)
```bash
source crm_venv/bin/activate
python automated_lead_manager.py --mode continuous --interval 30
```

### **Easy Startup Script**
```bash
./start_automation.sh
```
- Checks CRM backend status
- Starts continuous monitoring
- Shows real-time logs
- Handles graceful shutdown

### **Custom Configuration**
```bash
python automated_lead_manager.py --mode continuous --config your_config.json
```

---

## **📊 WHAT YOU'LL SEE**

### **Sample Output**
```
🔄 Starting automated lead management cycle
📊 Current metrics: 101 total, 101 available
🎯 Upload strategy: ['Total leads (101) below minimum (120)']
📈 Targets: {'A+': 10, 'A': 25, 'B': 15}
📁 Found 100 available leads
🎯 Selected 50 leads for automated upload
✅ Authentication successful
🎉 Automated upload complete: 45 leads uploaded, 5 duplicates, 0 errors
```

### **When No Action Needed**
```
📊 Current metrics: 156 total, 143 available
✅ Lead levels sufficient, no upload needed
```

---

## **🎛️ INTELLIGENT FEATURES**

### **Performance-Based Adjustments**
- **High Conversion Teams:** Gets more A+ leads automatically
- **Learning Teams:** Gets balanced A/B mix for skill building
- **Adaptive Strategy:** Changes based on 30-day performance data

### **Business Rules**
- **Agent Overload Protection:** Won't flood agents with too many leads
- **Business Hours Respect:** Optional timing controls
- **Source Management:** Tracks multiple lead source files

### **Safety Controls**
- **Duplicate Detection:** Never creates duplicate records
- **Rate Limiting:** Prevents system overload
- **Error Recovery:** Continues working despite temporary issues
- **Audit Trail:** Complete logging of all actions

---

## **🔧 TECHNICAL DETAILS**

### **System Requirements**
- CRM backend running (any port 8001-8006)
- PostgreSQL database connectivity
- `web/data/hot_leads.json` source file
- Python virtual environment activated

### **Database Integration**
- Direct PostgreSQL access for metrics
- CRM API for lead uploads (safer, more reliable)
- Real-time performance analysis
- Conversion rate tracking

### **File Management**
- **Source Files:** `web/data/hot_leads.json` (expandable)
- **Tracking:** `uploaded_leads_tracking.json` (auto-created)
- **Logs:** `automated_lead_manager.log` (detailed activity)
- **Config:** JSON-based configuration files

---

## **📈 MONITORING & ALERTS**

### **Log Files**
- **Real-time Activity:** `automated_lead_manager.log`
- **CRM Backend Logs:** Standard CRM logging
- **Upload History:** JSON tracking file

### **Health Checks**
- Backend connectivity verification
- Database connection monitoring
- Lead source file validation
- Performance metrics collection

---

## **🎯 LEAD REPLENISHMENT STRATEGY**

### **When Automation Triggers**
1. **Total leads** drop below minimum threshold
2. **Priority-specific** counts fall below minimums
3. **Performance metrics** suggest need for specific priorities

### **What Gets Uploaded**
1. **Priority Selection:** A+, A, B leads based on current needs
2. **Score-Based Ranking:** Highest scoring leads first
3. **Duplicate Avoidance:** Only new leads from source files
4. **Batch Processing:** Efficient bulk uploads

### **Smart Distribution**
- **Default Mix:** 20% A+, 50% A, 30% B
- **High Performers:** Bonus A+ leads for proven converters
- **New Teams:** More A/B mix for training
- **Load Balancing:** Considers current agent workload

---

## **🚨 TROUBLESHOOTING**

### **Common Issues**

**"No new leads available for upload"**
- All leads in source files already uploaded
- Add more source files to configuration
- Generate new lead extractions

**"Authentication failed"**
- CRM backend not running on expected port
- Database connectivity issues
- Check backend logs for details

**"Upload blocked: Must wait X minutes"**
- Safety cooldown period active
- Adjust `min_time_between_uploads_hours` if needed
- Wait for cooldown or restart with fresh tracking

**"Daily upload limit reached"**
- Configured daily limit hit
- Increase `max_daily_uploads` if appropriate
- Resets at midnight

---

## **🎉 SUCCESS METRICS**

### **What Success Looks Like**
- ✅ Lead inventory stays above minimum thresholds
- ✅ Agents always have fresh, high-quality leads
- ✅ No manual lead management required
- ✅ Performance-optimized lead distribution
- ✅ Zero duplicate records created

### **Expected Behavior**
- **Quiet Operation:** Most of the time, no action needed
- **Smart Triggers:** Only uploads when actually needed
- **Efficient Batching:** Bulk operations for performance
- **Error Recovery:** Continues working despite minor issues

---

## **🔮 FUTURE ENHANCEMENTS**

### **Planned Features**
- **Email Alerts:** Notify managers of low lead levels
- **Slack Integration:** Real-time notifications
- **Advanced Analytics:** Predictive lead demand
- **Multi-Source Management:** Automatic source file rotation
- **Geographic Balancing:** Ensure regional lead distribution

### **Configuration Expansions**
- **Business Hours Enforcement**
- **Holiday Awareness**  
- **Team-Specific Strategies**
- **Client Segment Targeting**

---

## **📞 SUPPORT**

The automated lead replenishment system is designed to be **"set it and forget it"**. Once configured and started, it monitors your CRM continuously and ensures agents never run out of high-quality leads.

**For Questions:**
- Check logs: `automated_lead_manager.log`
- Test single cycle: `--mode once`
- Verify backend: `curl localhost:8006/health`
- Review configuration: `automation_config.json`

**Your lead management is now FULLY AUTOMATED! 🚀** 