# Quick Start Guide

## 1-Minute Setup with UV 🚀

### Step 1: Run Setup (30 seconds)
```bash
# macOS/Linux
./setup.sh

# Windows
setup.bat
```

### Step 2: Add API Token (20 seconds)
Edit `.env` and add your Apify token:
```env
APIFY_API_TOKEN=apify_api_YOUR_TOKEN_HERE
```

Get your token from: https://console.apify.com/account/integrations

### Step 3: Start Scraping! (10 seconds)
```bash
# Activate environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate      # Windows

# Search and download images
python xhs_actor.py search "coffee" --download --max-items 20
```

## Common Commands

### Search Posts
```bash
# Basic search
python xhs_actor.py search "keyword"

# Search with image download
python xhs_actor.py search "keyword" --download

# Limit results
python xhs_actor.py search "keyword" --max-items 50
```

### Get Comments
```bash
python xhs_actor.py comments "https://xiaohongshu.com/explore/POST_ID"
```

### Get User Profile
```bash
python xhs_actor.py profile "https://xiaohongshu.com/user/profile/USER_ID"
```

### Get User Posts
```bash
python xhs_actor.py user-posts "PROFILE_URL" --download
```

## Why UV?

- **⚡ Lightning Fast**: 10-100x faster than pip
- **🎯 Reliable**: Built-in dependency resolution
- **📦 Modern**: Rust-powered performance
- **🔒 Secure**: Cryptographic verification of packages

## Troubleshooting

### UV Not Found
```bash
# Install UV manually
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Permission Denied
```bash
chmod +x setup.sh
```

### API Token Issues
- Make sure you copied the entire token from Apify
- Check there are no extra spaces in .env
- Verify token starts with `apify_api_`

## Need Help?

Check the full documentation: [src/scrapers/README.md](src/scrapers/README.md)