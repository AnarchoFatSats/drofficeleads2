#!/usr/bin/env python3
"""
VantagePoint CRM - Custom Domain Setup
Sets up api.vantagepointcrm.com for the production backend
"""

import boto3
import json
import sys

def setup_custom_domain():
    """Complete custom domain setup for VantagePoint CRM"""
    
    print("🚀 SETTING UP CUSTOM DOMAIN FOR VANTAGEPOINT CRM")
    print("=" * 60)
    
    # Configuration
    domain_name = "api.vantagepointcrm.com"
    root_domain = "vantagepointcrm.com"
    api_gateway_id = "blyqk7itsc"  # Current API Gateway ID
    stage_name = "prod"
    
    try:
        # Step 1: Request SSL Certificate
        print("📜 Step 1: Requesting SSL Certificate...")
        acm_client = boto3.client('acm', region_name='us-east-1')
        
        cert_response = acm_client.request_certificate(
            DomainName=domain_name,
            SubjectAlternativeNames=[root_domain, f"*.{root_domain}"],
            ValidationMethod='DNS',
            Tags=[
                {'Key': 'Project', 'Value': 'VantagePointCRM'},
                {'Key': 'Environment', 'Value': 'Production'}
            ]
        )
        
        certificate_arn = cert_response['CertificateArn']
        print(f"✅ SSL Certificate requested: {certificate_arn}")
        print("⚠️  IMPORTANT: You must validate this certificate in ACM console!")
        print(f"   Go to: https://console.aws.amazon.com/acm/home?region=us-east-1")
        print("   Add the DNS validation records to your Route 53 hosted zone")
        
        # Step 2: Wait for certificate validation (manual step)
        print("\n⏳ Waiting for certificate validation...")
        print("Please complete certificate validation and press Enter to continue...")
        input("Press Enter after validating the certificate...")
        
        # Step 3: Create Custom Domain in API Gateway
        print("\n🌐 Step 2: Creating Custom Domain in API Gateway...")
        apigateway_client = boto3.client('apigateway', region_name='us-east-1')
        
        domain_response = apigateway_client.create_domain_name(
            domainName=domain_name,
            certificateArn=certificate_arn,
            endpointConfiguration={'types': ['EDGE']},
            tags={
                'Project': 'VantagePointCRM',
                'Environment': 'Production'
            }
        )
        
        cloudfront_domain = domain_response['distributionDomainName']
        print(f"✅ Custom domain created: {domain_name}")
        print(f"📍 CloudFront domain: {cloudfront_domain}")
        
        # Step 4: Create Base Path Mapping
        print("\n🔗 Step 3: Creating Base Path Mapping...")
        apigateway_client.create_base_path_mapping(
            domainName=domain_name,
            restApiId=api_gateway_id,
            stage=stage_name
        )
        
        print(f"✅ Base path mapping created for API Gateway: {api_gateway_id}")
        
        # Step 5: Generate DNS Records
        print("\n📝 Step 4: DNS Records for Route 53...")
        print(f"Add this CNAME record to your {root_domain} hosted zone:")
        print(f"Name: api.vantagepointcrm.com")
        print(f"Type: CNAME")
        print(f"Value: {cloudfront_domain}")
        print(f"TTL: 300")
        
        # Step 6: Update Frontend Configuration
        print("\n🔧 Step 5: Update Frontend Configuration...")
        update_frontend_config(domain_name)
        
        print("\n" + "=" * 60)
        print("🎉 CUSTOM DOMAIN SETUP COMPLETE!")
        print(f"✅ Your API is now available at: https://{domain_name}")
        print("✅ Frontend configuration files updated")
        print("✅ Ready for production deployment")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return False

def update_frontend_config(new_domain):
    """Update all frontend configuration files with new domain"""
    
    old_url = "https://blyqk7itsc.execute-api.us-east-1.amazonaws.com/prod"
    new_url = f"https://{new_domain}"
    
    files_to_update = [
        "web/config.js",
        "aws_deploy/index.html",
        "aws_deploy/login.html", 
        "aws_deploy/debug_send_docs.html",
        "backend_team_handoff/aws_deploy/index.html",
        "backend_team_handoff/aws_deploy/login.html",
        "crm_enhanced_dashboard_v2.html",
        "crm_production_dashboard.html",
        "debug_send_docs.html"
    ]
    
    updated_files = []
    
    for file_path in files_to_update:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_url in content:
                updated_content = content.replace(old_url, new_url)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                updated_files.append(file_path)
                print(f"✅ Updated: {file_path}")
        
        except FileNotFoundError:
            print(f"⚠️  File not found: {file_path}")
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")
    
    return updated_files

if __name__ == "__main__":
    print("VantagePoint CRM - Custom Domain Setup")
    print("This script will:")
    print("1. Request SSL certificate for api.vantagepointcrm.com")
    print("2. Create custom domain in API Gateway")
    print("3. Update all frontend configuration files")
    print("4. Provide DNS records for Route 53")
    print()
    
    confirm = input("Do you want to proceed? (y/N): ")
    if confirm.lower() == 'y':
        setup_custom_domain()
    else:
        print("Setup cancelled.") 