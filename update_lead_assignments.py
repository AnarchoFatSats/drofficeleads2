#!/usr/bin/env python3
"""
🎯 Update Lead Assignments in Lambda Function
Assign first 20 leads to agent1 (user_id: 3), leave 2 unassigned
"""

import re

def update_lead_assignments():
    """Update the Lambda function to assign leads properly"""
    
    print("🎯 UPDATING LEAD ASSIGNMENTS IN LAMBDA FUNCTION")
    print("=" * 60)
    print("📋 Assigning first 20 leads to Agent1 (user_id: 3)")
    print("🆕 Leaving leads 21-22 unassigned for new agents")
    print("")
    
    # Read the current lambda function
    with open('lambda_package/lambda_function.py', 'r') as f:
        content = f.read()
    
    # Pattern to find lead assignments
    # We'll replace "assigned_user_id": None with "assigned_user_id": 3 for the first 20 leads
    
    lead_id = 1
    updated_count = 0
    
    # Find each lead block and update the assigned_user_id
    lines = content.split('\n')
    in_leads_section = False
    current_lead_id = None
    
    for i, line in enumerate(lines):
        # Check if we're in the LEADS array
        if 'LEADS = [' in line:
            in_leads_section = True
            continue
        
        # Check for end of LEADS array
        if in_leads_section and line.strip() == ']':
            in_leads_section = False
            continue
        
        # If we're in the leads section, look for lead IDs
        if in_leads_section and '"id":' in line:
            # Extract the lead ID
            id_match = re.search(r'"id":\s*(\d+)', line)
            if id_match:
                current_lead_id = int(id_match.group(1))
        
        # Update assigned_user_id for first 20 leads
        if (in_leads_section and 
            '"assigned_user_id":' in line and 
            current_lead_id is not None and 
            current_lead_id <= 20):
            
            if 'None' in line:
                lines[i] = line.replace('None', '3')
                updated_count += 1
                print(f"   ✅ Lead {current_lead_id}: Assigned to Agent1")
    
    # Write the updated content back
    updated_content = '\n'.join(lines)
    
    with open('lambda_package/lambda_function.py', 'w') as f:
        f.write(updated_content)
    
    print(f"\n📊 ASSIGNMENT SUMMARY:")
    print(f"✅ Updated {updated_count} lead assignments")
    print(f"👤 First 20 leads now assigned to Agent1")
    print(f"🆕 Leads 21-22 remain unassigned for new agents")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Deploy updated Lambda function")
    print("2. Agents will now see their full 20-lead portfolio")
    print("3. New agents will get leads from the unassigned pool")

if __name__ == "__main__":
    update_lead_assignments() 