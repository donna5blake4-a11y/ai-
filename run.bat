@echo off
title AI-Enhanced Amazon Deal Analyzer

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║    🤖 AI-Enhanced Amazon Deal Analyzer                      ║
echo ║                                                              ║
echo ║    نظام ذكي لتحليل العروض ومقارنة الأسعار                   ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+ first.
    echo 📥 Download from: https://python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if setup was run
if not exist "amz_products.db" (
    echo 🔧 First time setup required...
    echo Running setup.py...
    python setup.py
    if errorlevel 1 (
        echo ❌ Setup failed!
        pause
        exit /b 1
    )
    echo.
)

echo 🚀 Starting AI Deal Analyzer...
echo.

REM Run the main application
python main.py

if errorlevel 1 (
    echo.
    echo ❌ Application ended with errors
    pause
    exit /b 1
)

echo.
echo ✅ Application ended successfully
pause