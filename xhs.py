#!/usr/bin/env python3
"""
XHS CLI - Unified command-line interface for Xiaohongshu scraping and analysis
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import print as rprint
from rich.panel import Panel

from src.scrapers import MultiKeywordScraper, ScaleScraper, RetryScraper
from src.analyzers import ContentAnalyzer, AggregateAnalyzer
from src.core.config import config
from src.utils.file_handler import FileHandler

console = Console()


class XHSCli:
    """Main CLI class for XHS scraper"""

    def __init__(self):
        self.console = console
        self.file_handler = FileHandler()
        self.load_config()

    def load_config(self):
        """Load configuration including analysis types and presets"""
        config_path = Path(__file__).parent / "config.yaml"
        if config_path.exists():
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
        else:
            self.config_data = {"analysis_types": {}, "analysis_presets": {}}

    def run(self, args):
        """Main entry point"""
        if not config.is_configured and args.command != 'help':
            self.console.print(
                "[red]Error: API token not configured[/red]\n"
                "Please set APIFY_API_TOKEN in your .env file"
            )
            return

        handlers = {
            'scrape': self.handle_scrape,
            'analyze': self.handle_analyze,
            'list': self.handle_list,
            'interactive': self.handle_interactive,
            'help': self.handle_help
        }

        handler = handlers.get(args.command)
        if handler:
            handler(args)
        else:
            self.handle_help(args)

    def handle_scrape(self, args):
        """Handle scraping commands"""
        if args.interactive:
            self.interactive_scrape()
            return

        keywords = args.keywords
        if args.file:
            keywords = self.load_keywords_from_file(args.file)

        if not keywords:
            self.console.print("[red]No keywords provided[/red]")
            return

        # Choose scraper based on mode and scale
        if args.scale or args.posts > 50:
            self.console.print(f"[cyan]Using scale scraper for {args.posts} posts per keyword[/cyan]")
            scraper = ScaleScraper(batch_size=50, console=self.console)
            results = scraper.scrape(
                queries=keywords,
                posts_per_query=args.posts,
                combine=args.combine
            )
        elif args.retry:
            self.console.print("[cyan]Using retry scraper with fallback logic[/cyan]")
            scraper = RetryScraper(max_retries=args.retries, console=self.console)
            for keyword in keywords:
                scraper.scrape(keyword, max_items=args.posts)
        else:
            scraper = MultiKeywordScraper(console=self.console)
            results = scraper.scrape(
                keywords=keywords,
                posts_per_keyword=args.posts,
                combine=args.combine
            )

        self.console.print("[green]✓ Scraping completed[/green]")

    def handle_analyze(self, args):
        """Handle analysis commands"""
        if args.interactive:
            self.interactive_analyze()
            return

        # Determine analysis directory
        if args.dir:
            content_dir = Path(args.dir)
        elif args.latest:
            content_dir = self.get_latest_content_dir()
        else:
            self.console.print("[red]Please specify --dir or use --latest[/red]")
            return

        if not content_dir or not content_dir.exists():
            self.console.print(f"[red]Directory not found: {content_dir}[/red]")
            return

        # Determine analysis types
        analysis_types = []

        # Check for preset first
        if args.preset:
            preset = self.config_data.get("analysis_presets", {}).get(args.preset)
            if preset:
                analysis_types = preset.get("includes", [])
                self.console.print(f"[cyan]Using preset: {preset['name']}[/cyan]")
            else:
                self.console.print(f"[yellow]Unknown preset: {args.preset}[/yellow]")

        # Add individual analysis types
        type_flags = ['themes', 'semiotics', 'psychology', 'brand', 'innovation',
                     'trends', 'engagement', 'cultural', 'competitive']
        for flag in type_flags:
            if getattr(args, flag, False) and flag not in analysis_types:
                analysis_types.append(flag)

        if not analysis_types:
            analysis_types = ['basic']

        # Initialize analyzer
        analyzer = AggregateAnalyzer(llm_provider=args.provider, console=self.console)

        # Run analysis
        self.console.print(f"[cyan]Running analysis: {', '.join(analysis_types)}[/cyan]")

        results = analyzer.analyze(
            content_dir=content_dir,
            analysis_types=analysis_types,
            include_images=args.images,
            max_images=args.max_images
        )

        # Save results
        output_file = content_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.file_handler.write_json(output_file, results)

        # Create markdown report
        report_file = content_dir / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self.create_analysis_report(results, report_file, analysis_types)

        self.console.print(f"[green]✓ Analysis completed[/green]")
        self.console.print(f"Results: {output_file}")
        self.console.print(f"Report: {report_file}")

    def handle_list(self, args):
        """List available data and analysis options"""
        if args.what == 'data':
            self.list_data()
        elif args.what == 'presets':
            self.list_presets()
        elif args.what == 'types':
            self.list_analysis_types()
        else:
            self.list_data()

    def handle_interactive(self, args):
        """Launch fully interactive mode"""
        self.console.print(Panel.fit(
            "[bold cyan]XHS Scraper - Interactive Mode[/bold cyan]\n"
            "Choose your workflow below",
            border_style="cyan"
        ))

        choices = [
            "1. Scrape content from Xiaohongshu",
            "2. Analyze existing content",
            "3. View available data",
            "4. Exit"
        ]

        for choice in choices:
            self.console.print(f"  {choice}")

        selection = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4"])

        if selection == "1":
            self.interactive_scrape()
        elif selection == "2":
            self.interactive_analyze()
        elif selection == "3":
            self.list_data()
        elif selection == "4":
            self.console.print("[yellow]Goodbye![/yellow]")

    def interactive_scrape(self):
        """Interactive scraping workflow"""
        self.console.print("\n[bold cyan]Scraping Configuration[/bold cyan]")

        # Get keywords
        input_method = Prompt.ask(
            "How would you like to input keywords?",
            choices=["manual", "file"]
        )

        keywords = []
        if input_method == "manual":
            self.console.print("Enter keywords (one per line, empty line to finish):")
            while True:
                keyword = Prompt.ask("Keyword (or press Enter to finish)", default="")
                if not keyword:
                    break
                keywords.append(keyword)
        else:
            file_path = Prompt.ask("Enter path to keywords file")
            keywords = self.load_keywords_from_file(file_path)

        if not keywords:
            self.console.print("[red]No keywords provided[/red]")
            return

        # Get configuration
        posts = IntPrompt.ask("Posts per keyword", default=50)
        combine = Confirm.ask("Combine results into single folder?", default=False)

        # Determine scraper type
        if posts > 50:
            use_scale = Confirm.ask(
                f"Use scale scraper for {posts} posts? (recommended for >50)",
                default=True
            )
        else:
            use_scale = False

        # Execute scraping
        if use_scale:
            scraper = ScaleScraper(batch_size=50, console=self.console)
            combine_name = Prompt.ask("Combined folder name") if combine else None
            scraper.scrape(
                queries=keywords,
                posts_per_query=posts,
                combine=combine_name
            )
        else:
            scraper = MultiKeywordScraper(console=self.console)
            scraper.scrape(
                keywords=keywords,
                posts_per_keyword=posts,
                combine=combine
            )

        self.console.print("[green]✓ Scraping completed[/green]")

        if Confirm.ask("Would you like to analyze the results now?", default=True):
            self.interactive_analyze(use_latest=True)

    def interactive_analyze(self, use_latest=False):
        """Interactive analysis workflow"""
        self.console.print("\n[bold cyan]Analysis Configuration[/bold cyan]")

        # Get content directory
        if use_latest:
            content_dir = self.get_latest_content_dir()
        else:
            choice = Prompt.ask(
                "Select content to analyze",
                choices=["latest", "specific"]
            )

            if choice == "latest":
                content_dir = self.get_latest_content_dir()
            else:
                self.list_data()
                dir_path = Prompt.ask("Enter directory path")
                content_dir = Path(dir_path)

        if not content_dir or not content_dir.exists():
            self.console.print(f"[red]Directory not found[/red]")
            return

        self.console.print(f"[green]Analyzing: {content_dir}[/green]")

        # Choose analysis approach
        approach = Prompt.ask(
            "Analysis approach",
            choices=["preset", "custom", "quick"]
        )

        analysis_types = []

        if approach == "preset":
            # Show presets
            self.list_presets()
            preset_name = Prompt.ask("Select preset",
                                    choices=list(self.config_data.get("analysis_presets", {}).keys()))
            preset = self.config_data["analysis_presets"][preset_name]
            analysis_types = preset["includes"]

        elif approach == "custom":
            # Show available types
            self.list_analysis_types()
            self.console.print("\nSelect analysis types (comma-separated):")
            selected = Prompt.ask("Types").split(',')
            analysis_types = [t.strip() for t in selected]

        else:  # quick
            analysis_types = ["themes", "brand", "engagement"]

        # Image analysis
        include_images = Confirm.ask("Include image analysis?", default=True)
        max_images = 30
        if include_images:
            max_images = IntPrompt.ask("Maximum images to analyze", default=30)

        # LLM provider
        provider = Prompt.ask(
            "LLM Provider",
            choices=["openai", "gemini", "deepseek", "auto"],
            default="auto"
        )

        if provider == "auto":
            provider = None

        # Run analysis
        self.console.print(f"\n[cyan]Running {', '.join(analysis_types)} analysis...[/cyan]")

        analyzer = AggregateAnalyzer(llm_provider=provider, console=self.console)

        results = analyzer.analyze(
            content_dir=content_dir,
            analysis_types=analysis_types,
            include_images=include_images,
            max_images=max_images
        )

        # Save results
        output_file = content_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.file_handler.write_json(output_file, results)

        report_file = content_dir / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self.create_analysis_report(results, report_file, analysis_types)

        self.console.print(f"[green]✓ Analysis completed[/green]")
        self.console.print(f"Results: {output_file}")
        self.console.print(f"Report: {report_file}")

        if Confirm.ask("View report now?", default=True):
            self.display_analysis_report(results)

    def list_data(self):
        """List available scraped data"""
        self.console.print("\n[bold cyan]Available Data:[/bold cyan]")

        download_dir = config.download_dir
        if not download_dir.exists():
            self.console.print("[yellow]No data found[/yellow]")
            return

        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Date", style="dim")
        table.add_column("Keyword/Folder")
        table.add_column("Posts", justify="right")
        table.add_column("Analysis", style="green")

        date_folders = sorted(
            [d for d in download_dir.iterdir() if d.is_dir()],
            reverse=True
        )[:10]

        for folder in date_folders:
            keyword_folders = [d for d in folder.iterdir() if d.is_dir()]
            for kf in keyword_folders:
                # Count posts
                metadata_file = kf / "metadata.json"
                post_count = "?"
                if metadata_file.exists():
                    metadata = self.file_handler.read_json(metadata_file)
                    if metadata:
                        post_count = str(len(metadata))

                # Check for analysis
                has_analysis = "✓" if any(kf.glob("*analysis*.json")) else ""

                table.add_row(
                    folder.name,
                    kf.name,
                    post_count,
                    has_analysis
                )

        self.console.print(table)

    def list_presets(self):
        """List available analysis presets"""
        self.console.print("\n[bold cyan]Analysis Presets:[/bold cyan]")

        presets = self.config_data.get("analysis_presets", {})
        if not presets:
            self.console.print("[yellow]No presets configured[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Preset", style="cyan")
        table.add_column("Description")
        table.add_column("Includes", style="dim")

        for key, preset in presets.items():
            table.add_row(
                key,
                preset.get("description", ""),
                ", ".join(preset.get("includes", []))
            )

        self.console.print(table)

    def list_analysis_types(self):
        """List available analysis types"""
        self.console.print("\n[bold cyan]Analysis Types:[/bold cyan]")

        types = self.config_data.get("analysis_types", {})
        if not types:
            self.console.print("[yellow]No analysis types configured[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan")
        table.add_column("Name")
        table.add_column("Description", style="dim")

        for key, type_config in types.items():
            table.add_row(
                key,
                type_config.get("name", key),
                type_config.get("description", "")[:50] + "..."
            )

        self.console.print(table)

    def get_latest_content_dir(self) -> Optional[Path]:
        """Get the most recent content directory"""
        download_dir = config.download_dir
        if not download_dir.exists():
            return None

        # Get most recent date folder
        date_folders = sorted(
            [d for d in download_dir.iterdir() if d.is_dir()],
            reverse=True
        )

        if not date_folders:
            return None

        # Get most recent keyword folder
        latest_date = date_folders[0]
        keyword_folders = sorted(
            [d for d in latest_date.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        return keyword_folders[0] if keyword_folders else None

    def load_keywords_from_file(self, file_path: str) -> List[str]:
        """Load keywords from a text file"""
        path = Path(file_path)
        if not path.exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return []

        with open(path, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip()]

        return keywords

    def create_analysis_report(self, results: Dict[str, Any], output_file: Path, analysis_types: List[str]):
        """Create a markdown report from analysis results"""
        report = []
        report.append("# Xiaohongshu Content Analysis Report")
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\nAnalysis Types: {', '.join(analysis_types)}")

        # Add each analysis section
        for analysis_type in analysis_types:
            if analysis_type in results:
                report.append(f"\n## {analysis_type.title()} Analysis")

                type_results = results[analysis_type]
                if isinstance(type_results, dict):
                    for key, value in type_results.items():
                        report.append(f"\n### {key.replace('_', ' ').title()}")
                        if isinstance(value, list):
                            for item in value:
                                report.append(f"- {item}")
                        else:
                            report.append(str(value))
                else:
                    report.append(str(type_results))

        # Write report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

    def display_analysis_report(self, results: Dict[str, Any]):
        """Display analysis results in console"""
        for analysis_type, type_results in results.items():
            self.console.print(f"\n[bold cyan]{analysis_type.title()} Analysis:[/bold cyan]")

            if isinstance(type_results, dict):
                for key, value in type_results.items():
                    self.console.print(f"\n[yellow]{key.replace('_', ' ').title()}:[/yellow]")
                    if isinstance(value, list):
                        for item in value[:3]:  # Show first 3 items
                            self.console.print(f"  • {item}")
                        if len(value) > 3:
                            self.console.print(f"  ... and {len(value) - 3} more")
                    else:
                        self.console.print(f"  {str(value)[:200]}...")

    def handle_help(self, args):
        """Display help information"""
        help_text = """
