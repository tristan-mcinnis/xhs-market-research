"""Base analyzer class with common functionality"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional

from rich.console import Console

from ..utils.llm import LLMFactory, LLMProvider
from ..utils.file_handler import FileHandler
from ..core.config import config


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzers"""

    def __init__(
        self,
        llm_provider: Optional[str] = None,
        console: Optional[Console] = None
    ):
        """
        Initialize base analyzer

        Args:
            llm_provider: LLM provider name (openai, gemini, deepseek)
            console: Rich console for output
        """
        self.console = console or Console()
        self.llm = LLMFactory.create(llm_provider)
        self.file_handler = FileHandler()

    @abstractmethod
    def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """Abstract analysis method to be implemented"""
        pass

    def collect_content(self, content_dir: Path) -> Dict[str, Any]:
        """
        Collect content from directory

        Args:
            content_dir: Directory containing content

        Returns:
            Dictionary with collected content
        """
        metadata_file = content_dir / "metadata.json"
        raw_file = content_dir / "raw_scraper_results.json"

        content_data = {
            "metadata": self.file_handler.read_json(metadata_file),
            "raw_results": self.file_handler.read_json(raw_file),
            "media_dir": content_dir / "media",
            "post_count": 0,
            "images": [],
            "texts": []
        }

        # Collect post content
        if content_data["metadata"]:
            content_data["post_count"] = len(content_data["metadata"])

            for post in content_data["metadata"]:
                # Collect text
                if post.get("description"):
                    content_data["texts"].append(post["description"])

                # Collect image paths
                for img_path in post.get("images", []):
                    full_path = content_dir / img_path
                    if full_path.exists():
                        content_data["images"].append(str(full_path))

        return content_data

    def create_analysis_prompt(
        self,
        content: List[str],
        analysis_type: str = "general"
    ) -> str:
        """
        Create analysis prompt based on type

        Args:
            content: Content to analyze
            analysis_type: Type of analysis

        Returns:
            Formatted prompt
        """
        prompts = {
            "general": """
                Analyze the following social media posts and provide insights on:
                1. Main themes and topics
                2. User sentiments and opinions
                3. Key trends or patterns
                4. Notable insights

                Content:
                {content}
            """,
            "market": """
                Perform market analysis on these posts:
                1. Consumer preferences and behaviors
                2. Brand mentions and sentiment
                3. Product features most discussed
                4. Market opportunities

                Content:
                {content}
            """,
            "competitive": """
                Analyze competitive landscape from these posts:
                1. Brand comparisons
                2. Competitive advantages mentioned
                3. Consumer switching behaviors
                4. Market positioning insights

                Content:
                {content}
            """
        }

        prompt_template = prompts.get(analysis_type, prompts["general"])
        return prompt_template.format(content="\n\n".join(content))

    def save_results(
        self,
        results: Dict[str, Any],
        output_path: Path,
        filename: str = "analysis_results.json"
    ):
        """
        Save analysis results

        Args:
            results: Analysis results
            output_path: Output directory
            filename: Output filename
        """
        self.file_handler.ensure_directory(output_path)
        self.file_handler.write_json(results, output_path / filename)

        self.console.print(
            f"[green]✓ Results saved to {output_path / filename}[/green]"
        )

    def create_report(
        self,
        results: Dict[str, Any],
        output_path: Path,
        report_name: str = "analysis_report.md"
    ):
        """
        Create markdown report from results

        Args:
            results: Analysis results
            output_path: Output directory
            report_name: Report filename
        """
        report = self._format_report(results)
        report_path = output_path / report_name

        self.file_handler.write_text(report, report_path)
        self.console.print(f"[green]✓ Report saved to {report_path}[/green]")

    def _format_report(self, results: Dict[str, Any]) -> str:
        """Format results as markdown report"""
        report = ["# Analysis Report\n"]

        # Add summary section
        if "summary" in results:
            report.append("## Summary\n")
            report.append(f"{results['summary']}\n")

        # Add statistics
        if "statistics" in results:
            report.append("## Statistics\n")
            for key, value in results["statistics"].items():
                report.append(f"- **{key}**: {value}")
            report.append("")

        # Add insights
        if "insights" in results:
            report.append("## Key Insights\n")
            report.append(f"{results['insights']}\n")

        # Add recommendations
        if "recommendations" in results:
            report.append("## Recommendations\n")
            report.append(f"{results['recommendations']}\n")

        return "\n".join(report)