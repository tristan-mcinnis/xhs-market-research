# XHS Semiotic Analysis Pipeline

A complete end-to-end workflow for scraping, analyzing, and extracting insights from Xiaohongshu (小红书) content.

## 📋 Pipeline Overview

The pipeline consists of 7 sequential steps, each building on the previous:

1. **Step 1: XHS Scraper** (`step1_xhs_scraper.py`)
   - Scrapes posts and images from Xiaohongshu based on keywords
   - Downloads images for analysis
   - Output: `step1_scraped/` and `step1_images/`

2. **Step 2: Semiotic Analysis** (`step2_semiotic_analysis.py`)
   - Analyzes images using GPT-5-mini for semiotic insights
   - Extracts visual codes, cultural meaning, taboo navigation patterns
   - Output: `step2_analyses/`

3. **Step 3: Clustering** (`step3_clustering.py`)
   - Groups similar analyses into thematic clusters
   - Uses embeddings and KMeans/UMAP for visualization
   - Output: `step3_clusters/`

4. **Step 4: Comparative Analysis** (`step4_comparative_analysis.py`)
   - Compares patterns across different product groups
   - Identifies distinctive vs common elements
   - Output: `step4_comparative/`

5. **Step 5: Insight Extraction** (`step5_insight_extraction.py`)
   - Extracts rich insights using GPT-5-mini
   - Generates strategic codebook
   - Output: `step5_insights/`

6. **Step 6: Theme Enrichment** (`step6_theme_enrichment.py`)
   - Creates detailed themes from clusters using GPT-5-mini
   - Generates actionable recommendations
   - Output: `step6_themes/`

7. **Step 7: Visualization** (`step7_visualization.py`)
   - Creates visual outputs (Semiotic Atlas, Trend Radar)
   - Generates brand playbook
   - Output: `step7_visualizations/`

## 🚀 Quick Start

### Prerequisites

1. Install dependencies:
   ```bash
   ./setup.sh  # macOS/Linux
   # or
   setup.bat   # Windows
   ```

2. Configure API keys in `.env`:
   ```
   APIFY_API_TOKEN=your_apify_token
   OPENAI_API_KEY=your_openai_key
   ```

### Run Complete Pipeline

```bash
# Run full pipeline for a query
python run_pipeline.py "咖啡味避孕套"

# Run with options
python run_pipeline.py "Thai condoms" --max-items 50 --k-max 8

# Run specific steps only
python run_pipeline.py "your query" --start-step 2 --end-step 5

# Continue from existing workflow
python run_pipeline.py --continue-workflow --start-step 4
```

## 📁 Directory Structure

All outputs are organized in a unified structure:

```
data/
└── YYYYMMDD/                    # Date of analysis
    └── query_name/               # Clean query name
        ├── workflow_config.json  # Workflow configuration
        ├── pipeline_report.md    # Summary report
        ├── step1_scraped/        # Raw scraped data
        ├── step1_images/         # Downloaded images
        ├── step2_analyses/       # Semiotic analyses
        ├── step3_clusters/       # Clustering results
        ├── step4_comparative/    # Comparative analysis
        ├── step5_insights/       # Extracted insights
        ├── step6_themes/         # Enriched themes
        ├── step7_visualizations/ # Visual outputs
        └── logs/                 # Process logs
```

## 🔧 Running Individual Steps

Each step can also be run independently:

### Step 1: Scraping
```bash
python step1_xhs_scraper.py search "your keywords" --max-items 30 --download
```

### Step 2: Semiotic Analysis
```bash
python step2_semiotic_analysis.py \
  --image-dir "data/YYYYMMDD/query/step1_images" \
  --output-dir "data/YYYYMMDD/query/step2_analyses" \
  --synthesize
```

### Step 3: Clustering
```bash
python step3_clustering.py \
  --input-dir "data/YYYYMMDD/query/step2_analyses" \
  --out-dir "data/YYYYMMDD/query/step3_clusters" \
  --k-min 3 --k-max 10
```

### Step 4: Comparative Analysis
```bash
python step4_comparative_analysis.py \
  --json-dir "data/YYYYMMDD/query/step2_analyses" \
  --out-dir "data/YYYYMMDD/query/step4_comparative" \
  --top-k 20
```

### Step 5: Insight Extraction
```bash
python step5_insight_extraction.py \
  --json-dir "data/YYYYMMDD/query/step2_analyses" \
  --out-dir "data/YYYYMMDD/query/step5_insights" \
  --synthesize
```

### Step 6: Theme Enrichment
```bash
python step6_theme_enrichment.py \
  --cluster-dir "data/YYYYMMDD/query/step3_clusters" \
  --analysis-dir "data/YYYYMMDD/query/step2_analyses" \
  --output-dir "data/YYYYMMDD/query/step6_themes" \
  --synthesize
```

### Step 7: Visualization
```bash
python step7_visualization.py \
  --json-dir "data/YYYYMMDD/query/step2_analyses" \
  --codebook "data/YYYYMMDD/query/step5_insights/codebook.csv" \
  --out-dir "data/YYYYMMDD/query/step7_visualizations"
```

## 📊 Key Outputs

### Semiotic Codebook
- Visual codes and their meanings
- Cultural navigation strategies
- Consumer psychology patterns
- Platform-specific conventions

### Brand Playbook
- **Safe to Borrow**: Common patterns widely used
- **Momentum Bet**: Trending distinctive elements
- **Edge/Risky**: Unique but niche approaches
- **Watchlist**: Emerging patterns to monitor

### Visualizations
- **Semiotic Atlas**: 2D map of semantic relationships
- **Trend Radar**: Adoption vs Distinctiveness scatter plot

## 🔑 Configuration

### Workflow Configuration (`workflow_config.py`)

The central configuration manages:
- Directory structure
- Query/topic tracking
- Step coordination
- Output organization

### Environment Variables

Set in `.env` file:
```bash
# Required
APIFY_API_TOKEN=your_token
OPENAI_API_KEY=your_key

# Optional
WORKFLOW_QUERY="default query"
WORKFLOW_DATE="20240918"
```

## 📝 Tips

1. **Start Small**: Begin with 20-30 items for testing
2. **Monitor Costs**: GPT-5-mini analysis uses ~2000 tokens per image
3. **Batch Processing**: The pipeline includes delays between API-heavy steps
4. **Reuse Data**: Use `--continue-workflow` to resume or reanalyze
5. **Check Outputs**: Each step generates its own report/summary

## 🐛 Troubleshooting

### Missing Dependencies
```bash
# Reinstall requirements
pip install -r requirements.txt
```

### API Errors
- Check API keys in `.env`
- Verify API quotas/limits
- Add delays between requests

### Memory Issues
- Reduce `--max-items` for initial scraping
- Process in smaller batches
- Use `--start-step` and `--end-step` to run partial pipeline

## 📚 Additional Resources

- [Xiaohongshu API Documentation](https://console.apify.com/)
- [OpenAI GPT-5 Documentation](https://platform.openai.com/docs/)
- [Sentence Transformers](https://www.sbert.net/)

## 🤝 Contributing

Feel free to submit issues or pull requests to improve the pipeline!

---

Built with ❤️ for semiotic analysis of Chinese social commerce content.