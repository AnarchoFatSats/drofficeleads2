# Cura Genesis CRM - AWS Deployment Guide

## 🌐 Complete AWS Deployment for Production CRM

This guide will help you deploy your advanced CRM system to AWS with full functionality including the 20-lead distribution system, 24-hour recycling, and real-time features.

## 📋 Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Docker installed locally
- Domain name (optional but recommended)

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │────│   Application   │────│   RDS Database  │
│   (Frontend)    │    │   Load Balancer │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   ECS Fargate   │────│  ElastiCache    │
                       │   (CRM API)     │    │   (Redis)       │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Deployment Options

### Option 1: Quick Deploy with AWS Amplify + RDS (Recommended)

#### Step 1: Prepare Environment Variables

Create a `.env.production` file:

```bash
# Database Configuration
DATABASE_URL=postgresql://crmuser:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/cura_genesis_crm

# Security
SECRET_KEY=${GENERATED_SECRET_KEY}
DEBUG=false

# Redis Configuration  
REDIS_URL=redis://${ELASTICACHE_ENDPOINT}:6379/0

# CRM Configuration
ENABLE_GAMIFICATION=true
RECYCLING_ENABLED=true
RECYCLING_DAYS_DEFAULT=7
MIN_CONTACT_ATTEMPTS=3

# Application
APP_NAME=Cura Genesis CRM
CORS_ORIGINS=["https://your-domain.com"]

# Email (Optional - for notifications)
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=${SES_ACCESS_KEY}
SMTP_PASSWORD=${SES_SECRET_KEY}
FROM_EMAIL=noreply@curagenesis.com

# File Storage
UPLOAD_FOLDER=/tmp/uploads
MAX_FILE_SIZE=5242880

# Background Tasks
CELERY_BROKER_URL=redis://${ELASTICACHE_ENDPOINT}:6379/1
CELERY_RESULT_BACKEND=redis://${ELASTICACHE_ENDPOINT}:6379/2
```

#### Step 2: Create AWS Infrastructure

**Create RDS PostgreSQL Database:**

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name cura-genesis-subnet-group \
    --db-subnet-group-description "Subnet group for Cura Genesis CRM" \
    --subnet-ids subnet-12345678 subnet-87654321

# Create PostgreSQL database
aws rds create-db-instance \
    --db-instance-identifier cura-genesis-crm-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 14.9 \
    --master-username crmuser \
    --master-user-password "YourSecurePassword123!" \
    --allocated-storage 20 \
    --db-name cura_genesis_crm \
    --db-subnet-group-name cura-genesis-subnet-group \
    --vpc-security-group-ids sg-12345678 \
    --backup-retention-period 7 \
    --multi-az \
    --storage-encrypted
```

**Create ElastiCache Redis:**

```bash
# Create Redis cache
aws elasticache create-cache-cluster \
    --cache-cluster-id cura-genesis-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1 \
    --port 6379 \
    --security-group-ids sg-12345678
```

#### Step 3: Containerize the Application

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash crm
RUN chown -R crm:crm /app
USER crm

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start command
CMD ["python", "crm_main.py"]
```

Create `docker-compose.production.yml`:

```yaml
version: '3.8'

services:
  crm-api:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
      - REDIS_URL=${REDIS_URL}
      - ENABLE_GAMIFICATION=true
      - RECYCLING_ENABLED=true
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    
  worker:
    build: .
    command: celery -A crm_main.celery worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
    restart: unless-stopped

  scheduler:
    build: .
    command: celery -A crm_main.celery beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
    restart: unless-stopped
```

#### Step 4: Deploy to ECS with Fargate

Create `ecs-task-definition.json`:

```json
{
  "family": "cura-genesis-crm",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "crm-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/cura-genesis-crm:latest",
      "portMappings": [
        {
          "containerPort": 8001,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://crmuser:password@rds-endpoint:5432/cura_genesis_crm"
        },
        {
          "name": "REDIS_URL", 
          "value": "redis://elasticache-endpoint:6379/0"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cura-genesis-crm",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8001/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### Step 5: Deploy Frontend to CloudFront + S3

Create `buildspec.yml` for AWS CodeBuild:

```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
  
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
  
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker image...
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
      - echo Writing image definitions file...
      - printf '[{"name":"crm-api","imageUri":"%s"}]' $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG > imagedefinitions.json

artifacts:
  files:
    - imagedefinitions.json
    - crm_enhanced_dashboard.html
    - crm_launcher.html
    - manifest.json
    - styles.css
```

**Upload frontend files to S3:**

```bash
# Create S3 bucket for frontend
aws s3 mb s3://cura-genesis-crm-frontend

# Upload frontend files
aws s3 sync . s3://cura-genesis-crm-frontend \
    --exclude "*" \
    --include "*.html" \
    --include "*.css" \
    --include "*.js" \
    --include "manifest.json"

# Create CloudFront distribution
aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json
```

### Option 2: AWS Amplify Full-Stack Deployment

#### Step 1: Initialize Amplify

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize Amplify project
amplify init

# Add API (GraphQL/REST)
amplify add api

# Add hosting
amplify add hosting

# Add authentication
amplify add auth

# Deploy everything
amplify push
```

