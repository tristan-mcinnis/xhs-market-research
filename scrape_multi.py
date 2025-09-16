#!/usr/bin/env python3
"""
Enhanced Xiaohongshu scraper with multi-keyword support
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List

from apify_client import ApifyClient
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

sys.path.append(str(Path(__file__).parent))
from modules.media_downloader import XHSMediaDownloader as MediaDownloader

console = Console()


def scrape_keywords(keywords: List[str], posts_per_keyword: int = 10, combine: bool = False):
    """
    Scrape multiple keywords - either separately or combined

    Args:
        keywords: List of search terms (e.g., ["杜蕾斯", "口味"] or ["杜蕾斯 口味", "杜蕾斯 巧克力"])
        posts_per_keyword: Max posts to fetch per keyword
        combine: If True, saves all results in one folder for combined analysis
    """

    load_dotenv()
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    actor_id = "easyapi/all-in-one-rednote-xiaohongshu-scraper"

    date_folder = datetime.now().strftime("%Y%m%d")
    all_results = []

    console.print(Panel(
        f"[bold cyan]Multi-Keyword Scraping[/bold cyan]\n"
        f"Keywords: {', '.join(keywords)}\n"
        f"Posts per keyword: {posts_per_keyword}\n"
        f"Mode: {'Combined' if combine else 'Separate'}",
        style="cyan"
    ))

    # Scrape each keyword
    for i, keyword in enumerate(keywords, 1):
        console.print(f"\n[yellow]Scraping {i}/{len(keywords)}: {keyword}[/yellow]")

        run_input = {
            "mode": "search",
            "keywords": [keyword],
            "maxItems": posts_per_keyword,
            "includeComments": True,
            "downloadImages": True,
            "downloadVideos": True
        }

        try:
            run = client.actor(actor_id).call(run_input=run_input, timeout_secs=300)

            if run:
                results = []
                dataset_id = run.get('defaultDatasetId')
                if dataset_id:
                    for item in client.dataset(dataset_id).iterate_items():
                        # Tag each result with its search keyword
                        item['search_keyword_used'] = keyword
                        results.append(item)

                console.print(f"[green]✅ Found {len(results)} posts for '{keyword}'[/green]")

                if combine:
                    # Add to combined results
                    all_results.extend(results)
                else:
                    # Save separately
                    save_and_download(results, date_folder, keyword)

        except Exception as e:
            console.print(f"[red]Error scraping {keyword}: {e}[/red]")

        # Rate limiting
        if i < len(keywords):
            console.print("[dim]Waiting 5 seconds...[/dim]")
            time.sleep(5)

    # Save combined results if requested
    if combine and all_results:
        # Create a descriptive folder name
        if len(keywords) <= 3:
            folder_name = "_".join(k.replace(" ", "-") for k in keywords)
        else:
            folder_name = f"combined_{len(keywords)}_keywords"

        save_and_download(all_results, date_folder, folder_name)

        # Create a summary file
        summary = {
            "search_date": date_folder,
            "keywords_searched": keywords,
            "total_posts": len(all_results),
            "posts_per_keyword": {
                keyword: len([r for r in all_results if r.get('search_keyword_used') == keyword])
                for keyword in keywords
            }
        }

        summary_file = Path(f"data/downloaded_content/{date_folder}/{folder_name}/search_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        console.print(f"\n[green]Combined results: {len(all_results)} posts in {folder_name}/[/green]")

    console.print("\n[bold green]✅ Scraping complete![/bold green]")


def save_and_download(results: List, date_folder: str, folder_name: str):
    """Save results and download media"""

    output_dir = Path(f"data/downloaded_content/{date_folder}/{folder_name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save raw results
    raw_file = output_dir / "raw_scraper_results.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Download media
    console.print(f"[cyan]Downloading media for {folder_name}...[/cyan]")
    downloader = MediaDownloader(
        output_dir=str(output_dir.parent.parent),
        search_keyword=folder_name
    )
    downloader.download_all_content(results)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Multi-keyword Xiaohongshu scraper",
        epilog="""
Examples:
  # Scrape multiple keywords separately:
  python scrape_multi.py "杜蕾斯" "杰士邦" "冈本" --posts 10

  # Scrape and combine for aggregate analysis:
  python scrape_multi.py "杜蕾斯" "杰士邦" --posts 20 --combine

  # Scrape related searches:
  python scrape_multi.py "杜蕾斯 口味" "杜蕾斯 巧克力" "杜蕾斯 泰国" --posts 15 --combine
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('keywords', nargs='+', help='Keywords to search')
    parser.add_argument('--posts', type=int, default=10, help='Posts per keyword (default: 10)')
    parser.add_argument('--combine', action='store_true', help='Combine all results in one folder')

    args = parser.parse_args()

    scrape_keywords(args.keywords, args.posts, args.combine)