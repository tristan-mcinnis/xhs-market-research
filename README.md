# Xiaohongshu (小红书) Analysis Pipeline

<img width="1184" height="864" alt="Generated Image September 18, 2025 - 10_26PM" src="https://github.com/user-attachments/assets/b87d40c5-3c33-4586-ae0e-376555b0db3e" />

A complete end-to-end workflow for scraping, analyzing, and extracting insights from Xiaohongshu content using GPT-5-mini and advanced ML techniques.

## 🚀 Quick Start

### Prerequisites

1. **Install dependencies:**
   ```bash
   ./setup.sh  # macOS/Linux (requires Python 3.12+)
   # or
   setup.bat   # Windows
   ```

2. **Configure API keys in `.env`:**
   ```env
   APIFY_API_TOKEN=your_apify_token
   OPENAI_API_KEY=your_openai_key
   ```

### Run Complete Pipeline

```bash
# Analyze any Xiaohongshu topic
python run_pipeline.py "咖啡味避孕套"

# With options
python run_pipeline.py "Thai condoms" --max-items 50 --k-max 8

# Run specific steps only
python run_pipeline.py "your query" --start-step 2 --end-step 5

# Continue from existing workflow
python run_pipeline.py --continue-workflow --start-step 4
```

## 📋 Pipeline Overview

The pipeline consists of 7 sequential steps:

1. **Step 1: XHS Scraper** (`step1_xhs_scraper.py`) - Scrapes posts and downloads images
2. **Step 2: Semiotic Analysis** (`step2_semiotic_analysis.py`) - GPT-5-mini image analysis
3. **Step 3: Clustering** (`step3_clustering.py`) - Groups similar analyses thematically
4. **Step 4: Comparative Analysis** (`step4_comparative_analysis.py`) - Compares patterns across groups
5. **Step 5: Insight Extraction** (`step5_insight_extraction.py`) - Extracts strategic insights
6. **Step 6: Theme Enrichment** (`step6_theme_enrichment.py`) - Creates detailed themes
7. **Step 7: Visualization** (`step7_visualization.py`) - Generates visual outputs

## 📁 Output Structure

All outputs are organized by date and query:

```
data/
└── YYYYMMDD/                    # Date of analysis
    └── query_name/               # Your search query
        ├── step1_scraped/        # Raw scraped data
        ├── step1_images/         # Downloaded images
        ├── step2_analyses/       # Semiotic analyses
        ├── step3_clusters/       # Clustering results
        ├── step4_comparative/    # Comparative analysis
        ├── step5_insights/       # Extracted insights
        ├── step6_themes/         # Enriched themes
        ├── step7_visualizations/ # Charts & playbook
        └── pipeline_report.md    # Summary report
```

## 📊 Key Outputs

After running, check these files:

1. **Master Codebook**: `step5_insights/master_codebook_*.md`
   - Complete strategic playbook with visual codes, cultural patterns, consumer psychology

2. **Enriched Themes**: `step6_themes/enriched_themes_report.md`
   - Detailed analysis of each thematic cluster

3. **Visualizations**: `step7_visualizations/`
   - `semiotic_atlas.png` - Semantic relationships map
   - `trend_radar.png` - Adoption vs Distinctiveness analysis
   - `brand_playbook.csv` - Strategic recommendations

## 🧾 Final Report Builder

Turn the downstream artifacts into polished deliverables without rerunning upstream steps.

```bash
# Regenerate an SCQA narrative with Markdown + DOCX
python final_report_builder.py --workflow data/20241010/coffee_flavor --template scqa --deliverable docx

# Executive memo with both formats (default)
python final_report_builder.py --workflow latest --template executive_memo

# Social-ready LinkedIn brief
python final_report_builder.py --workflow data/20241010/coffee_flavor --template linkedin_brief --deliverable md
```

### Templates & Customisation

