#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 5: Practical Outputs — Semiotic Atlas, Trend Radar, Brand Playbook

What it does
------------
- Loads your Step 4 codebook.csv (phrases per section) and the original JSON analyses
- Computes per-phrase Adoption (normalized doc_freq) and Distinctiveness
  using group entropy over filename-based groups (thai/durex/other by default)
- Builds:
    1) Semiotic Atlas (2D map of phrases via sentence-transformers + UMAP/PCA)
    2) Trend Radar (Adoption vs Distinctiveness scatter)
    3) Brand Playbook table with quadrant classification
- Writes a compact Markdown report including both figures

Install
-------
pip install pandas numpy scikit-learn sentence-transformers matplotlib umap-learn

Example
-------
python step5_outputs.py \
  --json-dir /Users/tristanmcinnis/Documents/L_Code/xhs-scrape-test/semiotic_analysis_results \
  --codebook ./insight_outputs/codebook.csv \
  --out-dir ./report_outputs \
  --model all-MiniLM-L6-v2 \
  --top-per-section 15
"""

import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

try:
    import umap
    HAS_UMAP = True
except Exception:
    HAS_UMAP = False

from sentence_transformers import SentenceTransformer

from config_loader import get_config

# -----------------------------
# Canon + default group map
# -----------------------------

config = get_config()

CANON_SECTIONS_FALLBACK = [
    "VISUAL CODES",
    "CULTURAL MEANING",
    "TABOO NAVIGATION",
    "PLATFORM CONVENTIONS",
    "CONSUMER PSYCHOLOGY",
]

CANON_SECTIONS = config.get_canonical_sections() or CANON_SECTIONS_FALLBACK

DEFAULT_GROUPS_FALLBACK = {
    "coffee_flavor": r"(咖啡|coffee|咖啡味)",
    "thai_product": r"(泰国|Thailand|泰牌|thai)",
    "mens_product": r"(男生|男性|men|男士)",
    "voc_flavor": r"(voc|VOC)",
    "product_reviews": r"(避孕套|套|condom)",
    "relationship": r"(情侣|恋爱|couple|relationship)",
    "other": r".*",
}

DEFAULT_GROUPS = config.get_comparative_config().get('default_groups', DEFAULT_GROUPS_FALLBACK)

VIS_CONFIG = config.get_visualization_config() or {}
QUADRANT_THRESHOLDS = VIS_CONFIG.get('quadrant_thresholds', {})
VISUAL_SETTINGS = VIS_CONFIG.get('visualization_settings', {})

ATLAS_FIGSIZE = tuple(VISUAL_SETTINGS.get('atlas_figure_size', [10, 8]))
RADAR_FIGSIZE = tuple(VISUAL_SETTINGS.get('radar_figure_size', [9, 7]))
OUTPUT_DPI = VISUAL_SETTINGS.get('dpi', 200)
TOP_ANNOTATIONS = VISUAL_SETTINGS.get('top_annotations', 20)

SECTION_HEADER_RE = re.compile(r"^\s*(\d+)\)\s*([A-Za-z\u4e00-\u9fff\s/]+?):\s*(.*)$")

# -----------------------------
# Helpers
# -----------------------------

def normalize_section_name(name: str) -> str:
    n = re.sub(r"\s+", " ", name).strip().upper()
    for k in CANON_SECTIONS:
        if k in n:
            return k
    return n

def split_sections(text: str) -> Dict[str, str]:
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


def normalize_codebook_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure the codebook has the columns needed for visualization."""

    if df.empty:
        return pd.DataFrame(
            columns=[
                'section', 'phrase', 'doc_freq', 'total_score',
                'pattern_rank', 'example_sentence', 'example_files'
            ]
        )

    normalized = df.copy()

    if 'phrase' not in normalized.columns and 'pattern' in normalized.columns:
        normalized.rename(columns={'pattern': 'phrase'}, inplace=True)

    if 'doc_freq' not in normalized.columns:
        if 'doc_count' in normalized.columns:
            normalized.rename(columns={'doc_count': 'doc_freq'}, inplace=True)
        else:
            normalized['doc_freq'] = 0

    if 'pattern_rank' in normalized.columns:
        normalized['pattern_rank'] = pd.to_numeric(
            normalized['pattern_rank'], errors='coerce'
        ).fillna(0).astype(int)
    else:
        normalized['pattern_rank'] = 0

    normalized['doc_freq'] = pd.to_numeric(
        normalized['doc_freq'], errors='coerce'
    ).fillna(0).astype(int)

    if 'total_score' in normalized.columns:
        normalized['total_score'] = pd.to_numeric(
            normalized['total_score'], errors='coerce'
        ).fillna(0.0)
    else:
        max_rank = normalized['pattern_rank'].max() if not normalized['pattern_rank'].empty else 0
        offset = (max_rank - normalized['pattern_rank']).clip(lower=0)
        normalized['total_score'] = normalized['doc_freq'] + offset

    for col in ['section', 'phrase']:
        if col not in normalized.columns:
            normalized[col] = ''

    if 'example_sentence' not in normalized.columns:
        normalized['example_sentence'] = ''
    if 'example_files' not in normalized.columns:
        normalized['example_files'] = ''

    normalized['section'] = normalized['section'].astype(str).str.strip()
    normalized['phrase'] = normalized['phrase'].astype(str).str.strip()
    normalized['example_sentence'] = normalized['example_sentence'].fillna('').astype(str)
    normalized['example_files'] = normalized['example_files'].fillna('').astype(str)

    return normalized