#### Step 2: Configure Amplify for CRM

Create `amplify.yml`:

```yaml
version: 1
backend:
  phases:
    build:
      commands:
        - '# Execute Amplify CLI with the helper script'
        - amplifyPush --simple

frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - echo "Building CRM Frontend"
        - cp crm_enhanced_dashboard.html index.html
        - cp crm_launcher.html launcher.html
    postBuild:
      commands:
        - echo "Build completed"
  artifacts:
    baseDirectory: .
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

## 🔧 Environment Configuration

### Production Environment Variables

```bash
# Required for AWS deployment
export AWS_REGION=us-east-1
export RDS_ENDPOINT=your-rds-endpoint.region.rds.amazonaws.com
export ELASTICACHE_ENDPOINT=your-redis-cluster.cache.amazonaws.com
export SECRET_KEY=$(openssl rand -hex 32)
export DB_PASSWORD=YourSecurePassword123!

# Optional: Custom domain
export DOMAIN_NAME=crm.curagenesis.com
export CERTIFICATE_ARN=arn:aws:acm:region:account:certificate/cert-id
```

## 🚨 Security Configuration

### IAM Roles and Policies

**ECS Task Execution Role:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

**Security Groups:**

```bash
# Application Load Balancer security group
aws ec2 create-security-group \
    --group-name cura-genesis-alb-sg \
    --description "Security group for CRM ALB"

# Allow HTTP and HTTPS
aws ec2 authorize-security-group-ingress \
    --group-id sg-alb-id \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id sg-alb-id \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# ECS service security group
aws ec2 create-security-group \
    --group-name cura-genesis-ecs-sg \
    --description "Security group for CRM ECS tasks"

# Allow traffic from ALB
aws ec2 authorize-security-group-ingress \
    --group-id sg-ecs-id \
    --protocol tcp \
    --port 8001 \
    --source-group sg-alb-id
```

## 📊 Monitoring and Scaling

### CloudWatch Alarms

```bash
# CPU utilization alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "CRM-High-CPU" \
    --alarm-description "CRM service high CPU utilization" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 70 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2

# Memory utilization alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "CRM-High-Memory" \
    --alarm-description "CRM service high memory utilization" \
    --metric-name MemoryUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2
```

### Auto Scaling Configuration

```json
{
  "ServiceName": "cura-genesis-crm-service",
  "ScalableDimension": "ecs:service:DesiredCount",
  "MinCapacity": 2,
  "MaxCapacity": 10,
  "TargetTrackingScalingPolicy": {
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 300,
    "ScaleInCooldown": 300
  }
}
```

## 🗄️ Database Migration

### Production Database Setup

```bash
# Connect to RDS instance
psql -h your-rds-endpoint.region.rds.amazonaws.com -U crmuser -d cura_genesis_crm

# Run schema
\i crm_database_schema.sql

# Import lead data
python migrate_leads_to_crm.py --production
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy CRM to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: cura-genesis-crm
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
    
    - name: Deploy to ECS
      run: |
        aws ecs update-service \
          --cluster cura-genesis-cluster \
          --service cura-genesis-crm-service \
          --force-new-deployment
```

## 🎯 Post-Deployment Setup

### 1. Initialize Lead Distribution

```bash
# SSH into ECS task or run as one-time task
python setup_lead_distribution.py
```

### 2. Create Admin Users

```bash
# Run migration script
python migrate_leads_to_crm.py
```

### 3. Test System Health

```bash
# Check all endpoints
curl https://your-domain.com/health
curl https://your-domain.com/api/v1/distribution/stats
```

## 🌍 Domain and SSL Configuration

### Route 53 and Certificate Manager

```bash
# Create hosted zone
aws route53 create-hosted-zone \
    --name curagenesis.com \
    --caller-reference $(date +%s)

# Request SSL certificate
aws acm request-certificate \
    --domain-name crm.curagenesis.com \
    --domain-name *.curagenesis.com \
    --validation-method DNS
```

## 📱 Progressive Web App Configuration

Your CRM will be installable as a PWA with:
- ✅ Offline capability
- ✅ Push notifications  
- ✅ Native app-like experience
- ✅ Mobile optimization

## 🎉 Production Features Active

After deployment, your CRM will have:

- **🎯 20 leads per agent** - Automatically maintained
- **⏰ 24-hour recycling** - Background automation
- **🔄 Auto-redistribution** - On lead closure
- **🎮 Gamification** - Points, badges, leaderboards
- **📱 Mobile PWA** - Install on any device
- **🔒 Enterprise security** - AWS best practices
- **📊 Real-time updates** - WebSocket connections
- **🚀 Auto-scaling** - Handle growth automatically

## 📞 Support

Need help with deployment? Contact your development team or AWS support.

---

**⚠️ Important:** Replace all placeholder values (account IDs, endpoints, passwords) with your actual AWS resources before deployment. 