#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import base64
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from config_loader import get_config

# -----------------------------
# Config
# -----------------------------
IMAGE_DIR = "/Users/tristanmcinnis/Documents/L_Code/xhs-scrape-test/data/20250918/调味避孕套/images"
OUTPUT_DIR = "./semiotic_analysis_results"

# Load configuration
config = get_config()

# API configuration
MODEL = config.get_api_config('openai_model', 'gpt-5-mini')
MAX_OUTPUT_TOKENS = config.get_api_config('openai_max_output_tokens', 700)
RETRY_MAX_OUTPUT_TOKENS = config.get_api_config('openai_retry_max_tokens', 1100)
REASONING_EFFORT = config.get_api_config('openai_reasoning_effort', 'low')
VERBOSITY = config.get_api_config('openai_verbosity', 'low')

# Pipeline settings
RATE_LIMIT_DELAY = config.get_pipeline_setting('rate_limit_delay', 2)

# -----------------------------
# Helpers
# -----------------------------

def guess_mime(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    return "image/jpeg"

def to_data_url(image_path: str) -> str:
    mime = guess_mime(image_path)
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def _collect_texts_from_obj(obj) -> List[str]:
    texts: List[str] = []
    if isinstance(obj, dict):
        # prefer explicit text fields
        if isinstance(obj.get("text"), str):
            texts.append(obj["text"])
        for v in obj.values():
            texts.extend(_collect_texts_from_obj(v))
    elif isinstance(obj, list):
        for it in obj:
            texts.extend(_collect_texts_from_obj(it))
    return texts

def extract_output_text(resp, debug_path: Optional[Path] = None) -> str:
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

def make_multimodal_input(data_url: str, prompt: str) -> List[Dict[str, Any]]:
    # Put IMAGE FIRST, then the prompt text (often helps V+T grounding)
    return [
        {
            "role": "user",
            "content": [
                {"type": "input_image", "image_url": data_url},
                {"type": "input_text", "text": prompt},
            ],
        }
    ]

def call_responses(client: OpenAI, input_blocks: List[Dict[str, Any]], max_tokens: int):
    return client.responses.create(
        model=MODEL,
        input=input_blocks,
        max_output_tokens=max_tokens,
        reasoning={"effort": REASONING_EFFORT},
        text={"verbosity": VERBOSITY},
    )

# -----------------------------
# Core
# -----------------------------

def analyze_image(client: OpenAI, image_path: str, out_dir: Path) -> Dict[str, Any]:
    filename = Path(image_path).name
    try:
        data_url = to_data_url(image_path)
        # Get prompt from config
        system_prompt = config.get_prompt('step2_semiotic_analysis', 'system_prompt')
        main_prompt = config.get_prompt('step2_semiotic_analysis', 'main_prompt')
        full_prompt = system_prompt + "\n\n" + main_prompt
        input_blocks = make_multimodal_input(data_url, full_prompt)

        # First attempt
        resp = call_responses(client, input_blocks, MAX_OUTPUT_TOKENS)
        debug_json_path = out_dir / f"debug_response_{Path(filename).stem}.json"
        analysis_text = extract_output_text(resp, debug_path=debug_json_path)

        # If incomplete due to max_output_tokens or blank output, retry once with larger cap
        status = getattr(resp, "status", None)
        inc = getattr(resp, "incomplete_details", None)
        inc_reason = getattr(inc, "reason", None) if inc else None

        if (status == "incomplete" and inc_reason == "max_output_tokens") or not analysis_text.strip():
            resp2 = call_responses(client, input_blocks, RETRY_MAX_OUTPUT_TOKENS)
            debug_json_path2 = out_dir / f"debug_response_retry_{Path(filename).stem}.json"
            text2 = extract_output_text(resp2, debug_path=debug_json_path2)
            if text2.strip():
                analysis_text = text2

        usage = getattr(resp, "usage", None)
        tokens_used = getattr(usage, "total_tokens", 0) if usage else 0

        result = {
            "filename": filename,
            "analysis": analysis_text,
            "timestamp": datetime.now().isoformat(),
            "tokens_used": tokens_used,
            "model": MODEL,
        }
        if not analysis_text.strip():
            result["warning"] = (
                "Empty analysis after retry. See debug_response*.json; likely reasoning-token exhaustion or safety filter."
            )
        return result

    except Exception as e:
        return {
            "filename": filename,
            "error": f"{e}",
            "timestamp": datetime.now().isoformat(),
            "model": MODEL,
        }

def perform_corpus_synthesis(client: OpenAI, analyses: List[Dict[str, Any]], out_dir: Path) -> str:
    snips: List[str] = []
    for a in analyses:
        if "error" not in a and a.get("analysis"):
            snips.append(a["analysis"][:240])
        if len(snips) >= 40:
            break

    corpus_summary = "\n".join(f"- {s}" for s in snips)

    # Get synthesis prompt template from config and format it
    synthesis_prompt = config.get_prompt(
        'step2_semiotic_analysis',
        'synthesis_prompt_template',
        count=len(snips),
        corpus_summary=corpus_summary
    )

    def do_call(max_tokens: int):
        return client.responses.create(
            model=MODEL,
            input=synthesis_prompt,
            max_output_tokens=max_tokens,
            reasoning={"effort": REASONING_EFFORT},
            text={"verbosity": VERBOSITY},
        )

    resp = do_call(700)
    debug_json_path = out_dir / "debug_response__synthesis.json"
    text = extract_output_text(resp, debug_path=debug_json_path)

    status = getattr(resp, "status", None)
    inc = getattr(resp, "incomplete_details", None)
    inc_reason = getattr(inc, "reason", None) if inc else None
    if (status == "incomplete" and inc_reason == "max_output_tokens") or not text.strip():
        resp2 = do_call(1100)
        debug_json_path2 = out_dir / "debug_response__synthesis_retry.json"
        text2 = extract_output_text(resp2, debug_path=debug_json_path2)
        if text2.strip():
            text = text2

    return text

# -----------------------------
# CLI
# -----------------------------

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Semiotic analysis of local images with gpt-5-mini (Responses API).")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--image-dir", default=IMAGE_DIR)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--synthesize", action="store_true")
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set. Provide --api-key or set env var.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    out_dir = Path(args.output_dir); out_dir.mkdir(parents=True, exist_ok=True)

    # Collect images
    img_dir = Path(args.image_dir)
    patterns = ["*.jpg", "*.jpeg", "*.png", "*.webp"]
    image_files: List[Path] = []
    for p in patterns:
        image_files.extend(img_dir.glob(p))
    image_files = sorted(image_files)[: args.limit]

    print(f"Found {len(image_files)} images to analyze (limited to {args.limit})")

    analyses: List[Dict[str, Any]] = []
    total_tokens = 0

    for idx, p in enumerate(image_files, 1):
        print(f"\nAnalyzing image {idx}/{len(image_files)}: {p.name}")
        result = analyze_image(client, str(p), out_dir)
        analyses.append(result)

        if "error" in result:
            print(f"  ✗ Error: {result['error']}")
        else:
            tk = result.get("tokens_used", 0)
            total_tokens += tk
            status_icon = "✓" if result.get("analysis", "").strip() else "⚠︎"
            print(f"  {status_icon} Analysis tokens: {tk}")

        # Save per-image result
        per_path = out_dir / f"analysis_{idx:03d}_{p.stem[:30]}.json"
        with open(per_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        if idx < len(image_files):
            time.sleep(RATE_LIMIT_DELAY)

    # Save all results
    all_path = out_dir / f"all_analyses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(all_path, "w", encoding="utf-8") as f:
        json.dump(analyses, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print(f"  - Images analyzed: {len(analyses)}")
    print(f"  - Total tokens used (reported): {total_tokens:,}")
    print(f"  - Results saved to: {out_dir}")

    if args.synthesize and any(a.get("analysis") for a in analyses if "error" not in a):
        print("\nPerforming corpus synthesis...")
        try:
            synthesis_text = perform_corpus_synthesis(client, analyses, out_dir)
            synth_path = out_dir / f"synthesis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(synth_path, "w", encoding="utf-8") as f:
                f.write(synthesis_text)
            print(f"  ✓ Synthesis saved to: {synth_path}")
            print("\nSYNTHESIS PREVIEW:\n" + synthesis_text[:1000])
        except Exception as e:
            print(f"  ✗ Synthesis error: {e}")

    first_ok = next((a for a in analyses if a.get("analysis")), None)
    if first_ok:
        print("\n" + "=" * 60)
        print("EXAMPLE ANALYSIS OUTPUT:")
        print("=" * 60)
        print(f"File: {first_ok['filename']}\n")
        print(first_ok["analysis"])
    else:
        print("\n⚠︎ No non-empty analyses. Check debug_response*.json files.")

if __name__ == "__main__":
    main()
