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

#### Single Keyword (Original)
```bash
# Basic usage (10 posts)
python main.py --keyword "杜蕾斯 口味"

# Scrape more posts
python main.py --keyword "Galenic" --posts 50
```

#### Multiple Keywords (New)
```bash
# Scrape multiple keywords separately
python scrape_multi.py "杜蕾斯" "杰士邦" "冈本" --posts 20

# Scrape and combine for unified analysis
python scrape_multi.py "杜蕾斯" "口味" "巧克力" --posts 15 --combine

# Scrape related searches combined
python scrape_multi.py "杜蕾斯 口味" "杜蕾斯 巧克力" --posts 10 --combine
```

### 4. Analyze with Aggregate Themes

#### Single Folder Analysis
```bash
# Analyze latest scrape with thematic analysis
python analyze.py --latest --themes --semiotics --openai

# Full marketing analysis preset
python analyze.py --latest --preset marketing_full --openai
```

#### Multi-Folder Cross-Analysis (New)
```bash
# Analyze multiple folders together interactively
python analyze_multi.py

# Analyze specific folders for cross-query insights
python analyze_multi.py --folders "杜蕾斯" "杰士邦" --themes --brand

# Analyze a combined folder
python analyze_multi.py --folders "combined_3_keywords" --preset marketing_full
```

### 5. View Results

```bash
# View formatted analysis results
python view_analysis.py

# Or check the generated reports in:
# data/downloaded_content/YYYYMMDD/keyword/aggregate_analysis_report.md
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

## Search Approaches Explained

### Single Query (AND Logic)
```bash
python main.py --keyword "杜蕾斯 口味"
```
- Searches for posts containing BOTH "杜蕾斯" AND "口味"
- Results: Posts specifically about Durex flavors

### Multiple Separate Queries
```bash
python scrape_multi.py "杜蕾斯" "口味" "巧克力" --posts 20
```
- Runs 3 separate searches
- Creates 3 folders with different results
- Analyze each separately or together

### Multiple Combined Queries
```bash
python scrape_multi.py "杜蕾斯" "口味" --posts 20 --combine
```
- Runs separate searches but combines results
- Single folder for unified analysis
- Good for comparing different aspects

## Example Workflows

### Workflow 1: Single Brand Deep Dive
```bash
# 1. Scrape content about a brand
python main.py --keyword "科兰黎" --posts 20

# 2. Run comprehensive analysis
python analyze.py --latest --themes --semiotics --innovation --openai

# 3. View formatted results
python view_analysis.py
```

### Workflow 2: Competitive Analysis
```bash
# 1. Scrape multiple competitors
python scrape_multi.py "杜蕾斯" "杰士邦" "冈本" --posts 30 --combine

# 2. Run cross-brand analysis
python analyze_multi.py --folders "杜蕾斯_杰士邦_冈本" --preset competitive --brand

# 3. Results show competitive insights across brands
```

### Workflow 3: Topic Exploration
```bash
# 1. Scrape related topics
python scrape_multi.py "避孕套 口味" "安全套 巧克力" "情趣用品 果味" --posts 15 --combine

# 2. Analyze for market trends
python analyze.py --keyword "combined_3_keywords" --trends --innovation
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