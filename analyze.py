#!/usr/bin/env python3
"""
Analyze downloaded Xiaohongshu content using AI - Aggregate Analysis
"""

import os
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import sys

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from typing import List, Dict, Any
from collections import Counter
from utils.llm_providers import LLMFactory, LLMProvider
import yaml

console = Console()


def collect_all_content(keyword_path: Path) -> Dict[str, Any]:
    """Collect all content from posts for aggregate analysis"""

    all_texts = []
    all_metadata = []
    all_images = []
    post_count = 0

    console.print("[cyan]Collecting content from all posts...[/cyan]")

    # Load from each post directory
    for post_dir in sorted(keyword_path.iterdir()):
        if post_dir.is_dir() and not post_dir.name.startswith('.'):
            metadata_file = post_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    post = json.load(f)
                    post_count += 1

                    # Extract text content
                    text_content = post.get('text_content', {})
                    full_text = f"{text_content.get('title', '')} {text_content.get('description', '')}".strip()

                    if full_text:
                        all_texts.append(full_text)

                    # Collect metadata
                    engagement = post.get('engagement', {})
                    # Convert string values to integers
                    likes = engagement.get('likes', 0)
                    comments_val = engagement.get('comments', 0)
                    shares = engagement.get('shares', 0)

                    # Handle string values
                    likes = int(likes) if isinstance(likes, str) and likes.isdigit() else likes if isinstance(likes, int) else 0
                    comments_val = int(comments_val) if isinstance(comments_val, str) and comments_val.isdigit() else comments_val if isinstance(comments_val, int) else 0
                    shares = int(shares) if isinstance(shares, str) and shares.isdigit() else shares if isinstance(shares, int) else 0

                    all_metadata.append({
                        'post_id': post.get('post_id', ''),
                        'likes': likes,
                        'comments': comments_val,
                        'shares': shares,
                        'author': post.get('author', {}),
                        'text': full_text
                    })

                    # Collect image paths
                    for img_file in sorted(post_dir.glob("image_*")):
                        all_images.append(str(img_file))

    console.print(f"[green]Collected {post_count} posts with {len(all_texts)} text entries and {len(all_images)} images[/green]")

    return {
        'all_texts': all_texts,
        'all_metadata': all_metadata,
        'all_images': all_images,
        'post_count': post_count,
        'keyword': keyword_path.name
    }


def analyze_aggregated_content(content_data: Dict[str, Any],
                             llm_provider: str = "openai",
                             analysis_types: List[str] = None,
                             config: Dict = None) -> Dict[str, Any]:
    """Perform aggregate analysis across all content"""

    # Initialize LLM provider
    try:
        llm = LLMFactory.create_provider(llm_provider)
        console.print(f"\n[green]Using {llm_provider.upper()} for aggregate analysis[/green]")
    except Exception as e:
        console.print(f"[red]Failed to initialize {llm_provider}: {e}[/red]")
        return {}

    # Prepare aggregated text for analysis
    all_texts = content_data['all_texts']
    keyword = content_data['keyword']
    post_count = content_data['post_count']

    # Create a comprehensive corpus for analysis
    corpus = "\n\n---POST SEPARATOR---\n\n".join(all_texts)

    # Limit corpus size if too large (for token limits)
    max_chars = 30000  # Approximately 7500 tokens
    if len(corpus) > max_chars:
        console.print(f"[yellow]Corpus too large ({len(corpus)} chars), truncating to {max_chars} chars[/yellow]")
        corpus = corpus[:max_chars]

    results = {
        'metadata': {
            'keyword': keyword,
            'post_count': post_count,
            'text_count': len(all_texts),
            'provider': llm_provider
        },
        'analysis': {}
    }

    console.print(f"\n[bold cyan]Performing Aggregate Analysis on {post_count} Posts[/bold cyan]")
    console.print(f"[cyan]Keyword: {keyword}[/cyan]")
    console.print(f"[cyan]Analysis types: {', '.join(analysis_types)}[/cyan]\n")

    # Run each analysis type on the aggregated content
    for analysis_type in analysis_types:
        console.print(f"[yellow]Running {analysis_type} analysis...[/yellow]")

        # Get the aggregate prompt for this analysis type
        type_config = config['analysis_types'].get(analysis_type, {})

        # Create aggregate-specific prompt
        aggregate_prompt = f"""
You are analyzing {post_count} posts from Xiaohongshu about "{keyword}".
This is an AGGREGATE ANALYSIS - you should identify patterns, themes, and insights ACROSS ALL POSTS, not analyze individual posts.

IMPORTANT: Your analysis should:
1. Identify patterns and themes that emerge across multiple posts
2. Find commonalities and differences in how users discuss this topic
3. Extract insights that represent the collective conversation
4. Identify trends and recurring elements
5. Synthesize findings at the aggregate level

{type_config.get('text_prompt', '')}

CORPUS OF ALL POSTS:
{corpus}

Remember: This is aggregate analysis - look for patterns ACROSS posts, not within individual posts.
"""

        try:
            # Use the LLM to analyze the aggregated content
            result = llm.analyze_text(corpus, custom_prompt=aggregate_prompt)
            results['analysis'][analysis_type] = result

            # Show preview of results
            if isinstance(result, dict):
                console.print(f"[green]✓ {analysis_type} analysis complete[/green]")
                # Show first few keys
                keys = list(result.keys())[:5]
                console.print(f"  Found keys: {', '.join(keys)}")
            else:
                console.print(f"[green]✓ {analysis_type} analysis complete (text response)[/green]")

        except Exception as e:
            console.print(f"[red]Failed {analysis_type} analysis: {e}[/red]")
            results['analysis'][analysis_type] = {'error': str(e)}

    # Add summary statistics
    results['statistics'] = calculate_statistics(content_data['all_metadata'])

    return results


