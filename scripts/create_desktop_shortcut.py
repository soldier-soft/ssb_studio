"""Create a Windows Desktop Shortcut with embedded app icon for SSB Practice Studio."""

import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ICON_PATH = ROOT_DIR / "assets" / "app_icon.ico"
EXE_PATH = ROOT_DIR / "dist" / "SSBPracticeStudio" / "SSBPracticeStudio.exe"
BAT_PATH = ROOT_DIR / "run_app.bat"


def create_shortcut():
    target_path = EXE_PATH if EXE_PATH.exists() else BAT_PATH
    icon_target = ICON_PATH if ICON_PATH.exists() else target_path

    ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath "SSB Practice Studio.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "{str(target_path)}"
$Shortcut.WorkingDirectory = "{str(ROOT_DIR)}"
$Shortcut.IconLocation = "{str(icon_target)},0"
$Shortcut.Description = "SSB Practice Studio - Officer Assessment Psychological Tests"
$Shortcut.Save()
Write-Host "Created desktop shortcut at: $ShortcutPath"
"""
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            check=True,
        )
        print(res.stdout.strip())
    except Exception as e:
        print(f"Failed to create desktop shortcut: {e}")


if __name__ == "__main__":
    create_shortcut()
