# Rural Physician Leads Finder

A comprehensive data analysis platform to identify small, independent rural physician groups for targeted outreach. Built with Python data processing and a modern web dashboard for easy access.

## 🎯 Project Overview

This project analyzes NPPES (National Plan and Provider Enumeration System) data combined with rural classification (RUCA), health demographics (PLACES), and Medicare enrollment data to identify high-value physician prospects in rural areas.

### Target Criteria
- **Group Size**: 1-5 clinicians
- **Ownership**: Independent (not hospital/health system affiliated)
- **Location**: Rural ZIP codes (RUCA codes 4-10)
- **Specialties**: Podiatry, Wound Care, Mohs Surgery, Primary Care

### Key Results
- **33,442 total qualifying physician groups**
- **$403M+ estimated market opportunity**
- **4,955 rural ZIP codes covered**
- **100% contact rate** with phone numbers

---

## 📊 Deliverables

### 1. **CRM-Ready Excel Export**
- `rural_physician_leads_crm.xlsx` - Multi-tab workbook with:
  - Complete lead database with scoring
  - Hot prospects (A+/A priority)
  - Specialty-specific sheets
  - Geographic territory breakdown
  - Executive dashboard

### 2. **Web Dashboard**
- Live, interactive web application
- Real-time filtering and search
- Lead scoring and prioritization
- Mobile-responsive design
- **Perfect for AWS Amplify deployment**

### 3. **Analysis Reports**
- Comprehensive market breakdown
- Revenue opportunity analysis
- Geographic coverage reports

---

## 🚀 Quick Start

### Option 1: View Web Dashboard
1. **Deploy to AWS Amplify** (see deployment instructions below)
2. **Or run locally:**
   ```bash
   cd web
   python -m http.server 8000
   # Open http://localhost:8000
   ```

### Option 2: Run Analysis
```bash
# Install dependencies
pip install -r requirements.txt

# Run full analysis (requires NPPES data)
python comprehensive_rural_physician_finder.py

# Create CRM export
python create_crm_export.py

# Generate web data
python create_web_export.py
```

---

## 🌐 AWS Amplify Deployment

### Step 1: Prepare Repository
```bash
# Clone this repository
git clone <your-repo-url>
cd rural-physician-leads

# Ensure web data is generated
python create_web_export.py
```

### Step 2: Deploy to Amplify

#### Method A: GitHub Integration (Recommended)
1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit - Rural Physician Leads"
   git push origin main
   ```

2. **Connect to Amplify:**
   - Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
   - Click "Get Started" under "Host your web app"
   - Connect your GitHub repository
   - Select this repository and `main` branch

3. **Configure Build:**
   - **Build output directory:** `web`
   - Amplify will auto-detect the static site

#### Method B: Direct Upload
1. **Zip the web directory:**
   ```bash
   cd web
   zip -r ../amplify-deploy.zip .
   ```

2. **Upload to Amplify:**
   - Go to AWS Amplify Console
   - Choose "Deploy without Git provider"
   - Upload the `amplify-deploy.zip` file

### Step 3: Configure Custom Domain (Optional)
- In Amplify Console, go to "Domain management"
- Add your custom domain
- Amplify will handle SSL certificates automatically

### Step 4: Environment Variables (If needed)
If you plan to add backend features:
```bash
# In Amplify Console, go to Environment variables
DATA_UPDATE_FREQUENCY=monthly
API_ENDPOINT=your-api-endpoint
```

---

## 📁 Project Structure

```
rural-physician-leads/
├── web/                              # Web application (Amplify ready)
│   ├── index.html                   # Main dashboard
│   ├── styles.css                   # Modern responsive CSS
│   ├── script.js                    # JavaScript functionality
│   └── data/                        # JSON data files
│       ├── hot_leads.json          # Priority prospects
│       ├── summary.json            # Dashboard metrics
│       └── regions.json            # Geographic data
├── comprehensive_rural_physician_finder.py  # Main analysis engine
├── create_crm_export.py             # CRM Excel generator
├── create_web_export.py             # Web data generator
├── requirements.txt                 # Python dependencies
├── analysis_summary.txt             # Results summary
└── README.md                        # This file
```

---

## 🔧 Technical Details

### Data Sources
- **NPPES**: Provider directory and specialty information
- **RUCA**: Rural-Urban Commuting Area codes
- **PLACES**: ZIP code level health demographics
- **Medicare**: Beneficiary enrollment by county

### Analysis Pipeline
1. **Data Loading**: Process 21 NPPES chunks (33M+ providers)
2. **Rural Filtering**: Apply RUCA codes 4-10
3. **Specialty Matching**: Target taxonomy codes
4. **Group Identification**: Cluster by organization/address/EIN
5. **Independence Filtering**: Remove hospital affiliations
6. **Lead Scoring**: Priority-based scoring algorithm
7. **Export Generation**: Multiple output formats

### Web Application Features
- **Real-time filtering** by priority, specialty, location
- **Advanced search** across all fields
- **Lead scoring** with visual indicators
- **Contact actions** (click-to-call, copy info)
- **CSV export** of filtered results
- **Responsive design** for mobile/tablet/desktop

---

## 🎯 High-Priority Prospects

### Immediate Action Items
1. **6 Podiatrist + Wound Care groups** - Call today!
2. **11 Multi-specialty Podiatrist groups** - This week
3. **9 Multi-specialty Wound Care groups** - High priority
4. **78 Mohs Surgery specialists** - Rare opportunity

### Lead Scoring System
- **A+ Priority (90-100)**: Podiatrist + Wound Care combinations
- **A Priority (70-89)**: Multi-specialty high-value groups  
- **B Priority (50-69)**: Targeted specialty groups
- **C Priority (30-49)**: Standard prospects

---

## 📈 Market Opportunity

| Tier | Groups | Est. Revenue | Focus |
|------|--------|-------------|-------|
| High-Value | 17 | $765K | Podiatrist + Multi-specialty |
| Medium-Value | 87 | $2.2M | Wound Care + Mohs Surgery |
| Standard | 33,338 | $400M | Primary Care + Singles |
| **TOTAL** | **33,442** | **$403M** | **Complete Market** |

---

## 🔄 Updates and Maintenance

### Data Refresh (Quarterly)
```bash
# Download new NPPES data
# Update RUCA/PLACES data if available
python comprehensive_rural_physician_finder.py
python create_web_export.py

# Commit and push updates
git add web/data/
git commit -m "Data update - Q1 2025"
git push origin main
# Amplify will auto-deploy
```

### Add New Features
The web application is designed for easy enhancement:
- Add new filters in `script.js`
- Extend lead scoring in `create_web_export.py`
- Add visualizations with Chart.js or D3
- Integrate with CRM APIs

---

## 🛠️ Development

### Local Development
```bash
# Install Python dependencies
pip install pandas numpy openpyxl

# Run analysis
python comprehensive_rural_physician_finder.py

# Generate web data
python create_web_export.py

# Start local server
cd web
python -m http.server 8000
```

### Adding New Data Sources
1. Update `comprehensive_rural_physician_finder.py`
2. Modify `create_web_export.py` for web formatting
3. Update dashboard in `script.js`

---

## 📞 Support

For questions about deployment or customization:
- Check AWS Amplify documentation
- Review the analysis pipeline code
- Examine web application structure

---

## 📄 License

This project is for internal business use. All healthcare data is public domain from CMS/NPPES sources.

---

**🚀 Ready to deploy! Your rural physician leads dashboard is Amplify-ready and optimized for immediate outreach campaigns.** 