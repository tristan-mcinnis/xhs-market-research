@echo off
REM XHS Scraper Setup Script for Windows using UV

echo ================================
echo   XHS Scraper Setup with UV
echo ================================
echo.

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 is not installed
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Found Python %PYTHON_VERSION%

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

REM Create virtual environment
echo Creating virtual environment...
uv venv --python 3.8

REM Install dependencies in virtual environment
echo Installing dependencies...
uv pip install --python .venv\Scripts\python.exe -r requirements.txt

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