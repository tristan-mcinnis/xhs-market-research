#!/usr/bin/env python3
"""
Two-step Xiaohongshu scraper and downloader
Step 1: Use Apify to scrape post URLs and metadata
Step 2: Download actual media content from URLs
"""

import os
import json
from dotenv import load_dotenv
from apify_client import ApifyClient
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path
import sys

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from modules.media_downloader import XHSMediaDownloader

console = Console()


def scrape_xiaohongshu_posts(search_keyword: str, max_items: int = 10):
    """Step 1: Scrape posts using Apify"""

    console.print(Panel(
        f"[bold cyan]Step 1: Scraping Xiaohongshu Posts[/bold cyan]\n"
        f"Keyword: {search_keyword}\n"
        f"Max items: {max_items}",
        style="cyan"
    ))

    load_dotenv()
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))

    # Use the rented EasyAPI actor
    actor_id = "easyapi/all-in-one-rednote-xiaohongshu-scraper"

    # Correct input configuration - use "keywords" (plural)
    run_input = {
        "mode": "search",
        "keywords": [search_keyword],  # CORRECT parameter name!
        "maxItems": max_items,
        "includeComments": True,
        "downloadImages": True,
        "downloadVideos": True
    }

    console.print(f"[yellow]Starting Apify actor...[/yellow]")

    try:
        # Run the actor
        run = client.actor(actor_id).call(
            run_input=run_input,
            timeout_secs=300  # 5 minute timeout
        )

        if not run:
            console.print("[red]Failed to start actor run[/red]")
            return None

        console.print(f"[green]✅ Actor run completed: {run.get('id')}[/green]")

        # Get results
        results = []
        dataset_id = run.get('defaultDatasetId')

        if dataset_id:
            for item in client.dataset(dataset_id).iterate_items():
                results.append(item)

        console.print(f"[green]✅ Retrieved {len(results)} posts[/green]")

        # Save raw scraper results
        raw_results_file = Path('data/raw_scraper_results.json')
        raw_results_file.parent.mkdir(exist_ok=True)
        with open(raw_results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        console.print(f"[cyan]Raw results saved to: {raw_results_file}[/cyan]")

        return results

    except Exception as e:
        console.print(f"[red]Error during scraping: {e}[/red]")
        return None


def download_media_content(scraper_results: list, max_posts: int = None, search_keyword: str = None):
    """Step 2: Download actual media from scraped URLs"""

    console.print(Panel(
        f"[bold cyan]Step 2: Downloading Media Content[/bold cyan]\n"
        f"Posts to process: {max_posts if max_posts else len(scraper_results)}",
        style="cyan"
    ))

    downloader = XHSMediaDownloader(search_keyword=search_keyword)
    results = downloader.process_scraper_results(scraper_results, max_posts)

    return results


def display_results_summary(download_results: list):
    """Display a summary table of downloaded content"""

    table = Table(title="Download Results Summary", show_header=True)
    table.add_column("Post ID", style="cyan", max_width=20)
    table.add_column("Images", style="green")
    table.add_column("Videos", style="green")
    table.add_column("Title/Desc", style="yellow", max_width=40)
    table.add_column("Author", style="magenta")
    table.add_column("Engagement", style="blue")

    for result in download_results:
        metadata = result['metadata']

        # Get text content
        text = metadata['text_content'].get('title', '')
        if not text:
            text = metadata['text_content'].get('description', '')
        if text:
            text = text[:37] + "..." if len(text) > 40 else text

        # Get author
        author = metadata['author'].get('nickname', 'Unknown')

        # Get engagement
        engagement = metadata['engagement']
        eng_str = f"❤️{engagement.get('likes', '0')}"

        table.add_row(
            result['post_id'][:18] + "...",
            str(len(result['images_downloaded'])),
            str(len(result['videos_downloaded'])),
            text,
            author,
            eng_str
        )

    console.print(table)


def main():
    """Main function to run the two-step scraping and downloading process"""

    console.print("[bold magenta]Xiaohongshu Content Scraper & Downloader[/bold magenta]")
    console.print("="*60)

    # Configuration - can be modified or passed as arguments
    import argparse
    parser = argparse.ArgumentParser(description='Scrape and download Xiaohongshu content')
    parser.add_argument('--keyword', '-k', default="科兰黎", help='Search keyword (default: 科兰黎/Galenic)')
    parser.add_argument('--posts', '-p', type=int, default=10, help='Number of posts to scrape (default: 10)')
    parser.add_argument('--skip-download', action='store_true', help='Skip media download step')
    args = parser.parse_args()

    SEARCH_KEYWORD = args.keyword
    MAX_POSTS = args.posts

    console.print(f"[cyan]Configuration:[/cyan]")
    console.print(f"  • Keyword: {SEARCH_KEYWORD}")
    console.print(f"  • Max posts: {MAX_POSTS}")
    console.print()

    # Step 1: Scrape posts
    console.print("[bold]Step 1: Scraping Posts from Xiaohongshu[/bold]")
    scraper_results = scrape_xiaohongshu_posts(SEARCH_KEYWORD, MAX_POSTS)

    if not scraper_results:
        console.print("[red]Failed to scrape posts. Exiting.[/red]")
        return

    if args.skip_download:
        console.print("[yellow]Skipping download step as requested[/yellow]")
        console.print(f"Raw results saved to: data/raw_scraper_results.json")
        return

    # Step 2: Download media
    console.print("\n[bold]Step 2: Downloading Media Content[/bold]")
    download_results = download_media_content(scraper_results, MAX_POSTS, SEARCH_KEYWORD)

    if not download_results:
        console.print("[red]Failed to download media. Exiting.[/red]")
        return

    # Display summary
    console.print("\n[bold]Process Complete![/bold]\n")
    display_results_summary(download_results)

    # Show file location
    from datetime import datetime
    date_folder = datetime.now().strftime("%Y%m%d")

    console.print(f"\n[bold green]✨ Success![/bold green]")
    console.print(f"Downloaded content saved to: data/downloaded_content/{date_folder}/{SEARCH_KEYWORD}/")
    console.print(f"Each post has its own folder with:")
    console.print(f"  • Images (image_0.jpg, image_1.jpg, etc.)")
    console.print(f"  • Videos (video_0.mp4, video_1.mp4, etc.)")
    console.print(f"  • Metadata (metadata.json)")

    # Next steps
    console.print("\n[bold cyan]Next Steps:[/bold cyan]")
    console.print("1. Run 'python analyze.py' to analyze with AI")
    console.print("2. Check 'data/downloaded_content/' for all media files")
    console.print("3. View 'data/download_summary.json' for complete details")


if __name__ == "__main__":
    main()