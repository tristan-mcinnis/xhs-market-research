"""Multi-keyword scraper for batch operations"""

import json
from typing import List, Dict, Optional
from pathlib import Path

from rich.panel import Panel

from .base_scraper import BaseScraper
from ..utils.media import MediaDownloader
from ..core.constants import RAW_RESULTS_FILE, SUMMARY_FILE


class MultiKeywordScraper(BaseScraper):
    """Scraper for multiple keywords with optional combining"""

    def scrape(
        self,
        keywords: List[str],
        posts_per_keyword: int = 10,
        combine: bool = False
    ) -> Dict[str, List[Dict]]:
        """
        Scrape multiple keywords

        Args:
            keywords: List of search terms
            posts_per_keyword: Max posts per keyword
            combine: Whether to combine results

        Returns:
            Dictionary mapping keywords to results
        """
        self._display_config(keywords, posts_per_keyword, combine)

        all_results = {}
        combined_results = []

        for i, keyword in enumerate(keywords, 1):
            self.console.print(f"\n[yellow]Scraping {i}/{len(keywords)}: {keyword}[/yellow]")

            results = self._scrape_single(keyword, posts_per_keyword)

            if results:
                # Tag results with search keyword
                for item in results:
                    item['search_keyword_used'] = keyword

                all_results[keyword] = results

                if combine:
                    combined_results.extend(results)
                else:
                    self._save_results(results, keyword)

            # Apply rate limiting except for last keyword
            if i < len(keywords):
                self.console.print("[dim]Waiting for rate limit...[/dim]")
                self._apply_rate_limit()

        # Handle combined results
        if combine and combined_results:
            folder_name = self._get_combined_folder_name(keywords)
            self._save_combined_results(combined_results, keywords, folder_name)

        self.console.print("\n[bold green]✅ Multi-keyword scraping complete![/bold green]")
        return all_results

    def _scrape_single(self, keyword: str, max_items: int) -> List[Dict]:
        """Scrape a single keyword"""
        run_input = self._create_run_input(keyword, max_items)
        results = self._execute_scrape(run_input)

        self.console.print(f"[green]✅ Found {len(results)} posts for '{keyword}'[/green]")
        return results

    def _save_results(self, results: List[Dict], keyword: str):
        """Save results for a single keyword"""
        output_dir = self.get_output_dir(keyword)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save raw results
        raw_file = output_dir / RAW_RESULTS_FILE
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Download media
        self._download_media(results, output_dir)

    def _save_combined_results(
        self,
        results: List[Dict],
        keywords: List[str],
        folder_name: str
    ):
        """Save combined results with summary"""
        output_dir = self.get_output_dir(folder_name)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save raw results
        raw_file = output_dir / RAW_RESULTS_FILE
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Create summary
        summary = self._create_summary(results, keywords)
        summary_file = output_dir / SUMMARY_FILE
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # Download media
        self._download_media(results, output_dir)

        self.console.print(
            f"\n[green]Combined results: {len(results)} posts in {folder_name}/[/green]"
        )

    def _download_media(self, results: List[Dict], output_dir: Path):
        """Download media content"""
        self.console.print(f"[cyan]Downloading media...[/cyan]")
        downloader = MediaDownloader(output_dir)
        downloader.process_results(results)

    def _get_combined_folder_name(self, keywords: List[str]) -> str:
        """Generate folder name for combined results"""
        if len(keywords) <= 3:
            return "_".join(k.replace(" ", "-") for k in keywords)
        return f"combined_{len(keywords)}_keywords"

    def _create_summary(self, results: List[Dict], keywords: List[str]) -> Dict:
        """Create summary of search results"""
        return {
            "search_date": self.get_output_dir().name,
            "keywords_searched": keywords,
            "total_posts": len(results),
            "posts_per_keyword": {
                keyword: len([r for r in results if r.get('search_keyword_used') == keyword])
                for keyword in keywords
            }
        }

    def _display_config(self, keywords: List[str], posts: int, combine: bool):
        """Display scraping configuration"""
        self.console.print(Panel(
            f"[bold cyan]Multi-Keyword Scraping[/bold cyan]\n"
            f"Keywords: {', '.join(keywords)}\n"
            f"Posts per keyword: {posts}\n"
            f"Mode: {'Combined' if combine else 'Separate'}",
            style="cyan"
        ))