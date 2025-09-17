"""Constants used throughout the XHS Scraper"""

# Scraper modes
SCRAPE_MODE_SEARCH = "search"
SCRAPE_MODE_POST = "post_detail"

# Default values
DEFAULT_MAX_POSTS = 10
DEFAULT_RATE_LIMIT = 5  # seconds
DEFAULT_TIMEOUT = 300  # seconds
DEFAULT_RETRY_COUNT = 3

# File patterns
METADATA_FILE = "metadata.json"
RAW_RESULTS_FILE = "raw_scraper_results.json"
ANALYSIS_FILE = "aggregate_analysis.json"
SUMMARY_FILE = "search_summary.json"

# Media types
MEDIA_TYPE_IMAGE = "image"
MEDIA_TYPE_VIDEO = "video"

# Analysis defaults
DEFAULT_LLM_PROVIDER = "openai"
MAX_IMAGES_PER_ANALYSIS = 10

# Progress indicators
PROGRESS_SCRAPING = "Scraping"
PROGRESS_DOWNLOADING = "Downloading"
PROGRESS_ANALYZING = "Analyzing"