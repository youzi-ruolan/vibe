@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 检查 FFmpeg 路径
set "FFMPEG=C:\Users\PC\Downloads\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
if not exist "%FFMPEG%" (
    echo 找不到 FFmpeg：%FFMPEG%
    goto :error
)

:: 检查并安装 playwright
python -m pip show playwright >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

:: 安装浏览器
echo 正在检查 Playwright 浏览器...
python -m playwright install chromium

:: 运行主程序
echo 正在运行 pipeline.py...
python pipeline.py --ffmpeg "%FFMPEG%"
if errorlevel 1 goto :error

goto :end

:error
echo.
echo ========================================
echo   运行失败，请查看上方错误信息。
echo ========================================

:end
pause
exit /b