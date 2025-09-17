"""Aggregate analysis across multiple datasets"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter

from .base_analyzer import BaseAnalyzer


class AggregateAnalyzer(BaseAnalyzer):
    """Analyze aggregated content across multiple sources"""

    def analyze(
        self,
        content_dirs: List[Path],
        analysis_focus: str = "trends",
        cross_reference: bool = True
    ) -> Dict[str, Any]:
        """
        Perform aggregate analysis across multiple content directories

        Args:
            content_dirs: List of directories to analyze
            analysis_focus: Focus area (trends, patterns, comparison)
            cross_reference: Whether to cross-reference between datasets

        Returns:
            Aggregate analysis results
        """
        self.console.print(
            f"[cyan]Performing aggregate analysis across "
            f"{len(content_dirs)} datasets...[/cyan]"
        )

        # Collect all content
        all_content = self._collect_all_content(content_dirs)

        if not all_content["texts"]:
            self.console.print("[yellow]No content found for analysis[/yellow]")
            return {}

        # Perform analysis
        results = {
            "type": "aggregate_analysis",
            "datasets_analyzed": len(content_dirs),
            "total_posts": all_content["total_posts"],
            "analysis_focus": analysis_focus
        }

        # LLM analysis
        if self.llm:
            prompt = self._create_aggregate_prompt(
                all_content,
                analysis_focus,
                cross_reference
            )

            response = self.llm.analyze(prompt)
            if response:
                results["analysis"] = response
                results["key_findings"] = self._extract_key_findings(response)

        # Statistical analysis
        results["statistics"] = self._calculate_aggregate_statistics(all_content)

        # Trend analysis
        if analysis_focus == "trends":
            results["trends"] = self._analyze_trends(all_content)

        # Pattern detection
        if analysis_focus == "patterns":
            results["patterns"] = self._detect_patterns(all_content)

        return results

    def compare_datasets(
        self,
        dataset_a: Path,
        dataset_b: Path,
        comparison_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Compare two datasets

        Args:
            dataset_a: First dataset directory
            dataset_b: Second dataset directory
            comparison_type: Type of comparison

        Returns:
            Comparison results
        """
        self.console.print(
            f"[cyan]Comparing {dataset_a.name} vs {dataset_b.name}...[/cyan]"
        )

        # Collect content from both
        content_a = self.collect_content(dataset_a)
        content_b = self.collect_content(dataset_b)

        results = {
            "type": "comparison_analysis",
            "dataset_a": str(dataset_a),
            "dataset_b": str(dataset_b),
            "comparison_type": comparison_type
        }

        # Statistical comparison
        stats_a = self._calculate_statistics(content_a)
        stats_b = self._calculate_statistics(content_b)

        results["statistics_comparison"] = {
            "dataset_a": stats_a,
            "dataset_b": stats_b,
            "differences": self._calculate_differences(stats_a, stats_b)
        }

        # LLM comparative analysis
        if self.llm and content_a["texts"] and content_b["texts"]:
            prompt = self._create_comparison_prompt(
                content_a["texts"],
                content_b["texts"],
                comparison_type
            )

            response = self.llm.analyze(prompt)
            if response:
                results["comparative_analysis"] = response

        return results

    def _collect_all_content(
        self,
        content_dirs: List[Path]
    ) -> Dict[str, Any]:
        """Collect content from multiple directories"""
        all_content = {
            "texts": [],
            "images": [],
            "metadata": [],
            "total_posts": 0,
            "by_source": {}
        }

        for content_dir in content_dirs:
            if content_dir.exists():
                content = self.collect_content(content_dir)
                source_name = content_dir.name

                all_content["texts"].extend(content.get("texts", []))
                all_content["images"].extend(content.get("images", []))
                all_content["metadata"].extend(content.get("metadata", []))
                all_content["total_posts"] += content.get("post_count", 0)
                all_content["by_source"][source_name] = content

        return all_content

    def _create_aggregate_prompt(
        self,
        content: Dict[str, Any],
        focus: str,
        cross_reference: bool
    ) -> str:
        """Create prompt for aggregate analysis"""
        base_prompt = f"""
        Analyze the following aggregated social media content from
        {len(content['by_source'])} different sources with {content['total_posts']} total posts.
        """

        focus_prompts = {
            "trends": """
                Focus on identifying:
                1. Emerging trends across all datasets
                2. Common themes and topics
                3. Shifting sentiments over sources
                4. Notable patterns in user behavior
            """,
            "patterns": """
                Focus on detecting:
                1. Recurring patterns in content
                2. Common user concerns or interests
                3. Behavioral patterns
                4. Content engagement patterns
            """,
            "comparison": """
                Focus on comparing:
                1. Differences between sources
                2. Unique characteristics per dataset
                3. Common vs unique elements
                4. Relative performance metrics
            """
        }

        prompt = base_prompt + focus_prompts.get(focus, focus_prompts["trends"])

        if cross_reference:
            prompt += "\nCross-reference findings across sources to identify correlations."

        # Add sample content
        sample_texts = content["texts"][:50]  # Limit for prompt
        prompt += f"\n\nContent samples:\n" + "\n".join(sample_texts)

        return prompt

    def _calculate_aggregate_statistics(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate statistics across all content"""
        stats = {
            "total_posts": content["total_posts"],
            "total_sources": len(content["by_source"]),
            "total_text_items": len(content["texts"]),
            "total_images": len(content["images"])
        }

        # Engagement metrics if available
        if content["metadata"]:
            total_likes = sum(
                post.get("likes", 0) for post in content["metadata"]
            )
            total_comments = sum(
                post.get("comments_count", 0) for post in content["metadata"]
            )

            stats["total_engagement"] = total_likes + total_comments
            stats["avg_engagement_per_post"] = (
                stats["total_engagement"] // content["total_posts"]
                if content["total_posts"] > 0 else 0
            )

        # Per-source statistics
        stats["by_source"] = {}
        for source, data in content["by_source"].items():
            stats["by_source"][source] = {
                "posts": data.get("post_count", 0),
                "texts": len(data.get("texts", [])),
                "images": len(data.get("images", []))
            }

        return stats

    def _analyze_trends(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze trends in content"""
        trends = []

        # Word frequency analysis
        all_text = " ".join(content["texts"])
        words = all_text.lower().split()

        # Filter common words
        stop_words = {"的", "了", "是", "在", "和", "我", "你", "他", "她", "它"}
        words = [w for w in words if len(w) > 1 and w not in stop_words]

        word_freq = Counter(words)
        top_words = word_freq.most_common(20)

        trends.append({
            "type": "top_keywords",
            "data": [{"word": w, "count": c} for w, c in top_words]
        })

        return trends

    def _detect_patterns(self, content: Dict[str, Any]) -> List[str]:
        """Detect patterns in content"""
        patterns = []

        # Length patterns
        text_lengths = [len(t) for t in content["texts"]]
        if text_lengths:
            avg_length = sum(text_lengths) // len(text_lengths)
            patterns.append(f"Average post length: {avg_length} characters")

        # Engagement patterns (if metadata available)
        if content["metadata"]:
            high_engagement = [
                p for p in content["metadata"]
                if p.get("likes", 0) > 1000
            ]
            if high_engagement:
                patterns.append(
                    f"{len(high_engagement)} posts with >1000 likes"
                )

        return patterns

    def _extract_key_findings(self, analysis: str) -> List[str]:
        """Extract key findings from analysis text"""
        findings = []
        lines = analysis.split("\n")

        for line in lines:
            line = line.strip()
            # Look for numbered items or bullet points
            if (line.startswith(("1.", "2.", "3.", "4.", "5.")) or
                line.startswith(("•", "-", "*")) or
                "finding" in line.lower() or
                "trend" in line.lower()):
                if len(line) > 20:  # Filter short lines
                    findings.append(line)

        return findings[:10]

    def _calculate_statistics(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate basic statistics for a dataset"""
        return {
            "post_count": content.get("post_count", 0),
            "text_count": len(content.get("texts", [])),
            "image_count": len(content.get("images", []))
        }

    def _calculate_differences(
        self,
        stats_a: Dict[str, Any],
        stats_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate differences between two stat sets"""
        differences = {}

        for key in stats_a:
            if key in stats_b and isinstance(stats_a[key], (int, float)):
                differences[key] = {
                    "a": stats_a[key],
                    "b": stats_b[key],
                    "difference": stats_a[key] - stats_b[key],
                    "percent_change": (
                        ((stats_a[key] - stats_b[key]) / stats_b[key] * 100)
                        if stats_b[key] > 0 else 0
                    )
                }

        return differences

    def _create_comparison_prompt(
        self,
        texts_a: List[str],
        texts_b: List[str],
        comparison_type: str
    ) -> str:
        """Create prompt for comparison analysis"""
        return f"""
        Compare these two sets of social media posts:

        Dataset A ({len(texts_a)} posts):
        {' '.join(texts_a[:25])}

        Dataset B ({len(texts_b)} posts):
        {' '.join(texts_b[:25])}

        Provide analysis on:
        1. Key differences in themes and topics
        2. Sentiment comparison
        3. Unique characteristics of each dataset
        4. Common elements between both
        """