def calculate_statistics(all_metadata: List[Dict]) -> Dict[str, Any]:
    """Calculate aggregate statistics from metadata"""

    # Ensure we're working with integers
    total_likes = sum(int(post.get('likes', 0)) if isinstance(post.get('likes'), (int, float)) else 0 for post in all_metadata)
    total_comments = sum(int(post.get('comments', 0)) if isinstance(post.get('comments'), (int, float)) else 0 for post in all_metadata)
    total_shares = sum(int(post.get('shares', 0)) if isinstance(post.get('shares'), (int, float)) else 0 for post in all_metadata)

    # Get top performing posts
    top_by_likes = sorted(all_metadata, key=lambda x: x.get('likes', 0), reverse=True)[:5]

    # Author analysis
    authors = Counter(post.get('author', {}).get('name', 'Unknown') for post in all_metadata)

    return {
        'total_posts': len(all_metadata),
        'total_engagement': {
            'likes': total_likes,
            'comments': total_comments,
            'shares': total_shares
        },
        'average_engagement': {
            'likes': total_likes / len(all_metadata) if all_metadata else 0,
            'comments': total_comments / len(all_metadata) if all_metadata else 0,
            'shares': total_shares / len(all_metadata) if all_metadata else 0
        },
        'top_posts': [
            {
                'post_id': p.get('post_id', '')[:20],
                'likes': p.get('likes', 0),
                'text_preview': p.get('text', '')[:100]
            } for p in top_by_likes
        ],
        'top_authors': authors.most_common(5)
    }


def save_aggregate_results(results: Dict, keyword_path: Path):
    """Save aggregate analysis results"""

    output_file = keyword_path / "aggregate_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    console.print(f"\n[green]Results saved to: {output_file}[/green]")

    # Also create a markdown report
    create_markdown_report(results, keyword_path)


