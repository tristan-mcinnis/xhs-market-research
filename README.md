# Xiaohongshu (小红书) Scraper

A simple, focused scraper for collecting Xiaohongshu content using the Apify Actor API.

## 🚀 Quick Start

### Prerequisites

1. **Install dependencies:**
   ```bash
   ./setup.sh  # macOS/Linux (requires Python 3.12+)
   # or
   setup.bat   # Windows
   ```

2. **Configure Apify credentials in `.env`:**
   ```env
   APIFY_API_TOKEN=your_apify_token
   APIFY_ACTOR_ID=watk8sVZNzd40UtbQ
   ```

### Basic Usage

```bash
# Search and download images
python xhs_scraper.py search "咖啡" --max-items 30 --download

# Search without downloading
python xhs_scraper.py search "Thai condoms" --max-items 50

# Limit image downloads
python xhs_scraper.py search "luxury skincare" --download --max-downloads 20

# Get comments from posts
python xhs_scraper.py comments https://www.xiaohongshu.com/explore/...

# Get user profiles
python xhs_scraper.py profile https://www.xiaohongshu.com/user/profile/...

# Get posts from a user
python xhs_scraper.py user-posts https://www.xiaohongshu.com/user/profile/... --download

# Check configuration
python xhs_scraper.py config
```

## 📁 Output Structure

All outputs are organized by date and query:

```
data/
└── YYYYMMDD/              # Date of scrape
    └── query_name/        # Your search query
        ├── scraped/       # Raw JSON data
        └── images/        # Downloaded images
```

## 🔧 Configuration

### API Setup

1. Get your Apify API token from [Apify Console](https://console.apify.com/account/integrations)
2. Add credentials to `.env` file:

```bash
APIFY_API_TOKEN=your_apify_token_here
APIFY_ACTOR_ID=watk8sVZNzd40UtbQ
```

### Settings

Edit `pipeline_config.json` to adjust behavior (no secrets here):
- `default_max_items` - Default number of posts to scrape (default: 30)
- `default_max_downloads` - Default max images to download (default: 50)
- `request_delay` - Delay between image downloads in seconds (default: 0.5)
- `timeout` - Request timeout in seconds (default: 10)
- `max_retries` - Number of retry attempts (default: 3)
- `rate_limit_delay` - API rate limiting delay (default: 2)

## 📊 Features

- **Multi-mode scraping**: Search posts, get comments, fetch profiles, retrieve user posts
- **Image downloading**: Parallel downloads with rate limiting and retry logic
- **Smart organization**: Automatic directory structure based on date and query
- **Progress tracking**: Real-time feedback with statistics
- **Logging**: Detailed logs saved to `logs/` directory
- **Configurable**: Centralized settings in `pipeline_config.json`

## 🎯 Command Reference

### Search Posts
```bash
python xhs_scraper.py search KEYWORDS [OPTIONS]

Options:
  -m, --max-items N       Max posts to scrape (default: 30)
  -d, --download          Download images from posts
  --max-downloads N       Limit image downloads
```

### Get Comments
```bash
python xhs_scraper.py comments URL [URL...] [OPTIONS]

Options:
  -m, --max-items N       Max comments per post (default: 30)
```

### Get Profiles
```bash
python xhs_scraper.py profile URL [URL...]
```

### Get User Posts
```bash
python xhs_scraper.py user-posts URL [URL...] [OPTIONS]

Options:
  -m, --max-items N       Max posts per user (default: 30)
  -d, --download          Download images from posts
```

## 💡 Tips & Best Practices

### Performance
- Start with 20-30 items for testing
- Use `--max-downloads` to limit bandwidth usage
- Parallel downloads (5 workers) speed up image collection
- Rate limiting prevents API throttling

### Data Management
- Results are timestamped for version tracking
- Directory structure keeps data organized by date
- Logs are saved to `logs/` for debugging

## 🐛 Troubleshooting

**"API token not configured"**
→ Add your Apify token to `.env` file

**"No module named..."**
→ Run `./setup.sh` or `pip install -r requirements.txt`

**Rate limiting errors**
→ Increase `request_delay` in `pipeline_config.json`

**Download failures**
→ Check internet connection and Xiaohongshu availability

## 📚 Technical Details

### Core Technologies
- **Apify Actor**: Xiaohongshu data collection infrastructure
- **Requests**: HTTP library for image downloads
- **ThreadPoolExecutor**: Parallel image downloading
- **Python 3.12+**: Modern Python features

### API Configuration
The scraper uses Apify's Xiaohongshu Actor (`watk8sVZNzd40UtbQ`) which supports:
- Keyword search
- Comment extraction
- Profile information
- User post retrieval

### Output Format
All data is saved as JSON with the following structure:
- Timestamped filenames for versioning
- Complete metadata from Xiaohongshu
- Image URLs and download paths

## 📄 Archive

Previous analysis pipeline (steps 2-7) has been archived in the `archive/` directory. See `archive/PIPELINE_UPDATES.md` for details on the full analysis workflow.

For prompt documentation, see `prompts.md`.

## 🤝 Contributing

Feel free to submit issues or pull requests to improve the scraper!

## 📄 License

For educational and research purposes only.

---

Built for efficient Xiaohongshu data collection.
