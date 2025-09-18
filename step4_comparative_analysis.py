#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3: Comparative Analysis for semiotic JSON corpus.

- Loads *.json from a directory (your JSONs saved by semiotic_analysis.py)
- Splits each 'analysis' into sections (1) VISUAL CODES ... 5) CONSUMER PSYCHOLOGY)
- Computes TF-IDF salience:
    * Top terms per section (overall)
    * Top terms per group (filename-based regex groups)
    * Differential salience per group vs. the rest (ratio)
- Saves results to CSVs in --out-dir and prints compact summaries.

Dependencies: pandas, scikit-learn, numpy
    pip install pandas scikit-learn numpy

Example:
    python step3_comparative_analysis.py \
        --json-dir /Users/tristanmcinnis/Documents/L_Code/xhs-scrape-test/semiotic_analysis_results \
        --out-dir ./comparative_outputs \
        --top-k 20
"""

import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# -----------------------------
# Config (override via CLI)
# -----------------------------

CANON_SECTIONS = {
    "VISUAL CODES": "VISUAL CODES",
    "CULTURAL MEANING": "CULTURAL MEANING",
    "TABOO NAVIGATION": "TABOO NAVIGATION",
    "PLATFORM CONVENTIONS": "PLATFORM CONVENTIONS",
    "CONSUMER PSYCHOLOGY": "CONSUMER PSYCHOLOGY",
}

# Default filename-based groups; override with --group-map
# Updated to better categorize your content
DEFAULT_GROUPS = {
    "coffee_flavor": r"(咖啡|coffee|咖啡味)",
    "thai_product": r"(泰国|Thailand|泰牌|thai)",
    "mens_product": r"(男生|男性|men|男士)",
    "voc_flavor": r"(voc|VOC)",
    "product_reviews": r"(避孕套|套|condom)",
    "relationship": r"(情侣|恋爱|couple|relationship)",
    "other": r".*",  # fallback
}

DOMAIN_STOPWORDS = {
    # generic
    "image", "images", "visual", "codes", "cultural", "meaning", "platform",
    "conventions", "consumer", "psychology", "products", "product",
    "marketing", "brand", "brands", "china", "chinese", "modern", "young",
    "lifestyle", "aesthetic", "style", "design", "packaging",
    "taboo", "navigation", "influencer", "social", "media", "xhs",
    "xiaohongshu", "user", "users", "content", "post", "posts",
    "safe", "safety", "health", "wellness", "care",
    # frequent function words not in english stoplist sometimes
    "via", "vs",
}

SECTION_HEADER_RE = re.compile(
    r"^\s*(\d+)\)\s*([A-Za-z\u4e00-\u9fff\s/]+?):\s*(.*)$"
)

def normalize_section_name(name: str) -> str:
    n = re.sub(r"\s+", " ", name).strip().upper()
    # simple fuzzy map
    for k in CANON_SECTIONS.keys():
        if k in n:
            return k
    return n

def split_sections(text: str) -> Dict[str, str]:
    """Split enumerated analysis into {SECTION: text} using headings like '1) VISUAL CODES:'."""
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

def load_json_corpus(json_dir: Path) -> pd.DataFrame:
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
        analysis = obj.get("analysis") or ""
        if not analysis.strip():
            continue
        sections = split_sections(analysis)
        rows.append({
            "path": str(p),
            "filename_field": obj.get("filename", ""),
            "timestamp": obj.get("timestamp", ""),
            **{f"sec::{k}": sections.get(k, "") for k in CANON_SECTIONS.keys()},
            "full_text": analysis,
        })
    return pd.DataFrame(rows)

def assign_group(filename: str, group_map: Dict[str, str]) -> str:
    for g, pat in group_map.items():
        if re.search(pat, filename):
            return g
    return "other"

def tfidf_top_terms(texts: List[str], top_k: int, extra_stop: List[str] = None) -> List[Tuple[str, float]]:
    stop = "english"
    # Adjust min_df based on corpus size
    min_df = 1 if len(texts) < 10 else 2
    vec = TfidfVectorizer(
        stop_words=stop,
        token_pattern=r"(?u)\b[\w\-]{2,}\b",
        ngram_range=(1, 2),
        min_df=min_df
    )
    X = vec.fit_transform(texts)
    vocab = np.array(vec.get_feature_names_out())
    # Drop domain stopwords and extra stopwords post-hoc
    if extra_stop:
        extra = set(s.lower() for s in extra_stop)
    else:
        extra = set()
    mask = np.array([t.lower() not in DOMAIN_STOPWORDS and t.lower() not in extra for t in vocab])
    if mask.any():
        scores = np.asarray(X.sum(axis=0)).ravel()[mask]
        terms = vocab[mask]
    else:
        scores = np.asarray(X.sum(axis=0)).ravel()
        terms = vocab
    idx = np.argsort(scores)[::-1][:top_k]
    return [(terms[i], float(scores[i])) for i in idx]

def tfidf_group_contrast(docs_by_group: Dict[str, List[str]], top_k: int) -> Dict[str, List[Tuple[str, float]]]:
    # Build a shared vectorizer across all docs
    all_docs = [d for docs in docs_by_group.values() for d in docs]
    if len(all_docs) == 0:
        return {}
    # Adjust min_df based on corpus size
    min_df = 1 if len(all_docs) < 10 else 2
    vec = TfidfVectorizer(
        stop_words="english",
        token_pattern=r"(?u)\b[\w\-]{2,}\b",
        ngram_range=(1, 2),
        min_df=min_df
    )
    X = vec.fit_transform(all_docs)
    terms = np.array(vec.get_feature_names_out())
    # mask out domain stopwords
    mask = np.array([t.lower() not in DOMAIN_STOPWORDS for t in terms])
    terms = terms[mask]

    # Build group matrices
    result: Dict[str, List[Tuple[str, float]]] = {}
    start = 0
    idx_map = {}
    for g, docs in docs_by_group.items():
        idx_map[g] = (start, start + len(docs))
        start += len(docs)

    X = X[:, mask]
    eps = 1e-6
    for g, (a, b) in idx_map.items():
        if a == b:
            result[g] = []
            continue
        X_g = X[a:b]
        X_rest = X[np.r_[0:a, b:X.shape[0]]]
        mean_g = np.asarray(X_g.mean(axis=0)).ravel()
        mean_rest = np.asarray(X_rest.mean(axis=0)).ravel()
        ratio = (mean_g + eps) / (mean_rest + eps)
        top_idx = np.argsort(ratio)[::-1][:top_k]
        result[g] = [(terms[i], float(ratio[i])) for i in top_idx]
    return result

def main():
    ap = argparse.ArgumentParser(description="Step 3: Comparative Analysis (TF-IDF & contrasts).")
    ap.add_argument("--json-dir", required=True, help="Directory containing analysis_*.json files")
    ap.add_argument("--out-dir", default="./comparative_outputs", help="Where to write CSVs")
    ap.add_argument("--top-k", type=int, default=20)
    ap.add_argument("--group-map", type=str, default=None,
                    help='JSON mapping of {"group":"regex"} applied to `filename` field; default uses thai/durex/other')
    ap.add_argument("--extra-stopwords", type=str, default=None,
                    help='Comma-separated extra stopwords')
    args = ap.parse_args()

    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    group_map = DEFAULT_GROUPS if not args.group_map else json.loads(Path(args.group_map).read_text(encoding="utf-8"))
    extra_stop = [] if not args.extra_stopwords else [s.strip() for s in args.extra_stopwords.split(",") if s.strip()]

    df = load_json_corpus(Path(args.json_dir))
    if df.empty:
        print("No valid analyses found.")
        return

    # Assign groups from filename field; fallback to path name if missing
    filenames = df["filename_field"].fillna(df["path"]).astype(str)
    df["group"] = [assign_group(fn, group_map) for fn in filenames]

    # ---------- Overall per-section salience ----------
    overall_rows = []
    for sec in CANON_SECTIONS.keys():
        col = f"sec::{sec}"
        texts = [t for t in df[col].tolist() if t]
        if not texts:
            continue
        tops = tfidf_top_terms(texts, args.top_k, extra_stop)
        for term, score in tops:
            overall_rows.append({"section": sec, "term": term, "tfidf_sum": score})
    overall_df = pd.DataFrame(overall_rows).sort_values(["section", "tfidf_sum"], ascending=[True, False])
    overall_df.to_csv(out_dir / "top_terms_per_section_overall.csv", index=False)

    # ---------- By-group (all text combined per doc) ----------
    group_rows = []
    for g, gdf in df.groupby("group"):
        docs = gdf["full_text"].tolist()
        tops = tfidf_top_terms(docs, args.top_k, extra_stop)
        for term, score in tops:
            group_rows.append({"group": g, "term": term, "tfidf_sum": score})
    group_df = pd.DataFrame(group_rows).sort_values(["group", "tfidf_sum"], ascending=[True, False])
    group_df.to_csv(out_dir / "top_terms_per_group_overall.csv", index=False)

    # ---------- Differential salience (group vs rest) ----------
    docs_by_group = {g: gdf["full_text"].tolist() for g, gdf in df.groupby("group")}
    contrast = tfidf_group_contrast(docs_by_group, args.top_k)
    contrast_rows = []
    for g, items in contrast.items():
        for term, ratio in items:
            contrast_rows.append({"group": g, "term": term, "salience_ratio": ratio})
    contrast_df = pd.DataFrame(contrast_rows).sort_values(["group", "salience_ratio"], ascending=[True, False])
    contrast_df.to_csv(out_dir / "differential_salience_by_group.csv", index=False)

    # ---------- Console summaries ----------
    def print_table(title: str, rows: pd.DataFrame, key_cols: List[str], value_col: str, top_n: int = 10):
        print("\n" + title)
        print("-" * len(title))
        for key, sub in rows.groupby(key_cols):
            head = key if isinstance(key, str) else " / ".join(key)
            print(f"\n[{head}]")
            sub = sub.sort_values(value_col, ascending=False).head(top_n)
            for _, r in sub.iterrows():
                print(f"  {r['term']:<30} {value_col}={r[value_col]:.4f}")

    print_table("Top terms per SECTION (overall)", overall_df, ["section"], "tfidf_sum")
    print_table("Top terms per GROUP (overall)", group_df, ["group"], "tfidf_sum")
    print_table("Differential salience (GROUP vs rest)", contrast_df, ["group"], "salience_ratio")

    # ---------- Basic counts ----------
    counts = df.groupby("group").size().reset_index(name="n_docs")
    counts.to_csv(out_dir / "doc_counts_by_group.csv", index=False)
    print("\nDoc counts by group:")
    for _, row in counts.iterrows():
        print(f"  {row['group']}: {row['n_docs']}")

if __name__ == "__main__":
    main()