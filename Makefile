.PHONY: help install test lint format clean run setup

# Default target
help:
	@echo "AI Deals Manager - Available Commands:"
	@echo ""
	@echo "  setup     - Install dependencies and setup environment"
	@echo "  install   - Install production dependencies"
	@echo "  install-dev - Install development dependencies"
	@echo "  test      - Run all tests"
	@echo "  test-cov  - Run tests with coverage"
	@echo "  lint      - Run linting checks"
	@echo "  format    - Format code with black and isort"
	@echo "  clean     - Clean up temporary files"
	@echo "  run       - Run the AI Deals Manager"
	@echo "  run-test  - Run system test"
	@echo "  run-quick - Run quick start script"
	@echo "  build     - Build package"
	@echo "  install-hooks - Install pre-commit hooks"

# Setup environment
setup: install install-dev install-hooks
	@echo "✅ Environment setup complete!"

# Install production dependencies
install:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt

# Install development dependencies
install-dev:
	@echo "🔧 Installing development dependencies..."
	pip install -r requirements-dev.txt

# Install pre-commit hooks
install-hooks:
	@echo "🔗 Installing pre-commit hooks..."
	pre-commit install

# Run tests
test:
	@echo "🧪 Running tests..."
	python -m pytest

# Run tests with coverage
test-cov:
	@echo "📊 Running tests with coverage..."
	python -m pytest --cov=. --cov-report=html --cov-report=term

# Run linting
lint:
	@echo "🔍 Running linting checks..."
	flake8 .
	mypy .
	bandit -r . -f json -o bandit-report.json

# Format code
format:
	@echo "🎨 Formatting code..."
	black .
	isort .

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -f .coverage
	rm -f bandit-report.json

# Run AI Deals Manager
run:
	@echo "🚀 Starting AI Deals Manager..."
	python ai_deals_manager.py

# Run system test
run-test:
	@echo "🧪 Running system test..."
	python test_ai_system.py

# Run quick start
run-quick:
	@echo "⚡ Running quick start..."
	python run_ai_system.py

# Build package
build: clean
	@echo "📦 Building package..."
	python setup.py sdist bdist_wheel

# Create virtual environment
venv:
	@echo "🐍 Creating virtual environment..."
	python -m venv venv
	@echo "✅ Virtual environment created!"
	@echo "📝 To activate:"
	@echo "   source venv/bin/activate  # Linux/Mac"
	@echo "   venv\\Scripts\\activate     # Windows"

# Database operations
db-init:
	@echo "🗄️ Initializing database..."
	python -c "from enhanced_database import EnhancedDatabaseManager; db = EnhancedDatabaseManager(); print('✅ Database initialized')"

db-migrate:
	@echo "🔄 Migrating JSON data..."
	python -c "from ai_deals_manager import AIDealsManager; m = AIDealsManager(); m.migrate_json_data()"

# Development helpers
dev-install: install-dev install-hooks
	@echo "✅ Development environment ready!"

dev-test: format lint test
	@echo "✅ All development checks passed!"

# Docker helpers (if needed)
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t ai-deals-manager .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -it ai-deals-manager

# Documentation
docs-build:
	@echo "📚 Building documentation..."
	cd docs && make html

docs-serve:
	@echo "📚 Serving documentation..."
	cd docs/_build/html && python -m http.server 8000

# Security checks
security-check:
	@echo "🔒 Running security checks..."
	bandit -r . -f json -o bandit-report.json
	safety check

# Performance profiling
profile:
	@echo "⚡ Running performance profiling..."
	python -m cProfile -o profile.stats ai_deals_manager.py

# Backup
backup:
	@echo "💾 Creating backup..."
	tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz *.py *.json *.md *.txt *.yaml Makefile

# Update dependencies
update-deps:
	@echo "🔄 Updating dependencies..."
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt

# Show system info
info:
	@echo "📋 System Information:"
	@echo "Python version: $(shell python --version)"
	@echo "Pip version: $(shell pip --version)"
	@echo "Current directory: $(shell pwd)"
	@echo "Files in directory:"
	@ls -la

# Quick development cycle
dev-cycle: format lint test
	@echo "✅ Development cycle completed!"