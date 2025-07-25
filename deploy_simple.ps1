# Simple AWS ECS Deployment Script for Cura Genesis CRM

Write-Host "Deploying Cura Genesis CRM to AWS ECS Fargate" -ForegroundColor Blue

# Check AWS configuration
$REGION = aws configure get region
$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text

if (-not $REGION) {
    Write-Host "AWS region not configured. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}

Write-Host "Region: $REGION" -ForegroundColor Green
Write-Host "Account ID: $ACCOUNT_ID" -ForegroundColor Green

# Deploy CloudFormation stack
Write-Host "Deploying infrastructure with CloudFormation..." -ForegroundColor Blue

aws cloudformation deploy --template-file aws-ecs-deployment.yml --stack-name cura-genesis-crm --capabilities CAPABILITY_IAM --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "Infrastructure deployed successfully" -ForegroundColor Green
} else {
    Write-Host "Infrastructure deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "Deployment completed!" -ForegroundColor Green 