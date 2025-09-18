#!/bin/bash

# XHS Scraper Setup Script using UV
# Fast, modern Python package management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  XHS Scraper Setup with UV${NC}"
echo -e "${BLUE}================================${NC}"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Found Python ${PYTHON_VERSION}"

# Install UV if not present
if ! command_exists uv; then
    echo -e "${YELLOW}Installing UV package manager...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add UV to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"

    # Add to shell profile if not already there
    if [[ "$SHELL" == *"zsh"* ]]; then
        PROFILE="$HOME/.zshrc"
    else
        PROFILE="$HOME/.bashrc"
    fi

    if ! grep -q ".cargo/bin" "$PROFILE" 2>/dev/null; then
        echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> "$PROFILE"
        echo -e "${GREEN}✓${NC} Added UV to $PROFILE"
    fi

    echo -e "${GREEN}✓${NC} UV installed successfully"
else
    echo -e "${GREEN}✓${NC} UV is already installed"
fi

# Create virtual environment with UV
echo -e "${YELLOW}Creating virtual environment...${NC}"
uv venv --python 3.8

# Install dependencies in virtual environment
echo -e "${YELLOW}Installing dependencies...${NC}"
uv pip install --python .venv/bin/python -r requirements.txt

# Check for API token
if [ ! -f ".env" ]; then
    echo
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env 2>/dev/null || cat > .env << 'EOF'
# Xiaohongshu Scraper Configuration
# Get your token from: https://console.apify.com/account/integrations

APIFY_API_TOKEN=your_apify_token_here
EOF
    echo -e "${GREEN}✓${NC} Created .env file"
    echo -e "${YELLOW}⚠️  Please edit .env and add your Apify API token${NC}"
fi

# Create default config if not exists
if [ ! -f "config.json" ]; then
    echo -e "${YELLOW}Creating default configuration...${NC}"
    python3 -c "from src.scrapers.config import Config; Config.create_default_config()" 2>/dev/null || \
    uv run python -c "from src.scrapers.config import Config; Config.create_default_config()"
    echo -e "${GREEN}✓${NC} Created config.json"
fi

# Create necessary directories
echo -e "${YELLOW}Creating project directories...${NC}"
mkdir -p data/scraped data/images logs
echo -e "${GREEN}✓${NC} Directories created"

echo
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Setup Complete! 🎉${NC}"
echo -e "${GREEN}================================${NC}"
echo
echo -e "Next steps:"
echo -e "1. ${YELLOW}Edit .env${NC} and add your Apify API token"
echo -e "2. ${YELLOW}Activate the environment:${NC}"
echo -e "   ${BLUE}source .venv/bin/activate${NC}"
echo -e "3. ${YELLOW}Run the scraper:${NC}"
echo -e "   ${BLUE}python xhs_actor.py search 'keyword' --download${NC}"
echo
echo -e "For more options: ${BLUE}python xhs_actor.py --help${NC}"