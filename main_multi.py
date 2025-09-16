#!/usr/bin/env python3
"""
Multi-keyword Xiaohongshu scraper
Supports multiple search queries in one run
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from apify_client import ApifyClient
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from modules.media_downloader import MediaDownloader

console = Console()


def scrape_single_keyword(client: ApifyClient, keyword: str, max_items: int = 10) -> List[Dict]:
    """Scrape posts for a single keyword"""

    console.print(f"\n[yellow]Scraping: {keyword}[/yellow]")

    actor_id = "easyapi/all-in-one-rednote-xiaohongshu-scraper"

    run_input = {
        "mode": "search",
        "keywords": [keyword],
        "maxItems": max_items,
        "includeComments": True,
        "downloadImages": True,
        "downloadVideos": True
    }

    try:
        run = client.actor(actor_id).call(
            run_input=run_input,
            timeout_secs=300
        )

        if not run:
            console.print(f"[red]Failed to scrape {keyword}[/red]")
            return []

        results = []
        dataset_id = run.get('defaultDatasetId')

        if dataset_id:
            for item in client.dataset(dataset_id).iterate_items():
                results.append(item)

        console.print(f"[green]✅ Retrieved {len(results)} posts for '{keyword}'[/green]")
        return results

    except Exception as e:
        console.print(f"[red]Error scraping {keyword}: {e}[/red]")
        return []


def scrape_multiple_keywords(keywords: List[str], max_items_per: int = 10, combined_folder: str = None):
    """
    Scrape multiple keywords and optionally combine results

    Args:
        keywords: List of search terms
        max_items_per: Max items per keyword
        combined_folder: If provided, combines all results in one folder
    """

    console.print(Panel(
        f"[bold cyan]Multi-Keyword Scraping[/bold cyan]\n"
        f"Keywords: {', '.join(keywords)}\n"
        f"Max items per keyword: {max_items_per}\n"
        f"Combined: {'Yes' if combined_folder else 'No'}",
        style="cyan"
    ))

    load_dotenv()
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))

    all_results = {}
    date_folder = datetime.now().strftime("%Y%m%d")

    # Scrape each keyword
    for keyword in keywords:
        results = scrape_single_keyword(client, keyword, max_items_per)
        if results:
            all_results[keyword] = results

        # Rate limiting between searches
        if keyword != keywords[-1]:  # Not the last keyword
            console.print("[dim]Waiting 5 seconds before next search...[/dim]")
            time.sleep(5)

    # Save results
    if combined_folder:
        # Save all results in a combined folder
        output_dir = Path(f"data/downloaded_content/{date_folder}/{combined_folder}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save combined raw results
        combined_results = []
        for keyword, results in all_results.items():
            for result in results:
                result['search_keyword'] = keyword  # Tag each result
                combined_results.append(result)

        raw_file = output_dir / "raw_scraper_results.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, ensure_ascii=False, indent=2)

        console.print(f"\n[green]Combined results saved to: {output_dir}[/green]")

        # Download media for combined results
        console.print("\n[cyan]Downloading media for all keywords...[/cyan]")
        downloader = MediaDownloader(
            output_dir=str(output_dir.parent.parent),  # Base data directory
            search_keyword=combined_folder
        )
        downloader.download_all_content(combined_results)

    else:
        # Save each keyword separately (current behavior)
        for keyword, results in all_results.items():
            output_dir = Path(f"data/downloaded_content/{date_folder}/{keyword}")
            output_dir.mkdir(parents=True, exist_ok=True)

            raw_file = output_dir / "raw_scraper_results.json"
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            console.print(f"\n[green]Results for '{keyword}' saved to: {output_dir}[/green]")

            # Download media
            downloader = MediaDownloader(
                output_dir=str(output_dir.parent.parent),
                search_keyword=keyword
            )
            downloader.download_all_content(results)

    # Summary
    console.print("\n" + "="*60)
    console.print(Panel(
        f"[bold green]✅ Multi-Keyword Scraping Complete![/bold green]\n\n"
        f"Keywords scraped: {len(all_results)}\n"
        f"Total posts: {sum(len(r) for r in all_results.values())}\n"
        f"Location: data/downloaded_content/{date_folder}/",
        style="green"
    ))


def scrape_related_terms(base_keyword: str, related_terms: List[str], max_items_per: int = 10):
    """
    Scrape a base keyword and related terms, combining results

    Example:
        base_keyword="杜蕾斯"
        related_terms=["口味", "巧克力", "草莓"]

    This will search:
        - "杜蕾斯 口味"
        - "杜蕾斯 巧克力"
        - "杜蕾斯 草莓"
    """

    # Create combined search terms
    keywords = [f"{base_keyword} {term}" for term in related_terms]

    # Use base keyword as folder name
    combined_folder = f"{base_keyword}_combined"

    console.print(Panel(
        f"[bold cyan]Related Terms Search[/bold cyan]\n"
        f"Base: {base_keyword}\n"
        f"Related: {', '.join(related_terms)}\n"
        f"Searches: {', '.join(keywords)}",
        style="cyan"
    ))

    scrape_multiple_keywords(keywords, max_items_per, combined_folder)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Multi-keyword Xiaohongshu scraper")

    # Multiple keywords mode
    parser.add_argument('--keywords', nargs='+', help='Multiple keywords to search')
    parser.add_argument('--posts', type=int, default=10, help='Max posts per keyword')
    parser.add_argument('--combine', action='store_true', help='Combine results in one folder')
    parser.add_argument('--folder', type=str, help='Custom folder name for combined results')

    # Related terms mode
    parser.add_argument('--base', type=str, help='Base keyword for related searches')
    parser.add_argument('--related', nargs='+', help='Related terms to append to base')

    args = parser.parse_args()

    if args.base and args.related:
        # Related terms mode
        scrape_related_terms(args.base, args.related, args.posts)

    elif args.keywords:
        # Multiple keywords mode
        folder_name = args.folder or "multi_search" if args.combine else None
        scrape_multiple_keywords(args.keywords, args.posts, folder_name)

    else:
        console.print("[red]Please provide either --keywords or --base with --related[/red]")
        console.print("\nExamples:")
        console.print("  python main_multi.py --keywords 杜蕾斯 杰士邦 冈本 --posts 10")
        console.print("  python main_multi.py --keywords 杜蕾斯 口味 --combine --folder durex_flavors")
        console.print("  python main_multi.py --base 杜蕾斯 --related 口味 巧克力 草莓 --posts 15")