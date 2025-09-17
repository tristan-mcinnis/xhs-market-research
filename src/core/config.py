"""Configuration management for XHS Scraper"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Centralized configuration management"""

    def __init__(self):
        load_dotenv()
        self._load_config()

    def _load_config(self):
        """Load configuration from environment variables"""
        # API Configuration
        self.apify_api_token = os.getenv('APIFY_API_TOKEN')
        self.actor_id = "easyapi/all-in-one-rednote-xiaohongshu-scraper"

        # LLM Configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.moonshot_api_key = os.getenv('MOONSHOT_API_KEY')

        # Paths
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.base_dir / "data"
        self.download_dir = self.data_dir / "downloaded_content"
        self.analysis_dir = self.data_dir / "analysis_results"

        # Ensure directories exist
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

        # Scraping defaults
        self.default_max_posts = 10
        self.rate_limit_delay = 5  # seconds between API calls
        self.request_timeout = 300  # seconds

    @property
    def is_configured(self) -> bool:
        """Check if essential configuration is present"""
        return bool(self.apify_api_token)

    def get_llm_provider(self, provider: str = 'openai') -> Optional[str]:
        """Get API key for specified LLM provider"""
        providers = {
            'openai': self.openai_api_key,
            'gemini': self.gemini_api_key,
            'deepseek': self.deepseek_api_key,
            'moonshot': self.moonshot_api_key
        }
        return providers.get(provider.lower())


# Singleton instance
config = Config()