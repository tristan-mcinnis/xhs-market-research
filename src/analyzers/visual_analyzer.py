"""Visual content analysis for images and videos"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
import json

from .base_analyzer import BaseAnalyzer


class VisualAnalyzer(BaseAnalyzer):
    """Analyze visual content from posts"""

    def analyze(
        self,
        content_dir: Path,
        max_images: int = 10,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze visual content in a directory

        Args:
            content_dir: Directory containing media
            max_images: Maximum images to analyze
            include_metadata: Whether to include image metadata

        Returns:
            Visual analysis results
        """
        self.console.print(f"[cyan]Analyzing visual content in {content_dir}...[/cyan]")

        # Collect visual content
        visual_data = self._collect_visual_content(content_dir)

        if not visual_data["images"]:
            self.console.print("[yellow]No visual content found[/yellow]")
            return {}

        results = {
            "content_dir": str(content_dir),
            "total_images": len(visual_data["images"]),
            "total_videos": len(visual_data["videos"]),
            "images_analyzed": min(max_images, len(visual_data["images"]))
        }

        # Analyze with vision-capable LLM
        if self.llm and hasattr(self.llm, 'analyze'):
            images_to_analyze = visual_data["images"][:max_images]

            # Create visual analysis prompt
            prompt = self._create_visual_prompt(visual_data["captions"])

            response = self.llm.analyze(prompt, images_to_analyze)
            if response:
                results["visual_analysis"] = response
                results["visual_insights"] = self._extract_visual_insights(response)

        # Add image metadata if requested
        if include_metadata:
            results["image_metadata"] = self._get_image_metadata(
                visual_data["images"][:max_images]
            )

        # Statistical analysis
        results["visual_statistics"] = self._calculate_visual_stats(visual_data)

        return results

    def compare_visual_styles(
        self,
        dir_a: Path,
        dir_b: Path
    ) -> Dict[str, Any]:
        """
        Compare visual styles between two datasets

        Args:
            dir_a: First directory
            dir_b: Second directory

        Returns:
            Visual comparison results
        """
        self.console.print(
            f"[cyan]Comparing visual styles: "
            f"{dir_a.name} vs {dir_b.name}...[/cyan]"
        )

        visual_a = self._collect_visual_content(dir_a)
        visual_b = self._collect_visual_content(dir_b)

        results = {
            "type": "visual_comparison",
            "dataset_a": str(dir_a),
            "dataset_b": str(dir_b)
        }

        # Compare image characteristics
        if visual_a["images"] and visual_b["images"]:
            results["style_comparison"] = self._compare_image_styles(
                visual_a["images"][:5],
                visual_b["images"][:5]
            )

        # LLM visual comparison if available
        if self.llm:
            prompt = """
            Compare the visual styles of these two sets of images:
            1. Overall aesthetic differences
            2. Color palette comparison
            3. Composition and framing
            4. Content themes
            """

            combined_images = visual_a["images"][:3] + visual_b["images"][:3]
            response = self.llm.analyze(prompt, combined_images)

            if response:
                results["llm_comparison"] = response

        return results

    def _collect_visual_content(self, content_dir: Path) -> Dict[str, Any]:
        """Collect all visual content from directory"""
        visual_data = {
            "images": [],
            "videos": [],
            "captions": [],
            "metadata": []
        }

        media_dir = content_dir / "media"
        if not media_dir.exists():
            return visual_data

        # Collect images
        for img_path in media_dir.glob("**/*.jpg"):
            visual_data["images"].append(str(img_path))

        for img_path in media_dir.glob("**/*.png"):
            visual_data["images"].append(str(img_path))

        # Collect videos
        for vid_path in media_dir.glob("**/*.mp4"):
            visual_data["videos"].append(str(vid_path))

        # Load associated metadata
        metadata_file = content_dir / "metadata.json"
        if metadata_file.exists():
            metadata = self.file_handler.read_json(metadata_file)
            if metadata:
                visual_data["metadata"] = metadata
                # Extract captions/descriptions
                for post in metadata:
                    if post.get("description"):
                        visual_data["captions"].append(post["description"])

        return visual_data

    def _create_visual_prompt(self, captions: List[str]) -> str:
        """Create prompt for visual analysis"""
        prompt = """
        Analyze these images from social media posts and provide insights on:
        1. Visual themes and aesthetics
        2. Color schemes and mood
        3. Product presentation (if applicable)
        4. Photography quality and style
        5. Brand consistency (if applicable)
        """

        if captions:
            prompt += "\n\nAssociated captions:\n"
            prompt += "\n".join(captions[:10])

        return prompt

    def _get_image_metadata(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Extract metadata from images"""
        metadata = []

        for img_path in image_paths:
            try:
                img = Image.open(img_path)
                metadata.append({
                    "path": img_path,
                    "size": img.size,
                    "mode": img.mode,
                    "format": img.format,
                    "file_size": Path(img_path).stat().st_size
                })
            except Exception as e:
                self.console.print(f"[yellow]Error reading {img_path}: {e}[/yellow]")

        return metadata

    def _calculate_visual_stats(self, visual_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate visual content statistics"""
        stats = {
            "total_images": len(visual_data["images"]),
            "total_videos": len(visual_data["videos"]),
            "posts_with_media": 0
        }

        # Calculate from metadata if available
        if visual_data["metadata"]:
            posts_with_images = sum(
                1 for post in visual_data["metadata"]
                if post.get("images")
            )
            posts_with_videos = sum(
                1 for post in visual_data["metadata"]
                if post.get("videos")
            )

            stats["posts_with_images"] = posts_with_images
            stats["posts_with_videos"] = posts_with_videos
            stats["posts_with_media"] = posts_with_images + posts_with_videos

        return stats

    def _compare_image_styles(
        self,
        images_a: List[str],
        images_b: List[str]
    ) -> Dict[str, Any]:
        """Compare basic image characteristics"""
        comparison = {
            "dataset_a": {},
            "dataset_b": {}
        }

        # Analyze dataset A
        sizes_a = []
        for img_path in images_a:
            try:
                img = Image.open(img_path)
                sizes_a.append(img.size)
            except:
                pass

        if sizes_a:
            avg_width_a = sum(s[0] for s in sizes_a) // len(sizes_a)
            avg_height_a = sum(s[1] for s in sizes_a) // len(sizes_a)
            comparison["dataset_a"] = {
                "avg_width": avg_width_a,
                "avg_height": avg_height_a,
                "count": len(images_a)
            }

        # Analyze dataset B
        sizes_b = []
        for img_path in images_b:
            try:
                img = Image.open(img_path)
                sizes_b.append(img.size)
            except:
                pass

        if sizes_b:
            avg_width_b = sum(s[0] for s in sizes_b) // len(sizes_b)
            avg_height_b = sum(s[1] for s in sizes_b) // len(sizes_b)
            comparison["dataset_b"] = {
                "avg_width": avg_width_b,
                "avg_height": avg_height_b,
                "count": len(images_b)
            }

        return comparison

    def _extract_visual_insights(self, analysis: str) -> List[str]:
        """Extract key visual insights"""
        insights = []
        lines = analysis.split("\n")

        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in
                   ["visual", "color", "style", "aesthetic", "image", "photo"]):
                if len(line) > 20:
                    insights.append(line)

        return insights[:8]