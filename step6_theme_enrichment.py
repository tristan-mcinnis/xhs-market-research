#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cluster Theme Enrichment using GPT-5-mini
Generates rich, detailed themes from clustering results
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
from config_loader import get_config

# -----------------------------
# Config
# -----------------------------
# Load configuration
config = get_config()

# API configuration
MODEL = config.get_api_config('openai_model', 'gpt-5-mini')
MAX_OUTPUT_TOKENS = 1500
RETRY_MAX_OUTPUT_TOKENS = 2000
REASONING_EFFORT = config.get_api_config('openai_reasoning_effort', 'medium')
VERBOSITY = config.get_api_config('openai_verbosity', 'medium')

# -----------------------------
# Helpers (from semiotic_analysis.py)
# -----------------------------

def _collect_texts_from_obj(obj) -> List[str]:
    texts: List[str] = []
    if isinstance(obj, dict):
        if isinstance(obj.get("text"), str):
            texts.append(obj["text"])
        for v in obj.values():
            texts.extend(_collect_texts_from_obj(v))
    elif isinstance(obj, list):
        for it in obj:
            texts.extend(_collect_texts_from_obj(it))
    return texts

def extract_output_text(resp, debug_path=None) -> str:
    # 1) Straight path
    text = getattr(resp, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    # 2) Walk typed objects
    output = getattr(resp, "output", None)
    collected: List[str] = []
    if isinstance(output, list):
        for item in output:
            contents = getattr(item, "content", None)
            if isinstance(contents, list):
                for c in contents:
                    t = getattr(c, "text", None)
                    if isinstance(t, str) and t.strip():
                        collected.append(t.strip())
    if collected:
        return "\n".join(collected).strip()
    # 3) Raw JSON traversal
    try:
        raw_json = resp.model_dump_json()
        if debug_path:
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(raw_json)
        parsed = json.loads(raw_json)
        texts = _collect_texts_from_obj(parsed)
        merged = "\n".join([t for t in texts if t and t.strip()]).strip()
        if merged:
            return merged
    except Exception:
        s = str(resp)
        if debug_path:
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(s)
        return s
    return ""

def call_responses(client: OpenAI, input_text: str, max_tokens: int):
    return client.responses.create(
        model=MODEL,
        input=input_text,
        max_output_tokens=max_tokens,
        reasoning={"effort": REASONING_EFFORT},
        text={"verbosity": VERBOSITY},
    )

# -----------------------------
# Theme Generation
# -----------------------------

def load_cluster_data(cluster_dir: Path, analysis_dir: Path) -> Dict[int, Dict[str, Any]]:
    """Load cluster assignments and original analyses"""

    # Load cluster CSV
    clusters_df = pd.read_csv(cluster_dir / "clusters.csv")

    # Load cluster summary
    with open(cluster_dir / "clusters_summary.md", "r", encoding="utf-8") as f:
        summary_text = f.read()

    # Load original analyses for each cluster
    cluster_data = {}

    for cluster_id in clusters_df['cluster_id'].unique():
        cluster_items = clusters_df[clusters_df['cluster_id'] == cluster_id]

        # Collect analyses for this cluster
        analyses = []
        for _, row in cluster_items.iterrows():
            json_path = Path(row['path'])
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    analyses.append({
                        'filename': data.get('filename', ''),
                        'analysis': data.get('analysis', ''),
                        'is_exemplar': row.get('is_exemplar', False)
                    })

        cluster_data[cluster_id] = {
            'size': len(cluster_items),
            'analyses': analyses,
            'exemplars': [a for a in analyses if a['is_exemplar']]
        }

    return cluster_data, summary_text

def generate_rich_theme(client: OpenAI, cluster_id: int, cluster_info: Dict, out_dir: Path) -> Dict[str, Any]:
    """Generate rich theme for a single cluster using GPT-5-mini"""

    # Prepare cluster content
    analyses_sample = cluster_info['analyses'][:10]  # Take up to 10 samples
    exemplar = cluster_info['exemplars'][0] if cluster_info['exemplars'] else None

    # Build analysis snippets
    snippets = []
    for a in analyses_sample:
        if a['analysis']:
            # Take first 200 chars of each analysis
            snippet = a['analysis'][:200] + "..." if len(a['analysis']) > 200 else a['analysis']
            snippets.append(f"- {snippet}")

    cluster_content = f"""
Cluster {cluster_id} (n={cluster_info['size']} items)

EXEMPLAR ANALYSIS:
{exemplar['analysis'] if exemplar else 'No exemplar available'}

SAMPLE ANALYSES FROM THIS CLUSTER:
{chr(10).join(snippets[:7])}
"""

    # Get prompts from config
    system_prompt = config.get_prompt('step6_theme_enrichment', 'theme_generation_system')
    prompt_template = config.get_prompt(
        'step6_theme_enrichment',
        'theme_generation_prompt_template',
        cluster_content=cluster_content
    )

    full_prompt = f"{system_prompt}\n\n{prompt_template}"

    try:
        # First attempt
        resp = call_responses(client, full_prompt, MAX_OUTPUT_TOKENS)
        debug_path = out_dir / f"debug_theme_{cluster_id}.json"
        theme_text = extract_output_text(resp, debug_path=debug_path)

        # Retry if needed
        status = getattr(resp, "status", None)
        inc = getattr(resp, "incomplete_details", None)
        inc_reason = getattr(inc, "reason", None) if inc else None

        if (status == "incomplete" and inc_reason == "max_output_tokens") or not theme_text.strip():
            resp2 = call_responses(client, full_prompt, RETRY_MAX_OUTPUT_TOKENS)
            debug_path2 = out_dir / f"debug_theme_{cluster_id}_retry.json"
            text2 = extract_output_text(resp2, debug_path=debug_path2)
            if text2.strip():
                theme_text = text2

        usage = getattr(resp, "usage", None)
        tokens_used = getattr(usage, "total_tokens", 0) if usage else 0

        return {
            'cluster_id': cluster_id,
            'theme': theme_text,
            'tokens_used': tokens_used,
            'timestamp': datetime.now().isoformat(),
            'item_count': cluster_info['size']
        }

    except Exception as e:
        return {
            'cluster_id': cluster_id,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def generate_synthesis(client: OpenAI, themes: List[Dict], out_dir: Path) -> str:
    """Generate overall synthesis of all themes"""

    themes_text = "\n\n---\n\n".join([
        f"CLUSTER {t['cluster_id']}:\n{t['theme']}"
        for t in themes if 'theme' in t
    ])

    # Get synthesis prompt from config
    synthesis_prompt = config.get_prompt(
        'step6_theme_enrichment',
        'synthesis_prompt_template',
        theme_count=len(themes),
        themes_text=themes_text
    )

    try:
        resp = call_responses(client, synthesis_prompt, 1500)
        debug_path = out_dir / "debug_synthesis.json"
        return extract_output_text(resp, debug_path=debug_path)
    except Exception as e:
        return f"Error generating synthesis: {e}"

# -----------------------------
# Main
# -----------------------------

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate rich themes from cluster analysis using GPT-5-mini")
    parser.add_argument("--cluster-dir", default="./clusters_step2", help="Directory with clustering results")
    parser.add_argument("--analysis-dir", default="./semiotic_analysis_results", help="Directory with original analyses")
    parser.add_argument("--output-dir", default="./enriched_themes", help="Output directory")
    parser.add_argument("--api-key", default=None, help="OpenAI API key")
    parser.add_argument("--synthesize", action="store_true", help="Generate overall synthesis")
    args = parser.parse_args()

    # Setup
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set. Provide --api-key or set env var.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    cluster_dir = Path(args.cluster_dir)
    analysis_dir = Path(args.analysis_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading cluster data...")
    cluster_data, summary = load_cluster_data(cluster_dir, analysis_dir)

    print(f"Found {len(cluster_data)} clusters to analyze")
    print("=" * 60)

    themes = []
    total_tokens = 0

    # Generate theme for each cluster
    for cluster_id in sorted(cluster_data.keys()):
        print(f"\nGenerating rich theme for Cluster {cluster_id}...")
        print(f"  Items in cluster: {cluster_data[cluster_id]['size']}")

        theme_result = generate_rich_theme(client, cluster_id, cluster_data[cluster_id], out_dir)
        themes.append(theme_result)

        if 'error' in theme_result:
            print(f"  ✗ Error: {theme_result['error']}")
        else:
            tokens = theme_result.get('tokens_used', 0)
            total_tokens += tokens
            print(f"  ✓ Theme generated ({tokens} tokens)")

            # Save individual theme
            theme_path = out_dir / f"theme_cluster_{cluster_id}.md"
            with open(theme_path, "w", encoding="utf-8") as f:
                f.write(f"# Cluster {cluster_id} Theme Analysis\n\n")
                f.write(f"**Items in cluster:** {theme_result['item_count']}\n\n")
                f.write(theme_result['theme'])

        time.sleep(2)  # Rate limiting

    # Save all themes (convert numpy types to Python types for JSON serialization)
    all_themes_path = out_dir / f"all_themes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Convert numpy int64 to regular int for JSON serialization
    themes_json = []
    for theme in themes:
        theme_dict = {}
        for k, v in theme.items():
            if hasattr(v, 'item'):  # numpy type
                theme_dict[k] = int(v) if 'int' in str(type(v)) else float(v)
            else:
                theme_dict[k] = v
        themes_json.append(theme_dict)

    with open(all_themes_path, "w", encoding="utf-8") as f:
        json.dump(themes_json, f, ensure_ascii=False, indent=2)

    # Generate synthesis if requested
    if args.synthesize:
        print("\nGenerating overall synthesis...")
        synthesis = generate_synthesis(client, themes, out_dir)

        synthesis_path = out_dir / f"synthesis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(synthesis_path, "w", encoding="utf-8") as f:
            f.write("# Thematic Synthesis: Xiaohongshu Intimate Wellness Content\n\n")
            f.write(synthesis)

        print(f"  ✓ Synthesis saved to: {synthesis_path}")

    # Create combined report
    report_path = out_dir / "enriched_themes_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Enriched Cluster Themes Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total clusters analyzed: {len(themes)}\n")
        f.write(f"Total tokens used: {total_tokens:,}\n\n")
        f.write("---\n\n")

        for theme in themes:
            if 'theme' in theme:
                f.write(f"## Cluster {theme['cluster_id']}\n\n")
                f.write(f"**Items:** {theme['item_count']}\n\n")
                f.write(theme['theme'])
                f.write("\n\n---\n\n")

    print("\n" + "=" * 60)
    print("✅ Theme enrichment complete!")
    print(f"📊 Clusters analyzed: {len(themes)}")
    print(f"💰 Total tokens used: {total_tokens:,}")
    print(f"📁 Results saved to: {out_dir}")
    print(f"   - Individual themes: theme_cluster_*.md")
    print(f"   - Combined report: enriched_themes_report.md")
    if args.synthesize:
        print(f"   - Synthesis: synthesis_*.md")

if __name__ == "__main__":
    main()