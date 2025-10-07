# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

# Get comments from posts
python xhs_scraper.py comments https://www.xiaohongshu.com/explore/...

# Get user profiles
python xhs_scraper.py profile https://www.xiaohongshu.com/user/profile/...

# Check configuration
python xhs_scraper.py config
```

### Code Quality
```bash
# Format code
black *.py --line-length 100

# Lint code
ruff check *.py

# Run tests
python config_loader.py  # Tests config loading
```

## Architecture Overview

### Core Components

**Scraper** (`xhs_scraper.py`):
- Main scraper using Apify Actor API for Xiaohongshu data collection
- Supports multiple modes: search, comments, profiles, user posts
- Handles image downloading with parallel workers
- Manages directory structure automatically (data/YYYYMMDD/query/)

**Configuration Management** (`config_loader.py`, `pipeline_config.json`):
- Centralized API settings (Apify token, Actor ID)
- Pipeline settings (max items, delays, timeouts)
- All configuration externalized for easy modification

### Data Flow
```
Search Query → Apify Actor API → Raw JSON Data →
Extract Image URLs → Parallel Downloads → Organized Directory Structure
```

### Directory Structure
Each scrape creates a date-stamped directory:
```
data/YYYYMMDD/query_name/
  ├── scraped/    # Raw JSON from Apify
  └── images/     # Downloaded images
```

### Key Dependencies
- **Apify Client**: Xiaohongshu scraping via Actor API
- **Requests**: HTTP downloads for images
- **ThreadPoolExecutor**: Parallel image downloading
- **Python-dotenv**: Environment variable management

### Configuration Files

**`.env`** (secrets - never commit):
```bash
APIFY_API_TOKEN=your_token
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

## Archive

The previous 7-step analysis pipeline has been archived in `archive/`:
- `step2_semiotic_analysis.py` - GPT-5-mini image analysis
- `step3_clustering.py` - Clustering with embeddings
- `step4_comparative_analysis.py` - TF-IDF pattern extraction
- `step5_insight_extraction.py` - Strategic codebook generation
- `step6_theme_enrichment.py` - Thematic narratives
- `step7_visualization.py` - Charts and playbooks
- `run_pipeline.py` - Pipeline orchestrator
- `workflow_config.py` - Workflow state management
- `final_report_builder.py` - Report generation
- `report_templates/` - Jinja2 templates

For details on the archived pipeline, see `archive/PIPELINE_UPDATES.md`.

For all prompts used in the archived analysis pipeline, see `prompts.md`.
