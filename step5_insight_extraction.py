#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 4: Insight Extraction with GPT-5-mini
Enhanced version using GPT-5-mini for richer insight extraction

What it does
------------
- Loads analysis_*.json files from semiotic analysis
- Extracts key insights from each canonical section using GPT-5-mini
- Generates a comprehensive codebook with:
    - Key patterns and themes
    - Cultural insights
    - Strategic implications
    - Cross-cutting observations
- Outputs enriched insights in multiple formats

Dependencies
-----------
pip install pandas openai python-dotenv

Example
-------
python insight_extraction_step4_gpt5.py \
  --json-dir ./semiotic_analysis_results \
  --out-dir ./insight_outputs_gpt5 \
  --synthesize
"""

import os
import sys
import json
import time
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from config_loader import get_config

# -----------------------------
# Config
# -----------------------------
# Load configuration
config = get_config()

# API configuration
MODEL = config.get_api_config('openai_model', 'gpt-5-mini')
MAX_OUTPUT_TOKENS = config.get_api_config('openai_max_output_tokens', 1200)
RETRY_MAX_OUTPUT_TOKENS = config.get_api_config('openai_retry_max_tokens', 1800)
REASONING_EFFORT = config.get_api_config('openai_reasoning_effort', 'medium')
VERBOSITY = config.get_api_config('openai_verbosity', 'medium')

# Pipeline settings
RATE_LIMIT_DELAY = config.get_pipeline_setting('rate_limit_delay', 2)

# Canonical sections
CANON_SECTIONS = config.get_canonical_sections()

SECTION_HEADER_RE = re.compile(r"^\s*(\d+)\)\s*([A-Za-z\u4e00-\u9fff\s/]+?):\s*(.*)$")

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
# Section processing
# -----------------------------

def normalize_section_name(name: str) -> str:
    n = re.sub(r"\s+", " ", name).strip().upper()
    for k in CANON_SECTIONS:
        if k in n:
            return k
    return n

def split_sections(text: str) -> Dict[str, str]:
    """Split 'analysis' into {SECTION: text} using numbered headings."""
    parts: Dict[str, List[str]] = {}
    current = None
    for line in text.splitlines():
        m = SECTION_HEADER_RE.match(line)
        if m:
            current = normalize_section_name(m.group(2))
            parts[current] = [m.group(3).strip()]
        else:
            if current is not None:
                parts[current].append(line.strip())
    return {k: " ".join(v).strip() for k, v in parts.items() if " ".join(v).strip()}

# -----------------------------
# Data loading
# -----------------------------

def load_json_corpus(json_dir: Path) -> List[Dict]:
    rows = []
    for p in sorted(json_dir.glob("*.json")):
        # Skip combined analyses files
        if "all_analyses" in p.name:
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        # Skip if it's a list (wrong format)
        if isinstance(obj, list):
            continue
        analysis = (obj.get("analysis") or "").strip()
        if not analysis:
            continue
        sections = split_sections(analysis)
        rows.append({
            "path": str(p),
            "filename": obj.get("filename", Path(p).name),
            "analysis": analysis,
            "sections": sections,
            **{f"sec::{k}": sections.get(k, "") for k in CANON_SECTIONS},
        })
    return rows

# -----------------------------
# GPT-5 Insight Extraction
# -----------------------------

def extract_section_insights(client: OpenAI, section_name: str, section_texts: List[str], out_dir: Path) -> Dict[str, Any]:
    """Extract insights from multiple documents for a specific section"""

    # Sample up to 15 texts for the section
    sample = section_texts[:15] if len(section_texts) > 15 else section_texts

    # Build the content for analysis
    content_snippets = []
    for i, text in enumerate(sample, 1):
        snippet = text[:300] + "..." if len(text) > 300 else text
        content_snippets.append(f"Document {i}: {snippet}")

    combined_content = "\n\n".join(content_snippets)

    # Get prompt template from config and format it
    prompt = config.get_prompt(
        'step5_insight_extraction',
        'section_insights_prompt_template',
        section_name=section_name,
        doc_count=len(section_texts),
        combined_content=combined_content
    )

    try:
        # First attempt
        resp = call_responses(client, prompt, MAX_OUTPUT_TOKENS)
        debug_path = out_dir / f"debug_insights_{section_name.replace(' ', '_')}.json"
        insights_text = extract_output_text(resp, debug_path=debug_path)

        # Retry if needed
        status = getattr(resp, "status", None)
        inc = getattr(resp, "incomplete_details", None)
        inc_reason = getattr(inc, "reason", None) if inc else None

        if (status == "incomplete" and inc_reason == "max_output_tokens") or not insights_text.strip():
            resp2 = call_responses(client, prompt, RETRY_MAX_OUTPUT_TOKENS)
            debug_path2 = out_dir / f"debug_insights_{section_name.replace(' ', '_')}_retry.json"
            text2 = extract_output_text(resp2, debug_path=debug_path2)
            if text2.strip():
                insights_text = text2

        usage = getattr(resp, "usage", None)
        tokens_used = getattr(usage, "total_tokens", 0) if usage else 0

        return {
            'section': section_name,
            'insights': insights_text,
            'doc_count': len(section_texts),
            'tokens_used': tokens_used,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'section': section_name,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def generate_master_codebook(client: OpenAI, all_insights: List[Dict], out_dir: Path) -> str:
    """Generate a comprehensive codebook synthesis"""

    insights_text = "\n\n---\n\n".join([
        f"## {insight['section']}\n\n{insight['insights']}"
        for insight in all_insights if 'insights' in insight
    ])

    # Get master codebook prompt from config and format it
    synthesis_prompt = config.get_prompt(
        'step5_insight_extraction',
        'master_codebook_prompt_template',
        insights_text=insights_text
    )

    try:
        resp = call_responses(client, synthesis_prompt, 1800)
        debug_path = out_dir / "debug_master_codebook.json"
        return extract_output_text(resp, debug_path=debug_path)
    except Exception as e:
        return f"Error generating master codebook: {e}"

# -----------------------------
# Output formatting
# -----------------------------

def create_codebook_dataframe(insights: List[Dict]) -> pd.DataFrame:
    """Convert insights into a structured dataframe"""
    rows = []

    for insight in insights:
        if 'insights' not in insight:
            continue

        section = insight['section']
        text = insight['insights']

        # Extract key patterns using simple parsing
        patterns = re.findall(r'[-•]\s*([^-•\n]+)', text)

        for i, pattern in enumerate(patterns[:10]):  # Top 10 patterns per section
            rows.append({
                'section': section,
                'pattern_rank': i + 1,
                'pattern': pattern.strip(),
                'doc_count': insight['doc_count']
            })

    return pd.DataFrame(rows)

# -----------------------------
# Main
# -----------------------------

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Enhanced Insight Extraction with GPT-5-mini")
    parser.add_argument("--json-dir", required=True, help="Directory containing analysis_*.json files")
    parser.add_argument("--out-dir", default="./insight_outputs_gpt5", help="Directory to write outputs")
    parser.add_argument("--api-key", default=None, help="OpenAI API key")
    parser.add_argument("--synthesize", action="store_true", help="Generate master codebook synthesis")
    args = parser.parse_args()

    # Setup
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set. Provide --api-key or set env var.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    json_dir = Path(args.json_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading analysis corpus...")
    rows = load_json_corpus(json_dir)
    if not rows:
        print("No valid analyses found.")
        return

    print(f"Found {len(rows)} documents to analyze")
    print("=" * 60)

    # Group texts by section
    section_texts = defaultdict(list)
    for row in rows:
        for section in CANON_SECTIONS:
            text = row.get(f"sec::{section}", "")
            if text.strip():
                section_texts[section].append(text)

    # Extract insights for each section
    all_insights = []
    total_tokens = 0

    for section in CANON_SECTIONS:
        if section not in section_texts:
            continue

        print(f"\nExtracting insights for {section}...")
        print(f"  Documents with this section: {len(section_texts[section])}")

        insights = extract_section_insights(client, section, section_texts[section], out_dir)
        all_insights.append(insights)

        if 'error' in insights:
            print(f"  ✗ Error: {insights['error']}")
        else:
            tokens = insights.get('tokens_used', 0)
            total_tokens += tokens
            print(f"  ✓ Insights extracted ({tokens} tokens)")

            # Save individual section insights
            section_path = out_dir / f"insights_{section.replace(' ', '_').lower()}.md"
            with open(section_path, "w", encoding="utf-8") as f:
                f.write(f"# {section} - Insights\n\n")
                f.write(f"*Analyzed {insights['doc_count']} documents*\n\n")
                f.write(insights['insights'])

        time.sleep(RATE_LIMIT_DELAY)

    # Create structured codebook
    print("\nCreating structured codebook...")
    codebook_df = create_codebook_dataframe(all_insights)

    # Save outputs
    codebook_df.to_csv(out_dir / "codebook_patterns.csv", index=False)

    # Save all insights as JSON
    insights_path = out_dir / f"all_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(insights_path, "w", encoding="utf-8") as f:
        json.dump(all_insights, f, ensure_ascii=False, indent=2)

    # Generate master codebook if requested
    if args.synthesize:
        print("\nGenerating master codebook synthesis...")
        master_codebook = generate_master_codebook(client, all_insights, out_dir)

        master_path = out_dir / f"master_codebook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(master_path, "w", encoding="utf-8") as f:
            f.write("# Master Semiotic Codebook\n\n")
            f.write(f"*Generated from {len(rows)} Xiaohongshu analyses*\n\n")
            f.write(master_codebook)

        print(f"  ✓ Master codebook saved to: {master_path}")

    # Create combined report
    report_path = out_dir / "insight_extraction_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Insight Extraction Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"- Documents analyzed: {len(rows)}\n")
        f.write(f"- Sections processed: {len(all_insights)}\n")
        f.write(f"- Total tokens used: {total_tokens:,}\n\n")
        f.write("---\n\n")

        for insight in all_insights:
            if 'insights' in insight:
                f.write(f"## {insight['section']}\n\n")
                f.write(f"*{insight['doc_count']} documents analyzed*\n\n")
                f.write(insight['insights'])
                f.write("\n\n---\n\n")

    # Print summary statistics
    print("\n" + "=" * 60)
    print("✅ Insight extraction complete!")
    print(f"📊 Sections analyzed: {len(all_insights)}")
    print(f"📝 Total patterns extracted: {len(codebook_df)}")
    print(f"💰 Total tokens used: {total_tokens:,}")
    print(f"📁 Results saved to: {out_dir}")
    print(f"   - Section insights: insights_*.md")
    print(f"   - Pattern codebook: codebook_patterns.csv")
    print(f"   - Full report: insight_extraction_report.md")
    if args.synthesize:
        print(f"   - Master codebook: master_codebook_*.md")

if __name__ == "__main__":
    main()