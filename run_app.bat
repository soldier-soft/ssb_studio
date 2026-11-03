@echo off
title SSB Practice Studio
cd /d "%~dp0"

echo ========================================================
echo  Launching SSB Practice Studio...
echo ========================================================

if exist "dist\SSBPracticeStudio\SSBPracticeStudio.exe" (
    echo Launching packaged executable: dist\SSBPracticeStudio\SSBPracticeStudio.exe
    start "" "dist\SSBPracticeStudio\SSBPracticeStudio.exe"
    exit /b 0
)

echo Packaged binary not found. Launching via Python...
python -m app.main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%.
    pause
)
