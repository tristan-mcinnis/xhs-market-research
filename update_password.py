#!/usr/bin/env python3
"""
Update web interface password from .env file
Run this script whenever you change WEB_PASSWORD in .env
"""

import os
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get password from .env
password = os.getenv("WEB_PASSWORD", "")

if not password:
    print("❌ Error: WEB_PASSWORD not found in .env file")
    exit(1)

# Generate SHA-256 hash
password_hash = hashlib.sha256(password.encode()).hexdigest()

# Read app.js
app_js_path = Path("docs/app.js")
if not app_js_path.exists():
    print("❌ Error: docs/app.js not found")
    exit(1)

content = app_js_path.read_text()

# Find and replace the passwordHash line
import re
pattern = r"passwordHash: '[a-f0-9]{64}',"
replacement = f"passwordHash: '{password_hash}',"

if re.search(pattern, content):
    new_content = re.sub(pattern, replacement, content)
    app_js_path.write_text(new_content)
    print(f"✅ Password updated successfully!")
    print(f"   Password: {password}")
    print(f"   Hash: {password_hash}")
else:
    print("❌ Error: Could not find passwordHash in app.js")
    exit(1)
