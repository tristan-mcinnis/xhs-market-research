"""Large-scale scraper for comprehensive data collection"""

import time
from typing import List, Dict, Optional
from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from .base_scraper import BaseScraper
from ..utils.media import MediaDownloader
from ..utils.file_handler import FileHandler
from ..core.constants import RAW_RESULTS_FILE, DEFAULT_RATE_LIMIT


class ScaleScraper(BaseScraper):
    """Scraper optimized for large-scale collection (100+ posts)"""

    def __init__(self, batch_size: int = 50, console=None):
        """
        Initialize scale scraper

        Args:
            batch_size: Posts per batch request
            console: Rich console
        """
        super().__init__(console)
        self.batch_size = batch_size

    def scrape(
        self,
        queries: List[str],
        posts_per_query: int = 100,
        combine: bool = False
    ) -> Dict[str, List[Dict]]:
        """
        Scrape at scale with batching

        Args:
            queries: List of search queries
            posts_per_query: Target posts per query
            combine: Whether to combine results

        Returns:
            Dictionary mapping queries to results
        """
        self._display_plan(queries, posts_per_query)

        all_results = {}
        combined_results = []

        for query_idx, query in enumerate(queries):
            self.console.print(f"\n[bold cyan]Query {query_idx + 1}/{len(queries)}: {query}[/bold cyan]")

            # Collect in batches
            query_results = self._scrape_in_batches(query, posts_per_query)

            if query_results:
                all_results[query] = query_results

                if combine:
                    combined_results.extend(query_results)
                else:
                    self._save_query_results(query, query_results)

            # Rate limiting between queries
            if query_idx < len(queries) - 1:
                self._apply_rate_limit(delay=10)

        # Handle combined results
        if combine and combined_results:
            self._save_combined_results(combined_results, queries)

        self._display_summary(all_results)
        return all_results

    def _scrape_in_batches(
        self,
        query: str,
        total_posts: int
    ) -> List[Dict]:
        """Scrape in batches to handle large requests"""
        all_results = []
        batches = (total_posts + self.batch_size - 1) // self.batch_size

        for batch_num in range(batches):
            batch_size = min(self.batch_size, total_posts - len(all_results))

            self.console.print(
                f"[yellow]Batch {batch_num + 1}/{batches}: "
                f"Fetching {batch_size} posts...[/yellow]"
            )

            try:
                run_input = self._create_run_input(query, batch_size)
                results = self._execute_scrape(run_input)

                # Tag with query and batch info
                for item in results:
                    item['search_query'] = query
                    item['batch_number'] = batch_num + 1

                all_results.extend(results)

                self.console.print(
                    f"[green]✓ Batch {batch_num + 1}: "
                    f"{len(results)} posts collected[/green]"
                )

                # Stop if we have enough
                if len(all_results) >= total_posts:
                    break

                # Rate limiting between batches
                if batch_num < batches - 1:
                    self._apply_rate_limit()

            except Exception as e:
                self.console.print(f"[red]Batch {batch_num + 1} failed: {e}[/red]")

        return all_results[:total_posts]  # Trim to exact count

    def _save_query_results(self, query: str, results: List[Dict]):
        """Save results for a single query"""
        output_dir = self.get_output_dir(query.replace(" ", "_"))
        FileHandler.ensure_directory(output_dir)

        # Save raw results
        FileHandler.write_json(
            results,
            output_dir / RAW_RESULTS_FILE
        )

        # Download media
        self.console.print("[cyan]Downloading media...[/cyan]")
        downloader = MediaDownloader(output_dir, self.console)
        downloader.process_results(results)

    def _save_combined_results(
        self,
        results: List[Dict],
        queries: List[str]
    ):
        """Save combined results from multiple queries"""
        folder_name = f"combined_{len(queries)}_queries_{len(results)}_posts"
        output_dir = self.get_output_dir(folder_name)
        FileHandler.ensure_directory(output_dir)

        # Save results with summary
        FileHandler.write_json(results, output_dir / RAW_RESULTS_FILE)

        summary = {
            "queries": queries,
            "total_posts": len(results),
            "posts_per_query": {
                q: len([r for r in results if r.get('search_query') == q])
                for q in queries
            }
        }
        FileHandler.write_json(summary, output_dir / "collection_summary.json")

        # Download media
        self.console.print("[cyan]Downloading combined media...[/cyan]")
        downloader = MediaDownloader(output_dir, self.console)
        downloader.process_results(results)

    def _display_plan(self, queries: List[str], posts: int):
        """Display collection plan"""
        self.console.print(Panel(
            f"[bold cyan]Large-Scale Collection Plan[/bold cyan]\n"
            f"Queries: {len(queries)}\n"
            f"Posts per query: {posts}\n"
            f"Batch size: {self.batch_size}\n"
            f"Total expected: {len(queries) * posts} posts",
            style="cyan"
        ))

    def _display_summary(self, results: Dict[str, List[Dict]]):
        """Display collection summary"""
        table = Table(title="Collection Summary")
        table.add_column("Query", style="cyan")
        table.add_column("Posts", justify="right", style="green")

        total = 0
        for query, posts in results.items():
            count = len(posts)
            table.add_row(query, str(count))
            total += count

        table.add_row("", "")
        table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")

        self.console.print(table)