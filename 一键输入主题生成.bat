@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)
python -c "import sys; from pathlib import Path; from playwright.sync_api import sync_playwright; p=sync_playwright().start(); found=Path(p.chromium.executable_path).is_file(); p.stop(); sys.exit(0 if found else 1)" >nul 2>&1
if errorlevel 1 (
    python -m playwright install chromium
    if errorlevel 1 goto :error
)
python -X utf8 pipeline.py %*
if errorlevel 1 goto :error
goto :end
:error
echo.
echo Generation failed. Please check the message above.
:end
pause
exit /b
