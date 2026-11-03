import gc
import tempfile
from pathlib import Path
from typing import Generator
import pytest

from core.clock import TestClock
from database.connection import DatabaseConnection
from database.migrations import MigrationManager
from database.repositories import (
    AnalyticsRepository,
    ContentSetRepository,
    PresetRepository,
    SessionRepository,
    SettingsRepository,
)
from services.import_manager import ImportManager
from services.pdf_parser import DocumentParser
from services.report_service import ReportService
from services.session_service import SessionService


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        yield Path(td)
        gc.collect()


@pytest.fixture
def test_clock() -> TestClock:
    return TestClock(initial_time=1000.0)


@pytest.fixture
def db_conn(temp_dir: Path) -> DatabaseConnection:
    db_file = temp_dir / "test_ssb.db"
    conn = DatabaseConnection(db_file)
    migrator = MigrationManager(conn)
    migrator.apply_all()
    return conn


@pytest.fixture
def repos(db_conn: DatabaseConnection):
    return {
        "content": ContentSetRepository(db_conn),
        "preset": PresetRepository(db_conn),
        "session": SessionRepository(db_conn),
        "analytics": AnalyticsRepository(db_conn),
        "settings": SettingsRepository(db_conn),
    }


@pytest.fixture
def doc_parser() -> DocumentParser:
    return DocumentParser(ocr_service=None)


@pytest.fixture
def import_mgr(repos, doc_parser) -> ImportManager:
    return ImportManager(repos["content"], doc_parser)


@pytest.fixture
def session_service(repos) -> SessionService:
    return SessionService(repos["session"], repos["content"], repos["preset"])


@pytest.fixture
def report_service() -> ReportService:
    return ReportService()
