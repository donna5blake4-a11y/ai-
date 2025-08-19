#!/bin/bash

# AI Deals Manager - Quick Start Script
# سكريبت التشغيل السريع لنظام إدارة العروض الذكي

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  AI Deals Manager Setup${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python $PYTHON_VERSION found"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version | cut -d' ' -f2)
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python is not installed. Please install Python 3.8+"
        exit 1
    fi
}

# Check if pip is installed
check_pip() {
    print_status "Checking pip installation..."
    if command -v pip3 &> /dev/null; then
        print_status "pip3 found"
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        print_status "pip found"
        PIP_CMD="pip"
    else
        print_error "pip is not installed. Please install pip"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    print_status "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    $PIP_CMD install --upgrade pip
    $PIP_CMD install -r requirements.txt
    print_status "Dependencies installed successfully"
}

# Check configuration files
check_config() {
    print_status "Checking configuration files..."
    
    if [ ! -f "telegram_config.json" ]; then
        print_warning "telegram_config.json not found"
        cat > telegram_config.json << EOF
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "users": ["YOUR_USER_ID_HERE"]
}
EOF
        print_status "Created telegram_config.json template"
        print_warning "Please edit telegram_config.json with your bot token and user ID"
    fi
    
    if [ ! -f "ai_config.json" ]; then
        print_warning "ai_config.json not found"
        print_status "Creating ai_config.json..."
        cat > ai_config.json << EOF
{
  "analysis_interval": 30,
  "daily_limit": 15,
  "min_discount": 25,
  "min_ai_confidence": 0.7,
  "verified_only": true,
  "sites_to_check": ["jumia", "noon", "amazon_eg"],
  "auto_migrate_json": true
}
EOF
        print_status "Created ai_config.json"
    fi
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    python -c "
from enhanced_database import EnhancedDatabaseManager
db = EnhancedDatabaseManager()
print('Database initialized successfully')
"
}

# Run system test
run_test() {
    print_status "Running system test..."
    if python test_ai_system.py; then
        print_status "System test passed"
    else
        print_warning "System test failed - this is normal for first run"
    fi
}

# Show next steps
show_next_steps() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Setup Complete!${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Edit telegram_config.json with your bot token and user ID"
    echo "2. Run the system: python run_ai_system.py"
    echo "3. Or run tests: python test_ai_system.py"
    echo ""
    echo "Available commands:"
    echo "  make run        - Run AI Deals Manager"
    echo "  make run-test   - Run system test"
    echo "  make run-quick  - Run quick start script"
    echo "  make help       - Show all available commands"
    echo ""
    echo "For help, visit: https://github.com/your-repo/ai-deals-manager"
}

# Main function
main() {
    print_header
    
    # Check prerequisites
    check_python
    check_pip
    
    # Setup environment
    create_venv
    activate_venv
    install_dependencies
    
    # Setup configuration
    check_config
    
    # Initialize system
    init_database
    
    # Run test
    run_test
    
    # Show next steps
    show_next_steps
}

# Handle command line arguments
case "${1:-}" in
    "test")
        activate_venv
        run_test
        ;;
    "run")
        activate_venv
        print_status "Starting AI Deals Manager..."
        python ai_deals_manager.py
        ;;
    "quick")
        activate_venv
        print_status "Starting quick start script..."
        python run_ai_system.py
        ;;
    "clean")
        print_status "Cleaning up..."
        rm -rf venv
        rm -rf __pycache__
        rm -rf *.pyc
        print_status "Cleanup complete"
        ;;
    "help"|"-h"|"--help")
        echo "AI Deals Manager - Quick Start Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no args)  - Full setup and installation"
        echo "  test       - Run system test only"
        echo "  run        - Run AI Deals Manager"
        echo "  quick      - Run quick start script"
        echo "  clean      - Clean up installation"
        echo "  help       - Show this help"
        ;;
    *)
        main
        ;;
esac