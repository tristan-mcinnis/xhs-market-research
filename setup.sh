#!/usr/bin/env bash

# XHS Scraper Setup Script using UV
# Fast, modern Python package management with Python 3.12

set -euo pipefail

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

# Ensure uv is present
if ! command_exists uv; then
    echo -e "${RED}✗ uv not found.${NC}"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Prefer a specific Python 3.12 interpreter if available
PY_BIN="${PY_BIN:-$(command -v python3.12 || command -v python3 || true)}"
if [[ -z "${PY_BIN}" ]]; then
    echo -e "${RED}✗ python3 not found in PATH${NC}"
    exit 1
fi

echo "Detected Python at: ${PY_BIN}"
"${PY_BIN}" --version

# Require Python >= 3.12
if ! "${PY_BIN}" -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)"; then
    echo -e "${RED}✗ Python 3.12+ required.${NC}"
    echo "  Install python@3.12 and ensure it's first in PATH."
    echo "  macOS (Homebrew): brew install python@3.12 && brew link python@3.12 --force"
    echo "  Linux: sudo apt install python3.12 python3.12-venv"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3.12+ verified"

echo -e "${GREEN}✓${NC} UV is installed"

# Create virtual environment with Python 3.12
echo -e "${YELLOW}Creating virtual environment with Python 3.12...${NC}"
rm -rf .venv
uv venv --python 3.12

echo -e "${YELLOW}Activating virtual environment...${NC}"
# shellcheck disable=SC1091
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
if [[ -f "requirements.txt" ]]; then
    uv pip install -r requirements.txt
elif [[ -f "pyproject.toml" ]]; then
    uv sync
else
    echo -e "${YELLOW}⚠ No requirements.txt or pyproject.toml found; skipping install.${NC}"
fi

echo -e "${GREEN}✓${NC} Dependencies installed"
echo "Python version in venv: $(python --version)"

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