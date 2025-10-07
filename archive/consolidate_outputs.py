#!/usr/bin/env python3
"""
Consolidate Pipeline Outputs
Collects all important reports from scattered directories into one consolidated folder
"""

import shutil
from pathlib import Path
import sys
from datetime import datetime

def consolidate_workflow_outputs(workflow_dir: Path):
    """Consolidate all outputs from a workflow into a single directory"""

    # Create consolidated directory
    consolidated_dir = workflow_dir / "consolidated_outputs"
    consolidated_dir.mkdir(exist_ok=True)

    # Define what to copy and where
    copy_mapping = {
        # Consumer segmentation reports
        "step6_themes/enriched_themes_report.md": "01_consumer_segments_detailed.md",
        "step6_themes/theme_cluster_0.md": "06_segment_A_details.md",
        "step6_themes/theme_cluster_1.md": "07_segment_B_details.md",
        "step6_themes/theme_cluster_2.md": "08_segment_C_details.md",

        # Market analysis
        "MARKET_INSIGHTS_REPORT.md": "02_executive_market_report.md",
        "step6_themes/synthesis_*.md": "05_market_synthesis.md",

        # Final reports
        "final_reports/custom_linkedin_pet_travel.md": "03_linkedin_ready_insights.md",
        "pipeline_report.md": "04_pipeline_execution_report.md",

        # Insights
        "step5_insights/master_codebook_*.md": "09_strategic_codebook.md",
        "step5_insights/insight_extraction_report.md": "10_insight_extraction_summary.md",

        # Visualizations
        "step7_visualizations/semiotic_atlas.png": "visual_semiotic_atlas.png",
        "step7_visualizations/trend_radar.png": "visual_trend_radar.png",
        "step7_visualizations/brand_playbook.csv": "brand_playbook.csv",
    }

    # Copy files
    copied_files = []
    missing_files = []

    for source_pattern, dest_name in copy_mapping.items():
        source_path = workflow_dir / source_pattern
        dest_path = consolidated_dir / dest_name

        # Handle wildcards
        if '*' in str(source_pattern):
            base_dir = workflow_dir / Path(source_pattern).parent
            pattern = Path(source_pattern).name

            matching_files = list(base_dir.glob(pattern))
            if matching_files:
                # Take the most recent if multiple matches
                source_file = max(matching_files, key=lambda x: x.stat().st_mtime)
                try:
                    shutil.copy2(source_file, dest_path)
                    copied_files.append(dest_name)
                except Exception as e:
                    print(f"  ⚠️  Could not copy {source_file}: {e}")
            else:
                missing_files.append(source_pattern)
        else:
            if source_path.exists():
                try:
                    shutil.copy2(source_path, dest_path)
                    copied_files.append(dest_name)
                except Exception as e:
                    print(f"  ⚠️  Could not copy {source_path}: {e}")
            else:
                missing_files.append(source_pattern)

    # Create index README
    readme_content = f"""# Consolidated Analysis Outputs

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Workflow:** {workflow_dir}

## 📁 Contents

### Executive Reports
"""

    for file in sorted([f for f in copied_files if f.startswith('0')]):
        readme_content += f"- `{file}`\n"

    readme_content += "\n### Consumer Segments\n"
    for file in sorted([f for f in copied_files if f.startswith('06') or f.startswith('07') or f.startswith('08')]):
        readme_content += f"- `{file}`\n"

    readme_content += "\n### Strategic Analysis\n"
    for file in sorted([f for f in copied_files if f.startswith('09') or f.startswith('10')]):
        readme_content += f"- `{file}`\n"

    readme_content += "\n### Visualizations\n"
    for file in sorted([f for f in copied_files if f.startswith('visual') or f.endswith('.csv')]):
        readme_content += f"- `{file}`\n"

    if missing_files:
        readme_content += f"\n## ⚠️ Missing Files\n"
        for file in missing_files:
            readme_content += f"- {file}\n"

    readme_content += f"""
## Usage Guide

1. **For Strategic Overview**: Start with `02_executive_market_report.md`
2. **For Consumer Understanding**: Review segment files (06-08)
3. **For External Communication**: Use `03_linkedin_ready_insights.md`
4. **For Implementation**: Reference `05_market_synthesis.md` and `09_strategic_codebook.md`

## Statistics
- Files consolidated: {len(copied_files)}
- Missing files: {len(missing_files)}
"""

    # Write README
    readme_path = consolidated_dir / "README.md"
    readme_path.write_text(readme_content)

    # Print summary
    print(f"\n✅ Consolidated {len(copied_files)} files to: {consolidated_dir}")
    if missing_files:
        print(f"⚠️  {len(missing_files)} files were not found")
    print(f"📝 Index created at: {readme_path}")

    return consolidated_dir

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python consolidate_outputs.py <workflow_directory>")
        print("Example: python consolidate_outputs.py data/20250918/宠物飞机")
        sys.exit(1)

    workflow_dir = Path(sys.argv[1])

    if not workflow_dir.exists():
        print(f"❌ Directory not found: {workflow_dir}")
        sys.exit(1)

    consolidate_workflow_outputs(workflow_dir)

if __name__ == "__main__":
    main()