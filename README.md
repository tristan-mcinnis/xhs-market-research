# Xiaohongshu Content Scraper & Market Research Analyzer

A comprehensive scraping and analysis tool for Xiaohongshu (Little Red Book) content, designed for large-scale market research and consumer insights. Features both text AND visual analysis across hundreds of posts to identify patterns, trends, and cultural insights.

## 🆕 What's New

- **Scale Scraping**: New `scrape_scale.py` collects 100-200+ posts per query (vs 10-50 before)
- **Visual Analysis**: New `analyze_enhanced.py` analyzes images alongside text using GPT-4o-mini vision
- **Flexible Queries**: Removed all hardcoded content - works for ANY market research topic
- **Workaround Tools**: `scrape_with_retry.py` handles Apify timeouts with retry logic
- **Query Files**: Load multiple queries from text files for batch processing
- **Combined Analysis**: Merge multiple queries into unified analysis folders

## Key Features

- **Scale Scraping**: Collect 100-200+ posts per query for statistically meaningful insights
- **Visual + Text Analysis**: Analyzes both images and text content using vision-capable LLMs
- **Flexible Queries**: Works for ANY market research topic - beauty, tech, food, fashion, etc.
- **Multi-LLM Support**: OpenAI (with vision), Gemini (with vision), DeepSeek, and Kimi providers
- **Deep Market Research**: Thematic analysis, semiotics, consumer psychology, and innovation opportunities
- **Workaround Tools**: Handles Apify timeouts with retry logic and cached data fallback

## Quick Start

### 1. Setup

```bash
# Clone the repository
git clone [your-repo-url]
cd xhs-scraper

# Install dependencies (using UV for speed)
./setup.sh

# Or using pip
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file:

```bash
# Required for scraping
APIFY_API_TOKEN="your_apify_token"

# LLM Providers (add the ones you want to use)
OPENAI_API_KEY="your_openai_key"
GEMINI_API_KEY="your_gemini_key"
DEEPSEEK_API_KEY="your_deepseek_key"
MOONSHOT_API_KEY="your_moonshot_key"  # For Kimi
```

### 3. Using the Unified CLI

The new unified `xhs` command provides all functionality through clear subcommands:

#### 🎯 Interactive Mode (Recommended for Beginners)
```bash
# Launch interactive mode - guides you through the entire process
./xhs.py interactive

# Or use interactive mode for specific tasks
./xhs.py scrape --interactive
./xhs.py analyze --interactive
```

#### 📊 Scraping Content
```bash
# Basic scraping
./xhs.py scrape "keyword1" "keyword2" --posts 50

# Large-scale scraping (100-200 posts per query)
./xhs.py scrape "口红" --posts 200 --scale

# Multiple brands with combination
./xhs.py scrape "完美日记" "花西子" "橘朵" --posts 100 --combine makeup_brands

# Load keywords from file
./xhs.py scrape --file keywords.txt --posts 150 --scale

# With retry logic for timeouts
./xhs.py scrape "杜蕾斯" --posts 100 --retry --retries 3
```

#### 🔍 Analyzing Content
```bash
# Analyze latest scraped content with a preset
./xhs.py analyze --latest --preset marketing_full

# Analyze with specific analysis types and images
./xhs.py analyze --latest --themes --brand --innovation --images --max-images 30

# Analyze specific folder
./xhs.py analyze --dir data/20240101/keyword --themes --semiotics

# Choose LLM provider
./xhs.py analyze --latest --preset cultural_deep --provider openai
```

#### 📋 Listing Available Options
```bash
# List available scraped data
./xhs.py list data

# List analysis presets
./xhs.py list presets

# List analysis types
./xhs.py list types
```

#### Analysis Output Locations

| Search Method | Output Location |
|--------------|-----------------|
| Single keyword | `data/YYYYMMDD/keyword/aggregate_analysis.json` |
| Combined (--combine) | `data/YYYYMMDD/combined_folder/aggregate_analysis.json` |
| Multiple separate | `data/YYYYMMDD/cross_analysis_folders.json` |

### 4. View Results

Results are automatically saved with each analysis:
- **JSON Results**: `data/YYYYMMDD/keyword/analysis_TIMESTAMP.json`
- **Markdown Report**: `data/YYYYMMDD/keyword/analysis_report_TIMESTAMP.md`

In interactive mode, you'll be prompted to view results immediately after analysis.

## Analysis Types

The analyzer performs **aggregate-level analysis** across all posts to identify patterns:

- `--themes`: Deep thematic analysis with 4-5 detailed themes
- `--semiotics`: Cultural codes, signs, symbols, and meanings
- `--psychology`: Consumer psychology and behavioral triggers
- `--brand`: Brand positioning and perception analysis
- `--innovation`: Product innovation opportunities
- `--trends`: Emerging trends and cultural movements
- `--engagement`: Virality and engagement factors

### Analysis Presets

Combine multiple analysis types with presets:

- `marketing_full`: Comprehensive marketing analysis
- `cultural_deep`: Deep cultural and semiotic analysis
- `influencer_audit`: Influencer effectiveness evaluation
- `trend_research`: Trend identification and analysis

## Unified CLI Commands

The new `xhs.py` consolidates all functionality into a single, intuitive interface:

### Main Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `scrape` | Scrape content from Xiaohongshu | `./xhs.py scrape "keyword" --posts 100` |
| `analyze` | Analyze scraped content | `./xhs.py analyze --latest --preset marketing_full` |
| `list` | List data, presets, or analysis types | `./xhs.py list presets` |
| `interactive` | Guided interactive mode | `./xhs.py interactive` |
| `help` | Show help information | `./xhs.py help` |

### Key Features

- **Interactive Mode**: Step-by-step guidance for both scraping and analysis
- **Flexible Scraping**: Automatic selection of appropriate scraper (scale, retry, multi)
- **Analysis Presets**: Quick access to pre-configured analysis combinations
- **Unified Interface**: All functionality through one command with clear subcommands

## Output Structure

```
data/
├── downloaded_content/
│   └── YYYYMMDD/                    # Date of scraping
│       └── keyword/                 # Search term
│           ├── post_id_1/           # Individual posts
│           │   ├── image_*.webp     # Downloaded images
│           │   └── metadata.json    # Post metadata
│           ├── raw_scraper_results.json      # Raw Apify data
│           ├── aggregate_analysis.json       # Text-only analysis
│           ├── enhanced_analysis.json        # Text + visual analysis
│           └── aggregate_analysis_report.md  # Formatted report
└── example_queries/                 # Query templates
    ├── condom_research.txt
    ├── makeup_brands.txt
    └── coffee_war.txt
