#!/bin/bash

# Setup script for Agentic Red-Team Manager

set -e

echo "🚀 Setting up Agentic Red-Team Manager..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
if [ "$1" = "--dev" ]; then
    echo "🛠️ Installing development dependencies..."
    pip install -r requirements-dev.txt
    
    # Install pre-commit hooks
    echo "🪝 Setting up pre-commit hooks..."
    pre-commit install
fi

# Install package in editable mode
echo "📦 Installing package in editable mode..."
pip install -e .

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p reports logs data

# Copy example configuration
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys and configuration"
fi

# Check Docker availability
if command -v docker &> /dev/null; then
    echo "✅ Docker is available"
    
    # Test Docker access
    if docker ps &> /dev/null; then
        echo "✅ Docker daemon is accessible"
    else
        echo "⚠️ Docker daemon not accessible. You may need to start Docker or check permissions."
    fi
else
    echo "⚠️ Docker not found. Some features may not work without Docker."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'source venv/bin/activate' to activate the virtual environment"
echo "3. Try 'redteam --help' to see available commands"
echo "4. Run example scenario: 'redteam run examples/basic_prompt_injection.yaml'"
echo ""
echo "For development:"
echo "- Run tests: 'pytest'"
echo "- Format code: 'black src/ tests/'"
echo "- Check linting: 'flake8 src/ tests/'"
echo ""