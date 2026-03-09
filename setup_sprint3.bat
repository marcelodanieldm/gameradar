@echo off
REM ===============================================
REM GameRadar Sprint 3 - Setup Script (Windows)
REM Regional Payment Gateways & Talent-Ping System
REM ===============================================

echo.
echo ===============================================
echo  GameRadar Sprint 3 Setup
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3 is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed. Please install Node.js 18 or higher.
    exit /b 1
)

echo [OK] Python and Node.js detected
echo.

REM Setup Backend
echo ===============================================
echo  Setting up Backend...
echo ===============================================
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

echo [OK] Backend setup complete
echo.

REM Setup Frontend
echo ===============================================
echo  Setting up Frontend...
echo ===============================================
echo.

cd frontend

REM Install Node dependencies
echo Installing Node dependencies...
call npm install

echo [OK] Frontend setup complete
echo.

cd ..

REM Setup Environment Files
echo ===============================================
echo  Configuring Environment...
echo ===============================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] No .env file found. Creating from .env.example...
    copy .env.example .env
    echo [OK] Created .env - Please update with your credentials
) else (
    echo [OK] .env file already exists
)

REM Check if frontend .env.local exists
if not exist "frontend\.env.local" (
    echo [WARNING] No frontend .env.local found. Creating from .env.example...
    copy frontend\.env.example frontend\.env.local
    echo [OK] Created frontend\.env.local - Please update with your credentials
) else (
    echo [OK] frontend\.env.local file already exists
)

echo.
echo ===============================================
echo  Setup Complete!
echo ===============================================
echo.
echo Next Steps:
echo.
echo 1. Configure Environment Variables:
echo    - Edit .env with your credentials
echo    - Edit frontend\.env.local with your public keys
echo.
echo 2. Setup Database:
echo    - Go to Supabase SQL Editor
echo    - Run: database_schema.sql
echo.
echo 3. Configure Payment Gateways:
echo    - Razorpay: https://dashboard.razorpay.com/app/keys
echo    - Stripe: https://dashboard.stripe.com/apikeys
echo.
echo 4. Setup Notification Services:
echo    - WhatsApp Business API: https://developers.facebook.com/apps/
echo    - Telegram Bot: https://t.me/BotFather
echo    - SMTP: Configure your email provider
echo.
echo 5. Start Development Servers:
echo    Backend:  python api_routes_sprint3.py
echo    Frontend: cd frontend ^&^& npm run dev
echo.
echo Full documentation: SPRINT3_CASHFLOW_ENGAGEMENT.md
echo.

pause
