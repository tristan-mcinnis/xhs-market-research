#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 2: Local clustering & thematic mapping for semiotic analyses.

- Reads JSONs from an input directory
- Embeds with SentenceTransformers (multilingual-safe)
- Clusters with KMeans (auto-k via silhouette) or user-specified k
- Names clusters via TF-IDF top terms
- Saves: clusters.csv, clusters_summary.md, umap_2d.png, embeddings.npy, meta.json

Usage:
  python cluster_step2.py \
    --input-dir "/Users/tristanmcinnis/Documents/L_Code/xhs-scrape-test/semiotic_analysis_results" \
    --out-dir "./clusters_step2" \
    --model "paraphrase-multilingual-MiniLM-L12-v2" \
    --algo "auto" \
    --k-min 3 --k-max 10
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
import umap
import matplotlib.pyplot as plt

# -----------------------------
# IO
# -----------------------------

def load_json_corpus(input_dir: Path) -> pd.DataFrame:
    rows = []
    for p in sorted(input_dir.glob("*.json")):
        # Skip the combined analyses file
        if "all_analyses" in p.name:
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        # Handle both single object and array formats
        if isinstance(obj, list):
            # If it's an array, skip it or process each item
            continue
        analysis = (obj.get("analysis") or "").strip()
        if not analysis:
            continue
        rows.append({
            "filename": obj.get("filename") or p.stem,
            "analysis": analysis,
            "path": str(p)
        })
    if not rows:
        raise RuntimeError(f"No usable JSONs in {input_dir}")
    return pd.DataFrame(rows)

# -----------------------------
# Embeddings
# -----------------------------

def embed_texts(texts: List[str], model_name: str, batch_size: int = 32) -> np.ndarray:
    model = SentenceTransformer(model_name)
    emb = model.encode(texts, batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True)
    return np.asarray(emb, dtype=np.float32)

# -----------------------------
# Clustering (KMeans auto-K)
# -----------------------------

def auto_kmeans(x: np.ndarray, k_min: int, k_max: int, random_state: int = 42) -> Tuple[KMeans, int, float]:
    best_k, best_score, best_model = None, -1.0, None
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, n_init="auto", random_state=random_state)
        labels = km.fit_predict(x)
        # Silhouette requires >1 label and <n_samples labels
        if len(set(labels)) < 2 or len(set(labels)) >= len(x):
            continue
        score = silhouette_score(x, labels)
        if score > best_score:
            best_k, best_score, best_model = k, score, km
    if best_model is None:
        # Fallback: just use k_min
        best_model = KMeans(n_clusters=k_min, n_init="auto", random_state=random_state).fit(x)
        best_k, best_score = k_min, float("nan")
    return best_model, best_k, best_score

# -----------------------------
# Labeling clusters via TF-IDF
# -----------------------------

def top_terms_per_cluster(texts: List[str], labels: np.ndarray, top_n: int = 8) -> Dict[int, List[str]]:
    # Simple English stop words; analyses are mostly English w/ some Chinese terms
    vect = TfidfVectorizer(max_df=0.8, min_df=2, stop_words="english")
    X = vect.fit_transform(texts)
    terms = np.array(vect.get_feature_names_out())

    tops: Dict[int, List[str]] = {}
    for cid in sorted(set(labels)):
        idx = np.where(labels == cid)[0]
        if len(idx) == 0:
            tops[cid] = []
            continue
        # Convert sparse matrix mean to array properly
        mean_vec = np.asarray(X[idx].mean(axis=0)).flatten()
        mean_vec = normalize(mean_vec.reshape(1, -1))[0]
        top_idx = mean_vec.argsort()[-top_n:][::-1]
        tops[cid] = [t for t in terms[top_idx] if t.strip()]
    return tops

# -----------------------------
# Exemplars
# -----------------------------

def exemplars_kmeans(emb: np.ndarray, labels: np.ndarray, centers: np.ndarray) -> Dict[int, int]:
    """Return index of exemplar doc nearest to each centroid."""
    ex = {}
    for cid in range(centers.shape[0]):
        idx = np.where(labels == cid)[0]
        if len(idx) == 0:
            continue
        d = np.linalg.norm(emb[idx] - centers[cid], axis=1)
        ex[cid] = idx[np.argmin(d)]
    return ex

# -----------------------------
# 2D map
# -----------------------------

def make_umap(emb: np.ndarray, seed: int = 42) -> np.ndarray:
    reducer = umap.UMAP(n_components=2, random_state=seed, n_neighbors=15, min_dist=0.1, metric="cosine")
    return reducer.fit_transform(emb)

