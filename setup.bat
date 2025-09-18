@echo off
REM XHS Scraper Setup Script for Windows using UV
REM Enforces Python 3.12+

echo ================================
echo   XHS Scraper Setup with UV
echo ================================
echo.

REM Check for Python 3.12
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed
    echo Please install Python 3.12 or higher from https://python.org
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Check if Python is 3.12+
python -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.12+ required. Current version: %PYTHON_VERSION%
    echo Please install Python 3.12 from https://python.org
    pause
    exit /b 1
)

echo [OK] Python 3.12+ verified

REM Check/Install UV
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing UV package manager...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

    REM Add to PATH
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"

    echo [OK] UV installed successfully
) else (
    echo [OK] UV is already installed
)

REM Create virtual environment with Python 3.12
echo Creating virtual environment with Python 3.12...
if exist ".venv" (
    echo Removing old virtual environment...
    rmdir /s /q .venv
)
uv venv --python 3.12

REM Activate and install dependencies
echo Installing dependencies...
call .venv\Scripts\activate.bat

if exist "requirements.txt" (
    uv pip install -r requirements.txt
) else if exist "pyproject.toml" (
    uv sync
) else (
    echo [WARNING] No requirements.txt or pyproject.toml found; skipping install.
)

echo [OK] Dependencies installed
python --version

REM Check for .env file
if not exist ".env" (
    echo.
    echo Creating .env file...
    if exist ".env.example" (
        copy .env.example .env
    ) else (
        (
            echo # Xiaohongshu Scraper Configuration
            echo # Get your token from: https://console.apify.com/account/integrations
            echo.
            echo APIFY_API_TOKEN=your_apify_token_here
        ) > .env
    )
    echo [OK] Created .env file
    echo [WARNING] Please edit .env and add your Apify API token
)

REM Create default config
if not exist "config.json" (
    echo Creating default configuration...
    python -c "from src.scrapers.config import Config; Config.create_default_config()" 2>nul || (
        uv run python -c "from src.scrapers.config import Config; Config.create_default_config()"
    )
    echo [OK] Created config.json
)

REM Create directories
echo Creating project directories...
if not exist "data\scraped" mkdir data\scraped
if not exist "data\images" mkdir data\images
if not exist "logs" mkdir logs
echo [OK] Directories created

echo.
echo ================================
echo   Setup Complete!
echo ================================
echo.
echo Next steps:
echo 1. Edit .env and add your Apify API token
echo 2. Activate the environment:
echo    .venv\Scripts\activate
echo 3. Run the scraper:
echo    python xhs_actor.py search "keyword" --download
echo.
echo For more options: python xhs_actor.py --help
echo.
pause