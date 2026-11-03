"""Application dependency container and global service coordinator."""

import sys
if "pymupdf.layout" not in sys.modules:
    sys.modules["pymupdf.layout"] = None

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import (
    DEFAULT_SETTINGS,
    get_database_path,
    get_user_data_dir,
    get_app_root,
)
from database.connection import DatabaseConnection
from database.migrations import MigrationManager
from database.repositories import (
    AnalyticsRepository,
    ContentSetRepository,
    PresetRepository,
    SessionRepository,
    SettingsRepository,
    UserGoalRepository,
)
from services.import_manager import ImportManager
from services.ocr_service import OCRService
from services.pdf_parser import DocumentParser
from services.report_service import ReportService
from services.session_service import SessionService
from services.sound_service import SoundService

logger = logging.getLogger(__name__)


class AppContext:
    """Central container for database, repositories, services, and application settings."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path if db_path is not None else get_database_path()
        self.db = DatabaseConnection(self.db_path)

        # Apply schema migrations
        migrator = MigrationManager(self.db)
        migrator.apply_all()

        # Repositories
        self.content_repo = ContentSetRepository(self.db)
        self.preset_repo = PresetRepository(self.db)
        self.session_repo = SessionRepository(self.db)
        self.analytics_repo = AnalyticsRepository(self.db)
        self.settings_repo = SettingsRepository(self.db)
        self.goal_repo = UserGoalRepository(self.db)

        # Load persisted settings
        self.settings: Dict[str, Any] = self._load_settings()

        # Services
        custom_ocr_path = self.settings.get("tesseract_cmd")
        self.ocr_service = OCRService(custom_tesseract_path=custom_ocr_path)
        self.doc_parser = DocumentParser(ocr_service=self.ocr_service)
        self.import_manager = ImportManager(self.content_repo, self.doc_parser)
        self.session_service = SessionService(
            self.session_repo, self.content_repo, self.preset_repo
        )
        self.report_service = ReportService()
        self.sound_service = SoundService(
            enabled=bool(self.settings.get("sound_enabled", True)),
            volume=int(self.settings.get("sound_volume", 80)),
        )

        # Seed sample WAT, SRT, and TAT sets if none exist
        try:
            self.seed_sample_content_if_needed()
        except Exception as err:
            logger.warning(f"Initial sample content check: {err}")

        logger.info(f"AppContext initialized successfully. DB: {self.db_path}")

    def seed_sample_content_if_needed(self, force: bool = False) -> Dict[str, int]:
        """
        Auto-seed bundled sample WAT, SRT, and TAT content sets so the app is immediately usable.
        Returns dictionary of count of items seeded per test type.
        """
        seeded = {"WAT": 0, "SRT": 0, "TAT": 0}
        sample_dir = get_app_root() / "sample_content"
        if not sample_dir.exists():
            logger.warning(f"Sample content directory not found at {sample_dir}")
            return seeded

        # 1. WAT sample words
        existing_wat = self.content_repo.list_content_sets("WAT")
        if force or not existing_wat:
            wat_file = sample_dir / "sample_wat_words.txt"
            if wat_file.exists():
                try:
                    res = self.doc_parser.parse_wat_file(wat_file)
                    if res.words:
                        self.import_manager.import_wat_set(
                            name="Official WAT 60 Words (Sample Set)",
                            words=res.words,
                            source_file=str(wat_file),
                        )
                        seeded["WAT"] = len(res.words)
                        logger.info(f"Auto-seeded WAT sample set with {len(res.words)} words.")
                except Exception as e:
                    logger.error(f"Failed to seed WAT sample content: {e}")

        # 2. SRT sample situations
        existing_srt = self.content_repo.list_content_sets("SRT")
        if force or not existing_srt:
            srt_file = sample_dir / "sample_srt_situations.txt"
            if srt_file.exists():
                try:
                    res = self.doc_parser.parse_srt_file(srt_file)
                    if res.items:
                        self.import_manager.import_srt_set(
                            name="Standard SRT Situations (Sample Bank)",
                            items=res.items,
                            source_file=str(srt_file),
                        )
                        seeded["SRT"] = len(res.items)
                        logger.info(f"Auto-seeded SRT sample bank with {len(res.items)} situations.")
                except Exception as e:
                    logger.error(f"Failed to seed SRT sample content: {e}")

        # 3. TAT sample images
        existing_tat = self.content_repo.list_content_sets("TAT")
        if force or not existing_tat:
            tat_dir = sample_dir / "sample_tat_images"
            if tat_dir.exists():
                try:
                    unique_imgs, _ = self.import_manager.scan_tat_images([tat_dir])
                    if unique_imgs:
                        self.import_manager.import_tat_set(
                            name="Standard TAT Practice (Sample Images)",
                            image_paths=unique_imgs,
                            source_label=str(tat_dir),
                        )
                        seeded["TAT"] = len(unique_imgs)
                        logger.info(f"Auto-seeded TAT sample set with {len(unique_imgs)} images.")
                except Exception as e:
                    logger.error(f"Failed to seed TAT sample content: {e}")

        return seeded

    def _load_settings(self) -> Dict[str, Any]:
        persisted = self.settings_repo.get_all_settings()
        merged = dict(DEFAULT_SETTINGS)
        merged.update(persisted)
        return merged

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        self.settings[key] = value
        self.settings_repo.set_setting(key, value)

        if key == "tesseract_cmd":
            self.ocr_service.set_custom_path(value)
        elif key == "sound_enabled":
            self.sound_service.set_enabled(bool(value))
        elif key == "sound_volume":
            self.sound_service.set_volume(int(value))

    def reset_settings_to_defaults(self) -> None:
        for k, v in DEFAULT_SETTINGS.items():
            self.set_setting(k, v)
