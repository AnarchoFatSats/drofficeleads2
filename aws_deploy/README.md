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
