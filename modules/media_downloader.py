"""
Media downloader for Xiaohongshu content
Downloads actual images, videos and extracts comments from scraped URLs
"""

import os
import requests
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs
import json
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import time

console = Console()


class XHSMediaDownloader:
    """Downloads actual media content from Xiaohongshu URLs"""

    def __init__(self, output_dir: str = "data/downloaded_content", search_keyword: str = None):
        # Create nested structure: base_dir/YYYYMMDD/keyword/posts
        base_dir = Path(output_dir)
        date_folder = datetime.now().strftime("%Y%m%d")

        # Clean the keyword for use as a folder name
        if search_keyword:
            # Remove special characters that might cause issues
            safe_keyword = search_keyword.replace("/", "_").replace("\\", "_").replace(":", "_")
        else:
            safe_keyword = "unknown_query"

        # Create the nested path: data/downloaded_content/20240916/Icebreaker/
        self.output_dir = base_dir / date_folder / safe_keyword
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.search_keyword = search_keyword
        self.date_folder = date_folder

        # Headers to mimic browser requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
            'Referer': 'https://www.xiaohongshu.com/'
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _get_file_hash(self, url: str) -> str:
        """Generate unique filename from URL"""
        return hashlib.md5(url.encode()).hexdigest()

    def _extract_post_id(self, item: Dict) -> str:
        """Extract post ID from various data structures"""
        # Try different possible locations for post ID
        if 'id' in item:
            return item['id']
        if 'item' in item and isinstance(item['item'], dict):
            if 'id' in item['item']:
                return item['item']['id']
            if 'model_type' in item['item'] and 'note_card' in item['item']:
                # Extract from note structure
                return item['item'].get('id', 'unknown')
        if 'link' in item:
            # Extract from URL
            parts = item['link'].split('/')
            for part in parts:
                if len(part) > 20:  # XHS IDs are typically long
                    return part.split('?')[0]
        return f"post_{self._get_file_hash(str(item))[:8]}"

    def download_image(self, url: str, post_id: str, index: int) -> Optional[str]:
        """Download a single image"""
        try:
            # Clean URL - remove any query parameters that might interfere
            clean_url = url.split('?')[0] if '?' in url else url

            # Determine file extension
            ext = '.jpg'
            if 'webp' in url.lower():
                ext = '.webp'
            elif 'png' in url.lower():
                ext = '.png'

            # Create post directory
            post_dir = self.output_dir / post_id
            post_dir.mkdir(exist_ok=True)

            # Download image
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Save image
            filename = post_dir / f"image_{index}{ext}"
            with open(filename, 'wb') as f:
                f.write(response.content)

            return str(filename)

        except Exception as e:
            console.print(f"[yellow]Failed to download image from {url[:50]}...: {e}[/yellow]")
            return None

    def download_video(self, url: str, post_id: str, index: int) -> Optional[str]:
        """Download a single video"""
        try:
            # Create post directory
            post_dir = self.output_dir / post_id
            post_dir.mkdir(exist_ok=True)

            # Download video
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            # Save video
            filename = post_dir / f"video_{index}.mp4"
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return str(filename)

        except Exception as e:
            console.print(f"[yellow]Failed to download video from {url[:50]}...: {e}[/yellow]")
            return None

    def extract_content_from_item(self, item: Dict) -> Dict:
        """Extract all available content from a scraped item"""
        post_id = self._extract_post_id(item)

        result = {
            'post_id': post_id,
            'scraped_at': item.get('scrapedAt', datetime.now().isoformat()),
            'link': item.get('link', ''),
            'keyword': item.get('keyword', ''),
            'text_content': {},
            'images': [],
            'videos': [],
            'comments': [],
            'author': {},
            'engagement': {}
        }

        # Navigate through the nested structure
        note_data = item.get('item', {})
        if 'note_card' in note_data:
            note_card = note_data['note_card']

            # Extract text content (title, description)
            if 'display_title' in note_card:
                result['text_content']['title'] = note_card['display_title']
            elif 'title' in note_card:
                result['text_content']['title'] = note_card['title']

            if 'desc' in note_card:
                result['text_content']['description'] = note_card['desc']
            elif 'description' in note_card:
                result['text_content']['description'] = note_card['description']

            # Extract author info
            if 'user' in note_card:
                user = note_card['user']
                result['author'] = {
                    'nickname': user.get('nickname', user.get('nick_name', '')),
                    'user_id': user.get('user_id', ''),
                    'avatar_url': user.get('avatar', '')
                }

            # Extract engagement metrics
            if 'interact_info' in note_card:
                interact = note_card['interact_info']
                result['engagement'] = {
                    'likes': interact.get('liked_count', '0'),
                    'collects': interact.get('collected_count', '0'),
                    'comments': interact.get('comment_count', '0'),
                    'shares': interact.get('shared_count', '0')
                }

            # Extract image URLs
            if 'image_list' in note_card:
                for img in note_card['image_list']:
                    if 'info_list' in img:
                        for info in img['info_list']:
                            if 'url' in info:
                                result['images'].append(info['url'])
                    elif 'url' in img:
                        result['images'].append(img['url'])
            elif 'cover' in note_card:
                # Sometimes there's just a cover image
                cover = note_card['cover']
                if 'url_default' in cover:
                    result['images'].append(cover['url_default'])
                elif 'url' in cover:
                    result['images'].append(cover['url'])

            # Extract video URLs if present
            if 'video' in note_card:
                video = note_card['video']
                if 'url' in video:
                    result['videos'].append(video['url'])

        return result

    def download_post_media(self, post_data: Dict, download_images: bool = True,
                          download_videos: bool = True) -> Dict:
        """Download all media for a single post"""
        post_id = post_data['post_id']
        # Sanitize post_id for filesystem
        post_id = post_id.replace('#', '_').replace('/', '_')[:50]

        downloaded = {
            'post_id': post_id,
            'images_downloaded': [],
            'videos_downloaded': [],
            'metadata': post_data
        }

        # Download images
        if download_images and post_data['images']:
            for i, img_url in enumerate(post_data['images']):
                filepath = self.download_image(img_url, post_id, i)
                if filepath:
                    downloaded['images_downloaded'].append(filepath)

        # Download videos
        if download_videos and post_data['videos']:
            for i, vid_url in enumerate(post_data['videos']):
                filepath = self.download_video(vid_url, post_id, i)
                if filepath:
                    downloaded['videos_downloaded'].append(filepath)

        # Create post directory if it doesn't exist
        post_dir = self.output_dir / post_id
        post_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata
        metadata_file = post_dir / 'metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(post_data, f, ensure_ascii=False, indent=2)

        return downloaded

    def process_scraper_results(self, scraper_results: List[Dict],
                               max_posts: Optional[int] = None) -> List[Dict]:
        """Process results from Apify scraper and download all media"""

        results = []
        posts_to_process = scraper_results[:max_posts] if max_posts else scraper_results

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:

            task = progress.add_task(
                f"[cyan]Processing {len(posts_to_process)} posts...",
                total=len(posts_to_process)
            )

            for item in posts_to_process:
                # Extract content from scraped item
                post_data = self.extract_content_from_item(item)

                # Download media
                console.print(f"\n[yellow]Processing post {post_data['post_id']}[/yellow]")
                console.print(f"  Found: {len(post_data['images'])} images, {len(post_data['videos'])} videos")

                downloaded = self.download_post_media(post_data)

                console.print(f"  [green]Downloaded: {len(downloaded['images_downloaded'])} images, {len(downloaded['videos_downloaded'])} videos[/green]")

                results.append(downloaded)
                progress.update(task, advance=1)

                # Small delay to avoid rate limiting
                time.sleep(0.5)

        # Save summary
        summary_file = self.output_dir / 'download_summary.json'
        summary = {
            'total_posts': len(results),
            'total_images': sum(len(r['images_downloaded']) for r in results),
            'total_videos': sum(len(r['videos_downloaded']) for r in results),
            'download_time': datetime.now().isoformat(),
            'posts': results
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        console.print(f"\n[bold green]Download Summary:[/bold green]")
        console.print(f"  Posts processed: {summary['total_posts']}")
        console.print(f"  Images downloaded: {summary['total_images']}")
        console.print(f"  Videos downloaded: {summary['total_videos']}")
        console.print(f"  Results saved to: {self.output_dir}")
        console.print(f"  Structure: {self.date_folder}/{self.search_keyword}/[post_ids]/")

        return results