#!/usr/bin/env python3
"""Final Report Builder
====================

Merges downstream pipeline outputs (insights, themes, visualizations) into
analyst-ready Markdown and optional DOCX deliverables using configurable
Jinja2 templates.

Usage
-----
python final_report_builder.py --workflow data/20241010/my_query --template scqa --deliverable docx
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import textwrap
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from zipfile import ZipFile

import pandas as pd
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from config_loader import get_config
from workflow_config import WorkflowConfig, find_latest_workflow


@dataclass
class ResolvedAsset:
    """Representation of a file-based asset bundled with the report."""

    key: str
    title: Optional[str]
    description: Optional[str]
    kind: str
    required: bool = False
    copy_to_bundle: bool = True
    caption: Optional[str] = None
    text: Optional[str] = None
    source_paths: List[Path] = field(default_factory=list)
    relative_paths: List[str] = field(default_factory=list)
    filenames: List[str] = field(default_factory=list)
    in_bundle: bool = False

    @property
    def relative_path(self) -> Optional[str]:
        return self.relative_paths[0] if self.relative_paths else None

    @property
    def filename(self) -> Optional[str]:
        return self.filenames[0] if self.filenames else None


def load_workflow_config(workflow_arg: Optional[str]) -> WorkflowConfig:
    """Load an existing workflow configuration from path or 'latest'."""

    if not workflow_arg or workflow_arg.lower() == "latest":
        config = find_latest_workflow()
        if not config:
            raise FileNotFoundError(
                "No workflow found. Run the pipeline first or specify --workflow <path>."
            )
        return config

    workflow_path = Path(workflow_arg).expanduser().resolve()

    if workflow_path.is_dir():
        config_file = workflow_path / "workflow_config.json"
        if not config_file.exists():
            raise FileNotFoundError(
                f"workflow_config.json not found in {workflow_path}. "
                "Provide the workflow directory created by run_pipeline.py."
            )
        return WorkflowConfig.load_config(config_file)

    if workflow_path.is_file():
        return WorkflowConfig.load_config(workflow_path)

    raise FileNotFoundError(f"Workflow path not found: {workflow_path}")


def normalize_section_key(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().upper()


def strip_heading_block(text: str) -> str:
    lines = text.splitlines()
    cleaned: List[str] = []
    skipping = True
    for line in lines:
        if skipping:
            if line.startswith("#") or line.lower().startswith("*analyzed"):
                continue
            if not line.strip():
                continue
            skipping = False
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def take_bullet_snippets(text: str, max_lines: int = 3) -> str:
    bullets: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("-"):
            bullets.append(stripped.lstrip("- "))
        if len(bullets) >= max_lines:
            break
    if not bullets:
        first_sentence = text.strip().split(". ")[0].strip()
        if first_sentence:
            bullets.append(first_sentence)
    return "; ".join(bullets)


def truncate_markdown(text: str, words: int = 180) -> str:
    tokens = text.strip().split()
    if len(tokens) <= words:
        return text.strip()
    clipped = " ".join(tokens[:words])
    return clipped.rstrip() + " …"


def gather_step5_assets(config: WorkflowConfig, canonical_sections: Iterable[str]) -> Tuple[Dict[str, Any], List[str]]:
    data: Dict[str, Any] = {
        "section_insights": {},
    }
    warnings: List[str] = []

    try:
        step_dir = config.get_dir("step5_insights")
    except ValueError:
        warnings.append("Workflow directory not initialised with a query; cannot locate step5 outputs.")
        return data, warnings

    if not step_dir.exists():
        warnings.append(f"Step5 directory missing: {step_dir}")
        return data, warnings

    section_highlights: List[str] = []

    for section in canonical_sections:
        filename = f"insights_{section.replace(' ', '_').lower()}.md"
        path = step_dir / filename
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - defensive
            warnings.append(f"Failed to read {path.name}: {exc}")
            continue
        cleaned = strip_heading_block(text)
        data["section_insights"][normalize_section_key(section)] = {
            "path": path,
            "text": cleaned,
        }
        highlight = take_bullet_snippets(cleaned)
        if highlight:
            section_highlights.append(f"- **{section.title()}** — {highlight}")

    if section_highlights:
        data["section_highlights"] = "\n".join(section_highlights)

    master_path = max(
        step_dir.glob("master_codebook_*.md"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        default=None,
    )
    if master_path and master_path.exists():
        try:
            master_text = master_path.read_text(encoding="utf-8")
            data["master_codebook"] = {"path": master_path, "text": master_text}
            data["master_codebook_excerpt"] = truncate_markdown(strip_heading_block(master_text), 220)
        except Exception as exc:
            warnings.append(f"Failed to read master codebook ({master_path.name}): {exc}")
    else:
        warnings.append("Master codebook not found. Run step5 with --synthesize to generate it.")

    insight_report = step_dir / "insight_extraction_report.md"
    if insight_report.exists():
        try:
            data["insight_report"] = {
                "path": insight_report,
                "text": strip_heading_block(insight_report.read_text(encoding="utf-8")),
            }
        except Exception as exc:
            warnings.append(f"Failed to read insight_extraction_report.md: {exc}")

    for csv_name in ("codebook.csv", "codebook_patterns.csv"):
        csv_path = step_dir / csv_name
        if csv_path.exists():
            data[csv_name.replace(".csv", "_path")] = csv_path

    all_insights = sorted(step_dir.glob("all_insights_*.json"), key=lambda p: p.stat().st_mtime)
    if all_insights:
        data["all_insights_path"] = all_insights[-1]

    return data, warnings


def extract_theme_metadata(text: str) -> Tuple[Optional[str], Optional[str]]:
    title_match = re.search(r"\*\*Theme Title\*\*[:\-\s]+(.+)", text)
    insight_match = re.search(r"\*\*Core Insight\*\*[:\-\s]+(.+)", text)
    title = title_match.group(1).strip() if title_match else None
    insight = insight_match.group(1).strip() if insight_match else None
    return title, insight


def gather_step6_assets(config: WorkflowConfig) -> Tuple[Dict[str, Any], List[str]]:
    data: Dict[str, Any] = {}
    warnings: List[str] = []

    try:
        step_dir = config.get_dir("step6_themes")
    except ValueError:
        warnings.append("Workflow directory not initialised with a query; cannot locate step6 outputs.")
        return data, warnings

    if not step_dir.exists():
        warnings.append(f"Step6 directory missing: {step_dir}")
        return data, warnings

    enriched_report = step_dir / "enriched_themes_report.md"
    if enriched_report.exists():
        try:
            data["enriched_report"] = {
                "path": enriched_report,
                "text": enriched_report.read_text(encoding="utf-8").strip(),
            }
        except Exception as exc:
            warnings.append(f"Failed to read enriched_themes_report.md: {exc}")

    theme_files: List[Dict[str, Any]] = []
    for path in sorted(step_dir.glob("theme_cluster_*.md")):
        try:
            raw = path.read_text(encoding="utf-8")
        except Exception as exc:
            warnings.append(f"Failed to read {path.name}: {exc}")
            continue
        title, insight = extract_theme_metadata(raw)
        theme_files.append({
            "path": path,
            "text": raw.strip(),
            "title": title,
            "core_insight": insight,
        })
    if theme_files:
        data["theme_files"] = theme_files
        highlights: List[str] = []
        for idx, item in enumerate(theme_files, start=1):
            if item["title"] and item["core_insight"]:
                highlights.append(f"- **{item['title']}** — {item['core_insight']}")
            elif item["title"]:
                highlights.append(f"- **{item['title']}** — additional detail in appendix")
        if highlights:
            data["theme_highlights"] = "\n".join(highlights)
            data["lead_theme"] = highlights[0]

    synthesis_files = sorted(step_dir.glob("synthesis_*.md"), key=lambda p: p.stat().st_mtime)
    if synthesis_files:
        latest = synthesis_files[-1]
        try:
            data["synthesis"] = {
                "path": latest,
                "text": latest.read_text(encoding="utf-8").strip(),
            }
        except Exception as exc:
            warnings.append(f"Failed to read {latest.name}: {exc}")
    else:
        warnings.append("Theme synthesis file not found (run step6 with --synthesize).")

    return data, warnings


def load_playbook_dataframe(path: Path) -> Optional[pd.DataFrame]:
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        print(f"Warning: could not read {path.name}: {exc}")
        return None
    required_cols = {"phrase", "section", "adoption", "distinctiveness", "quadrant"}
    if missing := required_cols - set(df.columns):
        print(f"Warning: playbook CSV missing columns: {', '.join(sorted(missing))}")
    return df


def build_playbook_bullets(df: pd.DataFrame, max_items: int = 4) -> str:
    quadrant_order = ["Safe to Borrow", "Momentum Bet", "Edge / Risky", "Watchlist"]
    lines: List[str] = []
    for quadrant in quadrant_order:
        subset = df[df.get("quadrant", "").astype(str) == quadrant]
        if subset.empty:
            continue
        subset = subset.sort_values(["adoption", "distinctiveness"], ascending=[False, False]).head(max_items)
        lines.append(f"#### {quadrant}")
        for _, row in subset.iterrows():
            phrase = str(row.get("phrase", "")).strip()
            section = str(row.get("section", "")).strip()
            adoption = row.get("adoption")
            distinctiveness = row.get("distinctiveness")
            example = str(row.get("example_sentence", "")).strip()
            if len(example) > 140:
                example = example[:137].rstrip() + "…"
            adoption_txt = f"{float(adoption):.2f}" if pd.notna(adoption) else "n/a"
            distinct_txt = f"{float(distinctiveness):.2f}" if pd.notna(distinctiveness) else "n/a"
            lines.append(
                f"- **{phrase}** ({section}) — adoption {adoption_txt}, distinctiveness {distinct_txt}. {example}"
            )
        lines.append("")
    if not lines:
        return "_Playbook CSV did not contain actionable rows._"
    return "\n".join(lines).strip()


def build_social_snippet(df: pd.DataFrame, max_items: int = 3) -> str:
    ranked = df.sort_values(["distinctiveness", "adoption"], ascending=[False, False]).head(max_items)
    lines = []
    for _, row in ranked.iterrows():
        phrase = str(row.get("phrase", "")).strip()
        quadrant = str(row.get("quadrant", "")).strip()
        adoption = row.get("adoption")
        adoption_txt = f"{float(adoption):.2f}" if pd.notna(adoption) else "n/a"
        lines.append(f"• {phrase} ({quadrant}) — adoption {adoption_txt}")
    if lines:
        lines.append("Let’s turn these codes into launch creative — DM for the full atlas + playbook.")
        return "\n".join(lines)
    return "_Populate the playbook to unlock a social CTA._"


def gather_step7_assets(config: WorkflowConfig) -> Tuple[Dict[str, Any], List[str]]:
    data: Dict[str, Any] = {}
    warnings: List[str] = []

    try:
        step_dir = config.get_dir("step7_visualizations")
    except ValueError:
        warnings.append("Workflow directory not initialised with a query; cannot locate step7 outputs.")
        return data, warnings

    if not step_dir.exists():
        warnings.append(f"Step7 directory missing: {step_dir}")
        return data, warnings

    atlas = step_dir / "semiotic_atlas.png"
    if atlas.exists():
        data["semiotic_atlas"] = atlas
    else:
        warnings.append("Semiotic atlas not generated (missing semiotic_atlas.png).")

    radar = step_dir / "trend_radar.png"
    if radar.exists():
        data["trend_radar"] = radar
    else:
        warnings.append("Trend radar not generated (missing trend_radar.png).")

    playbook_csv = step_dir / "brand_playbook.csv"
    if playbook_csv.exists():
        data["brand_playbook_csv"] = playbook_csv
        df = load_playbook_dataframe(playbook_csv)
        if df is not None:
            data["playbook_dataframe"] = df
            data["playbook_bullets"] = build_playbook_bullets(df)
            data["social_snippet"] = build_social_snippet(df)
    else:
        warnings.append("brand_playbook.csv missing — rerun step7 to generate recommendations.")

    report_md = step_dir / "report.md"
    if report_md.exists():
        try:
            data["report_md"] = {
                "path": report_md,
                "text": report_md.read_text(encoding="utf-8").strip(),
            }
        except Exception as exc:
            warnings.append(f"Failed to read visualization report.md: {exc}")

    return data, warnings


def build_assets(template_def: Dict[str, Any], collected: Dict[str, Dict[str, Any]]) -> OrderedDict[str, ResolvedAsset]:
    assets: "OrderedDict[str, ResolvedAsset]" = OrderedDict()
    for asset_conf in template_def.get("assets", []):
        key = asset_conf.get("key")
        if not key:
            continue
        asset = ResolvedAsset(
            key=key,
            title=asset_conf.get("title"),
            description=asset_conf.get("description"),
            kind=asset_conf.get("kind", "file"),
            required=asset_conf.get("required", False),
            copy_to_bundle=asset_conf.get("copy_to_bundle", True),
            caption=asset_conf.get("caption"),
        )
        source = asset_conf.get("source")
        if not source:
            assets[key] = asset
            continue
        step = source.split(".")[0]
        step_payload = collected.get(step, {})
        if source == "step5.master_codebook":
            entry = step_payload.get("master_codebook")
            if entry:
                asset.source_paths.append(entry["path"])
                asset.filenames.append(entry["path"].name)
                asset.text = entry.get("text")
        elif source == "step6.enriched_report":
            entry = step_payload.get("enriched_report")
            if entry:
                asset.source_paths.append(entry["path"])
                asset.filenames.append(entry["path"].name)
                asset.text = entry.get("text")
        elif source == "step7.brand_playbook_csv":
            csv_path = step_payload.get("brand_playbook_csv")
            if csv_path:
                asset.source_paths.append(csv_path)
                asset.filenames.append(csv_path.name)
        elif source == "step7.semiotic_atlas":
            atlas = step_payload.get("semiotic_atlas")
            if atlas:
                asset.source_paths.append(atlas)
                asset.filenames.append(atlas.name)
        elif source == "step7.trend_radar":
            radar = step_payload.get("trend_radar")
            if radar:
                asset.source_paths.append(radar)
                asset.filenames.append(radar.name)
        elif source == "step7.visual_pairs":
            atlas = step_payload.get("semiotic_atlas")
            radar = step_payload.get("trend_radar")
            for path in (atlas, radar):
                if path:
                    asset.source_paths.append(path)
                    asset.filenames.append(path.name)
        else:
            # Unknown mapping is tolerated; sections/fallbacks will handle it
            pass
        assets[key] = asset
    return assets


def copy_assets_to_bundle(assets: OrderedDict[str, ResolvedAsset], output_dir: Path, warnings: List[str]) -> Path:
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    for asset in assets.values():
        if not asset.copy_to_bundle:
            continue
        if not asset.source_paths:
            if asset.required:
                warnings.append(f"Required asset '{asset.key}' missing; it will not appear in bundle.")
            continue
        for src in asset.source_paths:
            if not src.exists():
                warnings.append(f"Asset source missing: {src}")
                continue
            dest = assets_dir / src.name
            try:
                shutil.copy2(src, dest)
                asset.in_bundle = True
                asset.relative_paths.append(str(dest.relative_to(output_dir)))
                if dest.name not in asset.filenames:
                    asset.filenames.append(dest.name)
            except Exception as exc:
                warnings.append(f"Failed to copy asset {src.name}: {exc}")
        if not asset.relative_paths and asset.required:
            warnings.append(f"Required asset '{asset.key}' could not be copied.")
    return assets_dir


def zip_bundle(assets_dir: Path, output_dir: Path) -> Optional[Path]:
    files = [p for p in assets_dir.rglob("*") if p.is_file()]
    if not files:
        return None
    zip_path = output_dir / "assets_bundle.zip"
    with ZipFile(zip_path, "w") as zf:
        for file in files:
            zf.write(file, file.relative_to(output_dir))
    return zip_path


def resolve_text_source(
    source: Optional[str],
    collected: Dict[str, Dict[str, Any]],
    assets: OrderedDict[str, ResolvedAsset],
    metadata: Dict[str, Any],
) -> Tuple[Optional[str], List[str]]:
    warnings: List[str] = []
    if not source:
        return None, warnings
    if source.startswith("literal:"):
        return source.split(":", 1)[1], warnings

    if source.startswith("metadata."):
        key = source.split(".", 1)[1]
        value = metadata.get(key)
        if value is None:
            warnings.append(f"Metadata field '{key}' not available for template.")
        return value, warnings

    step_key, *rest = source.split(".")
    payload = collected.get(step_key, {})

    if source.startswith("step5.section_insights."):
        section_name = normalize_section_key(rest[-1]) if rest else ""
        entry = payload.get("section_insights", {}).get(section_name)
        if entry:
            return entry.get("text"), warnings
        warnings.append(f"Section insights missing for '{section_name}'.")
        return None, warnings

    if source == "step5.section_highlights":
        value = payload.get("section_highlights")
        if not value:
            warnings.append("Section highlights unavailable (step5 insights missing).")
        return value, warnings

    if source == "step5.master_codebook":
        entry = payload.get("master_codebook")
        if entry:
            return entry.get("text"), warnings
        warnings.append("Master codebook missing for template section.")
        return None, warnings

    if source == "step5.master_codebook_excerpt":
        value = payload.get("master_codebook_excerpt")
        if not value:
            warnings.append("Master codebook excerpt unavailable.")
        return value, warnings

    if source == "step5.insight_report":
        entry = payload.get("insight_report")
        if entry:
            return entry.get("text"), warnings
        warnings.append("Insight extraction report missing.")
        return None, warnings

    if source == "step6.synthesis":
        entry = payload.get("synthesis")
        if entry:
            return entry.get("text"), warnings
        warnings.append("Theme synthesis missing.")
        return None, warnings

    if source == "step6.enriched_report":
        entry = payload.get("enriched_report")
        if entry:
            return entry.get("text"), warnings
        warnings.append("Enriched themes report missing.")
        return None, warnings

    if source == "step6.theme_highlights":
        value = payload.get("theme_highlights")
        if not value:
            warnings.append("Theme highlights unavailable.")
        return value, warnings

    if source == "step6.lead_theme":
        value = payload.get("lead_theme")
        if not value:
            warnings.append("Lead theme unavailable.")
        return value, warnings

    if source == "step7.playbook_bullets":
        value = payload.get("playbook_bullets")
        if not value:
            warnings.append("Brand playbook bullets unavailable (missing CSV).")
        return value, warnings

    if source == "step7.social_snippet":
        value = payload.get("social_snippet")
        if not value:
            warnings.append("Social snippet unavailable (playbook CSV missing).")
        return value, warnings

    if source == "step7.visual_gallery":
        gallery_lines: List[str] = []
        for key in ("semiotic_atlas", "trend_radar"):
            asset = assets.get(key)
            if asset and asset.relative_path:
                gallery_lines.append(f"![{asset.title or key}]({asset.relative_path})")
                if asset.caption:
                    gallery_lines.append(f"*{asset.caption}*")
                gallery_lines.append("")
        if not gallery_lines:
            warnings.append("Visual gallery assets missing (atlas/radar not copied).")
            return None, warnings
        return "\n".join(gallery_lines).strip(), warnings

    warnings.append(f"Unmapped source '{source}' for template.")
    return None, warnings


def build_sections(
    template_def: Dict[str, Any],
    collected: Dict[str, Dict[str, Any]],
    assets: OrderedDict[str, ResolvedAsset],
    metadata: Dict[str, Any],
    warnings: List[str],
) -> OrderedDict[str, Dict[str, str]]:
    sections: "OrderedDict[str, Dict[str, str]]" = OrderedDict()
    for section_conf in template_def.get("sections", []):
        key = section_conf.get("key", "section")
        title = section_conf.get("title", key.replace("_", " ").title())
        fallback = section_conf.get("fallback", f"_Content not available for {title}._")
        body, extra_warnings = resolve_text_source(section_conf.get("source"), collected, assets, metadata)
        warnings.extend(extra_warnings)
        sections[key] = {
            "title": title,
            "body": (body or fallback).strip(),
        }
    return sections


def render_template(
    template_path: Path,
    context: Dict[str, Any],
    output_dir: Path,
    deliverable: str,
    warnings: List[str],
) -> Tuple[Path, Optional[Path]]:
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    try:
        template = env.get_template(template_path.name)
    except TemplateNotFound as exc:
        raise FileNotFoundError(f"Template file not found: {template_path} ({exc})")

    markdown_output = template.render(**context)
    md_path = output_dir / "report.md"
    md_path.write_text(markdown_output, encoding="utf-8")

    docx_path: Optional[Path] = None
    if deliverable in {"docx", "both"}:
        docx_path = output_dir / "report.docx"
        try:
            subprocess.run(
                ["pandoc", str(md_path), "-o", str(docx_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            warnings.append("Pandoc not installed; skipped DOCX export.")
            docx_path = None
        except subprocess.CalledProcessError as exc:
            warnings.append(f"Pandoc failed to build DOCX: {exc.stderr.decode('utf-8', errors='ignore')[:200]}")
            docx_path = None
    return md_path, docx_path


def write_metadata_file(
    template_key: str,
    template_def: Dict[str, Any],
    sections: OrderedDict[str, Dict[str, str]],
    assets: OrderedDict[str, ResolvedAsset],
    metadata: Dict[str, Any],
    warnings: List[str],
    output_dir: Path,
) -> Path:
    export = {
        "template_key": template_key,
        "template_display": template_def.get("display_name", template_key.title()),
        "generated_at": metadata.get("generated_at"),
        "workflow_dir": metadata.get("workflow_dir"),
        "query": metadata.get("query"),
        "sections": [
            {
                "key": key,
                "title": section["title"],
                "has_content": bool(section["body"]),
                "source": template_def.get("sections", [])[idx].get("source")
                if idx < len(template_def.get("sections", []))
                else None,
            }
            for idx, (key, section) in enumerate(sections.items())
        ],
        "assets": {
            key: {
                "files": asset.relative_paths,
                "copied": asset.in_bundle,
                "kind": asset.kind,
                "description": asset.description,
            }
            for key, asset in assets.items()
        },
        "warnings": warnings,
    }
    meta_path = output_dir / "report_metadata.json"
    meta_path.write_text(json.dumps(export, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta_path


def determine_output_directory(workflow: WorkflowConfig, template_key: str) -> Path:
    base_dir = workflow.get_dir("step7_visualizations").parent if workflow.query_dir else Path(".")
    output_root = base_dir / "final_reports" / template_key
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = output_root / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_metadata(workflow: WorkflowConfig, template_key: str, template_def: Dict[str, Any]) -> Dict[str, Any]:
    query = getattr(workflow, "query", None)
    metadata = {
        "query": query,
        "clean_query": getattr(workflow, "clean_query", query),
        "date": getattr(workflow, "date", datetime.now().strftime("%Y%m%d")),
        "workflow_dir": str(getattr(workflow, "query_dir", "")),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "template_key": template_key,
        "template_display": template_def.get("display_name", template_key.title()),
    }
    base_title = metadata["clean_query"] or metadata["query"] or "XHS Insights"
    metadata["title"] = f"{base_title} — {metadata['template_display']}"
    metadata["next_steps_note"] = textwrap.dedent(
        """
        1. Align with category/brand leads on the activation priorities within the next 48 hours.
        2. Brief creative partners on the top distinctiveness codes pulled from the playbook.
        3. Schedule a Mac-native working session to adapt the atlas and radar visuals for Keynote.
        """
    ).strip()
    return metadata


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble final reports from pipeline outputs.")
    parser.add_argument("--workflow", required=True, help="Path to workflow directory or 'latest'.")
    parser.add_argument("--template", default="scqa", help="Template key defined in pipeline_config.json")
    parser.add_argument(
        "--deliverable",
        choices=["md", "docx", "both"],
        default="both",
        help="Choose Markdown only, DOCX only, or both.",
    )
    args = parser.parse_args(argv)

    pipeline_config = get_config()
    try:
        template_def = pipeline_config.get_report_template(args.template)
    except KeyError as exc:
        print(exc)
        available = ", ".join(sorted(pipeline_config.get_report_templates().keys()))
        print(f"Available templates: {available}")
        return 1

    try:
        workflow = load_workflow_config(args.workflow)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1

    canonical_sections = pipeline_config.get_canonical_sections()

    collected: Dict[str, Dict[str, Any]] = {}
    warnings: List[str] = []

    step5_data, w5 = gather_step5_assets(workflow, canonical_sections)
    collected["step5"] = step5_data
    warnings.extend(w5)

    step6_data, w6 = gather_step6_assets(workflow)
    collected["step6"] = step6_data
    warnings.extend(w6)

    step7_data, w7 = gather_step7_assets(workflow)
    collected["step7"] = step7_data
    warnings.extend(w7)

    metadata = build_metadata(workflow, args.template, template_def)

    output_dir = determine_output_directory(workflow, args.template)

    assets = build_assets(template_def, collected)
    assets_dir = copy_assets_to_bundle(assets, output_dir, warnings)
    bundle_zip = zip_bundle(assets_dir, output_dir)
    if bundle_zip:
        metadata["asset_bundle"] = bundle_zip.name

    sections = build_sections(template_def, collected, assets, metadata, warnings)

    visuals = OrderedDict((key, asset) for key, asset in assets.items() if asset.kind.startswith("image"))

    context = {
        "metadata": metadata,
        "sections": sections,
        "assets": assets,
        "visuals": visuals,
        "warnings": warnings,
    }

    template_path = Path(template_def.get("template_path", args.template)).expanduser()
    if not template_path.is_absolute():
        template_path = Path(__file__).resolve().parent / template_path

    md_path, docx_path = render_template(template_path, context, output_dir, args.deliverable, warnings)
    meta_path = write_metadata_file(args.template, template_def, sections, assets, metadata, warnings, output_dir)

    print("\nFinal report generated:")
    print(f"  • Markdown: {md_path}")
    if docx_path:
        print(f"  • DOCX: {docx_path}")
    else:
        if args.deliverable in {"docx", "both"}:
            print("  • DOCX: skipped (see warnings)")
    if bundle_zip:
        print(f"  • Asset bundle: {bundle_zip}")
    else:
        print("  • Asset bundle: no files copied")
    print(f"  • Metadata: {meta_path}")

    if warnings:
        print("\nWarnings:")
        for item in warnings:
            print(f"  - {item}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