```

## Search & Analysis Decision Tree

### 🤔 Which Tool Should I Use?

```
Start with: python search.py or python query_builder.py

Then choose your analysis based on what you scraped:
```

| What You Did | What You Got | How to Analyze |
|-------------|--------------|----------------|
| Single search | One folder | `python analyze.py --latest` |
| Multiple with `--combine` | One combined folder | `python analyze.py --latest` |
| Multiple without combine | Multiple folders | `python analyze_multi.py` |
| Topic + variations | Combined folder | `python analyze.py --latest` |
| Competitor comparison | Separate or combined | Use `analyze_multi.py` for cross-brand insights |

### Search Approaches Explained

#### Single Query (AND Logic)
```bash
python main.py --keyword "杜蕾斯 口味"
```
- Searches for posts containing BOTH "杜蕾斯" AND "口味"
- Results: Posts specifically about Durex flavors
- Analysis: `python analyze.py --latest`

#### Multiple Separate Queries
```bash
python scrape_multi.py "杜蕾斯" "口味" "巧克力" --posts 20
```
- Runs 3 separate searches
- Creates 3 folders with different results
- Analysis: `python analyze_multi.py` for cross-query insights

#### Multiple Combined Queries
```bash
python scrape_multi.py "杜蕾斯" "口味" --posts 20 --combine
```
- Runs separate searches but combines results
- Single folder for unified analysis
- Analysis: `python analyze.py --latest`

## Example Workflows

### Workflow 1: Large-Scale Market Research (Recommended)
```bash
# 1. Create your query file
cat > my_research.txt << EOF
Brand1 product
Brand2 product
Brand3 product
Generic term
EOF

# 2. Scrape at scale (100-200 posts per query)
./xhs.py scrape --file my_research.txt --posts 150 --scale --combine market_study

# 3. Analyze with visual content
./xhs.py analyze --latest --themes --innovation --images --max-images 40

# 4. Results are automatically saved and displayed
```

### Workflow 2: Quick Competitive Analysis
```bash
# 1. Scrape multiple brands directly
./xhs.py scrape "Nike" "Adidas" "李宁" "安踏" --posts 100 --combine sportswear

# 2. Run analysis with preset
./xhs.py analyze --latest --preset marketing_full --images

# 3. View competitive insights in generated report
```

### Workflow 3: Interactive Mode for Beginners
```bash
# Simply run:
./xhs.py interactive

# The CLI will guide you through:
# - Choosing to scrape or analyze
# - Entering keywords or selecting folders
# - Choosing analysis types or presets
# - Viewing results
```

### Workflow 4: When Scraper Has Timeout Issues
```bash
# Use retry flag automatically
./xhs.py scrape "your_topic" --posts 50 --retry --retries 3

# Then analyze
./xhs.py analyze --latest --themes --images
```

## LLM Providers

| Provider | Model | Image Support | Best For |
|----------|-------|--------------|----------|
| OpenAI | GPT-4o-mini | ✅ | General analysis with images |
| Gemini | 2.0 Flash | ✅ | Fast analysis with images |
| DeepSeek | DeepSeek Chat | ❌ | Cost-effective text analysis |
| Kimi | Moonshot v1 | ❌ | Chinese content analysis |

## Customization

Edit `config.yaml` to customize:
- Analysis prompts for each type
- Create custom analysis presets
- Adjust thematic frameworks
- Modify output formatting

## API Key Resources

- **Apify**: https://console.apify.com/account/integrations
- **OpenAI**: https://platform.openai.com/api-keys
- **Gemini**: https://ai.google.dev/gemini-api/docs/quickstart
- **DeepSeek**: https://platform.deepseek.com/
- **Kimi/Moonshot**: https://platform.moonshot.cn/

## Troubleshooting

### Scraper Returns 0 Posts
- **Issue**: Apify actor times out or returns empty results
- **Solution**: Use `scrape_with_retry.py` or `--use-cache` flag to work with existing data

### ImportError: MediaDownloader
- **Issue**: Module import errors
- **Solution**: Fixed - use `from modules.media_downloader import XHSMediaDownloader`

### Analysis Takes Too Long
- **Issue**: Analyzing too many images
- **Solution**: Use `--images 10` to limit image analysis, or `--no-images` to skip

### Out of Memory
- **Issue**: Processing hundreds of posts at once
- **Solution**: Reduce `--posts` parameter or process in batches

## Requirements

- Python 3.8+
- 8GB RAM recommended for image analysis
- Stable internet connection for API calls
- Apify API token (for scraping)
- At least one LLM API key (OpenAI recommended for visual analysis)

## License

Private repository - All rights reserved