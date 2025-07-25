import boto3

try:
    print("Checking AWS Lambda functions...")
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    functions = lambda_client.list_functions()
    
    crm_functions = [f for f in functions['Functions'] if 'cura-genesis' in f['FunctionName']]
    
    if crm_functions:
        for func in crm_functions:
            print(f"✅ Found Lambda: {func['FunctionName']}")
            print(f"   ARN: {func['FunctionArn']}")
            print(f"   Runtime: {func['Runtime']}")
    else:
        print("❌ No CRM Lambda functions found")
    
    print("\nChecking API Gateways...")
    apigateway_client = boto3.client('apigateway', region_name='us-east-1')
    apis = apigateway_client.get_rest_apis()
    
    crm_apis = [api for api in apis['items'] if 'cura-genesis' in api['name']]
    
    if crm_apis:
        for api in crm_apis:
            print(f"✅ Found API Gateway: {api['name']}")
            print(f"   ID: {api['id']}")
            print(f"   HTTPS URL: https://{api['id']}.execute-api.us-east-1.amazonaws.com/prod")
    else:
        print("❌ No CRM API Gateways found")
        
except Exception as e:
    print(f"Error: {e}")
    print("Make sure AWS credentials are configured") 