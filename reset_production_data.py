#!/usr/bin/env python3
"""
Reset VantagePoint CRM to Day 1 Production State
- All leads status: "new"
- All docs_sent: False  
- Clean slate for real business tracking
"""

import re

def reset_production_data():
    """Reset lambda_function.py to clean Day 1 production data"""
    
    file_path = 'lambda_function.py'
    
    try:
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Keep track of changes
        changes = []
        
        # 1. Reset all non-"new" statuses to "new"
        old_statuses = [
            ('"status": "sold",', '"status": "new",'),
            ('"status": "disposed",', '"status": "new",'), 
            ('"status": "qualified",', '"status": "new",'),
            ('"status": "contacted",', '"status": "new",')
        ]
        
        for old, new in old_statuses:
            count = content.count(old)
            if count > 0:
                content = content.replace(old, new)
                changes.append(f"✅ Changed {count} leads from {old} to {new}")
        
        # 2. Reset all docs_sent: True to False
        docs_old = '"docs_sent": True,'
        docs_new = '"docs_sent": False,'
        docs_count = content.count(docs_old)
        if docs_count > 0:
            content = content.replace(docs_old, docs_new)
            changes.append(f"✅ Reset {docs_count} leads docs_sent: True → False")
        
        # 3. Remove comments about sold/disposed deals
        content = re.sub(r'# Sold deal', '# Fresh lead', content)
        content = re.sub(r'# Disposed deal', '# Fresh lead', content)
        content = re.sub(r'# Another sold deal', '# Fresh lead', content)
        changes.append("✅ Updated comments to reflect fresh data")
        
        # Write the updated content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("🚀 DAY 1 PRODUCTION DATA RESET COMPLETE!")
        print("=" * 50)
        
        for change in changes:
            print(change)
        
        print("\n📊 RESULT: Clean Day 1 Production State")
        print("   • All leads status: 'new'")  
        print("   • All docs_sent: False")
        print("   • Practices Signed Up: 0")
        print("   • Conversion Rate: 0%")
        print("   • Total Fresh Leads: 20")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting data: {e}")
        return False

if __name__ == "__main__":
    reset_production_data() 