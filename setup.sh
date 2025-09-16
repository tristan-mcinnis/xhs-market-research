#!/bin/bash

# Xiaohongshu Scraper Setup Script with UV
echo "=========================================="
echo "Xiaohongshu Scraper & Analyzer Setup (UV)"
echo "=========================================="
echo ""

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "📦 UV not found. Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add UV to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"

    # Check again
    if ! command -v uv &> /dev/null; then
        echo "❌ Failed to install UV. Please install it manually:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    echo "✅ UV installed successfully"
else
    echo "✅ UV found: $(uv --version)"
fi

echo ""

# Create virtual environment using UV if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment with UV..."
    uv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install requirements using UV
echo "📦 Installing requirements with UV..."
uv pip install -r requirements.txt

# Install additional dependencies that might be missing
echo "📦 Installing additional dependencies..."
uv pip install scikit-learn google-generativeai

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found. Creating template..."
    cat > .env << EOL
# API Keys and Credentials
APIFY_API_TOKEN="your_apify_token_here"

# LLM Providers
OPENAI_API_KEY="your_openai_key_here"
DEEPSEEK_API_KEY="your_deepseek_key_here"
GEMINI_API_KEY="your_gemini_key_here"
MOONSHOT_API_KEY="your_moonshot_key_here"
EOL
    echo "✅ .env template created. Please add your API keys."
else
    echo "✅ .env file exists"
fi

# Create data directories if they don't exist
echo ""
echo "📁 Creating data directories..."
mkdir -p data/downloaded_content
mkdir -p data/reports
mkdir -p logs

echo "✅ Directories created"

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Add your API keys to .env file"
echo "2. Activate the virtual environment: source .venv/bin/activate"
echo "3. Test scraping: python main.py --keyword 'test' --posts 5"
echo "4. Test analysis: python analyze.py --latest --openai"
echo ""
echo "UV tips:"
echo "• Use 'uv pip list' to see installed packages"
echo "• Use 'uv pip install <package>' for faster installs"
echo "• UV is 10-100x faster than pip!"
echo ""