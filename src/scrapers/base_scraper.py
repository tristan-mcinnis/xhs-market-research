"""Base scraper class with common functionality"""

import time
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod

from apify_client import ApifyClient
from rich.console import Console

from ..core.config import config
from ..core.constants import (
    SCRAPE_MODE_SEARCH,
    DEFAULT_RATE_LIMIT,
    DEFAULT_TIMEOUT
)


class BaseScraper(ABC):
    """Abstract base class for all scrapers"""

    def __init__(self, console: Optional[Console] = None):
        """Initialize base scraper"""
        if not config.is_configured:
            raise ValueError("Apify API token not configured. Please set APIFY_API_TOKEN in .env")

        self.client = ApifyClient(config.apify_api_token)
        self.actor_id = config.actor_id
        self.console = console or Console()

    def _create_run_input(
        self,
        keyword: str,
        max_items: int = 10,
        include_comments: bool = True,
        download_media: bool = True
    ) -> Dict:
        """Create standard run input for Apify actor"""
        return {
            "mode": SCRAPE_MODE_SEARCH,
            "keywords": [keyword],
            "maxItems": max_items,
            "includeComments": include_comments,
            "downloadImages": download_media,
            "downloadVideos": download_media
        }

    def _execute_scrape(
        self,
        run_input: Dict,
        timeout: int = DEFAULT_TIMEOUT
    ) -> List[Dict]:
        """Execute scraping with error handling"""
        try:
            run = self.client.actor(self.actor_id).call(
                run_input=run_input,
                timeout_secs=timeout
            )

            if run:
                results = []
                dataset_id = run.get('defaultDatasetId')
                if dataset_id:
                    for item in self.client.dataset(dataset_id).iterate_items():
                        results.append(item)
                return results

        except Exception as e:
            self.console.print(f"[red]Scraping error: {e}[/red]")
            raise

        return []

    def _apply_rate_limit(self, delay: int = DEFAULT_RATE_LIMIT):
        """Apply rate limiting between requests"""
        time.sleep(delay)

    def get_output_dir(self, keyword: str = None) -> Path:
        """Get output directory for results"""
        date_folder = datetime.now().strftime("%Y%m%d")
        if keyword:
            return config.download_dir / date_folder / keyword
        return config.download_dir / date_folder

    @abstractmethod
    def scrape(self, *args, **kwargs) -> List[Dict]:
        """Abstract method to be implemented by subclasses"""
        pass