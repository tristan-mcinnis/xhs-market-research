#!/usr/bin/env python3
"""
Interactive Query Builder for Xiaohongshu Scraper
Helps users build effective search strategies with a beautiful CLI
"""

import os
import sys
import subprocess
from typing import List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich.text import Text
from rich import box
from rich.columns import Columns
from rich.rule import Rule

console = Console()


class QueryBuilder:
    def __init__(self):
        self.queries = []
        self.search_strategy = None
        self.posts_per_query = 10
        self.combine = False

    def welcome(self):
        """Display welcome message"""
        console.clear()
        welcome_text = """
[bold cyan]🔍 Xiaohongshu Search Query Builder[/bold cyan]

This tool helps you build effective search strategies for market research.
You can create simple or complex queries to gather insights.
        """
        console.print(Panel(
            welcome_text.strip(),
            title="[bold white]Welcome[/bold white]",
            border_style="cyan",
            box=box.ROUNDED
        ))

    def show_strategy_guide(self):
        """Show different search strategies"""
        console.print("\n[bold yellow]📚 Search Strategy Guide[/bold yellow]\n")

        strategies = [
            {
                "title": "🎯 Single Focus",
                "desc": "One specific query",
                "example": "杜蕾斯 口味",
                "use": "Deep dive into one topic"
            },
            {
                "title": "🔀 Competitive",
                "desc": "Multiple brands",
                "example": "杜蕾斯, 杰士邦, 冈本",
                "use": "Compare competitors"
            },
            {
                "title": "🌐 Topic Exploration",
                "desc": "Different angles",
                "example": "品牌 + 口味, 品牌 + 价格",
                "use": "Explore various aspects"
            },
            {
                "title": "📊 Market Scan",
                "desc": "Broad then narrow",
                "example": "避孕套, 避孕套 进口",
                "use": "General to specific"
            }
        ]

        table = Table(
            title="Strategy Options",
            show_header=True,
            header_style="bold magenta",
            box=box.SIMPLE_HEAD,
            title_style="bold white"
        )

        table.add_column("Strategy", style="cyan", width=20)
        table.add_column("Description", style="white", width=25)
        table.add_column("Example", style="green", width=25)
        table.add_column("Best For", style="yellow", width=25)

        for s in strategies:
            table.add_row(s["title"], s["desc"], s["example"], s["use"])

        console.print(table)

    def select_strategy(self):
        """Let user select a search strategy"""
        console.print("\n[bold cyan]Select your search strategy:[/bold cyan]")

        choices = {
            "1": ("single", "Single focused query"),
            "2": ("competitive", "Competitive analysis (multiple brands)"),
            "3": ("exploration", "Topic exploration (brand + attributes)"),
            "4": ("market", "Market scan (broad to narrow)"),
            "5": ("custom", "Custom (build your own)")
        }

        for key, (_, desc) in choices.items():
            console.print(f"  [{key}] {desc}")

        choice = Prompt.ask(
            "\n[bold yellow]Your choice[/bold yellow]",
            choices=list(choices.keys()),
            default="5"
        )

        self.search_strategy = choices[choice][0]
        return self.search_strategy

    def build_single_query(self):
        """Build a single focused query"""
        console.print("\n[bold cyan]🎯 Single Focus Query[/bold cyan]")
        console.print("[dim]Example: 杜蕾斯 口味 (searches for posts with BOTH terms)[/dim]")

        query = Prompt.ask("\n[bold yellow]Enter your search query[/bold yellow]")
        self.queries = [query]

    def build_competitive_queries(self):
        """Build competitive analysis queries"""
        console.print("\n[bold cyan]🔀 Competitive Analysis[/bold cyan]")
        console.print("[dim]Enter brand names to compare[/dim]")

        brands = []
        console.print("\n[yellow]Enter brands one by one (press Enter with empty input to finish):[/yellow]")

        while True:
            brand = Prompt.ask(
                f"  Brand {len(brands) + 1}",
                default="" if brands else None
            )
            if not brand:
                if brands:
                    break
                console.print("[red]Please enter at least one brand![/red]")
            else:
                brands.append(brand)
                console.print(f"    [green]✓ Added: {brand}[/green]")

        # Ask if they want to add attributes
        if Confirm.ask("\n[yellow]Add specific attributes to search?[/yellow]", default=False):
            attributes = Prompt.ask("[yellow]Enter attributes (comma-separated)[/yellow]")
            attrs = [a.strip() for a in attributes.split(",")]

            # Create brand + attribute combinations
            self.queries = []
            for brand in brands:
                for attr in attrs:
                    self.queries.append(f"{brand} {attr}")
        else:
            self.queries = brands

        self.combine = Confirm.ask(
            "\n[yellow]Combine results for unified analysis?[/yellow]",
            default=True
        )

    def build_exploration_queries(self):
        """Build topic exploration queries"""
        console.print("\n[bold cyan]🌐 Topic Exploration[/bold cyan]")
        console.print("[dim]Explore different aspects of a main topic[/dim]")

        base = Prompt.ask("\n[bold yellow]Enter base term (e.g., brand name)[/bold yellow]")

        console.print("\n[yellow]Enter aspects to explore (press Enter to finish):[/yellow]")
        console.print("[dim]Examples: 口味, 价格, 质量, 用户体验, 包装[/dim]")

        aspects = []
        while True:
            aspect = Prompt.ask(
                f"  Aspect {len(aspects) + 1}",
                default="" if aspects else None
            )
            if not aspect:
                if aspects:
                    break
                console.print("[red]Please enter at least one aspect![/red]")
            else:
                aspects.append(aspect)
                console.print(f"    [green]✓ Will search: {base} {aspect}[/green]")

        self.queries = [f"{base} {aspect}" for aspect in aspects]
        self.combine = True

    def build_market_scan_queries(self):
        """Build market scan queries"""
        console.print("\n[bold cyan]📊 Market Scan[/bold cyan]")
        console.print("[dim]Start broad, then get specific[/dim]")

        # Broad query
        broad = Prompt.ask("\n[bold yellow]Enter broad category term[/bold yellow]")
        self.queries = [broad]

        # Narrow queries
        console.print("\n[yellow]Add specific refinements (press Enter to finish):[/yellow]")
        console.print(f"[dim]These will be searched as: {broad} + refinement[/dim]")

        while True:
            refinement = Prompt.ask(
                f"  Refinement {len(self.queries)}",
                default=""
            )
            if not refinement:
                break
            self.queries.append(f"{broad} {refinement}")
            console.print(f"    [green]✓ Added: {broad} {refinement}[/green]")

        self.combine = Confirm.ask(
            "\n[yellow]Combine for comparative analysis?[/yellow]",
            default=True
        )

    def build_custom_queries(self):
        """Build custom queries"""
        console.print("\n[bold cyan]✨ Custom Query Builder[/bold cyan]")
        console.print("[dim]Add queries one by one. Each query is a separate search.[/dim]")
        console.print("[dim]Example: '杜蕾斯 口味' searches for posts with BOTH terms[/dim]")

        console.print("\n[yellow]Enter queries (press Enter with empty input to finish):[/yellow]")

        while True:
            query = Prompt.ask(
                f"  Query {len(self.queries) + 1}",
                default="" if self.queries else None
            )
            if not query:
                if self.queries:
                    break
                console.print("[red]Please enter at least one query![/red]")
            else:
                self.queries.append(query)
                console.print(f"    [green]✓ Added[/green]")

        if len(self.queries) > 1:
            self.combine = Confirm.ask(
                "\n[yellow]Combine all results in one folder?[/yellow]",
                default=False
            )

    def get_posts_count(self):
        """Get number of posts per query"""
        console.print(Rule(style="dim"))

        self.posts_per_query = IntPrompt.ask(
            "\n[bold yellow]How many posts per query?[/bold yellow]",
            default=10,
            show_default=True
        )

    def show_summary(self):
        """Show summary of what will be executed"""
        console.print("\n" + "="*60)
        console.print("\n[bold green]📋 Search Summary[/bold green]\n")

        # Create summary table
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Strategy", self.search_strategy.title())
        table.add_row("Total Queries", str(len(self.queries)))
        table.add_row("Posts per Query", str(self.posts_per_query))
        table.add_row("Total Posts", str(len(self.queries) * self.posts_per_query))
        table.add_row("Combine Results", "Yes" if self.combine else "No")

        console.print(table)

        # Show queries
        console.print("\n[bold cyan]Queries to execute:[/bold cyan]")
        for i, query in enumerate(self.queries, 1):
            console.print(f"  {i}. [green]{query}[/green]")

    def build_command(self) -> str:
        """Build the command to execute"""
        if len(self.queries) == 1 and not self.combine:
            # Use simple scraper for single query
            cmd = f'python main.py --keyword "{self.queries[0]}" --posts {self.posts_per_query}'
        else:
            # Use multi scraper
            queries_str = ' '.join(f'"{q}"' for q in self.queries)
            cmd = f'python scrape_multi.py {queries_str} --posts {self.posts_per_query}'
            if self.combine:
                cmd += ' --combine'

        return cmd

    def execute(self, cmd: str):
        """Execute the built command"""
        console.print(f"\n[bold yellow]Command to execute:[/bold yellow]")
        console.print(f"[green]{cmd}[/green]")

        if Confirm.ask("\n[bold cyan]Execute this command?[/bold cyan]", default=True):
            console.print("\n[bold green]🚀 Starting scraper...[/bold green]\n")
            console.print(Rule(style="dim"))

            try:
                # Execute the command
                result = subprocess.run(cmd, shell=True, check=True)

                console.print(Rule(style="dim"))
                console.print("\n[bold green]✅ Scraping complete![/bold green]")

                # Suggest next steps
                self.suggest_next_steps()

            except subprocess.CalledProcessError as e:
                console.print(f"\n[red]❌ Error executing command: {e}[/red]")
            except KeyboardInterrupt:
                console.print("\n[yellow]Scraping interrupted by user[/yellow]")
        else:
            console.print("\n[yellow]Command not executed. You can copy and run it manually.[/yellow]")

    def suggest_next_steps(self):
        """Suggest next analysis steps"""
        console.print("\n[bold cyan]📊 Suggested Next Steps:[/bold cyan]\n")

        if self.combine or len(self.queries) == 1:
            console.print("1. Run aggregate analysis:")
            console.print("   [green]python analyze.py --latest --themes --semiotics --openai[/green]")
        else:
            console.print("1. Analyze individual folders:")
            console.print("   [green]python analyze.py --latest --themes --openai[/green]")
            console.print("\n2. Or run cross-query analysis:")
            console.print("   [green]python analyze_multi.py[/green]")

        console.print("\n3. View results:")
        console.print("   [green]python view_analysis.py[/green]")

    def run(self):
        """Main interactive flow"""
        self.welcome()
        self.show_strategy_guide()

        strategy = self.select_strategy()

        # Build queries based on strategy
        if strategy == "single":
            self.build_single_query()
        elif strategy == "competitive":
            self.build_competitive_queries()
        elif strategy == "exploration":
            self.build_exploration_queries()
        elif strategy == "market":
            self.build_market_scan_queries()
        else:  # custom
            self.build_custom_queries()

        # Get posts count
        self.get_posts_count()

        # Show summary
        self.show_summary()

        # Build and execute command
        cmd = self.build_command()
        self.execute(cmd)


def main():
    """Main entry point"""
    try:
        builder = QueryBuilder()
        builder.run()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Query builder cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()