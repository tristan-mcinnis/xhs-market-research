#!/usr/bin/env python3
"""
Xiaohongshu (RED) Scraper using Apify Actor
Clean, single-file implementation with all functionality
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try importing dependencies
try:
    from apify_client import ApifyClient
    from dotenv import load_dotenv
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: ./setup.sh (macOS/Linux) or setup.bat (Windows)")
    print("Or manually: pip install apify-client requests python-dotenv")
    sys.exit(1)

try:
    from config_loader import get_config
except ImportError:
    print("Error: Unable to import configuration loader (config_loader.py).")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Load configuration
config = get_config()

# Configuration
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN") or config.get_api_config("apify_api_token", "")
ACTOR_ID = config.get_api_config("actor_id", "watk8sVZNzd40UtbQ")

# Default settings (centralized via pipeline_config.json)
DEFAULT_MAX_ITEMS = config.get_pipeline_setting("default_max_items", 30)
DEFAULT_BASE_DIR = Path(config.get_pipeline_setting("default_output_dir", "data"))
REQUEST_DELAY = config.get_pipeline_setting("request_delay", 0.5)
TIMEOUT = config.get_pipeline_setting("timeout", 10)

# Image download headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.xiaohongshu.com/'
}


class XHSActor:
    """Main scraper class using Apify Actor"""

    def __init__(self, api_token: str = APIFY_API_TOKEN):
        if not api_token or api_token == "your_apify_token_here":
            print("❌ Error: Apify API token not configured")
            print("Please add your token to .env file:")
            print("APIFY_API_TOKEN=your_actual_token")
            sys.exit(1)

        self.client = ApifyClient(api_token)
        self.actor_id = ACTOR_ID
        self.current_query_dir = None
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"xhs_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_query_directory(
        self,
        query_name: str,
        scraped_dir: Optional[Path] = None,
        images_dir: Optional[Path] = None,
        query_dir: Optional[Path] = None,
        date_override: Optional[str] = None,
    ):
        """Setup directory structure for a specific query.

        When used inside the orchestration pipeline, directories are pre-created
        by :class:`WorkflowConfig`. In that case we simply reuse the provided
        paths rather than generating a new date-based folder.
        """

        # Allow orchestrator to pass explicit directories
        if scraped_dir and images_dir:
            self.scraped_dir = Path(scraped_dir)
            self.images_dir = Path(images_dir)
            self.scraped_dir.mkdir(parents=True, exist_ok=True)
            self.images_dir.mkdir(parents=True, exist_ok=True)
            parent = Path(query_dir) if query_dir else self.scraped_dir.parent
            parent.mkdir(parents=True, exist_ok=True)
            self.current_query_dir = parent
            self.logger.info(
                "Using provided workflow directories: scraped=%s, images=%s",
                self.scraped_dir,
                self.images_dir,
            )
            return self.current_query_dir

        # Fall back to legacy date-based structure for standalone runs
        date_dir = (date_override or datetime.now().strftime('%Y%m%d'))
        clean_query = "".join(
            c for c in query_name if c.isalnum() or c in (' ', '-', '_')
        ).strip()
        clean_query = clean_query.replace(' ', '_')[:50]

        self.current_query_dir = DEFAULT_BASE_DIR / date_dir / clean_query
        self.scraped_dir = self.current_query_dir / "scraped"
        self.images_dir = self.current_query_dir / "images"

        self.scraped_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Created query directory: {self.current_query_dir}")
        return self.current_query_dir

    def search(
        self,
        keywords: List[str],
        max_items: int = DEFAULT_MAX_ITEMS,
        scraped_dir: Optional[Path] = None,
        images_dir: Optional[Path] = None,
        query_dir: Optional[Path] = None,
        date_override: Optional[str] = None,
    ) -> List[Dict]:
        """Search posts by keywords"""
        query_name = "_".join(keywords)
        print(f"\n🔍 Searching for: {', '.join(keywords)}")
        print(f"   Max items: {max_items}")

        # Setup directory for this query
        self.setup_query_directory(
            query_name,
            scraped_dir=scraped_dir,
            images_dir=images_dir,
            query_dir=query_dir,
            date_override=date_override,
        )

        run_input = {
            "mode": "search",
            "keywords": keywords,
            "maxItems": max_items
        }

        try:
            print("   Running actor...")
            run = self.client.actor(self.actor_id).call(run_input=run_input)

            results = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append(item)

            print(f"✅ Found {len(results)} posts")
            print(f"📁 Saving to: {self.current_query_dir}")

            # Save results
            self.save_results(results, "search")

            # Show statistics
            self.show_statistics(results)

            return results

        except Exception as e:
            self.logger.error(f"Search error: {e}")
            print(f"❌ Error: {e}")
            return []

    def get_comments(self, post_urls: List[str], max_items: int = DEFAULT_MAX_ITEMS) -> List[Dict]:
        """Get comments from posts"""
        print(f"\n💬 Getting comments from {len(post_urls)} posts")

        # Setup directory for comments
        self.setup_query_directory("comments")

        run_input = {
            "mode": "comment",
            "postUrls": post_urls,
            "maxItems": max_items
        }

        try:
            run = self.client.actor(self.actor_id).call(run_input=run_input)

            results = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append(item)

            print(f"✅ Found {len(results)} comments")
            print(f"📁 Saving to: {self.current_query_dir}")
            self.save_results(results, "comments")

            return results

        except Exception as e:
            self.logger.error(f"Comments error: {e}")
            print(f"❌ Error: {e}")
            return []

    def get_profile(self, profile_urls: List[str]) -> List[Dict]:
        """Get user profiles"""
        print(f"\n👤 Getting {len(profile_urls)} profiles")

        # Setup directory for profiles
        self.setup_query_directory("profiles")

        run_input = {
            "mode": "profile",
            "profileUrls": profile_urls
        }

        try:
            run = self.client.actor(self.actor_id).call(run_input=run_input)

            results = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append(item)

            print(f"✅ Got {len(results)} profiles")
            print(f"📁 Saving to: {self.current_query_dir}")
            self.save_results(results, "profiles")

            return results

        except Exception as e:
            self.logger.error(f"Profile error: {e}")
            print(f"❌ Error: {e}")
            return []

    def get_user_posts(self, profile_urls: List[str], max_items: int = DEFAULT_MAX_ITEMS) -> List[Dict]:
        """Get posts from users"""
        print(f"\n📝 Getting posts from {len(profile_urls)} users")

        # Setup directory for user posts
        self.setup_query_directory("user_posts")

        run_input = {
            "mode": "userPosts",
            "profileUrls": profile_urls,
            "maxItems": max_items
        }

        try:
            run = self.client.actor(self.actor_id).call(run_input=run_input)

            results = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append(item)

            print(f"✅ Found {len(results)} user posts")
            print(f"📁 Saving to: {self.current_query_dir}")
            self.save_results(results, "user_posts")

            return results

        except Exception as e:
            self.logger.error(f"User posts error: {e}")
            print(f"❌ Error: {e}")
            return []

    def extract_image_urls(self, results: List[Dict]) -> List[Dict]:
        """Extract image URLs from results"""
        images = []

        for result in results:
            if 'item' in result and 'note_card' in result['item']:
                note = result['item']['note_card']
                title = note.get('display_title', 'untitled')
                post_id = result['item'].get('id', 'unknown')

                if 'image_list' in note:
                    for idx, img in enumerate(note['image_list']):
                        if 'info_list' in img:
                            for info in img['info_list']:
                                if 'url' in info and info.get('image_scene') == 'WB_DFT':
                                    images.append({
                                        'url': info['url'],
                                        'title': title[:50],
                                        'post_id': post_id,
                                        'index': idx
                                    })
                                    break

        return images

    def download_images(self, image_data: List[Dict], max_downloads: Optional[int] = None) -> int:
        """Download images from URLs"""
        if max_downloads:
            image_data = image_data[:max_downloads]

        print(f"\n📥 Downloading {len(image_data)} images...")

        # Use query-specific images directory
        output_dir = self.images_dir if self.current_query_dir else DEFAULT_BASE_DIR / "images"
        output_dir.mkdir(parents=True, exist_ok=True)

        downloaded = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}

            for img in image_data:
                filename = f"{img['post_id']}_{img['index']}_{img['title']}.jpg"
                save_path = output_dir / filename

                if save_path.exists():
                    continue

                future = executor.submit(self._download_single_image, img['url'], save_path)
                futures[future] = filename

            for future in as_completed(futures):
                filename = futures[future]
                success = future.result()

                if success:
                    downloaded += 1
                    print(f"  ✓ {filename[:50]}")
                else:
                    failed += 1
                    print(f"  ✗ {filename[:50]}")

                time.sleep(REQUEST_DELAY)

        print(f"\n✅ Downloaded: {downloaded}, Failed: {failed}")
        print(f"📁 Images saved to: {output_dir}")
        return downloaded

    def _download_single_image(self, url: str, save_path: Path) -> bool:
        """Download a single image"""
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                f.write(response.content)

            return True
        except Exception:
            return False

    def save_results(self, results: List[Dict], prefix: str):
        """Save results to JSON"""
        # Use query-specific scraped directory
        output_dir = self.scraped_dir if self.current_query_dir else DEFAULT_BASE_DIR / "scraped"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = output_dir / f"{prefix}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Results saved to {filename}")

    def show_statistics(self, results: List[Dict]):
        """Show statistics from results"""
        total_posts = len(results)
        total_images = 0
        total_likes = 0

        for result in results:
            if 'item' in result and 'note_card' in result['item']:
                note = result['item']['note_card']

                if 'image_list' in note:
                    total_images += len(note['image_list'])

                likes = note.get('interact_info', {}).get('liked_count', '0')
                try:
                    total_likes += int(likes.replace(',', ''))
                except:
                    pass

        print(f"\n📊 Statistics:")
        print(f"  - Total posts: {total_posts}")
        print(f"  - Total images: {total_images}")
        print(f"  - Total likes: {total_likes:,}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Xiaohongshu (RED) Scraper using Apify Actor',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search posts')
    search_parser.add_argument('keywords', nargs='+', help='Keywords to search')
    search_parser.add_argument('-m', '--max-items', type=int, default=DEFAULT_MAX_ITEMS,
                              help=f'Max items (default: {DEFAULT_MAX_ITEMS})')
    search_parser.add_argument('-d', '--download', action='store_true',
                              help='Download images')
    search_parser.add_argument('--max-downloads', type=int,
                              help='Max images to download (default: unlimited)')
    search_parser.add_argument('--scraped-dir', help='Directory to store raw scraped JSON files')
    search_parser.add_argument('--images-dir', help='Directory to store downloaded images')
    search_parser.add_argument('--query-dir', help='Workflow query directory (parent of step outputs)')
    search_parser.add_argument('--date', help='Override YYYYMMDD date for standalone runs')

    # Comments command
    comments_parser = subparsers.add_parser('comments', help='Get comments')
    comments_parser.add_argument('urls', nargs='+', help='Post URLs')
    comments_parser.add_argument('-m', '--max-items', type=int, default=DEFAULT_MAX_ITEMS,
                                help=f'Max comments (default: {DEFAULT_MAX_ITEMS})')

    # Profile command
    profile_parser = subparsers.add_parser('profile', help='Get profiles')
    profile_parser.add_argument('urls', nargs='+', help='Profile URLs')

    # User posts command
    posts_parser = subparsers.add_parser('user-posts', help='Get user posts')
    posts_parser.add_argument('urls', nargs='+', help='Profile URLs')
    posts_parser.add_argument('-m', '--max-items', type=int, default=DEFAULT_MAX_ITEMS,
                             help=f'Max posts (default: {DEFAULT_MAX_ITEMS})')
    posts_parser.add_argument('-d', '--download', action='store_true',
                             help='Download images')

    # Config command
    config_parser = subparsers.add_parser('config', help='Check configuration')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize scraper
    scraper = XHSActor()

    # Execute commands
    if args.command == 'search':
        results = scraper.search(
            args.keywords,
            max_items=args.max_items,
            scraped_dir=Path(args.scraped_dir) if args.scraped_dir else None,
            images_dir=Path(args.images_dir) if args.images_dir else None,
            query_dir=Path(args.query_dir) if args.query_dir else None,
            date_override=args.date,
        )

        if args.download and results:
            images = scraper.extract_image_urls(results)
            if images:
                scraper.download_images(images, args.max_downloads)

    elif args.command == 'comments':
        scraper.get_comments(args.urls, args.max_items)

    elif args.command == 'profile':
        scraper.get_profile(args.urls)

    elif args.command == 'user-posts':
        results = scraper.get_user_posts(args.urls, args.max_items)

        if args.download and results:
            # Extract images from user posts format
            images = []
            for result in results:
                if 'postData' in result:
                    post = result['postData']
                    if 'cover' in post and 'urlDefault' in post['cover']:
                        images.append({
                            'url': post['cover']['urlDefault'],
                            'title': post.get('displayTitle', 'untitled')[:50],
                            'post_id': post.get('noteId', 'unknown'),
                            'index': 0
                        })

            if images:
                scraper.download_images(images)

    elif args.command == 'config':
        print("Configuration:")
        print(f"  Actor ID: {ACTOR_ID}")
        print(f"  API Token: {'✓ Configured' if APIFY_API_TOKEN else '✗ Not configured'}")
        print(f"  Base Directory: {DEFAULT_BASE_DIR}")
        print(f"  Structure: data/YYYYMMDD/query_name/[scraped|images]")


if __name__ == "__main__":
    main()