# Xiaohongshu Content Scraper & Market Research Analyzer

A powerful two-step scraping and analysis tool for Xiaohongshu (Little Red Book) content, designed for market research and consumer insights. Features aggregate-level thematic analysis across posts to identify patterns, trends, and cultural insights.

## Key Features

- **Two-Step Scraping**: First scrapes URLs/metadata via Apify, then downloads actual media files
- **Aggregate Analysis**: Analyzes patterns across all posts from a query, not just individual posts
- **Multi-LLM Support**: OpenAI, Gemini, DeepSeek, and Kimi (Moonshot) providers
- **Deep Market Research**: Semiotic analysis, thematic clustering, consumer psychology, and innovation insights
- **Organized Output**: Content organized by date and keyword with comprehensive reports

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

#### 🎯 Interactive Mode (Recommended)
```bash
# Quick interactive search builder
python search.py

# Full-featured query builder with strategies
python query_builder.py
```

The interactive tools will:
- Guide you through search strategy selection
- Help build effective queries
- Execute the search automatically
- Suggest next analysis steps

#### Manual Mode

##### Single Keyword
```bash
# Basic usage (10 posts)
python main.py --keyword "杜蕾斯 口味"

# Scrape more posts
python main.py --keyword "Galenic" --posts 50
```

##### Multiple Keywords
```bash
# Scrape multiple keywords separately
python scrape_multi.py "杜蕾斯" "杰士邦" "冈本" --posts 20

# Scrape and combine for unified analysis
python scrape_multi.py "杜蕾斯" "口味" "巧克力" --posts 15 --combine

# Scrape related searches combined
python scrape_multi.py "杜蕾斯 口味" "杜蕾斯 巧克力" --posts 10 --combine
```

### 4. Analyze with Aggregate Themes

The analysis approach depends on how you scraped:

#### For Single Searches or Combined Folders
```bash
# If you used search.py/query_builder.py with combine, or single keyword
python analyze.py --latest --themes --semiotics --openai

# Full marketing analysis preset
python analyze.py --latest --preset marketing_full --openai

# Analyze specific combined folder
python analyze.py --keyword "杜蕾斯_口味_巧克力" --themes --innovation
```

#### For Multiple Separate Searches (Cross-Query Analysis)
```bash
# Interactive selection of folders to compare
python analyze_multi.py

# Compare specific brands/topics
python analyze_multi.py --folders "杜蕾斯" "杰士邦" --themes --brand

# Analyze all folders from today
python analyze_multi.py --folders all --preset competitive
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

## Output Structure

```
data/
├── downloaded_content/
│   └── YYYYMMDD/                    # Date of scraping
│       └── keyword/                 # Search term
│           ├── post_id_1/           # Individual posts
│           │   ├── image_*.webp
│           │   └── metadata.json
│           ├── aggregate_analysis.json       # Full analysis results
│           └── aggregate_analysis_report.md  # Formatted report
└── raw_scraper_results.json         # Raw Apify results
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

### Workflow 1: Interactive Single Brand Deep Dive
```bash
# 1. Use interactive search builder
python search.py
# Choose option 1 (single topic)
# Enter: "科兰黎 护肤"
# Posts: 30

# 2. Run comprehensive analysis
python analyze.py --latest --themes --semiotics --innovation --openai

# 3. View formatted results
python view_analysis.py
```

### Workflow 2: Interactive Competitive Analysis
```bash
# 1. Use query builder for competitive strategy
python query_builder.py
# Select: Competitive analysis
# Enter brands: 杜蕾斯, 杰士邦, 冈本
# Choose: Combine for unified analysis

# 2. Analyze combined results
python analyze.py --latest --preset marketing_full --brand

# 3. View competitive insights
python view_analysis.py
```

### Workflow 3: Cross-Query Topic Analysis
```bash
# 1. Interactive topic exploration
python search.py
# Choose option 3 (topic + variations)
# Base: "避孕套"
# Variations: "口味", "安全", "品牌", "进口"

# 2. If combined: Single analysis
python analyze.py --latest --trends --innovation

# 2. If separate: Cross-query analysis
python analyze_multi.py
# Select all folders for comparison
```

### Workflow 4: Manual Advanced Search
```bash
# 1. Scrape with specific parameters
python scrape_multi.py "杜蕾斯 口味" "杜蕾斯 泰国" "杜蕾斯 礼盒" --posts 20 --combine

# 2. Run targeted analysis
python analyze.py --keyword "杜蕾斯_口味_杜蕾斯_泰国_杜蕾斯_礼盒" --themes --cultural --engagement

# 3. Generate insights report
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

## Requirements

- Python 3.8+
- 8GB RAM recommended for image analysis
- Stable internet connection for API calls

## License

Private repository - All rights reserved