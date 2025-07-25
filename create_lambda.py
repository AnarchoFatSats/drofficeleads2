import boto3

def create_lambda():
    print("🚀 Creating Lambda function...")
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        # Read the ZIP file
        with open('lambda_deployment.zip', 'rb') as zip_file:
            zip_content = zip_file.read()
        
        # Create Lambda function
        response = lambda_client.create_function(
            FunctionName='cura-genesis-crm-api',
            Runtime='python3.11',
            Role='arn:aws:iam::337909762852:role/lambda-cura-genesis-crm',
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Timeout=30,
            Description='CRM Backend API'
        )
        
        print(f"✅ Lambda function created!")
        print(f"   Function: {response['FunctionName']}")
        print(f"   ARN: {response['FunctionArn']}")
        print(f"   Runtime: {response['Runtime']}")
        
        return response['FunctionArn']
        
    except Exception as e:
        print(f"❌ Error creating Lambda: {e}")
        return None

if __name__ == "__main__":
    create_lambda() 