def load_json_rows(json_dir: Path) -> pd.DataFrame:
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
            "filename_field": obj.get("filename", Path(p).name),
            "analysis": analysis,
            **{f"sec::{k}": sections.get(k, "") for k in CANON_SECTIONS},
        })
    return pd.DataFrame(rows)

def assign_group(filename: str, group_map: Dict[str, str]) -> str:
    for g, pat in group_map.items():
        if re.search(pat, filename):
            return g
    return "other"

def phrase_group_counts(df_docs: pd.DataFrame, phrase: str, per_section: Optional[str]) -> Dict[str, int]:
    """Count in how many docs per group the phrase appears (substring in chosen text)."""
    phrase_l = phrase.lower()
    counts: Dict[str, int] = {}
    col = "analysis" if per_section is None else f"sec::{per_section}"
    for g, sub in df_docs.groupby("group"):
        n = 0
        for txt in sub[col].fillna("").astype(str).tolist():
            if phrase_l in txt.lower():
                n += 1
        counts[g] = n
    return counts

def normalized_entropy(counts: Dict[str, int]) -> float:
    """Entropy over groups, normalized to [0,1]. 1.0 means uniform (not distinctive)."""
    total = sum(counts.values())
    if total == 0:
        return 1.0
    ps = [c / total for c in counts.values() if c > 0]
    if not ps:
        return 1.0
    H = -sum(p * math.log(p + 1e-12) for p in ps)
    Hmax = math.log(len(counts)) if len(counts) > 0 else 1.0
    return float(H / (Hmax + 1e-12))

def classify_quadrant(adoption: float, distinctive: float) -> str:
    """Rules of thumb; tweak thresholds via CLI if needed."""
    safe_cfg = {
        'adoption_min': 0.6,
        'distinctive_max': 0.4,
        **QUADRANT_THRESHOLDS.get('safe_to_borrow', {})
    }
    momentum_cfg = {
        'adoption_min': 0.5,
        'distinctive_min': 0.4,
        **QUADRANT_THRESHOLDS.get('momentum_bet', {})
    }
    edge_cfg = {
        'adoption_max': 0.5,
        'distinctive_min': 0.6,
        **QUADRANT_THRESHOLDS.get('edge_risky', {})
    }

    if adoption >= safe_cfg.get('adoption_min', 0.6) and distinctive <= safe_cfg.get('distinctive_max', 0.4):
        return "Safe to Borrow"
    if adoption >= momentum_cfg.get('adoption_min', 0.5) and distinctive >= momentum_cfg.get('distinctive_min', 0.4):
        return "Momentum Bet"
    if adoption <= edge_cfg.get('adoption_max', 0.5) and distinctive >= edge_cfg.get('distinctive_min', 0.6):
        return "Edge / Risky"
    return "Watchlist"

def embed_texts(model: SentenceTransformer, texts: List[str]) -> np.ndarray:
    emb = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.array(emb, dtype=np.float32)