def plot_umap(z: np.ndarray, labels: np.ndarray, out_path: Path):
    plt.figure(figsize=(7.5, 6))
    uniq = sorted(set(labels))
    for cid in uniq:
        mask = labels == cid
        plt.scatter(z[mask, 0], z[mask, 1], s=18, label=f"Cluster {cid}")
    plt.legend(loc="best", fontsize=8)
    plt.title("UMAP projection of analyses")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()

# -----------------------------
# Main
# -----------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True, help="Directory containing *.json analyses")
    ap.add_argument("--out-dir", default="./clusters_step2")
    ap.add_argument("--model", default="paraphrase-multilingual-MiniLM-L12-v2",
                    help="SentenceTransformers model")
    ap.add_argument("--algo", default="auto", choices=["auto", "kmeans"])
    ap.add_argument("--k", type=int, default=None, help="If set, force KMeans with this K")
    ap.add_argument("--k-min", type=int, default=4)
    ap.add_argument("--k-max", type=int, default=10)
    args = ap.parse_args()

    inp = Path(args.input_dir)
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)

    df = load_json_corpus(inp)
    texts = df["analysis"].tolist()

    print(f"Loaded {len(df)} analyses from {inp}")
    emb = embed_texts(texts, model_name=args.model)
    np.save(out / "embeddings.npy", emb)

    # Clustering
    if args.k is not None:
        km = KMeans(n_clusters=args.k, n_init="auto", random_state=42).fit(emb)
        k = args.k
        sil = silhouette_score(emb, km.labels_) if len(set(km.labels_)) > 1 else float("nan")
    else:
        km, k, sil = auto_kmeans(emb, args.k_min, args.k_max, random_state=42)

    labels = km.labels_
    centers = km.cluster_centers_
    df["cluster_id"] = labels

    # Cluster names
    tops = top_terms_per_cluster(texts, labels, top_n=8)

    # Exemplars
    ex_idx = exemplars_kmeans(emb, labels, centers)
    df["is_exemplar"] = False
    for cid, i in ex_idx.items():
        df.loc[i, "is_exemplar"] = True

    # 2D projection
    z = make_umap(emb, seed=42)
    np.save(out / "umap_2d.npy", z)
    plot_umap(z, labels, out / "umap_2d.png")

    # Save CSV
    df_out = df[["filename", "path", "cluster_id", "is_exemplar"]].copy()
    df_out.to_csv(out / "clusters.csv", index=False, encoding="utf-8")

    # Summary MD
    lines = []
    lines.append(f"# Clustering summary\n")
    lines.append(f"- Model: `{args.model}`")
    lines.append(f"- Algo: KMeans (k={k}, silhouette={sil:.3f})")
    lines.append(f"- Items: {len(df)}\n")
    for cid in sorted(set(labels)):
        size = int((labels == cid).sum())
        terms = ", ".join(tops.get(cid, [])[:8])
        ex_name = df.loc[df["is_exemplar"] & (df["cluster_id"] == cid), "filename"].tolist()
        ex_name = ex_name[0] if ex_name else "(none)"
        lines.append(f"## Cluster {cid}  (n={size})")
        lines.append(f"- Top terms: {terms if terms else '(n/a)'}")
        lines.append(f"- Exemplar: {ex_name}\n")
    (out / "clusters_summary.md").write_text("\n".join(lines), encoding="utf-8")

    # Meta
    meta = {
        "model": args.model,
        "algo": "kmeans",
        "k": int(k),
        "silhouette": float(sil),
        "input_dir": str(inp),
        "outputs": {
            "clusters_csv": str(out / "clusters.csv"),
            "summary_md": str(out / "clusters_summary.md"),
            "umap_png": str(out / "umap_2d.png"),
            "embeddings_npy": str(out / "embeddings.npy"),
            "umap_npy": str(out / "umap_2d.npy"),
        },
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"\n✅ Clustering complete!")
    print(f"📊 Found {k} clusters with silhouette score: {sil:.3f}")
    print(f"📁 Results saved to: {out}")
    print(f"   - clusters.csv: Document cluster assignments")
    print(f"   - clusters_summary.md: Human-readable summary")
    print(f"   - umap_2d.png: Visual cluster map")
    print(f"   - embeddings.npy: Raw embeddings")
    print(f"   - meta.json: Metadata")

if __name__ == "__main__":
    main()