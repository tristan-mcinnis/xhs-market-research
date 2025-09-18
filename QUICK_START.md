# 🚀 Quick Start Guide

## One-Command Pipeline

Run the complete analysis pipeline for any Xiaohongshu topic:

```bash
python run_pipeline.py "咖啡味避孕套"
```

This will automatically:
1. ✅ Scrape posts and download images
2. ✅ Analyze with GPT-5 for semiotic insights
3. ✅ Cluster into themes
4. ✅ Compare patterns across groups
5. ✅ Extract strategic insights
6. ✅ Generate enriched themes
7. ✅ Create visualizations and playbook

## 📁 Output Location

All results are organized in one place:
```
data/
  └── 20250918/                     # Today's date
      └── 咖啡味避孕套/              # Your query
          ├── step1_images/         # Downloaded images
          ├── step2_analyses/       # Semiotic analyses
          ├── step3_clusters/       # Thematic clusters
          ├── step4_comparative/    # Comparative analysis
          ├── step5_insights/       # Strategic insights
          ├── step6_themes/         # Enriched themes
          ├── step7_visualizations/ # Charts & playbook
          └── pipeline_report.md    # Summary report
```

## 🎯 Common Use Cases

### Analyze a New Topic
```bash
python run_pipeline.py "Thai condoms"
```

### Analyze More Posts (Default is 30)
```bash
python run_pipeline.py "luxury skincare" --max-items 100
```

### Skip Certain Steps
```bash
# Only run steps 1-3 (scrape, analyze, cluster)
python run_pipeline.py "your topic" --end-step 3

# Skip scraping, start from analysis (if images exist)
python run_pipeline.py "your topic" --start-step 2
```

### Continue Previous Analysis
```bash
# Resume from step 4
python run_pipeline.py --continue-workflow --start-step 4
```

## 📊 Key Outputs to Check

After running, check these files:

1. **Master Codebook**: `step5_insights/master_codebook_*.md`
   - Complete strategic playbook
   - Visual codes, cultural patterns, consumer psychology

2. **Enriched Themes**: `step6_themes/enriched_themes_report.md`
   - Detailed analysis of each cluster
   - Actionable recommendations

3. **Visualizations**: `step7_visualizations/`
   - `semiotic_atlas.png` - Semantic relationships map
   - `trend_radar.png` - Adoption vs Distinctiveness
   - `brand_playbook.csv` - Strategic recommendations

4. **Pipeline Report**: `pipeline_report.md`
   - Summary of all steps
   - Success/failure status
   - Output locations

## ⚡ Quick Commands Reference

```bash
# Basic run
python run_pipeline.py "your query"

# With options
python run_pipeline.py "your query" \
  --max-items 50 \       # Scrape more posts
  --k-max 8 \            # Allow more clusters
  --start-step 1 \       # Starting point
  --end-step 7           # Ending point

# Continue workflow
python run_pipeline.py --continue-workflow --start-step 4

# Check configuration
python workflow_config.py

# Run individual step (example: just clustering)
python step3_clustering.py \
  --input-dir "data/20250918/your_query/step2_analyses" \
  --out-dir "data/20250918/your_query/step3_clusters"
```

## 🔧 Prerequisites Checklist

Before running, ensure you have:

✅ **API Keys in `.env`**:
```
APIFY_API_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here
```

✅ **Dependencies Installed**:
```bash
./setup.sh  # or: pip install -r requirements.txt
```

✅ **Python 3.12+ Activated**:
```bash
source .venv/bin/activate
```

## 💡 Tips

- Start with 20-30 items for testing
- Each GPT-5 analysis uses ~2000 tokens
- Full pipeline takes 10-20 minutes for 30 items
- Results are cumulative - you can rerun steps without losing data

## 🆘 Troubleshooting

**"API key not configured"**
→ Add keys to `.env` file

**"No module named..."**
→ Run `./setup.sh` or `pip install -r requirements.txt`

**"No codebook found"**
→ Run step 5 before step 7

**Out of memory**
→ Reduce `--max-items` or run steps individually

---

Ready? Start with:
```bash
python run_pipeline.py "your topic here"
```