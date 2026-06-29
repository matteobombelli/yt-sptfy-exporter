@echo off
REM Double-click launcher for non-coders (Windows).
REM First run installs uv/ffmpeg/deno if missing; every run starts the app.
cd /d "%~dp0"

REM Use freshly-installed tools without needing to restart the terminal.
set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.deno\bin;%PATH%"

powershell -ExecutionPolicy Bypass -File install.ps1

where uv >nul 2>nul
if errorlevel 1 (
    echo.
    echo Setup just installed some tools. Double-click Start again to open the app.
    pause
    exit /b 0
)

echo.
echo Starting the app...
uv run app.py
if errorlevel 1 pause
