#!/usr/bin/env python3
"""
Backend Team Handoff Package Creator
Creates a comprehensive package with all files needed for backend team
"""

import os
import shutil
import json
import zipfile
from datetime import datetime

def create_backend_package():
    """Create a complete package for backend team"""
    
    print("🚀 Creating Backend Team Handoff Package...")
    print("=" * 50)
    
    # Create package directory
    package_dir = "backend_team_handoff"
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Files to include
    files_to_copy = [
        # Documentation
        "BACKEND_TEAM_HANDOFF_COMPLETE.md",
        "BACKEND_INTEGRATION_INSTRUCTIONS.md",
        
        # Core Lambda Files
        "lambda_function.py",
        
        # Lead Data
        "web/data/hot_leads.json",
        "lambda_leads_converted.json",
        
        # Transfer Scripts
        "smart_lead_injection_api.py",
        "automated_lead_manager.py", 
        "production_lead_manager.py",
        "start_automation.sh",
        
        # Configuration
        "requirements.txt",
        "amplify.yml",
        
        # Frontend Files (for reference)
        "aws_deploy/index.html",
        "aws_deploy/login.html",
    ]
    
    print("📁 Copying files to package...")
    copied_files = []
    missing_files = []
    
    for file_path in files_to_copy:
        if os.path.exists(file_path):
            # Create subdirectories if needed
            dest_path = os.path.join(package_dir, file_path)
            dest_dir = os.path.dirname(dest_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            shutil.copy2(file_path, dest_path)
            copied_files.append(file_path)
            print(f"  ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"  ❌ Missing: {file_path}")
    
    # Create summary file
    summary = {
        "package_created": datetime.now().isoformat(),
        "total_files": len(copied_files),
        "files_included": copied_files,
        "missing_files": missing_files,
        "priority_actions": [
            "1. Fix Lambda authentication (POST /api/v1/auth/login)",
            "2. Add POST /api/v1/leads endpoint", 
            "3. Run: python smart_lead_injection_api.py",
            "4. Verify frontend connectivity",
            "5. Deploy automation"
        ],
        "production_lambda": {
            "url": "https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod",
            "function_name": "cura-genesis-crm-api",
            "region": "us-east-1"
        },
        "frontend_url": "https://main.d2q8k9j5m6l3x4.amplifyapp.com",
        "test_credentials": {
            "username": "admin",
            "password": "admin123"
        }
    }
    
    with open(os.path.join(package_dir, "PACKAGE_SUMMARY.json"), 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Create quick start script
    quick_start = """#!/bin/bash
# Backend Team Quick Start Script

echo "🚀 CRM Backend Team Handoff - Quick Start"
echo "========================================"
echo ""
echo "📋 Priority Tasks:"
echo "1. Fix Lambda authentication"
echo "2. Add POST /api/v1/leads endpoint"
echo "3. Test transfer script"
echo ""
echo "🔧 Key Files:"
echo "- BACKEND_TEAM_HANDOFF_COMPLETE.md (START HERE)"
echo "- lambda_function.py (needs fixing)"
echo "- smart_lead_injection_api.py (ready to run)"
echo ""
echo "🧪 Test Lambda:"
echo "curl -X POST https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod/api/v1/auth/login \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\":\"admin\",\"password\":\"admin123\"}'"
echo ""
echo "📞 Status: System is 90% ready - just need Lambda fixes!"
"""
    
    with open(os.path.join(package_dir, "QUICK_START.sh"), 'w') as f:
        f.write(quick_start)
    
    # Make script executable
    os.chmod(os.path.join(package_dir, "QUICK_START.sh"), 0o755)
    
    # Create ZIP file
    zip_filename = f"backend_team_handoff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    print(f"\n📦 Creating ZIP file: {zip_filename}")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arc_path)
    
    print(f"\n✅ Package created successfully!")
    print(f"📁 Directory: {package_dir}/")
    print(f"📦 ZIP file: {zip_filename}")
    print(f"📊 Files included: {len(copied_files)}")
    
    if missing_files:
        print(f"⚠️  Missing files: {len(missing_files)}")
        for missing in missing_files:
            print(f"    - {missing}")
    
    print(f"\n🎯 Next Steps:")
    print(f"1. Send {zip_filename} to backend team")
    print(f"2. They should start with BACKEND_TEAM_HANDOFF_COMPLETE.md")
    print(f"3. Estimated fix time: 2-4 hours")
    
    return package_dir, zip_filename

if __name__ == "__main__":
    create_backend_package() 