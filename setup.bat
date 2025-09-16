@echo off
REM Xiaohongshu Scraper Setup Script for Windows with UV

echo ==========================================
echo Xiaohongshu Scraper ^& Analyzer Setup (UV)
echo ==========================================
echo.

REM Check if UV is installed
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing UV...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

    REM Check again after installation
    where uv >nul 2>&1
    if %errorlevel% neq 0 (
        echo X Failed to install UV. Please install it manually:
        echo   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
        pause
        exit /b 1
    )
    echo OK UV installed successfully
) else (
    echo OK UV found
)

echo.

REM Create virtual environment using UV if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment with UV...
    uv venv
    echo OK Virtual environment created
) else (
    echo OK Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

REM Install requirements using UV
echo Installing requirements with UV...
uv pip install -r requirements.txt

REM Install additional dependencies
echo Installing additional dependencies...
uv pip install scikit-learn google-generativeai

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo WARNING: No .env file found. Creating template...
    (
        echo # API Keys and Credentials
        echo APIFY_API_TOKEN="your_apify_token_here"
        echo.
        echo # LLM Providers
        echo OPENAI_API_KEY="your_openai_key_here"
        echo DEEPSEEK_API_KEY="your_deepseek_key_here"
        echo GEMINI_API_KEY="your_gemini_key_here"
        echo MOONSHOT_API_KEY="your_moonshot_key_here"
    ) > .env
    echo OK .env template created. Please add your API keys.
) else (
    echo OK .env file exists
)

REM Create data directories if they don't exist
echo.
echo Creating data directories...
if not exist "data\downloaded_content" mkdir data\downloaded_content
if not exist "data\reports" mkdir data\reports
if not exist "logs" mkdir logs

echo OK Directories created

echo.
echo ==========================================
echo OK Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Add your API keys to .env file
echo 2. Activate the virtual environment: .venv\Scripts\activate
echo 3. Test scraping: python main.py --keyword "test" --posts 5
echo 4. Test analysis: python analyze.py --latest --openai
echo.
echo UV tips:
echo - Use 'uv pip list' to see installed packages
echo - Use 'uv pip install ^<package^>' for faster installs
echo - UV is 10-100x faster than pip!
echo.
pause