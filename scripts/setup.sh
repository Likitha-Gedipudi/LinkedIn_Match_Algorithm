#!/bin/bash
# Setup script for LinkedIn Professional Matching System

set -e

echo "======================================"
echo "LinkedIn Matching System - Setup"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0.32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ Pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
echo "${YELLOW}This may take a few minutes...${NC}"
pip install -r requirements.txt > /dev/null 2>&1
echo "✓ Main dependencies installed"

if [ -f "requirements-dev.txt" ]; then
    echo "Installing development dependencies..."
    pip install -r requirements-dev.txt > /dev/null 2>&1
    echo "✓ Development dependencies installed"
fi
echo ""

# Create directories
echo "Creating directory structure..."
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/models
mkdir -p data/logs
mkdir -p notebooks
echo "✓ Directories created"
echo ""

# Create config file
echo "Setting up configuration..."
if [ ! -f "config/config.yaml" ]; then
    cp config/config.example.yaml config/config.yaml
    echo "✓ Configuration file created from template"
    echo "${YELLOW}⚠ Please edit config/config.yaml with your settings${NC}"
else
    echo "✓ Configuration file already exists"
fi
echo ""

# Create .env file
if [ ! -f ".env" ]; then
    cat > .env << EOF
# LinkedIn Matching System Environment Variables

# GitHub API (for GitHub scraper)
# LINKEDIN_MATCH_SCRAPERS_GITHUB_API_TOKEN=your_github_token_here

# Database (for production)
# LINKEDIN_MATCH_DATABASE_POSTGRES_PASSWORD=your_db_password

# API (for production)
# LINKEDIN_MATCH_API_AUTH_JWT_SECRET=your_secret_key_here

EOF
    echo "✓ .env file created"
    echo "${YELLOW}⚠ Please edit .env with your API keys and secrets${NC}"
else
    echo "✓ .env file already exists"
fi
echo ""

# Make scripts executable
echo "Making scripts executable..."
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true
echo "✓ Scripts are now executable"
echo ""

# Setup complete
echo "======================================"
echo "${GREEN}Setup Complete!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Edit config/config.yaml with your settings"
echo "3. Add API keys to .env file"
echo "4. Generate synthetic data: python scripts/run_scraper.py --source synthetic --count 10000"
echo "5. Generate dataset: python scripts/generate_dataset.py"
echo ""
echo "For more information, see README.md"
echo ""
