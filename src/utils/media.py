"""Media download and processing utilities"""

import json
import requests
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..core.constants import METADATA_FILE, MEDIA_TYPE_IMAGE, MEDIA_TYPE_VIDEO


class MediaDownloader:
    """Handle media downloads from XHS posts"""

    def __init__(self, output_dir: Path, console: Optional[Console] = None):
        """
        Initialize media downloader

        Args:
            output_dir: Directory for downloads
            console: Rich console for output
        """
        self.output_dir = Path(output_dir)
        self.console = console or Console()
        self.media_dir = self.output_dir / "media"
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def process_results(self, results: List[Dict]) -> Dict[str, int]:
        """
        Process scraper results and download media

        Args:
            results: List of post data from scraper

        Returns:
            Statistics about downloaded content
        """
        stats = {
            "total_posts": len(results),
            "images_downloaded": 0,
            "videos_downloaded": 0,
            "failed_downloads": 0
        }

        metadata = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task(
                "Downloading media...",
                total=len(results)
            )

            for i, post in enumerate(results):
                post_metadata = self._process_post(post, i + 1)
                if post_metadata:
                    metadata.append(post_metadata)

                    # Update stats
                    stats["images_downloaded"] += len(post_metadata.get("images", []))
                    stats["videos_downloaded"] += len(post_metadata.get("videos", []))

                progress.update(task, advance=1)

        # Save metadata
        self._save_metadata(metadata)
        self._display_stats(stats)

        return stats

    def _process_post(self, post: Dict, post_num: int) -> Optional[Dict]:
        """Process a single post"""
        try:
            post_id = post.get("id", f"post_{post_num}")
            post_dir = self.media_dir / f"post_{post_num:03d}_{post_id}"
            post_dir.mkdir(exist_ok=True)

            metadata = {
                "post_number": post_num,
                "post_id": post_id,
                "title": post.get("title", ""),
                "description": post.get("description", ""),
                "author": post.get("author", {}).get("name", "Unknown"),
                "likes": post.get("likes", 0),
                "comments_count": post.get("commentsCount", 0),
                "timestamp": post.get("timestamp", ""),
                "images": [],
                "videos": []
            }

            # Download images
            images = post.get("images", [])
            for img_idx, img_url in enumerate(images):
                if img_url:
                    file_path = self._download_file(
                        img_url,
                        post_dir / f"image_{img_idx + 1}.jpg",
                        MEDIA_TYPE_IMAGE
                    )
                    if file_path:
                        metadata["images"].append(str(file_path.relative_to(self.output_dir)))

            # Download videos
            videos = post.get("videos", [])
            for vid_idx, vid_url in enumerate(videos):
                if vid_url:
                    file_path = self._download_file(
                        vid_url,
                        post_dir / f"video_{vid_idx + 1}.mp4",
                        MEDIA_TYPE_VIDEO
                    )
                    if file_path:
                        metadata["videos"].append(str(file_path.relative_to(self.output_dir)))

            # Save post text content
            self._save_post_content(post, post_dir)

            return metadata

        except Exception as e:
            self.console.print(f"[red]Error processing post {post_num}: {e}[/red]")
            return None

    def _download_file(
        self,
        url: str,
        file_path: Path,
        media_type: str
    ) -> Optional[Path]:
        """Download a single file"""
        try:
            if file_path.exists():
                return file_path

            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Write file in chunks
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return file_path

        except Exception as e:
            self.console.print(f"[yellow]Failed to download {media_type}: {e}[/yellow]")
            return None

    def _save_post_content(self, post: Dict, post_dir: Path):
        """Save post text content"""
        content_file = post_dir / "content.json"
        content = {
            "title": post.get("title", ""),
            "description": post.get("description", ""),
            "author": post.get("author", {}),
            "stats": {
                "likes": post.get("likes", 0),
                "comments": post.get("commentsCount", 0),
                "shares": post.get("shares", 0)
            },
            "tags": post.get("tags", []),
            "timestamp": post.get("timestamp", "")
        }

        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

    def _save_metadata(self, metadata: List[Dict]):
        """Save download metadata"""
        metadata_file = self.output_dir / METADATA_FILE
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _display_stats(self, stats: Dict):
        """Display download statistics"""
        self.console.print(
            f"\n[green]Download complete:[/green]\n"
            f"  • Posts: {stats['total_posts']}\n"
            f"  • Images: {stats['images_downloaded']}\n"
            f"  • Videos: {stats['videos_downloaded']}"
        )