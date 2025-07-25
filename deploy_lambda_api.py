import boto3
import json
import time
import zipfile
import os

def main():
    print("🚀 Deploying CRM Backend to AWS Lambda + API Gateway...")
    
    # AWS clients
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    apigateway_client = boto3.client('apigateway', region_name='us-east-1')
    
    function_name = 'cura-genesis-crm-api'
    api_name = 'cura-genesis-crm-api'
    
    try:
        # Check if Lambda function exists
        print("📋 Checking Lambda function...")
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            print(f"✅ Lambda function exists: {response['Configuration']['FunctionName']}")
            lambda_arn = response['Configuration']['FunctionArn']
        except lambda_client.exceptions.ResourceNotFoundException:
            print("❌ Lambda function not found. Please create it first.")
            return
        
        # Create API Gateway
        print("🌐 Creating API Gateway...")
        api_response = apigateway_client.create_rest_api(
            name=api_name,
            description='CRM API Gateway with HTTPS',
            endpointConfiguration={'types': ['EDGE']}
        )
        api_id = api_response['id']
        print(f"✅ API Gateway created: {api_id}")
        
        # Get root resource
        resources = apigateway_client.get_resources(restApiId=api_id)
        root_resource_id = None
        for resource in resources['items']:
            if resource['path'] == '/':
                root_resource_id = resource['id']
                break
        
        # Create {proxy+} resource for catch-all
        print("📋 Creating proxy resource...")
        proxy_resource = apigateway_client.create_resource(
            restApiId=api_id,
            parentId=root_resource_id,
            pathPart='{proxy+}'
        )
        proxy_resource_id = proxy_resource['id']
        
        # Create ANY method on proxy resource
        print("🔧 Creating ANY method...")
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=proxy_resource_id,
            httpMethod='ANY',
            authorizationType='NONE'
        )
        
        # Create integration
        print("🔗 Setting up Lambda integration...")
        lambda_uri = f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=proxy_resource_id,
            httpMethod='ANY',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=lambda_uri
        )
        
        # Also create OPTIONS method for CORS
        print("🔧 Setting up CORS...")
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=proxy_resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=proxy_resource_id,
            httpMethod='OPTIONS',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=lambda_uri
        )
        
        # Give API Gateway permission to invoke Lambda
        print("🔐 Setting Lambda permissions...")
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId='api-gateway-invoke-lambda',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f"arn:aws:execute-api:us-east-1:337909762852:{api_id}/*/*"
            )
        except Exception as e:
            print(f"⚠️ Permission may already exist: {e}")
        
        # Create deployment
        print("🚀 Deploying API...")
        deploy_response = apigateway_client.create_deployment(
            restApiId=api_id,
            stageName='prod',
            description='Production deployment'
        )
        
        # Get the HTTPS URL
        api_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod"
        
        print("\n" + "="*60)
        print("🎉 DEPLOYMENT COMPLETE!")
        print("="*60)
        print(f"✅ Lambda Function: {function_name}")
        print(f"✅ API Gateway ID: {api_id}")
        print(f"🌐 HTTPS Backend URL: {api_url}")
        print("="*60)
        print("\n📋 NEXT STEPS:")
        print(f"1. Update frontend config.js with: {api_url}")
        print("2. Test endpoints:")
        print(f"   - Health: {api_url}/health")
        print(f"   - Login: {api_url}/api/v1/auth/login")
        print(f"   - Leads: {api_url}/api/v1/leads")
        print("\n🔑 Test Credentials: admin / admin123")
        
        return api_url
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    main() 