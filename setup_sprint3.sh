#!/bin/bash

# ===============================================
# GameRadar Sprint 3 - Setup Script
# Regional Payment Gateways & Talent-Ping System
# ===============================================

echo "🚀 GameRadar Sprint 3 Setup"
echo "=================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

echo "✅ Python and Node.js detected"
echo ""

# Setup Backend
echo "📦 Setting up Backend..."
echo "=================================="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate || venv\Scripts\activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Backend setup complete"
echo ""

# Setup Frontend
echo "📦 Setting up Frontend..."
echo "=================================="
cd frontend

# Install Node dependencies
echo "Installing Node dependencies..."
npm install

echo "✅ Frontend setup complete"
echo ""

# Setup Environment Files
echo "🔧 Configuring Environment..."
echo "=================================="

cd ..

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env - Please update with your credentials"
else
    echo "✅ .env file already exists"
fi

# Check if frontend .env.local exists
if [ ! -f "frontend/.env.local" ]; then
    echo "⚠️  No frontend .env.local found. Creating from .env.example..."
    cp frontend/.env.example frontend/.env.local
    echo "✅ Created frontend/.env.local - Please update with your credentials"
else
    echo "✅ frontend/.env.local file already exists"
fi

echo ""
echo "="=================================="
echo "🎉 Setup Complete!"
echo "=================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Configure Environment Variables:"
echo "   - Edit .env with your credentials"
echo "   - Edit frontend/.env.local with your public keys"
echo ""
echo "2. Setup Database:"
echo "   - Go to Supabase SQL Editor"
echo "   - Run: database_schema.sql"
echo "   - Or use: psql -f database_schema.sql"
echo ""
echo "3. Configure Payment Gateways:"
echo "   - Razorpay: https://dashboard.razorpay.com/app/keys"
echo "   - Stripe: https://dashboard.stripe.com/apikeys"
echo ""
echo "4. Setup Notification Services:"
echo "   - WhatsApp Business API: https://developers.facebook.com/apps/"
echo "   - Telegram Bot: https://t.me/BotFather"
echo "   - SMTP: Configure your email provider"
echo ""
echo "5. Start Development Servers:"
echo "   Backend:  python api_routes_sprint3.py"
echo "   Frontend: cd frontend && npm run dev"
echo ""
echo "📖 Full documentation: SPRINT3_CASHFLOW_ENGAGEMENT.md"
echo ""
