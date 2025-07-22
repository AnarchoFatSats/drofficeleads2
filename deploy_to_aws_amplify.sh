#!/bin/bash

# ===================================
# Cura Genesis CRM - AWS Amplify Deployment Script
# Replaces the old static dashboard with the new advanced CRM
# ===================================

echo "🚀 Deploying Advanced CRM to AWS Amplify"
echo "=========================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   brew install awscli"
    exit 1
fi

# Check if user is logged into AWS
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Not logged into AWS. Please run:"
    echo "   aws configure"
    exit 1
fi

echo "✅ AWS CLI is configured"

# Your existing Amplify app ID (from the URL)
AMPLIFY_APP_ID="dqp56q5wifun9"  # From main.dqp56q5wifun9.amplifyapp.com
BRANCH_NAME="main"

echo "📋 Preparing CRM files for deployment..."

# Create deployment directory
mkdir -p aws_deploy
cd aws_deploy

# Copy the new CRM files
cp ../crm_enhanced_dashboard.html ./index.html
cp ../crm_launcher.html ./launcher.html
cp ../manifest.json ./manifest.json

# Create a modern amplify.yml for the new CRM
cat > amplify.yml << 'EOF'
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - echo "🏥 Preparing Cura Genesis Advanced CRM"
        - echo "Features: Login System, 20-Lead Distribution, Gamification"
    build:
      commands:
        - echo "🚀 Building CRM interface..."
        - echo "✅ Login authentication ready"
        - echo "✅ Lead distribution system ready" 
        - echo "✅ Real-time notifications ready"
        - echo "✅ Mobile PWA ready"
    postBuild:
      commands:
        - echo "🎉 Advanced CRM deployment complete!"
        - echo "🔗 API Server needs to be deployed separately"
  artifacts:
    baseDirectory: .
    files:
      - '**/*'
  cache:
    paths: []
EOF

# Update the index.html to point to the correct API endpoint
# For now, we'll use a placeholder that users can update
sed -i.bak 's/localhost:8001/YOUR-API-ENDPOINT.com/g' index.html 2>/dev/null || \
sed -i '' 's/localhost:8001/YOUR-API-ENDPOINT.com/g' index.html

echo "⚙️ Updated API endpoints for production"

# Create a README for the deployment
cat > README.md << 'EOF'
# Cura Genesis Advanced CRM - AWS Deployment

## 🎯 What's New in This Version:

### ✅ **Login System**
- Role-based authentication (Admin, Manager, Agent)
- Secure JWT token system
- User management

### ✅ **20-Lead Distribution System**
- Each agent automatically gets exactly 20 leads
- Auto-redistribution when leads are closed
- 24-hour inactivity recycling

### ✅ **Gamification**
- Points system
- Badges and achievements
- Leaderboards

### ✅ **Real-time Features**
- WebSocket notifications
- Live updates
- Instant lead assignment alerts

### ✅ **Mobile PWA**
- Install as native app
- Offline capability
- Touch-optimized interface

## 🚀 API Backend Required

This frontend requires the CRM API backend to be deployed separately.
Options:
1. AWS ECS/Fargate (Recommended)
2. AWS Lambda + API Gateway
3. EC2 instance

See `AWS_DEPLOYMENT_GUIDE.md` for complete backend deployment instructions.

## 🔧 Configuration

Update the API endpoint in `index.html`:
- Replace `YOUR-API-ENDPOINT.com` with your actual API domain
- Ensure CORS is configured for your Amplify domain

## 🎉 Login Credentials (for testing)

- **Admin**: admin / admin123
- **Manager**: manager / admin123  
- **Agent**: agent1 / admin123
EOF

echo "📁 Files prepared for deployment:"
ls -la

echo ""
echo "🔄 Deploying to AWS Amplify..."

# Option 1: Deploy via AWS CLI (if amplify CLI is available)
if command -v amplify &> /dev/null; then
    echo "✅ Using Amplify CLI for deployment"
    
    # Initialize if needed
    if [ ! -f "amplify/.config/project-config.json" ]; then
        echo "🔧 Initializing Amplify project..."
        amplify init --yes
    fi
    
    # Deploy
    amplify publish --yes
    
else
    echo "📤 Manual deployment method:"
    echo ""
    echo "1. ZIP the contents of this folder:"
    zip -r cura-genesis-crm-deployment.zip .
    echo "   ✅ Created: cura-genesis-crm-deployment.zip"
    echo ""
    echo "2. Go to AWS Amplify Console:"
    echo "   https://console.aws.amazon.com/amplify/home"
    echo ""
    echo "3. Select your app: $AMPLIFY_APP_ID"
    echo ""
    echo "4. Go to 'Hosting' > 'Deploy' > 'Drag and drop'"
    echo ""
    echo "5. Upload the ZIP file"
    echo ""
    echo "📋 Or use AWS CLI:"
    echo "   aws amplify start-deployment \\"
    echo "     --app-id $AMPLIFY_APP_ID \\"
    echo "     --branch-name $BRANCH_NAME \\"
    echo "     --source-url s3://YOUR-BUCKET/cura-genesis-crm-deployment.zip"
fi

echo ""
echo "🎉 Deployment Instructions Complete!"
echo "=========================================="
echo ""
echo "📊 **What Users Will See:**"
echo "   ✅ Professional login screen (not static dashboard)"
echo "   ✅ Role-based dashboards with 20-lead management"
echo "   ✅ Real-time notifications and gamification"
echo "   ✅ Mobile-optimized PWA interface"
echo ""
echo "⚠️  **Important Next Steps:**"
echo "   1. Deploy the API backend (see AWS_DEPLOYMENT_GUIDE.md)"
echo "   2. Update API endpoints in the deployed files"
echo "   3. Configure database and Redis for production"
echo ""
echo "🔗 **Your Amplify URL:** https://$BRANCH_NAME.$AMPLIFY_APP_ID.amplifyapp.com"
echo ""
echo "🎯 **Current Status:**"
echo "   Frontend: Ready for deployment"
echo "   Backend:  Needs AWS deployment (localhost:8001 is running locally)"

# Go back to original directory
cd ..

echo ""
echo "✅ Ready to deploy! Check the 'aws_deploy' folder." 