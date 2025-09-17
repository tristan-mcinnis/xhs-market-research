"""Scraper with retry logic and fallback to cached data"""

import time
from typing import List, Dict, Optional
from pathlib import Path

from rich.panel import Panel

from .base_scraper import BaseScraper
from ..utils.file_handler import FileHandler
from ..core.constants import RAW_RESULTS_FILE, DEFAULT_RETRY_COUNT


class RetryScraper(BaseScraper):
    """Scraper with automatic retry and cache fallback"""

    def __init__(self, max_retries: int = DEFAULT_RETRY_COUNT, console=None):
        """
        Initialize retry scraper

        Args:
            max_retries: Maximum retry attempts
            console: Rich console
        """
        super().__init__(console)
        self.max_retries = max_retries

    def scrape(
        self,
        keyword: str,
        max_items: int = 10,
        use_cache_on_fail: bool = True
    ) -> List[Dict]:
        """
        Scrape with retry logic

        Args:
            keyword: Search keyword
            max_items: Maximum posts to fetch
            use_cache_on_fail: Whether to use cached data on failure

        Returns:
            List of scraped posts
        """
        self.console.print(Panel(
            f"[bold cyan]Scraping with Retry[/bold cyan]\n"
            f"Keyword: {keyword}\n"
            f"Posts: {max_items}\n"
            f"Max retries: {self.max_retries}",
            style="cyan"
        ))

        for attempt in range(1, self.max_retries + 1):
            self.console.print(f"\n[yellow]Attempt {attempt}/{self.max_retries}...[/yellow]")

            try:
                results = self._attempt_scrape(keyword, max_items)

                if results:
                    self.console.print(
                        f"[green]✓ Success on attempt {attempt}: "
                        f"{len(results)} posts collected[/green]"
                    )
                    self._save_results(keyword, results)
                    return results

            except Exception as e:
                self.console.print(f"[red]Attempt {attempt} failed: {e}[/red]")

                if attempt < self.max_retries:
                    wait_time = self._get_backoff_time(attempt)
                    self.console.print(
                        f"[yellow]Waiting {wait_time} seconds before retry...[/yellow]"
                    )
                    time.sleep(wait_time)

        # All retries failed
        self.console.print("[red]All retry attempts failed[/red]")

        if use_cache_on_fail:
            cached = self._get_cached_data(keyword)
            if cached:
                self.console.print(
                    f"[yellow]Using cached data: {len(cached)} posts[/yellow]"
                )
                return cached

        return []

    def _attempt_scrape(self, keyword: str, max_items: int) -> List[Dict]:
        """Single scrape attempt"""
        run_input = self._create_run_input(keyword, max_items)
        return self._execute_scrape(run_input)

    def _get_backoff_time(self, attempt: int) -> int:
        """Calculate exponential backoff time"""
        return min(2 ** attempt, 30)  # Max 30 seconds

    def _save_results(self, keyword: str, results: List[Dict]):
        """Save scrape results"""
        output_dir = self.get_output_dir(keyword)
        FileHandler.ensure_directory(output_dir)
        FileHandler.write_json(results, output_dir / RAW_RESULTS_FILE)

    def _get_cached_data(self, keyword: str) -> Optional[List[Dict]]:
        """Try to load cached data from previous runs"""
        # Look for recent data folders
        recent_folders = FileHandler.get_recent_folders(self.get_output_dir().parent)

        for folder in recent_folders:
            keyword_dir = folder / keyword
            if keyword_dir.exists():
                raw_file = keyword_dir / RAW_RESULTS_FILE
                cached = FileHandler.read_json(raw_file)
                if cached:
                    self.console.print(
                        f"[green]Found cached data from {folder.name}[/green]"
                    )
                    return cached

        return None

    def scrape_with_fallback(
        self,
        keywords: List[str],
        max_items_per: int = 10
    ) -> Dict[str, List[Dict]]:
        """
        Scrape multiple keywords with retry and fallback

        Args:
            keywords: List of search keywords
            max_items_per: Posts per keyword

        Returns:
            Dictionary mapping keywords to results
        """
        results = {}

        for keyword in keywords:
            self.console.print(f"\n[cyan]Processing: {keyword}[/cyan]")
            posts = self.scrape(keyword, max_items_per, use_cache_on_fail=True)
            results[keyword] = posts

        return results