def create_markdown_report(results: Dict, keyword_path: Path):
    """Create a readable markdown report"""

    report = []
    report.append(f"# Aggregate Analysis Report: {results['metadata']['keyword']}")
    report.append(f"\n## Overview")
    report.append(f"- **Total Posts Analyzed**: {results['metadata']['post_count']}")
    report.append(f"- **Analysis Provider**: {results['metadata']['provider']}")

    # Add statistics
    stats = results.get('statistics', {})
    if stats:
        report.append(f"\n## Engagement Statistics")
        report.append(f"- **Total Likes**: {stats['total_engagement']['likes']:,}")
        report.append(f"- **Total Comments**: {stats['total_engagement']['comments']:,}")
        report.append(f"- **Average Likes per Post**: {stats['average_engagement']['likes']:.1f}")

        if stats.get('top_posts'):
            report.append(f"\n### Top Performing Posts")
            for i, post in enumerate(stats['top_posts'][:3], 1):
                report.append(f"{i}. Post {post['post_id']} - {post['likes']} likes")
                report.append(f"   > {post['text_preview']}...")

    # Add analysis results
    for analysis_type, content in results['analysis'].items():
        report.append(f"\n## {analysis_type.replace('_', ' ').title()} Analysis")

        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, list):
                    report.append(f"\n### {key.replace('_', ' ').title()}")
                    for item in value[:5]:  # Limit to first 5 items
                        if isinstance(item, dict):
                            report.append(f"- {json.dumps(item, ensure_ascii=False)}")
                        else:
                            report.append(f"- {item}")
                elif isinstance(value, dict):
                    report.append(f"\n### {key.replace('_', ' ').title()}")
                    report.append(f"```json\n{json.dumps(value, ensure_ascii=False, indent=2)}\n```")
                else:
                    report.append(f"\n### {key.replace('_', ' ').title()}")
                    report.append(str(value))
        else:
            report.append(str(content))

    # Save markdown report
    report_file = keyword_path / "aggregate_analysis_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    console.print(f"[green]Markdown report saved to: {report_file}[/green]")


