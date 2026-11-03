"""Script to package SSB Practice Studio into a distributable ZIP with a 1-click desktop shortcut installer."""

import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
APP_DIR = DIST_DIR / "SSBPracticeStudio"
EXE_FILE = APP_DIR / "SSBPracticeStudio.exe"
ZIP_OUTPUT = DIST_DIR / "SSB_Practice_Studio_Windows.zip"

SHORTCUT_BAT_CONTENT = r"""@echo off
setlocal enabledelayedexpansion
title SSB Practice Studio - Desktop Shortcut Setup
cls
echo =======================================================================
echo          SSB PRACTICE STUDIO - 1-CLICK DESKTOP SHORTCUT SETUP
echo =======================================================================
echo.
echo  Detecting installation directory and Windows Desktop environment...
echo.

set "SCRIPT_DIR=%~dp0"
set "EXE_PATH=%SCRIPT_DIR%SSBPracticeStudio\SSBPracticeStudio.exe"
set "ICON_PATH=%SCRIPT_DIR%SSBPracticeStudio\_internal\assets\app_icon.ico"

if not exist "%EXE_PATH%" (
    if exist "%SCRIPT_DIR%SSBPracticeStudio.exe" (
        set "EXE_PATH=%SCRIPT_DIR%SSBPracticeStudio.exe"
        set "ICON_PATH=%SCRIPT_DIR%_internal\assets\app_icon.ico"
    )
)

if not exist "%EXE_PATH%" (
    echo [ERROR] SSBPracticeStudio.exe was not found!
    echo Please make sure you unzipped the full archive before running this script.
    echo.
    pause
    exit /b 1
)

if not exist "%ICON_PATH%" (
    set "ICON_PATH=%EXE_PATH%"
)

echo  Creating Windows Desktop Shortcut with embedded high-res icon...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop); " ^
    "$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath 'SSB Practice Studio.lnk'; " ^
    "$Shortcut = $WshShell.CreateShortcut($ShortcutPath); " ^
    "$Shortcut.TargetPath = '%EXE_PATH%'; " ^
    "$Shortcut.WorkingDirectory = (Split-Path -Parent '%EXE_PATH%'); " ^
    "$Shortcut.IconLocation = '%ICON_PATH%,0'; " ^
    "$Shortcut.Description = 'SSB Practice Studio - Officer Assessment Psychological Tests (WAT, SRT, TAT)'; " ^
    "$Shortcut.Save(); " ^
    "Write-Host '[SUCCESS] Desktop shortcut created at:' $ShortcutPath -ForegroundColor Green"

echo.
echo =======================================================================
echo   SETUP COMPLETED SUCCESSFULLY!
echo   Launching SSB Practice Studio now...
echo =======================================================================
echo.
start "" "%EXE_PATH%"
timeout /t 3 >nul
exit /b 0
"""

README_CONTENT = """=======================================================================
               SSB PRACTICE STUDIO — 100% OFFLINE PREPARATION
=======================================================================

Thank you for downloading SSB Practice Studio!
Designed for Indian Armed Forces Aspirants (NDA, CDS, AFCAT, SSB Interviews).

QUICK 3-STEP SETUP:
-------------------
1. Extract all contents of this ZIP archive to any folder (e.g. C:\\SSB_Studio or Desktop).
2. Double-click:
   --> Setup_And_Create_Desktop_Shortcut.bat
3. A shortcut named 'SSB Practice Studio' will instantly be placed on your
   Windows Desktop with the official application icon, and the app will open!

KEY FEATURES:
-------------
- 100% Offline: No internet connection required. All practice data and scores stay on your device.
- WAT (Word Association Test): Realistic 15-second timer with automatic slide transitions.
- SRT (Situation Reaction Test): 30-second pacing or 30-minute exam mode, natural 1-60 ordering, '( ... )' endings.
- TAT (Thematic Apperception Test): 30s viewing phase followed by 4min writing, blank slide #12 support.
- Custom Import: Easily load your coaching notes, PDFs, Word documents, text lists, or image folders.
- Performance Analytics: Comprehensive response speed, character density, and PDF export reports.

SYSTEM REQUIREMENTS:
--------------------
- OS: Windows 10 or Windows 11 (64-bit)
- RAM: 2 GB minimum

FOR ASSISTANCE & SOURCE CODE:
----------------------------
Official Repository: https://github.com/soldier-soft/ssb_studio
Live Web Portal:    https://soldier-soft.github.io/ssb_studio/
=======================================================================
"""


def create_release_zip():
    if not EXE_FILE.exists():
        print(f"Error: {EXE_FILE} not found. Run python scripts/build_windows.py first.")
        sys.exit(1)

    print("=" * 60)
    print("Packaging SSB Practice Studio Distributable Archive")
    print("=" * 60)

    # 1. Write setup files to DIST_DIR
    bat_file = DIST_DIR / "Setup_And_Create_Desktop_Shortcut.bat"
    readme_file = DIST_DIR / "README_INSTALL.txt"

    bat_file.write_text(SHORTCUT_BAT_CONTENT, encoding="utf-8")
    readme_file.write_text(README_CONTENT, encoding="utf-8")
    print(f"Created: {bat_file.name}")
    print(f"Created: {readme_file.name}")

    # 2. Build ZIP archive
    print(f"Creating ZIP archive at {ZIP_OUTPUT}...")
    if ZIP_OUTPUT.exists():
        ZIP_OUTPUT.unlink()

    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # Add root setup files
        zf.write(bat_file, arcname="Setup_And_Create_Desktop_Shortcut.bat")
        zf.write(readme_file, arcname="README_INSTALL.txt")

        # Add all files from SSBPracticeStudio directory
        total_files = sum(1 for _ in APP_DIR.rglob("*") if _.is_file())
        count = 0
        for file_path in APP_DIR.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(DIST_DIR)
                zf.write(file_path, arcname=str(arcname))
                count += 1
                if count % 50 == 0 or count == total_files:
                    print(f"  Zipping files: {count}/{total_files}...")

    zip_size_mb = ZIP_OUTPUT.stat().st_size / (1024 * 1024)
    print("=" * 60)
    print("PACKAGE CREATED SUCCESSFULLY!")
    print(f"ZIP Archive: {ZIP_OUTPUT}")
    print(f"Size:        {zip_size_mb:.2f} MB")
    print("=" * 60)


if __name__ == "__main__":
    create_release_zip()
