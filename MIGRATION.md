# CLI Consolidation Migration Guide

## Overview
The XHS Scraper codebase has been consolidated from multiple separate scripts into a unified CLI interface (`xhs.py`). This provides a cleaner, more intuitive user experience with consistent commands and interactive options.

## New Unified CLI

### Main Command
- **`xhs.py`** - Single entry point for all functionality
  - Subcommands: `scrape`, `analyze`, `list`, `interactive`, `help`
  - Interactive mode for guided workflows
  - All analysis presets surfaced as CLI options
  - Automatic scraper selection based on scale

## Legacy Scripts to Remove

The following scripts are now redundant and should be removed as their functionality has been fully integrated into `xhs.py`:

### Scraping Scripts (REMOVE)
- `main.py` - Basic single keyword scraping → Use `xhs.py scrape`
- `scrape_multi.py` - Multiple keyword scraping → Use `xhs.py scrape` with multiple keywords
- `scrape_scale.py` - Large-scale scraping → Use `xhs.py scrape --scale`
- `scrape_with_retry.py` - Retry logic → Use `xhs.py scrape --retry`
- `search.py` - Interactive search builder → Use `xhs.py scrape --interactive`
- `query_builder.py` - Query building → Use `xhs.py scrape --interactive`
- `demo_with_cached.py` - Demo/cache functionality → No longer needed

### Analysis Scripts (REMOVE)
- `analyze.py` - Basic analysis → Use `xhs.py analyze`
- `analyze_enhanced.py` - Image analysis → Use `xhs.py analyze --images`
- `analyze_multi.py` - Cross-query analysis → Use `xhs.py analyze` with appropriate flags
- `view_analysis.py` - View results → Results shown automatically in interactive mode

## Scripts to Keep

### Core Implementation (KEEP)
- `xhs.py` - New unified CLI (main entry point)
- `xhs_scraper.py` - Can be kept as alternate name or symlink to xhs.py
- `src/` directory - All implementation modules
- `config.yaml` - Configuration file
- `requirements.txt` - Dependencies
- `.env.example` - Environment template

## Migration Steps

1. **Update documentation** ✅
   - README.md has been updated with new CLI commands
   - All example workflows updated to use `xhs.py`

2. **Test new CLI** ✅
   - Verify all commands work: `./xhs.py help`
   - Test interactive mode: `./xhs.py interactive`
   - Test listing functions: `./xhs.py list presets`

3. **Remove legacy scripts**
   ```bash
   # Create backup first (optional)
   mkdir legacy_scripts_backup
   mv main.py scrape_*.py analyze*.py search.py query_builder.py demo_*.py view_*.py legacy_scripts_backup/

   # Or remove directly if confident
   rm -f main.py scrape_multi.py scrape_scale.py scrape_with_retry.py
   rm -f analyze.py analyze_enhanced.py analyze_multi.py view_analysis.py
   rm -f search.py query_builder.py demo_with_cached.py
   ```

4. **Create convenience symlink (optional)**
   ```bash
   ln -s xhs.py xhs
   chmod +x xhs
   # Now can use: ./xhs scrape "keyword"
   ```

## Command Translation Guide

| Old Command | New Command |
|-------------|------------|
| `python main.py --keyword "X"` | `./xhs.py scrape "X"` |
| `python scrape_multi.py "A" "B" "C"` | `./xhs.py scrape "A" "B" "C"` |
| `python scrape_scale.py "X" --posts 200` | `./xhs.py scrape "X" --posts 200 --scale` |
| `python scrape_with_retry.py "X"` | `./xhs.py scrape "X" --retry` |
| `python search.py` | `./xhs.py scrape --interactive` |
| `python analyze.py --latest` | `./xhs.py analyze --latest` |
| `python analyze_enhanced.py --images 30` | `./xhs.py analyze --images --max-images 30` |
| `python view_analysis.py` | Built into interactive mode |

## Benefits of Consolidation

1. **Single Entry Point**: One command to remember (`xhs.py`)
2. **Consistent Interface**: Uniform argument structure across all functions
3. **Interactive Mode**: Guided workflows for beginners
4. **Better Discovery**: `list` commands show available presets and analysis types
5. **Reduced Confusion**: No more choosing between multiple similar scripts
6. **Maintainability**: Single codebase to update instead of multiple scripts

## Notes

- All existing functionality is preserved in the new CLI
- The underlying implementation in `src/` remains unchanged
- Configuration in `config.yaml` is still used for analysis prompts
- API keys still configured via `.env` file