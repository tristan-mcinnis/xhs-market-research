"""Content analysis for posts and media"""

from pathlib import Path
from typing import Dict, Any, List, Optional

from .base_analyzer import BaseAnalyzer


class ContentAnalyzer(BaseAnalyzer):
    """Analyze individual posts and content"""

    def analyze(
        self,
        content_dir: Path,
        analysis_type: str = "general",
        include_images: bool = False,
        max_posts: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze content from a directory

        Args:
            content_dir: Directory with content to analyze
            analysis_type: Type of analysis (general, market, competitive)
            include_images: Whether to include images in analysis
            max_posts: Maximum posts to analyze

        Returns:
            Analysis results
        """
        self.console.print(f"[cyan]Analyzing content in {content_dir}...[/cyan]")

        # Collect content
        content_data = self.collect_content(content_dir)

        if not content_data["texts"]:
            self.console.print("[yellow]No content found to analyze[/yellow]")
            return {}

        # Limit posts if specified
        texts = content_data["texts"][:max_posts] if max_posts else content_data["texts"]
        images = content_data["images"][:max_posts] if max_posts else content_data["images"]

        # Create analysis
        results = {
            "content_dir": str(content_dir),
            "posts_analyzed": len(texts),
            "analysis_type": analysis_type
        }

        # Analyze with LLM
        if self.llm:
            prompt = self.create_analysis_prompt(texts, analysis_type)

            # Include images if requested and available
            analysis_images = images[:10] if include_images else None

            response = self.llm.analyze(prompt, analysis_images)
            if response:
                results["analysis"] = response
                results["insights"] = self._extract_insights(response)
            else:
                self.console.print("[yellow]LLM analysis failed[/yellow]")

        # Add statistics
        results["statistics"] = self._calculate_statistics(content_data)

        return results

    def batch_analyze(
        self,
        content_dirs: List[Path],
        analysis_type: str = "general",
        combine_results: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze multiple content directories

        Args:
            content_dirs: List of directories to analyze
            analysis_type: Type of analysis
            combine_results: Whether to combine all results

        Returns:
            Batch analysis results
        """
        all_results = {}
        combined_texts = []
        combined_stats = {}

        for content_dir in content_dirs:
            if content_dir.exists():
                result = self.analyze(content_dir, analysis_type)

                if combine_results:
                    # Collect for combined analysis
                    content_data = self.collect_content(content_dir)
                    combined_texts.extend(content_data.get("texts", []))
                    # Merge statistics
                    stats = result.get("statistics", {})
                    for key, value in stats.items():
                        if key not in combined_stats:
                            combined_stats[key] = 0
                        if isinstance(value, (int, float)):
                            combined_stats[key] += value
                else:
                    all_results[str(content_dir)] = result

        if combine_results and combined_texts:
            # Create combined analysis
            prompt = self.create_analysis_prompt(combined_texts, analysis_type)
            if self.llm:
                response = self.llm.analyze(prompt)
                all_results = {
                    "type": "combined_analysis",
                    "directories_analyzed": len(content_dirs),
                    "total_posts": len(combined_texts),
                    "analysis": response,
                    "statistics": combined_stats
                }

        return all_results

    def _calculate_statistics(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate content statistics"""
        stats = {
            "total_posts": content_data["post_count"],
            "posts_with_text": len(content_data["texts"]),
            "total_images": len(content_data["images"]),
            "avg_text_length": 0
        }

        if content_data["texts"]:
            stats["avg_text_length"] = sum(
                len(text) for text in content_data["texts"]
            ) // len(content_data["texts"])

        # Extract engagement stats if available
        if content_data["metadata"]:
            total_likes = sum(
                post.get("likes", 0) for post in content_data["metadata"]
            )
            total_comments = sum(
                post.get("comments_count", 0) for post in content_data["metadata"]
            )

            stats["total_likes"] = total_likes
            stats["total_comments"] = total_comments
            stats["avg_likes_per_post"] = total_likes // content_data["post_count"]
            stats["avg_comments_per_post"] = total_comments // content_data["post_count"]

        return stats

    def _extract_insights(self, analysis_text: str) -> List[str]:
        """Extract key insights from analysis"""
        insights = []

        # Simple extraction based on common patterns
        lines = analysis_text.split("\n")
        for line in lines:
            line = line.strip()
            if any(marker in line.lower() for marker in ["insight:", "finding:", "trend:", "pattern:"]):
                insights.append(line)
            elif line.startswith("•") or line.startswith("-") or line.startswith("*"):
                if len(line) > 10:  # Filter out short bullets
                    insights.append(line[1:].strip())

        return insights[:10]  # Limit to top 10 insights