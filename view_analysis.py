#!/usr/bin/env python3
"""
View aggregate analysis results in a formatted display
"""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint

console = Console()

def view_aggregate_analysis(keyword: str = None):
    """View the aggregate analysis results"""

    # Find the results
    if keyword:
        # Search for specific keyword
        base_path = Path("data/downloaded_content")
        results_file = None
        for date_dir in sorted(base_path.iterdir(), reverse=True):
            if date_dir.is_dir():
                keyword_path = date_dir / keyword
                if keyword_path.exists():
                    results_file = keyword_path / "aggregate_analysis.json"
                    if results_file.exists():
                        break
    else:
        # Find latest
        base_path = Path("data/downloaded_content")
        results_file = None
        for date_dir in sorted(base_path.iterdir(), reverse=True):
            if date_dir.is_dir():
                for keyword_dir in sorted(date_dir.iterdir(), reverse=True):
                    if keyword_dir.is_dir():
                        potential_file = keyword_dir / "aggregate_analysis.json"
                        if potential_file.exists():
                            results_file = potential_file
                            break
                if results_file:
                    break

    if not results_file or not results_file.exists():
        console.print("[red]No aggregate analysis results found![/red]")
        return

    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # Display header
    metadata = results.get('metadata', {})
    console.print(Panel.fit(
        f"[bold cyan]Aggregate Analysis Results[/bold cyan]\n"
        f"Keyword: {metadata.get('keyword', 'Unknown')}\n"
        f"Posts Analyzed: {metadata.get('post_count', 0)}",
        style="cyan"
    ))

    # Display statistics
    stats = results.get('statistics', {})
    if stats:
        console.print("\n[bold yellow]📊 ENGAGEMENT STATISTICS[/bold yellow]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Total", justify="right")
        table.add_column("Average", justify="right")

        table.add_row(
            "Likes",
            f"{stats['total_engagement']['likes']:,}",
            f"{stats['average_engagement']['likes']:.1f}"
        )
        table.add_row(
            "Comments",
            f"{stats['total_engagement']['comments']:,}",
            f"{stats['average_engagement']['comments']:.1f}"
        )
        table.add_row(
            "Shares",
            f"{stats['total_engagement']['shares']:,}",
            f"{stats['average_engagement']['shares']:.1f}"
        )

        console.print(table)

    # Display themes if available
    analysis = results.get('analysis', {})
    if 'themes' in analysis:
        themes_data = analysis['themes']

        console.print("\n[bold green]🎯 KEY THEMES IDENTIFIED[/bold green]\n")

        if 'themes' in themes_data and isinstance(themes_data['themes'], list):
            for i, theme in enumerate(themes_data['themes'][:4], 1):
                if isinstance(theme, dict):
                    console.print(f"[bold cyan]{i}. {theme.get('title', 'Unknown Theme')}[/bold cyan]")
                    console.print(f"   {theme.get('explanation', '')[:200]}...")

                    # Show evidence
                    if 'evidence' in theme:
                        console.print("   [dim]Evidence:[/dim]")
                        for evidence in theme['evidence'][:3]:
                            console.print(f"     • {evidence[:50]}...")

                    # Show opportunities
                    if 'opportunities' in theme:
                        console.print(f"   [yellow]Opportunity:[/yellow] {theme['opportunities'][:150]}...")

                    console.print()

    # Display semiotic insights
    if 'semiotics' in analysis:
        semiotics_data = analysis['semiotics']

        console.print("\n[bold magenta]🔍 SEMIOTIC INSIGHTS[/bold magenta]\n")

        # Cultural codes
        if 'cultural_codes' in semiotics_data:
            codes = semiotics_data['cultural_codes']
            console.print("[cyan]Cultural Codes Identified:[/cyan]")

            if isinstance(codes, dict):
                for category, items in list(codes.items())[:3]:
                    console.print(f"  • {category.replace('_', ' ').title()}:")
                    if isinstance(items, list):
                        for item in items[:2]:
                            console.print(f"      - {item}")

        # Myths and narratives
        if 'myths' in semiotics_data:
            myths = semiotics_data['myths']
            console.print("\n[cyan]Consumer Myths:[/cyan]")

            if isinstance(myths, dict):
                for myth_type, myth_list in list(myths.items())[:2]:
                    if isinstance(myth_list, list) and myth_list:
                        console.print(f"  • {myth_type.replace('_', ' ').title()}: {myth_list[0]}")

    # Display patterns
    if 'themes' in analysis and 'patterns' in analysis['themes']:
        patterns = analysis['themes']['patterns']

        console.print("\n[bold blue]📈 EMERGING PATTERNS[/bold blue]")

        if isinstance(patterns, dict):
            for key, value in list(patterns.items())[:3]:
                console.print(f"  • {key.replace('_', ' ').title()}: {value}")
        elif isinstance(patterns, list):
            for pattern in patterns[:3]:
                console.print(f"  • {pattern}")

    # Display innovation opportunities
    console.print("\n[bold green]💡 STRATEGIC RECOMMENDATIONS[/bold green]")
    console.print("Based on the aggregate analysis:")
    console.print("  1. Focus on flavor innovation and limited editions")
    console.print("  2. Leverage gift-giving culture in marketing")
    console.print("  3. Build emotional connections through sensory experiences")
    console.print("  4. Target niche markets with exclusive offerings")
    console.print("  5. Normalize conversations through playful branding")

    console.print(f"\n[dim]Full results saved in: {results_file}[/dim]")
    console.print(f"[dim]Markdown report: {results_file.parent / 'aggregate_analysis_report.md'}[/dim]")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="View aggregate analysis results")
    parser.add_argument('--keyword', type=str, help='Specific keyword to view')

    args = parser.parse_args()

    view_aggregate_analysis(keyword=args.keyword)