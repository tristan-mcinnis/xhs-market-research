# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a **simplified Xiaohongshu scraper** focused solely on data collection. The analysis pipeline has been archived.

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

# Search without downloading
python xhs_scraper.py search "query" --max-items 50

# Limit image downloads
python xhs_scraper.py search "coffee" --download --max-downloads 20

# Get comments from posts
python xhs_scraper.py comments https://www.xiaohongshu.com/explore/...

# Get user profiles
python xhs_scraper.py profile https://www.xiaohongshu.com/user/profile/...

# Get posts from a user
python xhs_scraper.py user-posts https://www.xiaohongshu.com/user/profile/... --download

# Check configuration
python xhs_scraper.py config
```

### Code Quality
```bash
# Format code
black xhs_scraper.py --line-length 100

# Lint code
ruff check xhs_scraper.py
```

## Architecture Overview

### Single-File Design

The codebase consists of **one main file**:
- `xhs_scraper.py` - Complete scraper with all functionality

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

### Dependencies

**Runtime (3 packages):**
- `apify-client` - Apify Actor API wrapper
- `requests` - HTTP library for image downloads
- `python-dotenv` - Environment variable loading

**Dev (optional):**
- `black` - Code formatting
- `ruff` - Linting

### Configuration Files

**`.env`** (secrets - never commit to git):
```bash
APIFY_API_TOKEN=your_token_here
APIFY_ACTOR_ID=watk8sVZNzd40UtbQ
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
- Skips already-downloaded files

### Error Handling
- Graceful degradation if config files missing
- Comprehensive logging to `logs/` directory
- User-friendly error messages for common issues (missing API token, etc.)

### CLI Interface
- Subcommand-based design (`search`, `comments`, `profile`, `user-posts`)
- Argparse for argument parsing
- Consistent option naming across commands

## Archive

The previous 7-step analysis pipeline has been archived in `archive/`:

**Analysis Steps:**
- `step2_semiotic_analysis.py` - GPT-5-mini image analysis
- `step3_clustering.py` - Clustering with sentence embeddings
- `step4_comparative_analysis.py` - TF-IDF pattern extraction
- `step5_insight_extraction.py` - Strategic codebook generation
- `step6_theme_enrichment.py` - Thematic narratives
- `step7_visualization.py` - Charts and brand playbooks

**Orchestration:**
- `run_pipeline.py` - Pipeline coordinator
- `workflow_config.py` - State management
- `final_report_builder.py` - Report generation with Jinja2 templates

**Configuration:**
- `config_loader.py` - Old configuration loader (replaced with inline version)
- `report_templates/` - Jinja2 templates for reports

**Documentation:**
- `prompts.md` - All GPT prompts used in analysis pipeline
- `PIPELINE_UPDATES.md` - Pipeline change history

### Why Archived?

The analysis pipeline required:
- OpenAI API (GPT-5-mini) for semiotic analysis
- Heavy ML dependencies (sentence-transformers, scikit-learn, UMAP)
- Multiple processing steps and orchestration
- Significant computational resources

The current version focuses on **data collection only**, which:
- Reduces complexity (1 file vs 7+ step files)
- Minimizes dependencies (3 vs 15+ packages)
- Faster setup and easier maintenance
- Can be extended later if analysis is needed

## Common Tasks

### Adding a New Scraping Mode

1. Add a new method to `XHSActor` class
2. Configure Apify Actor input parameters
3. Add CLI subcommand in `main()` function
4. Update documentation

### Modifying Default Settings

Edit `pipeline_config.json`:
```json
{
  "pipeline_settings": {
    "default_max_items": 50,  // Changed from 30
    "request_delay": 1.0      // Slower for rate limiting
  }
}
```

### Debugging

Check logs in `logs/xhs_YYYYMMDD.log` for detailed execution history.

Enable verbose mode (if needed, modify logging level in scraper):
```python
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

### Security
- **Never commit `.env`** - It contains API credentials
- Always use `.env.example` as template
- Keep secrets in `.env`, settings in `pipeline_config.json`

### Code Style
- Line length: 100 characters (configured in `setup.cfg` for tools)
- Use type hints for function signatures
- Document complex logic with inline comments
- Keep functions focused and single-purpose

### Git Workflow
- Use descriptive commit messages
- Reference issue numbers if applicable
- Keep commits atomic (one logical change per commit)

## Troubleshooting

**"API token not configured"**
→ Set `APIFY_API_TOKEN` in `.env` file

**"No module named apify_client"**
→ Run `./setup.sh` or `pip install -r requirements.txt`

**Rate limiting errors**
→ Increase `request_delay` in `pipeline_config.json`

**Images not downloading**
→ Check `logs/` for network errors
→ Verify Xiaohongshu accessibility

**"Actor not found"**
→ Verify `APIFY_ACTOR_ID` in `.env` matches the Xiaohongshu actor

## Future Enhancements

If analysis capabilities are needed again:
1. Review `archive/` for the full pipeline
2. Restore required dependencies to `requirements.txt`
3. Copy analysis steps back to root
4. Update `pipeline_config.json` with analysis prompts
5. Set `OPENAI_API_KEY` in `.env`

For now, the scraper provides a **clean foundation** for data collection that can be extended as needed.
