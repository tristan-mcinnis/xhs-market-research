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

### 3. Scrape Content

#### 🚀 Large-Scale Scraping (100-200 posts per query)
```bash
# Single topic at scale
python scrape_scale.py "口红" --posts 200

# Multiple brands for competitive analysis
python scrape_scale.py "完美日记" "花西子" "橘朵" --posts 100 --combine makeup_brands

# From a query file
python scrape_scale.py --file example_queries/coffee_war.txt --posts 150 --combine coffee_analysis
```

#### 🛠️ If Scraper Has Timeout Issues
```bash
# Use retry logic with fallback to cached data
python scrape_with_retry.py "杜蕾斯" --posts 100

# Work with existing cached data
python scrape_with_retry.py "your_query" --use-cache

# Set up demo data from cache
python demo_with_cached.py
```

#### 🎯 Interactive Mode
```bash
# Quick interactive search builder
python search.py

# Full-featured query builder with strategies
python query_builder.py
```

#### Standard Scraping
```bash
# Basic usage
python main.py --keyword "SK-II" --posts 50

# Multiple keywords with combination
python scrape_multi.py "特斯拉" "蔚来" "小鹏" --posts 30 --combine ev_analysis
```

### 4. Analyze Content (Text + Visual)

#### 🎨 Enhanced Analysis with Image Analysis
```bash
# Analyze with visual content (recommended for comprehensive insights)
python analyze_enhanced.py --latest --themes --images 30 --openai

# Analyze specific folder with more images
python analyze_enhanced.py --keyword makeup_brands --themes --semiotics --images 50

# Skip image analysis for faster results
python analyze_enhanced.py --latest --themes --no-images
```

#### Standard Text-Only Analysis
```bash
# Quick analysis of latest scrape
python analyze.py --latest --themes --semiotics --openai

# Full marketing analysis preset
python analyze.py --latest --preset marketing_full --openai

# Cross-query analysis for multiple folders
python analyze_multi.py --folders "brand1" "brand2" --themes --brand
```

#### Analysis Output Locations

| Search Method | Output Location |
|--------------|-----------------|
| Single keyword | `data/YYYYMMDD/keyword/aggregate_analysis.json` |
| Combined (--combine) | `data/YYYYMMDD/combined_folder/aggregate_analysis.json` |
| Multiple separate | `data/YYYYMMDD/cross_analysis_folders.json` |

### 5. View Results

```bash
# View formatted analysis results
python view_analysis.py

# View specific analysis
python view_analysis.py --keyword "杜蕾斯"

# Check markdown reports directly:
# - Single/Combined: data/YYYYMMDD/keyword/aggregate_analysis_report.md
# - Cross-query: data/YYYYMMDD/cross_analysis_*.json
```

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

## Tools Overview

### Scraping Tools

| Tool | Purpose | Posts Target | Best For |
|------|---------|--------------|----------|
| `scrape_scale.py` | Large-scale collection | 100-200 per query | Production research |
| `scrape_with_retry.py` | Handles timeouts | Flexible | When Apify is unstable |
| `scrape_multi.py` | Multiple queries | 10-50 per query | Quick comparisons |
| `main.py` | Single query | 10-50 | Testing/small samples |
| `search.py` | Interactive builder | Any | User-friendly scraping |

### Analysis Tools

| Tool | Features | Visual Analysis | Use Case |
|------|----------|-----------------|----------|
| `analyze_enhanced.py` | Text + Images + Comments | ✅ Yes | Comprehensive insights |
| `analyze.py` | Text only | ❌ No | Quick text analysis |
| `analyze_multi.py` | Cross-query comparison | ❌ No | Competitive analysis |
| `view_analysis.py` | Display results | N/A | View formatted output |

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
python scrape_scale.py --file my_research.txt --posts 150 --combine market_study

# 3. Analyze with visual content
python analyze_enhanced.py --keyword market_study --themes --innovation --images 40

# 4. View results
python view_analysis.py
```

### Workflow 2: Quick Competitive Analysis
```bash
# 1. Scrape multiple brands directly
python scrape_scale.py "Nike" "Adidas" "李宁" "安踏" --posts 100 --combine sportswear

# 2. Run enhanced analysis with images
python analyze_enhanced.py --keyword sportswear --themes --brand --images 30

# 3. View competitive insights
python view_analysis.py
```

### Workflow 3: When Scraper Has Timeout Issues
```bash
# 1. Try with retry logic
python scrape_with_retry.py "your_topic" --posts 50 --retries 3

# 2. If still failing, use cached data
python scrape_with_retry.py "your_topic" --use-cache

# 3. Analyze whatever data you have
python analyze_enhanced.py --latest --themes --images 20
```

### Workflow 4: Interactive Mode for Beginners
```bash
# 1. Use interactive builder
python search.py
# Select option, enter keywords, choose combine option

# 2. Run visual + text analysis
python analyze_enhanced.py --latest --themes --semiotics --images 25

# 3. View formatted output
python view_analysis.py
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