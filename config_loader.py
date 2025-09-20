#!/usr/bin/env python3
"""
Configuration and Prompt Loader
Centralized configuration management for the pipeline
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class PipelineConfig:
    """Manages all configuration and prompts for the pipeline"""

    def __init__(self, config_path: str = "pipeline_config.json"):
        """Initialize configuration from JSON file"""
        self.config_path = Path(config_path)

        # Try multiple locations
        if not self.config_path.exists():
            # Try in same directory as script
            alt_path = Path(__file__).parent / "pipeline_config.json"
            if alt_path.exists():
                self.config_path = alt_path
            else:
                # Fall back to old config.json
                old_config = Path("config.json")
                if old_config.exists():
                    self.config_path = old_config

        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # Override with environment variables if present
        self._override_with_env()

    def _override_with_env(self):
        """Override config values with environment variables if they exist"""
        # API tokens
        if os.getenv('APIFY_API_TOKEN'):
            self.config['api_config']['apify_api_token'] = os.getenv('APIFY_API_TOKEN')

        if os.getenv('OPENAI_API_KEY'):
            self.config['api_config']['openai_api_key'] = os.getenv('OPENAI_API_KEY')

    def get_api_config(self, key: str, default=None) -> Any:
        """Get API configuration value"""
        return self.config.get('api_config', {}).get(key, default)

    def get_pipeline_setting(self, key: str, default=None) -> Any:
        """Get pipeline setting value"""
        return self.config.get('pipeline_settings', {}).get(key, default)

    def get_prompt(self, step: str, prompt_name: str, **kwargs) -> str:
        """
        Get a prompt for a specific step and format it with kwargs

        Args:
            step: Step name (e.g., 'step2_semiotic_analysis')
            prompt_name: Name of the prompt (e.g., 'main_prompt')
            **kwargs: Values to format the prompt template with

        Returns:
            Formatted prompt string
        """
        prompts = self.config.get('prompts', {})
        step_prompts = prompts.get(step, {})

        if prompt_name not in step_prompts:
            raise KeyError(f"Prompt '{prompt_name}' not found for step '{step}'")

        prompt = step_prompts[prompt_name]

        # Format if it's a template
        if kwargs and '{' in prompt:
            prompt = prompt.format(**kwargs)

        return prompt

    def get_all_prompts_for_step(self, step: str) -> Dict[str, str]:
        """Get all prompts for a specific step"""
        return self.config.get('prompts', {}).get(step, {})

    def get_canonical_sections(self) -> list:
        """Get canonical section names"""
        return self.config.get('canonical_sections', [])

    def get_clustering_config(self) -> Dict[str, Any]:
        """Get clustering configuration"""
        return self.config.get('clustering_config', {})

    def get_comparative_config(self) -> Dict[str, Any]:
        """Get comparative analysis configuration"""
        return self.config.get('comparative_analysis_config', {})

    def get_visualization_config(self) -> Dict[str, Any]:
        """Get visualization configuration""" 
        return self.config.get('visualization_config', {})

    def get_report_templates(self) -> Dict[str, Any]:
        """Return configured report templates"""
        return self.config.get('report_templates', {})

    def get_report_template(self, name: str) -> Dict[str, Any]:
        """Return a single report template configuration"""
        templates = self.get_report_templates()
        if name not in templates:
            available = ", ".join(sorted(templates.keys())) or "<none>"
            raise KeyError(f"Report template '{name}' not found. Available: {available}")
        return templates[name]

    def update_prompt(self, step: str, prompt_name: str, new_prompt: str):
        """
        Update a prompt and save to config file

        Args:
            step: Step name
            prompt_name: Name of the prompt
            new_prompt: New prompt text
        """
        if 'prompts' not in self.config:
            self.config['prompts'] = {}

        if step not in self.config['prompts']:
            self.config['prompts'][step] = {}

        self.config['prompts'][step][prompt_name] = new_prompt

        # Save to file
        self.save()

    def save(self):
        """Save current configuration to file"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def print_prompts_summary(self):
        """Print a summary of all available prompts"""
        prompts = self.config.get('prompts', {})

        print("\n📝 Available Prompts in Configuration:")
        print("=" * 60)

        for step, step_prompts in prompts.items():
            print(f"\n{step}:")
            for prompt_name in step_prompts.keys():
                prompt_preview = str(step_prompts[prompt_name])[:100] + "..."
                print(f"  - {prompt_name}: {prompt_preview}")

        print("\n" + "=" * 60)

    def export_prompts_to_markdown(self, output_path: str = "PROMPTS_REFERENCE.md"):
        """Export all prompts to a markdown file for easy reference"""
        prompts = self.config.get('prompts', {})

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Pipeline Prompts Reference\n\n")
            f.write("All prompts used in the XHS analysis pipeline.\n\n")
            f.write("---\n\n")

            for step, step_prompts in prompts.items():
                # Skip non-prompt config sections
                if not isinstance(step_prompts, dict):
                    continue

                step_clean = step.replace('_', ' ').title()
                f.write(f"## {step_clean}\n\n")

                for prompt_name, prompt_text in step_prompts.items():
                    # Only process string prompts
                    if not isinstance(prompt_text, str):
                        continue

                    prompt_clean = prompt_name.replace('_', ' ').title()
                    f.write(f"### {prompt_clean}\n\n")
                    f.write("```\n")
                    f.write(str(prompt_text))
                    f.write("\n```\n\n")

            f.write("\n---\n\n")
            f.write("To modify prompts, edit `pipeline_config.json`\n")

        print(f"✅ Prompts exported to {output_path}")


# Convenience functions
def get_config(config_path: Optional[str] = None) -> PipelineConfig:
    """Get or create configuration instance"""
    if config_path:
        return PipelineConfig(config_path)
    return PipelineConfig()


def test_config():
    """Test configuration loading"""
    try:
        config = get_config()

        print("✅ Configuration loaded successfully")
        print(f"📁 Config file: {config.config_path}")

        # Test getting different types of config
        print(f"\nAPI Config - Model: {config.get_api_config('openai_model')}")
        print(f"Pipeline - Max Items: {config.get_pipeline_setting('default_max_items')}")

        # Test getting a prompt
        sections = config.get_canonical_sections()
        print(f"\nCanonical Sections: {sections}")

        # Print summary
        config.print_prompts_summary()

        # Export to markdown
        config.export_prompts_to_markdown()

        return True

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False


if __name__ == "__main__":
    test_config()