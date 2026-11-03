"""Application settings, directory paths, and default configurations."""

import os
import sys
from pathlib import Path

APP_NAME = "SSB Practice Studio"
APP_VERSION = "1.0.0"
ORG_NAME = "SSBPracticeStudio"


def get_app_root() -> Path:
    """Return the base path for application resources, handling both dev and PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_user_data_dir() -> Path:
    """
    Return the user data directory for local database and persistent assets.
    Uses %LOCALAPPDATA%/SSBPracticeStudio on Windows, falling back to ~/.ssbpracticestudio.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base_dir = Path(local_app_data) / "SSBPracticeStudio"
    else:
        base_dir = Path.home() / ".ssbpracticestudio"

    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def get_database_path() -> Path:
    """Return absolute path to SQLite database."""
    return get_user_data_dir() / "ssb_studio.db"


def get_library_asset_dir() -> Path:
    """Return directory where imported TAT images and sets are copied safely."""
    path = get_user_data_dir() / "library_assets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_backup_dir() -> Path:
    """Return directory for SQLite database backups."""
    path = get_user_data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_reports_dir() -> Path:
    """Return default directory for exported PDF and CSV reports."""
    path = get_user_data_dir() / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


# Timing presets & defaults
DEFAULT_TAT_VIEW_SECONDS = 30.0
DEFAULT_TAT_WRITE_SECONDS = 270.0  # 4 minutes 30 seconds
DEFAULT_WAT_INTERVAL_SECONDS = 15.0
DEFAULT_SRT_INTERVAL_SECONDS = 30.0

DEFAULT_START_COUNTDOWN_SECONDS = 3

DEFAULT_SETTINGS = {
    "theme": "dark",
    "font_size": 13,
    "sound_enabled": True,
    "sound_volume": 80,
    "fullscreen_exam": False,
    "start_countdown": 3,
    "tesseract_cmd": "",
    "autosave_debounce_ms": 1500,
    "default_import_folder": "",
}
