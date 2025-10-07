#!/usr/bin/env python3
"""
Unified Workflow Configuration
Manages directory structure and pipeline settings
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

class WorkflowConfig:
    """Central configuration for the entire analysis pipeline"""

    def __init__(self, base_dir: str = "data", query: Optional[str] = None, date: Optional[str] = None):
        """
        Initialize workflow configuration

        Args:
            base_dir: Base directory for all data (default: "data")
            query: Query/topic name for this analysis
            date: Date string (YYYYMMDD format), defaults to today
        """
        self.base_dir = Path(base_dir)
        self.date = date or datetime.now().strftime('%Y%m%d')

        if query:
            self.set_query(query)
        else:
            self.query = None
            self.query_dir = None

    def set_query(self, query: str):
        """Set the query and create directory structure"""
        # Clean query name for directory
        self.query = query
        clean_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).strip()
        self.clean_query = clean_query.replace(' ', '_')[:50]

        # Main query directory: data/YYYYMMDD/query_name/
        self.query_dir = self.base_dir / self.date / self.clean_query

        # Step-specific subdirectories
        self.dirs = {
            'step1_scraped': self.query_dir / 'step1_scraped',
            'step1_images': self.query_dir / 'step1_images',
            'step2_analyses': self.query_dir / 'step2_analyses',
            'step3_clusters': self.query_dir / 'step3_clusters',
            'step4_comparative': self.query_dir / 'step4_comparative',
            'step5_insights': self.query_dir / 'step5_insights',
            'step6_themes': self.query_dir / 'step6_themes',
            'step7_visualizations': self.query_dir / 'step7_visualizations',
            'logs': self.query_dir / 'logs',
        }

        # Create all directories
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

    def get_dir(self, step: str) -> Path:
        """Get directory for a specific step"""
        if not self.query_dir:
            raise ValueError("Query not set. Call set_query() first.")
        return self.dirs.get(step, self.query_dir)

    def get_latest_file(self, step: str, pattern: str = "*.json") -> Optional[Path]:
        """Get the most recent file from a step's directory"""
        step_dir = self.get_dir(step)
        files = list(step_dir.glob(pattern))
        if files:
            return max(files, key=lambda x: x.stat().st_mtime)
        return None

    def save_config(self):
        """Save configuration to the query directory"""
        if not self.query_dir:
            return

        config_file = self.query_dir / "workflow_config.json"
        import json
        config_data = {
            'query': self.query,
            'clean_query': self.clean_query,
            'date': self.date,
            'base_dir': str(self.base_dir),
            'query_dir': str(self.query_dir),
            'directories': {k: str(v) for k, v in self.dirs.items()},
            'created_at': datetime.now().isoformat()
        }

        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

    @classmethod
    def load_config(cls, config_path: Path) -> 'WorkflowConfig':
        """Load configuration from a saved config file"""
        import json
        with open(config_path, 'r') as f:
            data = json.load(f)

        config = cls(base_dir=data['base_dir'], query=data['query'], date=data['date'])
        return config

    def __str__(self):
        """String representation"""
        if self.query:
            return f"WorkflowConfig(query='{self.query}', date='{self.date}', dir='{self.query_dir}')"
        return f"WorkflowConfig(date='{self.date}', base='{self.base_dir}')"


# Convenience functions for command-line usage
def get_workflow_config(query: Optional[str] = None, date: Optional[str] = None) -> WorkflowConfig:
    """Get or create workflow configuration"""
    # Check for environment variable
    if not query:
        query = os.getenv('WORKFLOW_QUERY')

    if not date:
        date = os.getenv('WORKFLOW_DATE')

    config = WorkflowConfig(query=query, date=date)

    if query:
        config.save_config()
        print(f"📁 Workflow directory: {config.query_dir}")

    return config


def find_latest_workflow(base_dir: str = "data") -> Optional[WorkflowConfig]:
    """Find the most recent workflow configuration"""
    base = Path(base_dir)

    # Look for most recent config file
    configs = list(base.glob("*/*/workflow_config.json"))

    if configs:
        latest = max(configs, key=lambda x: x.stat().st_mtime)
        return WorkflowConfig.load_config(latest)

    return None


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        config = get_workflow_config(query=query)
        print(f"\nCreated workflow structure:")
        for name, path in config.dirs.items():
            print(f"  {name}: {path}")
    else:
        # Try to find latest workflow
        latest = find_latest_workflow()
        if latest:
            print(f"Latest workflow: {latest}")
        else:
            print("No existing workflows found")
            print("Usage: python workflow_config.py <query name>")