def reduce_2d(vectors: np.ndarray, method: str = "umap") -> np.ndarray:
    if method == "umap" and HAS_UMAP and vectors.shape[0] >= 5:
        reducer = umap.UMAP(n_neighbors=10, min_dist=0.15, metric="cosine", random_state=42)
        return reducer.fit_transform(vectors)
    if vectors.shape[0] >= 3:
        p = PCA(n_components=2, random_state=42).fit_transform(vectors)
        return p
    # fallback: zeros
    return np.zeros((vectors.shape[0], 2), dtype=np.float32)

# -----------------------------
# Main pipeline
# -----------------------------

def build_playbook(df_codebook: pd.DataFrame,
                   df_docs: pd.DataFrame,
                   group_map: Dict[str, str],
                   top_per_section: int) -> pd.DataFrame:
    # Limit phrases considered
    chosen = []
    for sec in CANON_SECTIONS:
        sub = df_codebook[df_codebook["section"] == sec] \
                .sort_values(["doc_freq", "total_score"], ascending=False) \
                .head(top_per_section)
        if not sub.empty:
            chosen.append(sub)

    if not chosen:
        return pd.DataFrame(columns=[
            "section", "phrase", "doc_freq", "adoption", "distinctiveness",
            "quadrant", "example_sentence", "example_files"
        ])

    phrases_df = pd.concat(chosen, ignore_index=True)
    # Attach group membership per document
    df_docs["group"] = [assign_group(x, group_map) for x in df_docs["filename_field"].astype(str)]

    # Compute adoption & distinctiveness
    rows = []
    max_df = max(1, phrases_df["doc_freq"].max())
    for _, r in phrases_df.iterrows():
        sec = r["section"]
        phrase = r["phrase"]
        dfreq = int(r["doc_freq"])
        adoption = dfreq / max_df  # 0..1
        # group entropy on occurrences (search in section text)
        counts = phrase_group_counts(df_docs, phrase, per_section=sec)
        Hn = normalized_entropy(counts)          # 1 = uniform
        distinctive = 1.0 - Hn                   # 1 = concentrated (distinctive)
        quadrant = classify_quadrant(adoption, distinctive)
        rows.append({
            "section": sec,
            "phrase": phrase,
            "doc_freq": dfreq,
            "adoption": float(adoption),
            "distinctiveness": float(distinctive),
            "quadrant": quadrant,
            "example_sentence": r.get("example_sentence", ""),
            "example_files": r.get("example_files", ""),
        })
    return pd.DataFrame(rows)

def plot_semiotic_atlas(phrases_df: pd.DataFrame, model_name: str, out_path: Path):
    if phrases_df.empty:
        return

    labels = phrases_df["phrase"].tolist()
    sections = phrases_df["section"].tolist()
    model = SentenceTransformer(model_name)
    vecs = embed_texts(model, labels)
    xy = reduce_2d(vecs, method="umap")
    # Plot
    plt.figure(figsize=ATLAS_FIGSIZE)
    # color by section (simple mapping)
    sec_list = list(dict.fromkeys(sections))
    colors = {s: i for i, s in enumerate(sec_list)}
    for s in sec_list:
        mask = [sec == s for sec in sections]
        plt.scatter(xy[mask, 0], xy[mask, 1], s=30, label=s, alpha=0.75)
    # annotate a few most adopted & distinctive (top 20 by sum)
    scores = phrases_df["adoption"].values + phrases_df["distinctiveness"].values
    top_idx = np.argsort(scores)[::-1][:TOP_ANNOTATIONS]
    for i in top_idx:
        plt.text(xy[i, 0], xy[i, 1], labels[i][:28], fontsize=8)
    plt.title("Semiotic Atlas (phrase map)")
    plt.legend(loc="best", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=OUTPUT_DPI)
    plt.close()

def plot_trend_radar(playbook_df: pd.DataFrame, out_path: Path):
    if playbook_df.empty:
        return

    plt.figure(figsize=RADAR_FIGSIZE)
    # scatter by quadrant
    quads = playbook_df["quadrant"].unique().tolist()
    for q in quads:
        sub = playbook_df[playbook_df["quadrant"] == q]
        plt.scatter(sub["adoption"], sub["distinctiveness"], s=35, alpha=0.8, label=q)
    # annotate top
    # label top adoption and top distinctiveness
    top_a = playbook_df.sort_values("adoption", ascending=False).head(10)
    top_d = playbook_df.sort_values("distinctiveness", ascending=False).head(10)
    ann = pd.concat([top_a, top_d]).drop_duplicates(subset=["phrase"])
    for _, r in ann.iterrows():
        plt.text(r["adoption"] + 0.01, r["distinctiveness"] + 0.01, r["phrase"][:26], fontsize=8)
    plt.xlabel("Adoption (normalized doc frequency)")
    plt.ylabel("Distinctiveness (1 - group entropy)")
    plt.title("Trend Radar: Adoption vs Distinctiveness")
    plt.xlim(0, 1.0); plt.ylim(0, 1.0)
    plt.grid(True, alpha=0.25)
    plt.legend(loc="best", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=OUTPUT_DPI)
    plt.close()

