# Xiaohongshu (RED) Scraper

Clean, professional scraper for Xiaohongshu (小红书/RED) using Apify Actor infrastructure.

> **🚀 Fast Setup with UV** - The blazing-fast Python package manager (10-100x faster than pip!)
> **✨ Single-file implementation** - All functionality in one clean `xhs_actor.py` file

## Features

- 🔍 **Search** - Find posts by keywords
- 💬 **Comments** - Extract comments from posts
- 👤 **Profiles** - Get user profile information
- 📝 **User Posts** - Scrape posts from specific users
- 🖼️ **Images** - Download images with parallel processing

## Quick Start

### Installation with UV (Recommended - Fast!)

```bash
# macOS/Linux
./setup.sh

# Windows
setup.bat
```

The setup script will:
- ✅ Install UV package manager (if needed)
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Create config files
- ✅ Set up project directories

### Manual Installation

```bash
# Install UV first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -r requirements.txt

# Check configuration
python xhs_actor.py config
```

### Basic Usage

```bash
# Search posts
python xhs_actor.py search "keyword" --max-items 20

# Search and download images
python xhs_actor.py search "keyword" --download

# Get user profile
python xhs_actor.py profile "https://www.xiaohongshu.com/user/profile/USER_ID"

# Get user posts with images
python xhs_actor.py user-posts "PROFILE_URL" --download

# Get comments from a post
python xhs_actor.py comments "POST_URL" --max-items 30
```

## Project Structure

```
├── xhs_actor.py         # Main scraper (single file, all functionality)
├── setup.sh             # Quick setup for macOS/Linux
├── setup.bat            # Quick setup for Windows
├── .env                 # API configuration (create from .env.example)
├── config.json          # Optional settings
├── data/
│   ├── scraped/        # JSON results
│   └── images/         # Downloaded images
└── logs/               # Application logs
```

## Configuration

The only required configuration is your Apify API token in `.env`:

```env
APIFY_API_TOKEN=apify_api_YOUR_TOKEN_HERE
```

Get your token from: https://console.apify.com/account/integrations

## How It Works

This scraper uses the Apify Actor `watk8sVZNzd40UtbQ` which provides:
- **Search Mode**: Find posts by keywords
- **Comment Mode**: Extract comments from posts
- **Profile Mode**: Get user information
- **User Posts Mode**: Get all posts from users

All results are saved to `data/scraped/` as JSON files with timestamps.
Downloaded images go to `data/images/`.

## License

For educational and research purposes only.