def analyze_downloaded_content(content_dir: str = "data/downloaded_content",
                              llm_provider: str = "openai",
                              analysis_types: List[str] = None,
                              use_preset: str = None,
                              target_keyword: str = None,
                              use_latest: bool = False):
    """Main entry point for aggregate analysis"""

    content_path = Path(content_dir)
    if not content_path.exists():
        console.print("[red]No downloaded content found. Please run 'python main.py' first.[/red]")
        return

    # Find the most recent date folder
    date_folders = sorted([d for d in content_path.iterdir() if d.is_dir()])
    if not date_folders:
        console.print("[red]No date folders found. Please run 'python main.py' first.[/red]")
        return

    # Determine which folder to analyze
    keyword_path = None

    if use_latest:
        # Find the most recently modified folder across all dates
        all_keyword_folders = []
        for date_folder in date_folders:
            for keyword_folder in date_folder.iterdir():
                if keyword_folder.is_dir():
                    # Get modification time
                    mtime = keyword_folder.stat().st_mtime
                    all_keyword_folders.append((mtime, keyword_folder))

        if all_keyword_folders:
            # Sort by modification time and get the latest
            all_keyword_folders.sort(key=lambda x: x[0], reverse=True)
            keyword_path = all_keyword_folders[0][1]
            console.print(f"[cyan]Using latest scrape: {keyword_path.parent.name}/{keyword_path.name}[/cyan]")
        else:
            console.print("[red]No keyword folders found.[/red]")
            return

    elif target_keyword:
        # Search for the specific keyword folder
        for date_folder in reversed(date_folders):
            potential_path = date_folder / target_keyword
            if potential_path.exists():
                keyword_path = potential_path
                console.print(f"[cyan]Found in: {date_folder.name}/{target_keyword}[/cyan]")
                break
        else:
            console.print(f"[red]Keyword folder '{target_keyword}' not found.[/red]")
            return

    else:
        # Interactive selection
        latest_date = date_folders[-1]
        keyword_folders = sorted([k for k in latest_date.iterdir() if k.is_dir()])

        if not keyword_folders:
            console.print("[red]No keyword folders found.[/red]")
            return

        if len(keyword_folders) > 1:
            console.print("\n[cyan]Multiple keywords found. Choose which to analyze:[/cyan]")
            for i, folder in enumerate(keyword_folders, 1):
                post_count = len([p for p in folder.iterdir() if p.is_dir()])
                console.print(f"{i}. {folder.name} ({post_count} posts)")
            choice = input("\nEnter number (default: 1): ").strip() or "1"
            keyword_path = keyword_folders[int(choice) - 1]
        else:
            keyword_path = keyword_folders[0]

    console.print(f"\n[bold cyan]Analyzing content from: {keyword_path}[/bold cyan]")

    # Load config
    config_path = Path(__file__).parent / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Determine analysis types to use
    if use_preset:
        # Use a preset combination
        if use_preset in config.get('analysis_presets', {}):
            preset = config['analysis_presets'][use_preset]
            analysis_types = preset['includes']
            console.print(f"[cyan]Using preset: {preset['name']}[/cyan]")
        else:
            console.print(f"[red]Unknown preset: {use_preset}[/red]")
            return
    elif not analysis_types:
        # Default to basic and themes for aggregate analysis
        analysis_types = ['themes', 'semiotics']

    # Show selected analysis types
    console.print("\n[bold cyan]Analysis Types Selected:[/bold cyan]")
    for atype in analysis_types:
        if atype in config['analysis_types']:
            console.print(f"  • {config['analysis_types'][atype]['name']}: {config['analysis_types'][atype]['description']}")

    # Collect all content
    content_data = collect_all_content(keyword_path)

    if not content_data['all_texts']:
        console.print("[red]No text content found to analyze[/red]")
        return

    # Perform aggregate analysis
    results = analyze_aggregated_content(
        content_data,
        llm_provider=llm_provider,
        analysis_types=analysis_types,
        config=config
    )

    # Save results
    save_aggregate_results(results, keyword_path)

    # Display summary
    console.print("\n" + "="*60)
    console.print(Panel(
        f"[bold green]✓ Aggregate Analysis Complete![/bold green]\n\n"
        f"Analyzed {content_data['post_count']} posts about '{content_data['keyword']}'\n"
        f"Results saved to: {keyword_path}/aggregate_analysis.json",
        style="green"
    ))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze downloaded Xiaohongshu content")

    # LLM Provider selection
    parser.add_argument('--openai', action='store_true', help='Use OpenAI (default)')
    parser.add_argument('--gemini', action='store_true', help='Use Google Gemini')
    parser.add_argument('--deepseek', action='store_true', help='Use DeepSeek')
    parser.add_argument('--kimi', action='store_true', help='Use Kimi (Moonshot)')

    # Analysis type selection
    parser.add_argument('--basic', action='store_true', help='Basic sentiment and theme analysis')
    parser.add_argument('--semiotics', action='store_true', help='Semiotic analysis of signs and symbols')
    parser.add_argument('--themes', action='store_true', help='Deep thematic analysis')
    parser.add_argument('--psychology', action='store_true', help='Consumer psychology analysis')
    parser.add_argument('--brand', action='store_true', help='Brand analysis')
    parser.add_argument('--influencer', action='store_true', help='Influencer marketing analysis')
    parser.add_argument('--trends', action='store_true', help='Trend analysis')
    parser.add_argument('--competitive', action='store_true', help='Competitive intelligence')
    parser.add_argument('--cultural', action='store_true', help='Cultural analysis')
    parser.add_argument('--engagement', action='store_true', help='Engagement analysis')
    parser.add_argument('--innovation', action='store_true', help='Innovation opportunities')

    # Analysis presets
    parser.add_argument('--preset', type=str, help='Use a preset combination (marketing_full, cultural_deep, influencer_audit, trend_research)')

    # Folder selection
    parser.add_argument('--keyword', type=str, help='Specific keyword folder to analyze')
    parser.add_argument('--latest', action='store_true', help='Analyze the most recently scraped content')

    args = parser.parse_args()

    # Determine LLM provider
    if args.gemini:
        provider = 'gemini'
    elif args.deepseek:
        provider = 'deepseek'
    elif args.kimi:
        provider = 'kimi'
    else:
        provider = 'openai'

    # Collect analysis types
    analysis_types = []
    type_flags = ['basic', 'semiotics', 'themes', 'psychology', 'brand',
                  'influencer', 'trends', 'competitive', 'cultural',
                  'engagement', 'innovation']

    for flag in type_flags:
        if getattr(args, flag, False):
            analysis_types.append(flag)

    # Run analysis
    analyze_downloaded_content(
        llm_provider=provider,
        analysis_types=analysis_types if analysis_types else None,
        use_preset=args.preset,
        target_keyword=args.keyword,
        use_latest=args.latest
    )