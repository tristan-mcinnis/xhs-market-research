"""CLI commands for XHS Scraper"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers import MultiKeywordScraper, ScaleScraper, RetryScraper
from src.analyzers import ContentAnalyzer, AggregateAnalyzer
from src.core.config import config


console = Console()


def scrape_command(args):
    """Execute scraping command"""
    if args.mode == "multi":
        scraper = MultiKeywordScraper(console=console)
        scraper.scrape(
            keywords=args.keywords,
            posts_per_keyword=args.posts,
            combine=args.combine
        )
    elif args.mode == "scale":
        scraper = ScaleScraper(batch_size=50, console=console)
        scraper.scrape(
            queries=args.keywords,
            posts_per_query=args.posts,
            combine=args.combine
        )
    elif args.mode == "retry":
        scraper = RetryScraper(max_retries=args.retries, console=console)
        for keyword in args.keywords:
            scraper.scrape(keyword, max_items=args.posts)
    else:
        console.print("[red]Invalid scraping mode[/red]")


def analyze_command(args):
    """Execute analysis command"""
    analyzer = ContentAnalyzer(llm_provider=args.provider, console=console)

    if args.dir:
        content_dir = Path(args.dir)
        if content_dir.exists():
            results = analyzer.analyze(
                content_dir,
                analysis_type=args.type,
                include_images=args.images
            )

            # Save results
            output_dir = config.analysis_dir / content_dir.name
            analyzer.save_results(results, output_dir)
            analyzer.create_report(results, output_dir)
        else:
            console.print(f"[red]Directory not found: {args.dir}[/red]")
    else:
        console.print("[red]Please specify a directory to analyze[/red]")


def list_command(args):
    """List available data"""
    console.print("\n[bold cyan]Available Data:[/bold cyan]")

    # List recent download folders
    download_dir = config.download_dir
    if download_dir.exists():
        date_folders = sorted(
            [d for d in download_dir.iterdir() if d.is_dir()],
            reverse=True
        )[:10]

        for folder in date_folders:
            keyword_folders = [d for d in folder.iterdir() if d.is_dir()]
            console.print(f"\n[yellow]{folder.name}:[/yellow]")
            for kf in keyword_folders:
                # Count posts
                metadata_file = kf / "metadata.json"
                post_count = "?"
                if metadata_file.exists():
                    from src.utils.file_handler import FileHandler
                    metadata = FileHandler.read_json(metadata_file)
                    if metadata:
                        post_count = len(metadata)

                console.print(f"  • {kf.name} ({post_count} posts)")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="XHS Scraper - Professional Xiaohongshu Content Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape content")
    scrape_parser.add_argument("keywords", nargs="+", help="Keywords to search")
    scrape_parser.add_argument("--mode", choices=["multi", "scale", "retry"],
                               default="multi", help="Scraping mode")
    scrape_parser.add_argument("--posts", type=int, default=10,
                               help="Posts per keyword")
    scrape_parser.add_argument("--combine", action="store_true",
                               help="Combine results")
    scrape_parser.add_argument("--retries", type=int, default=3,
                               help="Max retries for retry mode")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze content")
    analyze_parser.add_argument("--dir", help="Directory to analyze")
    analyze_parser.add_argument("--type", choices=["general", "market", "competitive"],
                                default="general", help="Analysis type")
    analyze_parser.add_argument("--provider", choices=["openai", "gemini", "deepseek"],
                                help="LLM provider")
    analyze_parser.add_argument("--images", action="store_true",
                                help="Include images in analysis")

    # List command
    list_parser = subparsers.add_parser("list", help="List available data")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Check configuration
    if not config.is_configured:
        console.print(
            "[red]Error: API token not configured[/red]\n"
            "Please set APIFY_API_TOKEN in your .env file"
        )
        return

    # Execute command
    if args.command == "scrape":
        scrape_command(args)
    elif args.command == "analyze":
        analyze_command(args)
    elif args.command == "list":
        list_command(args)


if __name__ == "__main__":
    main()