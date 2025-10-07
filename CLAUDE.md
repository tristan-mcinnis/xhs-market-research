# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a **simplified Xiaohongshu scraper** with two interfaces:
1. **CLI** - Command-line interface for developers
2. **Web Interface** - Password-protected GitHub Pages site for team members

Data collection is handled via the Apify Actor API.

## Commands

### Development Setup
```bash
# Install dependencies (Python 3.12+ required)
./setup.sh    # macOS/Linux
setup.bat     # Windows

# Or manually install
pip install -r requirements.txt
```

### Running the Scraper
```bash
# Search and download images
python xhs_scraper.py search "search term" --max-items 30 --download

# Search without downloading images
python xhs_scraper.py search "query" --max-items 50

# Limit number of image downloads
python xhs_scraper.py search "coffee" --download --max-downloads 20

# Get comments from posts
python xhs_scraper.py comments https://www.xiaohongshu.com/explore/...

# Get user profiles
python xhs_scraper.py profile https://www.xiaohongshu.com/user/profile/...

# Get posts from a user
python xhs_scraper.py user-posts https://www.xiaohongshu.com/user/profile/... --download

# Check current configuration
python xhs_scraper.py config
```

### Web Interface Management
```bash
# Update team password (after editing .env)
python update_password.py

# Deploy to GitHub Pages (automatic after push to main)
git add docs/
git commit -m "Update web interface"
git push
```

### Code Quality
```bash
# Format code
black xhs_scraper.py --line-length 100

# Lint code
ruff check xhs_scraper.py
```

## Architecture Overview

### Core Files

**Scraper (CLI):**
- `xhs_scraper.py` - Complete scraper with all functionality (510 lines)
- `pipeline_config.json` - Configuration settings
- `.env` - API credentials and web password

**Web Interface:**
- `docs/index.html` - Password-protected web UI
- `docs/app.js` - Frontend logic and GitHub Actions integration
- `docs/styles.css` - UI styling
- `docs/audit.json` - Public audit log (auto-updated)

**GitHub Actions:**
- `.github/workflows/web-scrape.yml` - Serverless scraping workflow

**Utilities:**
- `update_password.py` - Update web interface password from .env

### Core Components

**Scraper Class** (`XHSActor`):
- Wraps Apify Actor API for Xiaohongshu data collection
- Supports 4 modes: `search`, `comments`, `profile`, `user-posts`
- Handles parallel image downloading (5 concurrent workers)
- Manages directory structure automatically

**Configuration Loading**:
- Inline function in `xhs_scraper.py` (no external dependency)
- Reads from `pipeline_config.json` for non-sensitive settings
- Reads from `.env` for API credentials
- Graceful fallback to defaults if files missing

### Data Flow
```
User Query → Apify Actor API → Raw JSON Response →
Parse Results → Extract Image URLs → Parallel Downloads →
Save to data/YYYYMMDD/query_name/[scraped|images]/
```

### Directory Structure

Each scrape creates a timestamped directory:
```
data/YYYYMMDD/query_name/
  ├── scraped/    # Raw JSON from Apify
  │   └── search_20241007_123456.json
  └── images/     # Downloaded images
      └── {post_id}_{index}_{title}.jpg
```

Logs are saved separately:
```
logs/
  └── xhs_20241007.log
```

### Dependencies

**Runtime (3 packages):**
- `apify-client>=1.6.0` - Apify Actor API wrapper
- `requests>=2.31.0` - HTTP library for image downloads
- `python-dotenv>=1.0.0` - Environment variable loading

**Dev (optional):**
- `black` - Code formatting
- `ruff` - Linting

### Configuration Files

**`.env`** (secrets - never commit to git):
```bash
APIFY_API_TOKEN=your_token_here
APIFY_ACTOR_ID=watk8sVZNzd40UtbQ
WEB_PASSWORD=your_team_password_here

# Optional LLM keys for future analysis features
OPENAI_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
MOONSHOT_API_KEY=your_key_here
```

**`pipeline_config.json`** (settings - safe to commit):
```json
{
  "pipeline_settings": {
    "default_max_items": 30,
    "default_max_downloads": 50,
    "request_delay": 0.5,
    "max_retries": 3,
    "timeout": 10,
    "rate_limit_delay": 2
  }
}
```

**`.env.example`** (template for new users):
- Shows required environment variables
- Safe to commit as documentation

## Key Implementation Details

### Image Downloading
- Uses `ThreadPoolExecutor` with 5 concurrent workers
- Rate limiting via `REQUEST_DELAY` (default: 0.5s between downloads)
- Automatic retry logic for failed downloads
- Skips already-downloaded files to avoid duplicates
- Saves with descriptive filenames: `{post_id}_{index}_{title}.jpg`

### Error Handling
- Graceful degradation if config files missing (falls back to defaults)
- Comprehensive logging to `logs/` directory with daily rotation
- User-friendly error messages for common issues (missing API token, network errors)
- Per-image error tracking (logs failures without stopping entire batch)

