@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "FFMPEG=C:\Users\PC\Downloads\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
if not exist "%FFMPEG%" (
    echo Error: FFmpeg not found!
    pause
    exit /b 1
)

python -m pip show playwright >nul 2>&1
if errorlevel 1 (
    python -m pip install -r requirements.txt
)

python -m playwright install chromium
python pipeline.py --ffmpeg "%FFMPEG%"

if errorlevel 1 (
    echo Run failed.
)
pause