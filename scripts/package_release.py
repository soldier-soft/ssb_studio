"""Script to package SSB Practice Studio into an optimized distributable ZIP with 1-click desktop shortcut setup.
Developed by Lt. V. Elangovan
"""

import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
APP_DIR = DIST_DIR / "SSBPracticeStudio"
EXE_FILE = APP_DIR / "SSBPracticeStudio.exe"
ZIP_OUTPUT_DIST = DIST_DIR / "SSB_Practice_Studio_Windows.zip"
DOCS_DOWNLOAD_DIR = ROOT_DIR / "docs" / "download"
ZIP_OUTPUT_DOCS = DOCS_DOWNLOAD_DIR / "SSB_Practice_Studio_Windows.zip"

SHORTCUT_BAT_CONTENT = r"""@echo off
setlocal enabledelayedexpansion
title SSB Practice Studio - Desktop Shortcut Setup (Developed by Lt. V. Elangovan)
cls
echo =======================================================================
echo          SSB PRACTICE STUDIO - 1-CLICK DESKTOP SHORTCUT SETUP
echo                 Developed by Lt. V. Elangovan
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
    "$Shortcut.Description = 'SSB Practice Studio - Officer Assessment Psychological Tests (Developed by Lt. V. Elangovan)'; " ^
    "$Shortcut.Save(); " ^
    "Write-Host '[SUCCESS] Desktop shortcut created at:' $ShortcutPath -ForegroundColor Green"

echo.
echo =======================================================================
echo   SETUP COMPLETED SUCCESSFULLY!
echo   Launching SSB Practice Studio now...
echo   Developed by Lt. V. Elangovan
echo =======================================================================
echo.
start "" "%EXE_PATH%"
timeout /t 3 >nul
exit /b 0
"""

README_CONTENT = """=======================================================================
               SSB PRACTICE STUDIO — 100% OFFLINE PREPARATION
                       Developed by Lt. V. Elangovan
=======================================================================

Thank you for downloading SSB Practice Studio!
Engineered specifically for Indian Armed Forces Aspirants (NDA, CDS, AFCAT, SSB Interviews).

QUICK 3-STEP SETUP:
-------------------
1. Extract all contents of this ZIP archive to any folder (e.g. C:\\SSB_Studio or Downloads).
2. Double-click:
   --> Setup_And_Create_Desktop_Shortcut.bat
3. A shortcut named 'SSB Practice Studio' will instantly be placed on your
   Windows Desktop with the official application icon, and the app will open!

KEY FEATURES:
-------------
- 100% Offline & Private: No internet connection required. All practice data and scores stay on your device.
- WAT (Word Association Test): Realistic 15-second timer with automatic slide transitions.
- SRT (Situation Reaction Test): 30-second pacing or 30-minute exam mode, natural 1-60 ordering, '( ... )' endings.
- TAT (Thematic Apperception Test): 30s viewing phase followed by 4min writing, blank slide #12 support.
- Custom Import: Easily load your coaching notes, PDFs, Word documents, text lists, or image folders.
- Performance Analytics: Comprehensive response speed, character density, and PDF export reports.

SYSTEM REQUIREMENTS:
--------------------
- OS: Windows 10 or Windows 11 (64-bit)
- RAM: 2 GB minimum

CREDITS & DEVELOPER:
-------------------
Developed by Lt. V. Elangovan
Official Repository: https://github.com/soldier-soft/ssb_studio
Live Web Portal:    https://soldier-soft.github.io/ssb_studio/
=======================================================================
"""

# Files and patterns to exclude from zip package to keep it < 100 MB
# Note: .yaml files in pymupdf/layout/resources/onnx ARE KEPT to satisfy PyMuPDF layout checks!
EXCLUDE_PATTERNS = [
    "opengl32sw.dll",      # 19.7 MB software OpenGL fallback (not needed on Win 10/11)
    "mupdf-devel",         # Development C headers and static .lib archives
    "Qt6Quick",            # Unused QML/Quick runtime DLLs
    "Qt6Qml",
    "Qt6Pdf",
    ".onnx",               # 48 MB deep-learning ONNX model weights (layout analysis disabled)
]


def should_exclude(rel_path_str: str) -> bool:
    """Return True if the file should be excluded from the distributable zip."""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in rel_path_str:
            return True
    return False


def create_release_zip():
    if not EXE_FILE.exists():
        print(f"Error: {EXE_FILE} not found. Build the executable first.")
        sys.exit(1)

    print("=" * 65)
    print("Packaging SSB Practice Studio Distributable Archive")
    print("Developed by Lt. V. Elangovan")
    print("=" * 65)

    # 1. Write setup files to DIST_DIR
    bat_file = DIST_DIR / "Setup_And_Create_Desktop_Shortcut.bat"
    readme_file = DIST_DIR / "README_INSTALL.txt"

    bat_file.write_text(SHORTCUT_BAT_CONTENT, encoding="utf-8")
    readme_file.write_text(README_CONTENT, encoding="utf-8")
    print(f"Created setup batch script: {bat_file.name}")
    print(f"Created readme: {readme_file.name}")

    # Ensure docs/download directory exists
    DOCS_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Build ZIP archive
    print(f"Creating optimized ZIP archive...")
    if ZIP_OUTPUT_DIST.exists():
        ZIP_OUTPUT_DIST.unlink()

    total_files = sum(1 for _ in APP_DIR.rglob("*") if _.is_file())
    included_files = 0
    excluded_files = 0

    with zipfile.ZipFile(ZIP_OUTPUT_DIST, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # Add root setup files
        zf.write(bat_file, arcname="Setup_And_Create_Desktop_Shortcut.bat")
        zf.write(readme_file, arcname="README_INSTALL.txt")

        for file_path in APP_DIR.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(DIST_DIR)
                rel_str = str(rel_path)

                if should_exclude(rel_str):
                    excluded_files += 1
                    continue

                zf.write(file_path, arcname=rel_str)
                included_files += 1
                if included_files % 100 == 0:
                    print(f"  Zipping files: {included_files} included...")

    zip_size_mb = ZIP_OUTPUT_DIST.stat().st_size / (1024 * 1024)
    print(f"Total files examined: {total_files}")
    print(f"Files included: {included_files}, files excluded (heavy unneeded): {excluded_files}")
    print(f"Package Size: {zip_size_mb:.2f} MB (Threshold < 100.0 MB for GitHub push: {'PASSED' if zip_size_mb < 100 else 'FAILED'})")

    # 3. Copy to docs/download for GitHub Pages direct download
    print(f"Copying package to {ZIP_OUTPUT_DOCS}...")
    shutil.copy2(ZIP_OUTPUT_DIST, ZIP_OUTPUT_DOCS)

    print("=" * 65)
    print("SUCCESS: SSB Practice Studio package is ready!")
    print(f"Dist location: {ZIP_OUTPUT_DIST}")
    print(f"Docs location: {ZIP_OUTPUT_DOCS}")
    print("=" * 65)


if __name__ == "__main__":
    create_release_zip()