### CLI Interface
- Subcommand-based design: `search`, `comments`, `profile`, `user-posts`, `config`
- Argparse for argument parsing with help text
- Consistent option naming across commands (`--max-items`, `--download`, etc.)
- Optional arguments with sensible defaults

### API Integration
- Uses Apify's Xiaohongshu Actor (`watk8sVZNzd40UtbQ`)
- Supports all actor modes via `mode` parameter
- Handles pagination and rate limiting
- Respects Apify API quotas and throttling

## Web Interface

### How It Works

1. **Password Protection**: User enters password → SHA-256 hash verified client-side
2. **Search Form**: User configures search parameters (keywords, max items, download options)
3. **Trigger Workflow**: Frontend calls GitHub Actions API to start workflow
4. **Monitor Progress**: Polls workflow status every 5 seconds
5. **Download Results**: Provides link to download artifacts (JSON + images)
6. **Audit Log**: Auto-updated after each run with statistics

### Password Management

**Current password:** `IC@XHS_scrape202510` (stored in `.env`)

**To change:**
```bash
# 1. Edit .env
nano .env  # Change WEB_PASSWORD value

# 2. Update hash in docs/app.js
python update_password.py

# 3. Commit and push
git add .env docs/app.js
git commit -m "Update web password"
git push
```

**Security notes:**
- Password is hashed (SHA-256) and verified client-side
- Not cryptographically secure (can be bypassed by determined users)
- Suitable for internal team use, not sensitive data
- All API keys stored securely in GitHub Secrets

### Audit Log

**Location:** `docs/audit.json` (publicly accessible)

**Auto-logged after each scrape:**
- Timestamp (UTC)
- Keywords searched
- Configuration (max items, download settings)
- Actual results (posts scraped, images downloaded)
- Success/failure status
- Link to GitHub Actions run

**Viewing:**
- Web interface: 📊 Audit Log section
- Direct URL: https://tristan-mcinnis.github.io/xhs-market-research/audit.json
- Shows summary stats: total runs, posts, images

**Privacy:** Only search queries and counts are logged - no content or images included.

## Common Tasks

### Updating the Web Password

```bash
# 1. Edit .env file
nano .env

# 2. Change WEB_PASSWORD to new value
WEB_PASSWORD="NewPassword123"

# 3. Run update script
python update_password.py

# 4. Commit changes
git add docs/app.js
git commit -m "Update web password"
git push
```

### Adding a New Scraping Mode

1. **Add method to `XHSActor` class:**
```python
def get_trending(self, max_items: int = DEFAULT_MAX_ITEMS) -> List[Dict]:
    """Get trending posts"""
    run_input = {
        "mode": "trending",
        "maxItems": max_items
    }
    # ... implementation
```

2. **Add CLI subcommand in `main()` function:**
```python
trending_parser = subparsers.add_parser('trending', help='Get trending posts')
trending_parser.add_argument('-m', '--max-items', type=int, default=DEFAULT_MAX_ITEMS)
```

3. **Update documentation** (README.md, this file)

### Modifying Default Settings

Edit `pipeline_config.json`:
```json
{
  "pipeline_settings": {
    "default_max_items": 50,      // Changed from 30
    "request_delay": 1.0,          // Slower for stricter rate limiting
    "timeout": 15                  // Longer timeout for slow networks
  }
}
```

Changes take effect immediately on next run (no restart needed).

### Debugging

**Check logs:**
```bash
tail -f logs/xhs_$(date +%Y%m%d).log
```

**Enable verbose logging** (modify in `xhs_scraper.py`):
```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    # ...
)
```

**Test configuration:**
```bash
python xhs_scraper.py config
```

## Best Practices

### Security
- **Never commit `.env`** - It contains API credentials (already in `.gitignore`)
- Always use `.env.example` as template for new setups
- Keep secrets in `.env`, settings in `pipeline_config.json`
- Rotate API tokens periodically
- Don't share API tokens in issue reports or documentation

### Code Style
- Line length: 100 characters max
- Use type hints for function signatures
- Document complex logic with inline comments
- Keep functions focused and single-purpose
- Prefer explicit over implicit (clear variable names)

