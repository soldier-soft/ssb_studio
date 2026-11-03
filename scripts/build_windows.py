"""Automated build script to package SSB Practice Studio into a distributable Windows executable."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def build():
    print("=" * 60)
    print("Building SSB Practice Studio Windows Executable")
    print("=" * 60)

    spec_file = ROOT_DIR / "ssb_studio.spec"
    if not spec_file.exists():
        print(f"Error: Spec file not found at {spec_file}")
        sys.exit(1)

    # 1. Terminate any running instances of the application before cleaning/building
    print("Terminating any running instances of SSBPracticeStudio...")
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "SSBPracticeStudio.exe", "/T"],
            capture_output=True,
            check=False,
        )
    except Exception as e:
        print(f"Note on process kill: {e}")

    # Clean previous build artifacts
    dist_dir = ROOT_DIR / "dist"
    build_dir = ROOT_DIR / "build"
    if dist_dir.exists():
        print(f"Cleaning {dist_dir}...")
        shutil.rmtree(dist_dir, ignore_errors=True)
    if build_dir.exists():
        print(f"Cleaning {build_dir}...")
        shutil.rmtree(build_dir, ignore_errors=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file),
    ]

    print(f"Running PyInstaller: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT_DIR))

    if result.returncode == 0:
        exe_path = dist_dir / "SSBPracticeStudio" / "SSBPracticeStudio.exe"
        # Clean intermediate build artifacts so users don't enter build folder
        if build_dir.exists():
            shutil.rmtree(build_dir, ignore_errors=True)
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"Distributable folder: {dist_dir / 'SSBPracticeStudio'}")
        if exe_path.exists():
            print(f"Executable binary:    {exe_path}")

        # Automatically create / update desktop shortcut
        try:
            if str(ROOT_DIR) not in sys.path:
                sys.path.insert(0, str(ROOT_DIR))
            from scripts.create_desktop_shortcut import create_shortcut
            print("\nUpdating Desktop Shortcut...")
            create_shortcut()
        except Exception as err:
            print(f"Desktop shortcut update note: {err}")

        print("=" * 60)
    else:
        print(f"\nBuild failed with exit code: {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
