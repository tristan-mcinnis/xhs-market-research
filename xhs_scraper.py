#!/usr/bin/env python3
"""
XHS Scraper - Legacy entry point
This file is kept for backward compatibility.
Please use xhs.py for the new unified CLI interface.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the new unified CLI
from xhs import main

if __name__ == "__main__":
    print("[Note] xhs_scraper.py is deprecated. Please use xhs.py instead.")
    print("")
    main()