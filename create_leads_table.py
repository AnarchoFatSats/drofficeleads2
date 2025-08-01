#!/usr/bin/env python3
"""
Create DynamoDB table for VantagePoint CRM Leads
Critical fix for lead persistence issue
"""

import boto3
import json
from botocore.exceptions import ClientError

def create_leads_table():
    """Create the vantagepoint-leads DynamoDB table"""
    
    # Initialize DynamoDB client
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    table_name = 'vantagepoint-leads'
    
    try:
        # Check if table already exists
        try:
            response = dynamodb.describe_table(TableName=table_name)
            print(f"✅ Table '{table_name}' already exists!")
            print(f"Table Status: {response['Table']['TableStatus']}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise e
            print(f"📋 Table '{table_name}' doesn't exist. Creating...")
        
        # Create the table
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'N'  # Number type
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand pricing
        )
        
        print(f"🚀 Creating table '{table_name}'...")
        print(f"Table ARN: {response['TableDescription']['TableArn']}")
        
        # Wait for table to be created
        print("⏳ Waiting for table to become active...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        # Verify table is ready
        response = dynamodb.describe_table(TableName=table_name)
        print(f"✅ Table '{table_name}' created successfully!")
        print(f"Table Status: {response['Table']['TableStatus']}")
        print(f"Item Count: {response['Table']['ItemCount']}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error creating table: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def setup_lambda_permissions():
    """Ensure Lambda has permissions for the leads table"""
    
    iam = boto3.client('iam')
    
    # Policy for DynamoDB access to leads table
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Scan",
                    "dynamodb:Query"
                ],
                "Resource": "arn:aws:dynamodb:us-east-1:*:table/vantagepoint-leads"
            }
        ]
    }
    
    try:
        # Create inline policy for Lambda role
        iam.put_role_policy(
            RoleName='cura-genesis-crm-api-role-mfuo4t7u',  # Lambda execution role
            PolicyName='VantagePointLeadsTableAccess',
            PolicyDocument=json.dumps(policy_document)
        )
        
        print("✅ Lambda permissions updated for leads table")
        return True
        
    except ClientError as e:
        print(f"⚠️  Permission setup warning: {e}")
        print("You may need to manually add DynamoDB permissions to Lambda role")
        return False

if __name__ == "__main__":
    print("🚨 CRITICAL FIX: Creating DynamoDB table for lead persistence")
    print("=" * 60)
    
    # Create the table
    if create_leads_table():
        print("\n🔐 Setting up Lambda permissions...")
        setup_lambda_permissions()
        
        print("\n🎯 NEXT STEPS:")
        print("1. Update Lambda function code to use DynamoDB")
        print("2. Migrate existing leads to DynamoDB")
        print("3. Deploy updated Lambda function")
        print("4. Test lead assignment functionality")
        
        print("\n✅ DynamoDB leads table setup complete!")
    else:
        print("\n❌ Failed to create table. Check AWS credentials and permissions.")