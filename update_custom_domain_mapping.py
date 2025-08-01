#!/usr/bin/env python3
"""
Update custom domain mapping to point to new API Gateway
Fix for lead persistence deployment
"""

import boto3
from botocore.exceptions import ClientError

def update_domain_mapping():
    """Update custom domain to point to new API Gateway"""
    
    api_gateway = boto3.client('apigateway', region_name='us-east-1')
    domain_name = 'api.vantagepointcrm.com'
    new_api_id = '7yf0tokab2'  # New API Gateway with lead persistence
    
    try:
        print(f"🔄 Updating custom domain mapping for {domain_name}...")
        
        # Delete existing base path mapping
        print("🗑️  Deleting old base path mapping...")
        try:
            api_gateway.delete_base_path_mapping(
                domainName=domain_name,
                basePath='(none)'
            )
            print("   ✅ Old mapping deleted")
        except ClientError as e:
            if 'NotFoundException' in str(e):
                print("   ⚠️  No existing mapping found")
            else:
                print(f"   ⚠️  Error deleting old mapping: {e}")
        
        # Create new base path mapping
        print(f"➕ Creating new mapping to API Gateway {new_api_id}...")
        api_gateway.create_base_path_mapping(
            domainName=domain_name,
            restApiId=new_api_id,
            stage='prod'
        )
        
        print("   ✅ New mapping created")
        
        # Verify the mapping
        print("🔍 Verifying new mapping...")
        response = api_gateway.get_base_path_mappings(domainName=domain_name)
        
        for mapping in response.get('items', []):
            rest_api_id = mapping.get('restApiId')
            stage = mapping.get('stage')
            base_path = mapping.get('basePath')
            print(f"   📋 Mapping: {base_path} → {rest_api_id} ({stage})")
        
        print(f"\n✅ Custom domain update complete!")
        print(f"🌐 URL: https://{domain_name}")
        print("🔄 DNS propagation may take a few minutes...")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error updating domain mapping: {e}")
        return False

if __name__ == "__main__":
    print("🚨 UPDATING CUSTOM DOMAIN FOR LEAD PERSISTENCE")
    print("=" * 50)
    update_domain_mapping()