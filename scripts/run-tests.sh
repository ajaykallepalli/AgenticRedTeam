#!/bin/bash

# Test runner script for Agentic Red-Team Manager

set -e

echo "🧪 Running test suite for Agentic Red-Team Manager..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Install test dependencies if needed
echo "📦 Ensuring test dependencies are installed..."
pip install -r requirements-dev.txt > /dev/null 2>&1 || true

# Run linting
echo "🔍 Running code quality checks..."

echo "  - Black formatting check..."
black --check src/ tests/ || {
    echo "❌ Code formatting issues found. Run 'black src/ tests/' to fix."
    exit 1
}

echo "  - Flake8 linting..."
flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503 || {
    echo "❌ Linting issues found."
    exit 1
}

echo "  - Import sorting check..."
isort --check-only src/ tests/ || {
    echo "❌ Import sorting issues found. Run 'isort src/ tests/' to fix."
    exit 1
}

# Run type checking
echo "  - Type checking with mypy..."
mypy src/ --ignore-missing-imports || {
    echo "⚠️ Type checking issues found."
}

# Run security checks
echo "🔒 Running security checks..."
bandit -r src/ -f text || {
    echo "⚠️ Security issues found."
}

# Run tests with coverage
echo "🧪 Running unit tests..."
pytest tests/ \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-fail-under=80 \
    -v

echo "✅ All tests passed!"

# Display coverage report location
if [ -d "htmlcov" ]; then
    echo "📊 Coverage report generated: htmlcov/index.html"
fi

echo ""
echo "🎉 Test suite completed successfully!"