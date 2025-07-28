#!/usr/bin/env python3
"""
VantagePoint CRM - Update Frontend to Custom Domain
Updates all configuration files to use api.vantagepointcrm.com
"""

import os
import sys

def update_frontend_to_custom_domain():
    """Update all frontend files to use custom domain"""
    
    print("🔧 UPDATING FRONTEND TO CUSTOM DOMAIN")
    print("=" * 50)
    
    # URLs to replace
    old_url = "https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod"
    new_url = "https://api.vantagepointcrm.com"
    
    # Files that need updating
    files_to_update = [
        "web/config.js",
        "aws_deploy/index.html",
        "aws_deploy/index_simple.html",
        "aws_deploy/login.html", 
        "aws_deploy/debug_send_docs.html",
        "backend_team_handoff/aws_deploy/index.html",
        "backend_team_handoff/aws_deploy/login.html",
        "backend_team_handoff/PACKAGE_SUMMARY.json",
        "crm_enhanced_dashboard_v2.html",
        "crm_production_dashboard.html",
        "debug_send_docs.html"
    ]
    
    updated_files = []
    missing_files = []
    
    print(f"🔄 Replacing: {old_url}")
    print(f"🎯 With: {new_url}")
    print()
    
    for file_path in files_to_update:
        try:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_url in content:
                updated_content = content.replace(old_url, new_url)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                updated_files.append(file_path)
                print(f"✅ Updated: {file_path}")
            else:
                print(f"ℹ️  No changes needed: {file_path}")
        
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")
    
    print()
    print("=" * 50)
    print("📊 UPDATE SUMMARY")
    print("=" * 50)
    print(f"✅ Files updated: {len(updated_files)}")
    print(f"ℹ️  Files unchanged: {len(files_to_update) - len(updated_files) - len(missing_files)}")
    print(f"⚠️  Files missing: {len(missing_files)}")
    
    if updated_files:
        print("\n✅ UPDATED FILES:")
        for file in updated_files:
            print(f"   • {file}")
    
    if missing_files:
        print("\n⚠️  MISSING FILES:")
        for file in missing_files:
            print(f"   • {file}")
    
    print(f"\n🎯 All frontend configuration now points to: {new_url}")
    
    return len(updated_files)

if __name__ == "__main__":
    print("VantagePoint CRM - Frontend Domain Update")
    print("This will update all frontend files to use api.vantagepointcrm.com")
    print()
    
    updated_count = update_frontend_to_custom_domain()
    
    if updated_count > 0:
        print("\n🚀 NEXT STEPS:")
        print("1. Set up SSL certificate for api.vantagepointcrm.com in AWS ACM")
        print("2. Create custom domain in API Gateway") 
        print("3. Add CNAME record to Route 53 hosted zone")
        print("4. Commit and push these changes")
        print("\nRun: python setup_custom_domain.py for full AWS setup")
    else:
        print("\n⚠️  No files were updated. Check if the old URL still exists.") 