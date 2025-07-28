#!/bin/bash

# Cura Genesis CRM - Automated Lead Management Service
# This script starts the automated lead replenishment system

echo "🤖 Starting Cura Genesis Automated Lead Management System"
echo "=" * 60

# Activate virtual environment
if [ -d "crm_venv" ]; then
    echo "📦 Activating virtual environment..."
    source crm_venv/bin/activate
else
    echo "❌ Virtual environment not found! Please run setup first."
    exit 1
fi

# Check if CRM backend is running
echo "🔍 Checking CRM backend status..."
if curl -s http://localhost:8006/health > /dev/null; then
    echo "✅ CRM backend is running"
else
    echo "⚠️  CRM backend not detected on port 8006"
    echo "💡 Make sure your CRM is running before starting automation"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create logs directory
mkdir -p logs

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down automated lead management..."
    kill $AUTOMATION_PID 2>/dev/null
    echo "✅ Automation stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the automation system
echo "🚀 Starting continuous lead monitoring..."
echo "📋 Check interval: 30 minutes"
echo "📊 Monitoring logs: automated_lead_manager.log"
echo "🔄 Press Ctrl+C to stop"
echo ""

# Run automation in background and capture PID
python automated_lead_manager.py --mode continuous --interval 30 &
AUTOMATION_PID=$!

# Show real-time logs
echo "📋 Live automation logs:"
echo "---"
tail -f automated_lead_manager.log &
TAIL_PID=$!

# Wait for automation process
wait $AUTOMATION_PID

# Clean up log tail
kill $TAIL_PID 2>/dev/null 