- Templates live in `report_templates/` (`scqa.md.jinja`, `executive_memo.md.jinja`, `linkedin_brief.md.jinja`).
- Each template is registered in `pipeline_config.json > report_templates`; edit the section/asset mappings to pull in different insights, themes, or visuals.
- Add new templates by copying a Jinja file and wiring a new entry into `report_templates` (point the `template_path`, `sections`, and `assets` accordingly).
- The builder renders Markdown with Jinja2 and, if [Pandoc](https://pandoc.org/installing.html) is available, exports a `.docx` that drops cleanly into Mac Pages or Keynote workflows.

### Embedded Visuals & Asset Bundles

- Semiotic atlas, radar PNGs, and the brand playbook CSV are copied into `final_reports/<template>/<timestamp>/assets/` for direct Keynote/Pages hand-off.
- An `assets_bundle.zip` is produced alongside the report so you can AirDrop a single archive to collaborators.
- Missing files degrade gracefully—the script logs warnings yet still produces the Markdown deliverable.

### Output Structure

```
data/20241010/coffee_flavor/
└── final_reports/
    └── scqa/
        └── 20241012_153000/
            ├── report.md
            ├── report.docx        # if Pandoc is installed
            ├── report_metadata.json
            ├── assets/
            │   ├── semiotic_atlas.png
            │   ├── trend_radar.png
            │   └── brand_playbook.csv
            └── assets_bundle.zip
```

> **Tip for Mac users:** install Pandoc via `brew install pandoc` so the DOCX export is always available.

## 🔧 Configuration

### Centralized Prompts & Settings

All prompts and configuration are managed in `pipeline_config.json`:
- Edit prompts without modifying code
- Adjust API parameters (model, tokens, reasoning effort)
- Configure clustering and visualization settings

To view all prompts:
```bash
python config_loader.py
```

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

## 🎯 Common Use Cases

### Analyze a New Topic
```bash
python run_pipeline.py "luxury skincare" --max-items 100
```

### Skip Certain Steps
```bash
# Only run steps 1-3
python run_pipeline.py "your topic" --end-step 3

# Skip scraping if images exist
python run_pipeline.py "your topic" --start-step 2
```

### Run Individual Steps
```bash
# Just clustering
python step3_clustering.py \
  --input-dir "data/20250918/query/step2_analyses" \
  --out-dir "data/20250918/query/step3_clusters"

# Just visualization
python step7_visualization.py \
  --json-dir "data/20250918/query/step2_analyses" \
  --codebook "data/20250918/query/step5_insights/codebook.csv" \
  --out-dir "data/20250918/query/step7_visualizations"
```

## 💡 Tips

- Start with 20-30 items for testing
- Each GPT-5 analysis uses ~2000 tokens
- Full pipeline takes 10-20 minutes for 30 items
- Results are cumulative - you can rerun steps without losing data

## 🐛 Troubleshooting

**"API key not configured"**
→ Add keys to `.env` file

**"No module named..."**
→ Run `./setup.sh` or `pip install -r requirements.txt`

**"No codebook found"**
→ Run step 5 before step 7

**Out of memory**
→ Reduce `--max-items` or run steps individually

## 📚 Technical Details

### Core Technologies
- **Scraping**: Apify Actor infrastructure for Xiaohongshu
- **Analysis**: GPT-5-mini via OpenAI Responses API
- **ML Stack**: sentence-transformers, scikit-learn, UMAP
- **Visualization**: matplotlib, pandas

### Semiotic Analysis Structure
Each image is analyzed across 5 canonical sections:
1. **VISUAL CODES** - Aesthetic strategy, colors, composition
2. **CULTURAL MEANING** - Values/lifestyle being sold
3. **TABOO NAVIGATION** - How sensitive topics are handled
4. **PLATFORM CONVENTIONS** - Xiaohongshu-specific elements
5. **CONSUMER PSYCHOLOGY** - Core persuasion mechanisms

### Strategic Framework
The pipeline generates insights organized into:
- **Safe to Borrow** - Common patterns widely used
- **Momentum Bet** - Trending distinctive elements
- **Edge/Risky** - Unique but niche approaches
- **Watchlist** - Emerging patterns to monitor

## 🤝 Contributing

Feel free to submit issues or pull requests to improve the pipeline!

## 📄 License

For educational and research purposes only.

---

Built with ❤️ for semiotic analysis of Chinese social commerce content.
