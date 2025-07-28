#!/bin/bash

# Cura Genesis CRM - AWS ECS Deployment Script
# This script builds the Docker image and deploys to AWS ECS Fargate

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Cura Genesis CRM to AWS ECS Fargate${NC}"
echo "================================================================"

# Configuration
STACK_NAME="cura-genesis-crm"
IMAGE_NAME="cura-genesis-crm"
REGION=$(aws configure get region)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [ -z "$REGION" ]; then
    echo -e "${RED}❌ AWS region not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${GREEN}📍 Region: $REGION${NC}"
echo -e "${GREEN}🔑 Account ID: $ACCOUNT_ID${NC}"

# Step 1: Deploy CloudFormation stack (infrastructure)
echo -e "${BLUE}📋 Step 1: Deploying infrastructure with CloudFormation...${NC}"

aws cloudformation deploy \
    --template-file aws-ecs-deployment.yml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        DatabaseURL="postgresql://crmuser:CuraGenesis2024!SecurePassword@cura-genesis-crm-db.c6ds4c4qok1n.us-east-1.rds.amazonaws.com:5432/cura_genesis_crm" \
        SecretKey="cura-genesis-crm-super-secret-key-change-in-production-2025" \
    --region $REGION

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Infrastructure deployed successfully${NC}"
else
    echo -e "${RED}❌ Infrastructure deployment failed${NC}"
    exit 1
fi

# Get ECR repository URI from CloudFormation outputs
ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' \
    --output text \
    --region $REGION)

echo -e "${GREEN}📦 ECR Repository: $ECR_URI${NC}"

# Step 2: Build and push Docker image
echo -e "${BLUE}🐳 Step 2: Building and pushing Docker image...${NC}"

# Login to ECR
echo -e "${BLUE}🔐 Logging in to ECR...${NC}"
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI

# Build the Docker image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker build -t $IMAGE_NAME .

# Tag the image for ECR
docker tag $IMAGE_NAME:latest $ECR_URI:latest

# Push the image to ECR
echo -e "${BLUE}📤 Pushing image to ECR...${NC}"
docker push $ECR_URI:latest

echo -e "${GREEN}✅ Docker image pushed successfully${NC}"

# Step 3: Update ECS service to use new image
echo -e "${BLUE}🔄 Step 3: Updating ECS service...${NC}"

# Force new deployment to use the latest image
aws ecs update-service \
    --cluster $STACK_NAME-cluster \
    --service cura-genesis-crm-service \
    --force-new-deployment \
    --region $REGION

echo -e "${GREEN}✅ ECS service update initiated${NC}"

# Step 4: Wait for deployment to complete
echo -e "${BLUE}⏳ Step 4: Waiting for deployment to complete...${NC}"

aws ecs wait services-stable \
    --cluster $STACK_NAME-cluster \
    --services cura-genesis-crm-service \
    --region $REGION

# Get the Load Balancer URL
LB_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
    --output text \
    --region $REGION)

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "================================================================"
echo -e "${GREEN}📊 CRM API URL: $LB_URL${NC}"
echo -e "${GREEN}🏥 Health Check: $LB_URL/health${NC}"
echo -e "${GREEN}📋 API Docs: $LB_URL/docs${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Test the API endpoints"
echo "2. Update frontend configuration to use the new API URL"
echo "3. Configure custom domain (optional)"
echo "4. Set up monitoring and alerts"
echo ""
echo -e "${YELLOW}⚠️  Note: It may take a few minutes for the service to fully start${NC}"

# Test the health endpoint
echo -e "${BLUE}🔍 Testing health endpoint...${NC}"
sleep 30  # Give the service time to start

for i in {1..5}; do
    if curl -f -s "$LB_URL/health" > /dev/null; then
        echo -e "${GREEN}✅ Health check passed!${NC}"
        break
    else
        echo -e "${YELLOW}⏳ Waiting for service to become healthy... (attempt $i/5)${NC}"
        sleep 30
    fi
done

echo ""
echo -e "${GREEN}🚀 Cura Genesis CRM is now running in production!${NC}" 