### Git Workflow
- Use descriptive commit messages (what and why)
- Reference issue numbers if applicable (#123)
- Keep commits atomic (one logical change per commit)
- Don't commit generated data (`data/`, `logs/`)
- Always include Co-Authored-By for Claude Code contributions

### Data Management
- Results are timestamped automatically
- Keep `data/` directory gitignored
- Clean old scrapes periodically to save space
- Archive important datasets separately

## Troubleshooting

### Common Errors

**"API token not configured"**
```
Error: Apify API token not configured
```
→ Set `APIFY_API_TOKEN` in `.env` file
→ Get token from: https://console.apify.com/account/integrations

**"No module named apify_client"**
```
ModuleNotFoundError: No module named 'apify_client'
```
→ Run `./setup.sh` or `pip install -r requirements.txt`
→ Ensure you're using the correct Python environment

**Rate limiting errors**
```
429 Too Many Requests
```
→ Increase `request_delay` in `pipeline_config.json`
→ Reduce `default_max_items` to make smaller requests
→ Check Apify account quota/limits

**Images not downloading**
```
✗ Failed: {filename}
```
→ Check `logs/` for network errors
→ Verify Xiaohongshu accessibility (not blocked in your region)
→ Check internet connection
→ Try reducing parallel workers (edit `ThreadPoolExecutor(max_workers=5)`)

**"Actor not found"**
```
Actor with ID '...' was not found
```
→ Verify `APIFY_ACTOR_ID` in `.env` matches the Xiaohongshu actor
→ Check if actor is still active on Apify platform
→ Default should be: `watk8sVZNzd40UtbQ`

**Empty results**
```
Found 0 posts
```
→ Check if query is too specific
→ Verify Xiaohongshu has content for that query
→ Try different keywords or broader search terms

### Performance Issues

**Slow downloads**
→ Check network connection speed
→ Reduce `max_workers` in ThreadPoolExecutor
→ Increase `timeout` in `pipeline_config.json`

**High memory usage**
→ Reduce `default_max_items` to process in smaller batches
→ Don't download images for large scrapes (omit `--download` flag)

## Project Structure

```
xhs-scrape-test/
├── xhs_scraper.py          # Main scraper (single file)
├── pipeline_config.json    # Non-sensitive settings
├── requirements.txt        # Python dependencies (3 packages)
├── .env                    # API credentials (gitignored)
├── .env.example            # Template for .env
├── setup.sh / setup.bat    # Dependency installers
├── README.md               # User documentation
├── CLAUDE.md               # This file (developer guide)
├── prompts.md              # Reference documentation
├── data/                   # Output directory (gitignored)
│   └── YYYYMMDD/
│       └── query_name/
│           ├── scraped/
│           └── images/
└── logs/                   # Log files (gitignored)
    └── xhs_YYYYMMDD.log
```

## Extending the Scraper

### Adding Analysis Features

If you need to add analysis capabilities later:

1. **Install additional dependencies:**
```bash
pip install openai pandas numpy scikit-learn
```

2. **Add to requirements.txt:**
```txt
openai>=1.0.0
pandas>=2.1.0
numpy>=1.26.0
```

3. **Create analysis module:**
```python
# analysis.py
def analyze_images(image_dir: Path):
    """Analyze scraped images"""
    # Your analysis logic here
    pass
```

4. **Integrate with scraper:**
```python
# In xhs_scraper.py
if args.analyze:
    from analysis import analyze_images
    analyze_images(scraper.images_dir)
```

### Integration with Other Tools

**Export to CSV:**
```python
import pandas as pd
import json

with open('data/20241007/query/scraped/search_*.json') as f:
    data = json.load(f)
    df = pd.DataFrame(data)
    df.to_csv('export.csv', index=False)
```

**Send to database:**
```python
import sqlite3

conn = sqlite3.connect('xhs_data.db')
# Insert scraped data into database
conn.commit()
```

## Development Tips

### Testing Changes

1. **Test with small queries first:**
```bash
python xhs_scraper.py search "test" --max-items 5
```

2. **Check logs for errors:**
```bash
cat logs/xhs_$(date +%Y%m%d).log | grep ERROR
```

3. **Verify output structure:**
```bash
tree data/ -L 3
```

### Code Modification Workflow

1. **Make changes to `xhs_scraper.py`**
2. **Format code:** `black xhs_scraper.py --line-length 100`
3. **Check linting:** `ruff check xhs_scraper.py`
4. **Test functionality:** Run scraper with test query
5. **Commit changes:** Use descriptive commit message
6. **Push to GitHub**

### Adding New Features Checklist

- [ ] Implement feature in `xhs_scraper.py`
- [ ] Add CLI arguments if needed
- [ ] Update `README.md` with usage examples
- [ ] Update this file (`CLAUDE.md`) with implementation details
- [ ] Test with various inputs
- [ ] Check error handling
- [ ] Review logging output
- [ ] Format and lint code
- [ ] Commit and push

## Resources

- **Apify Console:** https://console.apify.com/
- **Apify Documentation:** https://docs.apify.com/
- **Xiaohongshu Actor:** https://apify.com/watk8sVZNzd40UtbQ
- **Python Requests:** https://requests.readthedocs.io/
- **Dotenv:** https://github.com/theskumar/python-dotenv

## Support

For issues or questions:
1. Check this documentation first
2. Review logs in `logs/` directory
3. Try test queries with `--max-items 5`
4. Check Apify Console for quota/issues
5. Open GitHub issue with logs and error messages

---

*This scraper provides a clean foundation for Xiaohongshu data collection that can be extended as needed.*