[bold cyan]XHS CLI - Xiaohongshu Content Scraper & Analyzer[/bold cyan]

[yellow]Commands:[/yellow]
  scrape     - Scrape content from Xiaohongshu
  analyze    - Analyze scraped content
  list       - List available data, presets, or analysis types
  interactive - Launch interactive mode
  help       - Show this help message

[yellow]Examples:[/yellow]
  # Scrape content
  xhs scrape "keyword1" "keyword2" --posts 100 --combine
  xhs scrape --file keywords.txt --scale --posts 200
  xhs scrape --interactive

  # Analyze content
  xhs analyze --latest --preset marketing_full
  xhs analyze --dir data/20240101/keyword --themes --brand --images 30
  xhs analyze --interactive

  # List available options
  xhs list data
  xhs list presets
  xhs list types

  # Interactive mode
  xhs interactive

[yellow]Quick Start:[/yellow]
  1. Set APIFY_API_TOKEN in .env file
  2. Run: xhs interactive
  3. Follow the prompts
"""
        self.console.print(help_text)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="XHS CLI - Unified interface for Xiaohongshu scraping and analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape content')
    scrape_parser.add_argument('keywords', nargs='*', help='Keywords to search')
    scrape_parser.add_argument('--file', help='Load keywords from file')
    scrape_parser.add_argument('--posts', type=int, default=50, help='Posts per keyword (default: 50)')
    scrape_parser.add_argument('--combine', help='Combine results into named folder')
    scrape_parser.add_argument('--scale', action='store_true', help='Use scale scraper for large collections')
    scrape_parser.add_argument('--retry', action='store_true', help='Use retry logic for timeouts')
    scrape_parser.add_argument('--retries', type=int, default=3, help='Max retries (default: 3)')
    scrape_parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze content')
    analyze_parser.add_argument('--dir', help='Directory to analyze')
    analyze_parser.add_argument('--latest', action='store_true', help='Analyze latest scraped content')
    analyze_parser.add_argument('--preset', help='Use analysis preset (e.g., marketing_full)')
    analyze_parser.add_argument('--provider', choices=['openai', 'gemini', 'deepseek'], help='LLM provider')
    analyze_parser.add_argument('--images', action='store_true', help='Include image analysis')
    analyze_parser.add_argument('--max-images', type=int, default=30, help='Max images to analyze (default: 30)')
    analyze_parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')

    # Individual analysis type flags
    analyze_parser.add_argument('--themes', action='store_true', help='Thematic analysis')
    analyze_parser.add_argument('--semiotics', action='store_true', help='Semiotic analysis')
    analyze_parser.add_argument('--psychology', action='store_true', help='Consumer psychology')
    analyze_parser.add_argument('--brand', action='store_true', help='Brand analysis')
    analyze_parser.add_argument('--innovation', action='store_true', help='Innovation opportunities')
    analyze_parser.add_argument('--trends', action='store_true', help='Trend analysis')
    analyze_parser.add_argument('--engagement', action='store_true', help='Engagement analysis')
    analyze_parser.add_argument('--cultural', action='store_true', help='Cultural analysis')
    analyze_parser.add_argument('--competitive', action='store_true', help='Competitive analysis')

    # List command
    list_parser = subparsers.add_parser('list', help='List available options')
    list_parser.add_argument('what', nargs='?', choices=['data', 'presets', 'types'],
                           default='data', help='What to list')

    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Launch interactive mode')

    # Help command
    help_parser = subparsers.add_parser('help', help='Show help message')

    # Parse arguments
    args = parser.parse_args()

    # Default to interactive if no command
    if not args.command:
        args.command = 'interactive'

    # Run CLI
    cli = XHSCli()
    cli.run(args)


if __name__ == "__main__":
    main()