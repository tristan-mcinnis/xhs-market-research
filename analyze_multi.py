#!/usr/bin/env python3
"""
Analyze multiple keyword folders together for cross-query insights
"""

import os
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import sys

sys.path.append(str(Path(__file__).parent))

from typing import List, Dict, Any
from collections import Counter
from utils.llm_providers import LLMFactory
import yaml

console = Console()


def analyze_multiple_folders(
    keyword_folders: List[str] = None,
    date_folder: str = None,
    llm_provider: str = "openai",
    analysis_types: List[str] = None
):
    """
    Analyze multiple keyword folders together

    Args:
        keyword_folders: List of folder names to analyze together
        date_folder: Specific date folder (defaults to latest)
        llm_provider: LLM to use
        analysis_types: Types of analysis to perform
    """

    base_path = Path("data/downloaded_content")

    # Find date folder
    if not date_folder:
        date_folders = sorted([d for d in base_path.iterdir() if d.is_dir()])
        if not date_folders:
            console.print("[red]No data folders found[/red]")
            return
        date_folder = date_folders[-1].name

    date_path = base_path / date_folder

    # Find keyword folders to analyze
    if not keyword_folders:
        # Let user select
        available = [d.name for d in date_path.iterdir() if d.is_dir()]
        if not available:
            console.print("[red]No keyword folders found[/red]")
            return

        console.print("\n[cyan]Available folders:[/cyan]")
        for i, folder in enumerate(available, 1):
            # Count posts in folder
            folder_path = date_path / folder
            post_count = len([p for p in folder_path.iterdir() if p.is_dir()])
            console.print(f"{i}. {folder} ({post_count} posts)")

        console.print("\n[yellow]Enter folder numbers to analyze (comma-separated, or 'all'):[/yellow]")
        choice = input("> ").strip()

        if choice.lower() == 'all':
            keyword_folders = available
        else:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            keyword_folders = [available[i] for i in indices]

    # Collect all content from selected folders
    console.print(Panel(
        f"[bold cyan]Multi-Folder Analysis[/bold cyan]\n"
        f"Folders: {', '.join(keyword_folders)}\n"
        f"Date: {date_folder}",
        style="cyan"
    ))

    all_texts = []
    all_metadata = []
    folder_stats = {}

    for folder_name in keyword_folders:
        folder_path = date_path / folder_name
        if not folder_path.exists():
            console.print(f"[yellow]Warning: {folder_path} not found[/yellow]")
            continue

        console.print(f"\n[cyan]Loading content from {folder_name}...[/cyan]")

        texts = []
        metadata = []

        # Check if it has a search_summary (combined folder)
        summary_file = folder_path / "search_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
                console.print(f"  Combined folder with {summary['total_posts']} posts from {len(summary['keywords_searched'])} searches")

        # Load posts
        for post_dir in folder_path.iterdir():
            if post_dir.is_dir() and not post_dir.name.startswith('.'):
                metadata_file = post_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        post = json.load(f)

                        # Extract text
                        text_content = post.get('text_content', {})
                        full_text = f"{text_content.get('title', '')} {text_content.get('description', '')}".strip()

                        if full_text:
                            texts.append(full_text)

                        # Extract engagement
                        engagement = post.get('engagement', {})
                        metadata.append({
                            'folder': folder_name,
                            'post_id': post.get('post_id', ''),
                            'likes': int(engagement.get('likes', 0)) if isinstance(engagement.get('likes'), (str, int)) else 0,
                            'text': full_text[:100]
                        })

        folder_stats[folder_name] = {
            'posts': len(texts),
            'has_text': len([t for t in texts if t])
        }

        all_texts.extend(texts)
        all_metadata.extend(metadata)

        console.print(f"  Loaded {len(texts)} posts")

    if not all_texts:
        console.print("[red]No text content found to analyze[/red]")
        return

    # Display statistics
    console.print("\n[bold yellow]Content Statistics:[/bold yellow]")
    total_posts = sum(s['posts'] for s in folder_stats.values())
    console.print(f"  Total posts: {total_posts}")
    console.print(f"  Total with text: {len(all_texts)}")
    for folder, stats in folder_stats.items():
        console.print(f"  {folder}: {stats['posts']} posts")

    # Load config
    config_path = Path(__file__).parent / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if not analysis_types:
        analysis_types = ['themes', 'semiotics']

    # Perform aggregate analysis
    console.print(f"\n[bold cyan]Performing Cross-Query Analysis[/bold cyan]")
    console.print(f"Provider: {llm_provider}")
    console.print(f"Analysis types: {', '.join(analysis_types)}")

    # Create corpus
    corpus = "\n\n---POST SEPARATOR---\n\n".join(all_texts)
    max_chars = 30000
    if len(corpus) > max_chars:
        console.print(f"[yellow]Corpus too large, truncating...[/yellow]")
        corpus = corpus[:max_chars]

    # Initialize LLM
    try:
        llm = LLMFactory.create_provider(llm_provider)
    except Exception as e:
        console.print(f"[red]Failed to initialize {llm_provider}: {e}[/red]")
        return

    results = {
        'metadata': {
            'folders_analyzed': keyword_folders,
            'date': date_folder,
            'total_posts': total_posts,
            'text_count': len(all_texts),
            'provider': llm_provider
        },
        'folder_stats': folder_stats,
        'analysis': {}
    }

    # Run analysis
    for analysis_type in analysis_types:
        console.print(f"\n[yellow]Running {analysis_type} analysis...[/yellow]")

        type_config = config['analysis_types'].get(analysis_type, {})

        # Create cross-query prompt
        prompt = f"""
You are analyzing {total_posts} posts from Xiaohongshu across MULTIPLE search queries.
Queries/Folders analyzed: {', '.join(keyword_folders)}

This is a CROSS-QUERY ANALYSIS - you should:
1. Identify patterns that span across different searches
2. Compare and contrast findings between different keywords
3. Find unexpected connections between different topics
4. Identify overarching themes that emerge from the combined dataset
5. Note differences in engagement, sentiment, or approach between queries

{type_config.get('text_prompt', '')}

CORPUS FROM ALL QUERIES:
{corpus}

Remember: Look for patterns ACROSS different search queries, not just within them.
"""

        try:
            result = llm.analyze_text(corpus, custom_prompt=prompt)
            results['analysis'][analysis_type] = result
            console.print(f"[green]✓ {analysis_type} complete[/green]")
        except Exception as e:
            console.print(f"[red]Failed {analysis_type}: {e}[/red]")

    # Save results
    output_name = "_".join(keyword_folders[:3]) if len(keyword_folders) <= 3 else f"multi_{len(keyword_folders)}_folders"
    output_file = date_path / f"cross_analysis_{output_name}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    console.print(f"\n[green]Results saved to: {output_file}[/green]")

    # Create summary
    console.print("\n" + "="*60)
    console.print(Panel(
        f"[bold green]✅ Cross-Query Analysis Complete![/bold green]\n\n"
        f"Analyzed {len(keyword_folders)} folders with {total_posts} total posts\n"
        f"Results: {output_file}",
        style="green"
    ))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze multiple keyword folders together",
        epilog="""
Examples:
  # Analyze all folders interactively:
  python analyze_multi.py

  # Analyze specific folders:
  python analyze_multi.py --folders "杜蕾斯" "杰士邦" --themes --brand

  # Analyze combined folder:
  python analyze_multi.py --folders "combined_3_keywords" --preset marketing_full
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--folders', nargs='+', help='Specific folders to analyze')
    parser.add_argument('--date', type=str, help='Date folder (YYYYMMDD)')

    # LLM Provider
    parser.add_argument('--openai', action='store_true', help='Use OpenAI')
    parser.add_argument('--gemini', action='store_true', help='Use Gemini')
    parser.add_argument('--deepseek', action='store_true', help='Use DeepSeek')

    # Analysis types
    parser.add_argument('--themes', action='store_true', help='Thematic analysis')
    parser.add_argument('--semiotics', action='store_true', help='Semiotic analysis')
    parser.add_argument('--brand', action='store_true', help='Brand analysis')
    parser.add_argument('--trends', action='store_true', help='Trend analysis')
    parser.add_argument('--preset', type=str, help='Use preset')

    args = parser.parse_args()

    # Determine provider
    if args.gemini:
        provider = 'gemini'
    elif args.deepseek:
        provider = 'deepseek'
    else:
        provider = 'openai'

    # Collect analysis types
    analysis_types = []
    for flag in ['themes', 'semiotics', 'brand', 'trends']:
        if getattr(args, flag, False):
            analysis_types.append(flag)

    if args.preset:
        # Load preset from config
        config_path = Path(__file__).parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        if args.preset in config.get('analysis_presets', {}):
            analysis_types = config['analysis_presets'][args.preset]['includes']

    analyze_multiple_folders(
        keyword_folders=args.folders,
        date_folder=args.date,
        llm_provider=provider,
        analysis_types=analysis_types if analysis_types else None
    )