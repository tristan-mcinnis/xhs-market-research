"""
Multi-LLM provider support for Xiaohongshu content analysis
Supports: OpenAI (GPT-4o-mini), Gemini (2.0 Flash), DeepSeek, Kimi
"""

import os
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import json
import yaml
from pathlib import Path

load_dotenv()

# Load analysis config
config_path = Path(__file__).parent.parent / 'config.yaml'
with open(config_path, 'r') as f:
    CONFIG = yaml.safe_load(f)


class LLMProvider(ABC):
    """Base class for LLM providers"""

    @abstractmethod
    def analyze_text(self, text: str, prompt: str = None, analysis_type: str = "basic", custom_prompt: str = None) -> Dict:
        """Analyze text content"""
        pass

    @abstractmethod
    def analyze_image_with_text(self, image_path: str, text: str = None, analysis_type: str = "basic") -> Dict:
        """Analyze image with optional text context"""
        pass

    @property
    @abstractmethod
    def supports_vision(self) -> bool:
        """Whether this provider supports image analysis"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider (GPT-4o-mini)"""

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"

    def analyze_text(self, text: str, prompt: str = None, analysis_type: str = "basic", custom_prompt: str = None) -> Dict:
        # Support custom prompts for aggregate analysis
        if custom_prompt:
            prompt = custom_prompt
        elif prompt is None:
            # Use prompt from config based on analysis type
            analysis_config = CONFIG['analysis_types'].get(analysis_type, CONFIG['analysis_types']['basic'])
            prompt = analysis_config['text_prompt']

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert social media and marketing analyst. Always return valid JSON."},
                {"role": "user", "content": f"{prompt}\n\nContent to analyze:\n{text}"}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def analyze_image_with_text(self, image_path: str, text: str = None, analysis_type: str = "basic") -> Dict:
        import base64

        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Use prompt from config based on analysis type
        analysis_config = CONFIG['analysis_types'].get(analysis_type, CONFIG['analysis_types']['basic'])
        prompt = analysis_config['image_prompt']
        if text:
            prompt += f"\n\nAdditional context: {text}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/webp;base64,{base64_image}"}}
                    ]
                }
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    @property
    def supports_vision(self) -> bool:
        return True


class GeminiProvider(LLMProvider):
    """Google Gemini provider (Gemini 2.0 Flash)"""

    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def analyze_text(self, text: str, prompt: str = None, analysis_type: str = "basic", custom_prompt: str = None) -> Dict:
        # Support custom prompts for aggregate analysis
        if custom_prompt:
            prompt = custom_prompt
        elif prompt is None:
            # Use prompt from config based on analysis type
            analysis_config = CONFIG['analysis_types'].get(analysis_type, CONFIG['analysis_types']['basic'])
            prompt = analysis_config['text_prompt']

        full_prompt = f"{prompt}\n\nContent to analyze:\n{text}\n\nReturn the analysis as a valid JSON object."
        response = self.model.generate_content(full_prompt)

        # Extract JSON from response
        response_text = response.text
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw_response": response_text}

    def analyze_image_with_text(self, image_path: str, text: str = None, analysis_type: str = "basic") -> Dict:
        from PIL import Image

        img = Image.open(image_path)

        # Use prompt from config based on analysis type
        analysis_config = CONFIG['analysis_types'].get(analysis_type, CONFIG['analysis_types']['basic'])
        prompt = analysis_config['image_prompt']
        if text:
            prompt += f"\n\nAdditional context: {text}"
        prompt += "\n\nReturn the analysis as a valid JSON object."

        response = self.model.generate_content([prompt, img])

        # Extract JSON from response
        response_text = response.text
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw_response": response_text}

    @property
    def supports_vision(self) -> bool:
        return True


class DeepSeekProvider(LLMProvider):
    """DeepSeek provider (text-only)"""

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com/v1"
        )
        self.model = "deepseek-chat"

    def analyze_text(self, text: str, prompt: str = None, analysis_type: str = "basic", custom_prompt: str = None) -> Dict:
        # Support custom prompts for aggregate analysis
        if custom_prompt:
            prompt = custom_prompt
        elif prompt is None:
            # Use prompt from config based on analysis type
            analysis_config = CONFIG['analysis_types'].get(analysis_type, CONFIG['analysis_types']['basic'])
            prompt = analysis_config['text_prompt']

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert social media and marketing analyst. Always respond with valid JSON."},
                {"role": "user", "content": f"{prompt}\n\nContent to analyze:\n{text}"}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def analyze_image_with_text(self, image_path: str, text: str = None, analysis_type: str = "basic") -> Dict:
        # DeepSeek doesn't support vision, analyze text only
        if text:
            return self.analyze_text(text, analysis_type=analysis_type)
        return {"error": "DeepSeek doesn't support image analysis and no text was provided"}

    @property
    def supports_vision(self) -> bool:
        return False


class KimiProvider(LLMProvider):
    """Kimi (Moonshot) provider (text-only)"""

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=os.getenv('MOONSHOT_API_KEY'),
            base_url="https://api.moonshot.cn/v1"
        )
        self.model = "moonshot-v1-8k"  # Using 8k context model for efficiency

    def analyze_text(self, text: str, prompt: str = None, analysis_type: str = "basic", custom_prompt: str = None) -> Dict:
        # Support custom prompts for aggregate analysis
        if custom_prompt:
            prompt = custom_prompt
        elif prompt is None:
            # Use prompt from config based on analysis type
            analysis_config = CONFIG['analysis_types'].get(analysis_type, CONFIG['analysis_types']['basic'])
            prompt = analysis_config['text_prompt']

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专业的社交媒体和营销分析师。请用JSON格式返回分析结果。You are an expert social media analyst. Return valid JSON."
                },
                {"role": "user", "content": f"{prompt}\n\nContent to analyze:\n{text}"}
            ],
            temperature=0.6
        )

        response_text = response.choices[0].message.content

        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw_response": response_text}

    def analyze_image_with_text(self, image_path: str, text: str = None, analysis_type: str = "basic") -> Dict:
        # Kimi doesn't support vision, analyze text only
        if text:
            return self.analyze_text(text, analysis_type=analysis_type)
        return {"error": "Kimi doesn't support image analysis and no text was provided"}

    @property
    def supports_vision(self) -> bool:
        return False


class LLMFactory:
    """Factory class to create LLM providers"""

    @staticmethod
    def create_provider(provider_name: str) -> LLMProvider:
        """Create an LLM provider by name"""

        providers = {
            'openai': OpenAIProvider,
            'gemini': GeminiProvider,
            'deepseek': DeepSeekProvider,
            'kimi': KimiProvider
        }

        if provider_name.lower() not in providers:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(providers.keys())}")

        return providers[provider_name.lower()]()

    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available providers"""
        return ['openai', 'gemini', 'deepseek', 'kimi']

    @staticmethod
    def get_vision_providers() -> List[str]:
        """Get list of providers that support vision"""
        return ['openai', 'gemini']

    @staticmethod
    def get_analysis_types() -> List[str]:
        """Get available analysis types from config"""
        return list(CONFIG['analysis_types'].keys())

    @staticmethod
    def get_analysis_presets() -> List[str]:
        """Get available analysis presets from config"""
        return list(CONFIG.get('analysis_presets', {}).keys())