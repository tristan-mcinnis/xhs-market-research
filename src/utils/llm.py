"""LLM provider utilities for analysis"""

import os
import base64
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from pathlib import Path

from rich.console import Console

from ..core.config import config


console = Console()


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def analyze(self, prompt: str, images: List[str] = None) -> Optional[str]:
        """Analyze content with optional images"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""

    def __init__(self):
        super().__init__(config.openai_api_key)
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                console.print("[yellow]OpenAI library not installed[/yellow]")

    def analyze(self, prompt: str, images: List[str] = None) -> Optional[str]:
        """Analyze using GPT-4 Vision"""
        if not self.client:
            return None

        try:
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

            if images:
                for img_path in images[:10]:  # Limit images
                    if Path(img_path).exists():
                        base64_img = self.encode_image(img_path)
                        messages[0]["content"].append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_img}"
                            }
                        })

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            console.print(f"[red]OpenAI error: {e}[/red]")
            return None

    def is_available(self) -> bool:
        return bool(self.client and self.api_key)


class GeminiProvider(LLMProvider):
    """Google Gemini provider"""

    def __init__(self):
        super().__init__(config.gemini_api_key)
        self.model = None
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except ImportError:
                console.print("[yellow]Google AI library not installed[/yellow]")

    def analyze(self, prompt: str, images: List[str] = None) -> Optional[str]:
        """Analyze using Gemini"""
        if not self.model:
            return None

        try:
            from PIL import Image

            content = [prompt]
            if images:
                for img_path in images[:10]:
                    if Path(img_path).exists():
                        img = Image.open(img_path)
                        content.append(img)

            response = self.model.generate_content(content)
            return response.text

        except Exception as e:
            console.print(f"[red]Gemini error: {e}[/red]")
            return None

    def is_available(self) -> bool:
        return bool(self.model and self.api_key)


class DeepSeekProvider(LLMProvider):
    """DeepSeek provider"""

    def __init__(self):
        super().__init__(config.deepseek_api_key)
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.deepseek.com"
                )
            except ImportError:
                console.print("[yellow]OpenAI library needed for DeepSeek[/yellow]")

    def analyze(self, prompt: str, images: List[str] = None) -> Optional[str]:
        """Analyze using DeepSeek"""
        if not self.client:
            return None

        try:
            # DeepSeek doesn't support images, ignore them
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            console.print(f"[red]DeepSeek error: {e}[/red]")
            return None

    def is_available(self) -> bool:
        return bool(self.client and self.api_key)


class LLMFactory:
    """Factory for creating LLM providers"""

    _providers = {
        'openai': OpenAIProvider,
        'gemini': GeminiProvider,
        'deepseek': DeepSeekProvider
    }

    @classmethod
    def create(cls, provider_name: str = None) -> Optional[LLMProvider]:
        """
        Create LLM provider instance

        Args:
            provider_name: Name of provider or None for auto-selection

        Returns:
            LLMProvider instance or None
        """
        if provider_name:
            provider_class = cls._providers.get(provider_name.lower())
            if provider_class:
                provider = provider_class()
                if provider.is_available():
                    console.print(f"[green]Using {provider_name} provider[/green]")
                    return provider

        # Auto-select first available provider
        for name, provider_class in cls._providers.items():
            provider = provider_class()
            if provider.is_available():
                console.print(f"[green]Auto-selected {name} provider[/green]")
                return provider

        console.print("[red]No LLM provider available[/red]")
        return None

    @classmethod
    def list_available(cls) -> List[str]:
        """List available providers"""
        available = []
        for name, provider_class in cls._providers.items():
            provider = provider_class()
            if provider.is_available():
                available.append(name)
        return available