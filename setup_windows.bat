@echo off
title SSB Practice Studio - Windows Setup
echo ========================================================
echo  SSB Practice Studio Environment Setup
echo ========================================================
echo.

python --version
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in system PATH.
    echo Please install Python 3.12+ from python.org.
    pause
    exit /b 1
)

echo.
echo Installing application dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error installing dependencies.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Running automated verification tests...
pytest -v
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Some automated tests encountered issues.
) else (
    echo All verification tests passed successfully!
)

echo.
echo ========================================================
echo  Setup Complete! Double-click run_app.bat to launch.
echo ========================================================
pause
