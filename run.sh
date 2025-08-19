#!/bin/bash

# AI-Enhanced Amazon Deal Analyzer - Linux/Mac Launcher

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║    🤖 AI-Enhanced Amazon Deal Analyzer                      ║"
echo "║                                                              ║"
echo "║    نظام ذكي لتحليل العروض ومقارنة الأسعار                   ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python not found! Please install Python 3.8+ first."
        echo "📥 Install with: sudo apt install python3 python3-pip (Ubuntu/Debian)"
        echo "📥 Install with: brew install python3 (macOS)"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "✅ Python found ($PYTHON_CMD)"
echo ""

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION+ required. Found: $PYTHON_VERSION"
    exit 1
fi

# Check if setup was run
if [ ! -f "amz_products.db" ]; then
    echo "🔧 First time setup required..."
    echo "Running setup.py..."
    $PYTHON_CMD setup.py
    if [ $? -ne 0 ]; then
        echo "❌ Setup failed!"
        exit 1
    fi
    echo ""
fi

echo "🚀 Starting AI Deal Analyzer..."
echo ""

# Make script executable
chmod +x "$0"

# Run the main application
$PYTHON_CMD main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Application ended with errors"
    exit 1
fi

echo ""
echo "✅ Application ended successfully"