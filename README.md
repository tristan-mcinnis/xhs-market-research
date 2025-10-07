# Xiaohongshu (小红书) Market Research

A simple scraper for collecting Xiaohongshu content.

## 🌐 Web Interface

**[Click here to access the scraper](https://tristan-mcinnis.github.io/xhs-market-research/)**

*Ask Tristan for the password if it has been updated.*

---

## For Developers

<details>
<summary>Command Line Interface</summary>

### Setup

```bash
# Install dependencies (Python 3.12+)
pip install -r requirements.txt

# Configure API credentials in .env
APIFY_API_TOKEN=your_token_here
```

### Usage

```bash
# Search and download images
python xhs_scraper.py search "keywords" --max-items 30 --download

# Get comments from posts
python xhs_scraper.py comments URL

# Get user profiles
python xhs_scraper.py profile URL

# Get posts from a user
python xhs_scraper.py user-posts URL --download
```

### Output Structure

```
data/
└── YYYYMMDD/
    └── query_name/
        ├── scraped/    # Raw JSON data
        └── images/     # Downloaded images
```

</details>

<details>
<summary>Admin: Update Web Password</summary>

```bash
# 1. Edit .env file
nano .env  # Change WEB_PASSWORD="new_password_here"

# 2. Update web interface
python update_password.py

# 3. Commit and push
git add docs/app.js
git commit -m "Update web password"
git push
```

</details>

---

For detailed documentation, see `CLAUDE.md`.
