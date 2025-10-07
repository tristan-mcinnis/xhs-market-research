# Team Guide - XHS Scraper Web Interface

## Quick Start

### Accessing the Scraper

1. Visit: **https://tristan-mcinnis.github.io/xhs-market-research/**
2. Enter password: `IC@XHS_scrape202510`
3. Start scraping!

## Using the Web Interface

### Running a Scrape

1. **Enter Keywords**: Type your search terms (space-separated)
   - Example: `coffee shops tokyo`
   - Example: `luxury skincare`

2. **Configure Settings**:
   - **Max Items**: How many posts to scrape (default: 30)
   - **Max Downloads**: Limit image downloads (leave empty for unlimited)
   - **Download Images**: Toggle on/off

3. **Click "Run Scraper"**

4. **Wait for Completion**: Status updates every 5 seconds

5. **Download Results**: Click the download button when ready

## What You Get

Results are packaged as a ZIP file containing:

- **`scraped/`** - JSON files with post data (titles, likes, comments, etc.)
- **`images/`** - Downloaded images (if enabled)
- **`SUMMARY.txt`** - Statistics about your scrape

## Audit Log

Every scrape is logged publicly for transparency:

- **Location**: Scroll down to "📊 Audit Log" section
- **Shows**: All past scrapes with dates, keywords, and results
- **Statistics**: Total runs, posts scraped, images downloaded

## Tips

### Best Practices

- **Start small**: Try 20-30 items first to test
- **Specific keywords**: More specific = better results
- **Limit downloads**: Use max downloads to save bandwidth
- **Check audit log**: See what others have searched

### Examples

**Light scrape** (no images):
- Keywords: `thai street food`
- Max items: 50
- Download images: ❌

**Full scrape** (with images):
- Keywords: `cafe aesthetic seoul`
- Max items: 30
- Download images: ✓
- Max downloads: 20

**Large dataset**:
- Keywords: `sustainable fashion`
- Max items: 100
- Download images: ❌

## Troubleshooting

### Password Not Working
- Make sure you're using the current password
- Contact admin if password has been updated

### Workflow Fails
- Click "View Logs" button to see error details
- Check if keywords are too generic
- Try reducing max items

### No Results
- Keywords may be too specific
- Try different search terms
- Check if Xiaohongshu has content for that query

### Download Not Working
- Click the "View" link to access GitHub Actions page
- Artifacts appear at the bottom of the workflow page
- Files expire after 7 days

## For Administrators

### Updating Password

```bash
# 1. Edit .env file
nano .env

# 2. Change WEB_PASSWORD value
WEB_PASSWORD="NewPassword123"

# 3. Run update script
python update_password.py

# 4. Commit and push
git add docs/app.js
git commit -m "Update web password"
git push

# 5. Notify team of new password
```

### Viewing Raw Audit Log

Direct link: https://tristan-mcinnis.github.io/xhs-market-research/audit.json

## Support

For issues or questions:
- Check the audit log to see if similar searches have succeeded
- View GitHub Actions logs for detailed error messages
- Contact repository administrator

---

**Current Password**: `IC@XHS_scrape202510`
**Update Frequency**: Password rotates periodically - check with admin