def write_report_md(playbook_df: pd.DataFrame, atlas_path: Path, radar_path: Path, out_path: Path):
    lines = []
    lines.append("# Semiotic Outputs\n")
    lines.append("## Figures\n")
    if atlas_path.exists():
        lines.append(f"![Semiotic Atlas]({atlas_path.name})\n")
    if radar_path.exists():
        lines.append(f"![Trend Radar]({radar_path.name})\n")
    lines.append("## Brand Playbook (Auto)\n")
    for quad in ["Safe to Borrow", "Momentum Bet", "Edge / Risky", "Watchlist"]:
        sub = playbook_df[playbook_df["quadrant"] == quad] \
                .sort_values(["adoption", "distinctiveness"], ascending=[False, False]) \
                .head(12)
        if sub.empty: 
            continue
        lines.append(f"### {quad}")
        for _, r in sub.iterrows():
            lines.append(f"- **{r['phrase']}** ({r['section']}) — "
                         f"adoption={r['adoption']:.2f}, distinctive={r['distinctiveness']:.2f}; "
                         f"e.g., *{(r['example_sentence'] or '')[:160]}*")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser(description="Step 5: Practical Outputs (Atlas, Radar, Playbook, Report)")
    ap.add_argument("--json-dir", required=True, help="Directory with analysis_*.json")
    ap.add_argument("--codebook", required=True, help="Path to Step 4 codebook.csv")
    ap.add_argument("--out-dir", default="./report_outputs")
    ap.add_argument("--model", default="all-MiniLM-L6-v2", help="sentence-transformers model")
    ap.add_argument("--top-per-section", type=int, default=15)
    ap.add_argument("--group-map", type=str, default=None, help='Path to JSON {"group":"regex"}')
    args = ap.parse_args()

    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    atlas_path = out_dir / "semiotic_atlas.png"
    radar_path = out_dir / "trend_radar.png"
    report_path = out_dir / "report.md"
    playbook_csv = out_dir / "brand_playbook.csv"

    # Load inputs
    df_codebook = pd.read_csv(args.codebook)
    df_codebook = normalize_codebook_schema(df_codebook)
    df_codebook = df_codebook[df_codebook['phrase'].astype(str).str.strip() != '']
    if df_codebook.empty:
        print("codebook.csv contains no usable phrases.")
        return
    df_docs = load_json_rows(Path(args.json_dir))
    if df_docs.empty:
        print("No analyses found in json-dir.")
        return

    group_map = DEFAULT_GROUPS
    if args.group_map:
        try:
            group_map = json.loads(Path(args.group_map).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Warning: failed to load group-map, using defaults. Error: {e}")

    # Build playbook table
    playbook_df = build_playbook(df_codebook, df_docs, group_map, top_per_section=args.top_per_section)
    if playbook_df.empty:
        print("Warning: No qualifying phrases found for visualization.")
    playbook_df.sort_values(["quadrant", "adoption", "distinctiveness"], ascending=[True, False, False], inplace=True)
    playbook_df.to_csv(playbook_csv, index=False)

    # Figures
    try:
        plot_semiotic_atlas(playbook_df, args.model, atlas_path)
    except Exception as e:
        print(f"Atlas plot failed: {e}")
    try:
        plot_trend_radar(playbook_df, radar_path)
    except Exception as e:
        print(f"Trend radar failed: {e}")

    # Report
    write_report_md(playbook_df, atlas_path, radar_path, report_path)

    print("✓ Wrote:")
    print(f"  - {playbook_csv}")
    print(f"  - {atlas_path}")
    print(f"  - {radar_path}")
    print(f"  - {report_path}")

if __name__ == "__main__":
    main()