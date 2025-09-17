#!/usr/bin/env python3
"""
XHS Scraper - Professional Xiaohongshu Content Scraper
Main entry point for the refactored application
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.cli.commands import main

if __name__ == "__main__":
    main()