"""Database migration manager and schema definitions."""

import logging
from datetime import datetime
from typing import List, Tuple

from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

MIGRATION_V1_SQL: List[str] = [
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS content_sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_type TEXT NOT NULL,
        name TEXT NOT NULL,
        source_file TEXT,
        item_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        metadata_json TEXT DEFAULT '{}'
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS tat_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        set_id INTEGER NOT NULL REFERENCES content_sets(id) ON DELETE CASCADE,
        item_order INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        title TEXT DEFAULT ''
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS wat_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        set_id INTEGER NOT NULL REFERENCES content_sets(id) ON DELETE CASCADE,
        item_order INTEGER NOT NULL,
        word TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS srt_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        set_id INTEGER NOT NULL REFERENCES content_sets(id) ON DELETE CASCADE,
        item_order INTEGER NOT NULL,
        original_serial TEXT NOT NULL,
        situation_text TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS presets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        test_type TEXT NOT NULL,
        view_duration REAL DEFAULT 0.0,
        write_duration REAL NOT NULL,
        item_count INTEGER NOT NULL,
        randomize INTEGER DEFAULT 0,
        repeat INTEGER DEFAULT 0,
        countdown_seconds INTEGER DEFAULT 3,
        sound_enabled INTEGER DEFAULT 1,
        exam_mode INTEGER DEFAULT 1,
        is_builtin INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        preset_id INTEGER REFERENCES presets(id) ON DELETE SET NULL,
        test_type TEXT NOT NULL,
        preset_name TEXT NOT NULL,
        content_set_id INTEGER REFERENCES content_sets(id) ON DELETE SET NULL,
        content_set_name TEXT DEFAULT '',
        total_items INTEGER NOT NULL,
        completed_items INTEGER DEFAULT 0,
        is_exam_mode INTEGER DEFAULT 1,
        view_duration REAL DEFAULT 0.0,
        write_duration REAL NOT NULL,
        status TEXT DEFAULT 'IN_PROGRESS',
        start_time TEXT NOT NULL,
        end_time TEXT,
        elapsed_seconds REAL DEFAULT 0.0,
        evaluator_notes TEXT DEFAULT '',
        user_rating INTEGER
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS session_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        item_index INTEGER NOT NULL,
        item_identifier TEXT NOT NULL,
        prompt_text TEXT NOT NULL,
        response_text TEXT DEFAULT '',
        response_length INTEGER DEFAULT 0,
        time_spent_seconds REAL DEFAULT 0.0,
        is_completed INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS user_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_type TEXT NOT NULL,
        goal_text TEXT NOT NULL,
        target_count INTEGER DEFAULT 0,
        target_date TEXT,
        is_achieved INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_content_sets_type ON content_sets(test_type);",
    "CREATE INDEX IF NOT EXISTS idx_tat_items_set ON tat_items(set_id, item_order);",
    "CREATE INDEX IF NOT EXISTS idx_wat_items_set ON wat_items(set_id, item_order);",
    "CREATE INDEX IF NOT EXISTS idx_srt_items_set ON srt_items(set_id, item_order);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_type ON sessions(test_type, start_time);",
    "CREATE INDEX IF NOT EXISTS idx_responses_session ON session_responses(session_id, item_index);",
]

BUILTIN_PRESETS = [
    # name, test_type, view_duration, write_duration, item_count, randomize, repeat, countdown, sound, exam_mode, is_builtin
    ("TAT Standard Exam (12 Pics)", "TAT", 30.0, 270.0, 12, 0, 0, 3, 1, 1, 1),
    ("TAT Quick Practice (3 Pics)", "TAT", 30.0, 270.0, 3, 0, 0, 3, 1, 0, 1),
    ("WAT 10-Word Rapid Drill", "WAT", 0.0, 15.0, 10, 0, 0, 3, 1, 0, 1),
    ("WAT 30-Word Sprint", "WAT", 0.0, 15.0, 30, 0, 0, 3, 1, 1, 1),
    ("WAT 60-Word Official Standard", "WAT", 0.0, 15.0, 60, 0, 0, 3, 1, 1, 1),
    ("SRT 15-Situation Practice", "SRT", 0.0, 30.0, 15, 0, 0, 3, 1, 0, 1),
    ("SRT 60-Situation Official Exam", "SRT", 0.0, 30.0, 60, 0, 0, 3, 1, 1, 1),
]


class MigrationManager:
    """Applies schema migrations idempotently and seeds necessary default presets."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db

    def apply_all(self) -> None:
        """Run all pending database migrations."""
        with self.db.transaction() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
                """
            )
            cur = conn.cursor()
            cur.execute("SELECT version FROM schema_migrations ORDER BY version ASC;")
            applied_versions = {row[0] for row in cur.fetchall()}

            if 1 not in applied_versions:
                self._apply_v1(conn)

    def _apply_v1(self, conn) -> None:
        logger.info("Applying database migration v1...")
        for sql in MIGRATION_V1_SQL:
            conn.execute(sql)

        # Seed builtin presets if not already seeded
        now = datetime.now().isoformat()
        for preset in BUILTIN_PRESETS:
            conn.execute(
                """
                INSERT INTO presets (
                    name, test_type, view_duration, write_duration, item_count,
                    randomize, repeat, countdown_seconds, sound_enabled, exam_mode,
                    is_builtin, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (*preset, now),
            )

        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (1, ?);",
            (now,),
        )
        logger.info("Migration v1 applied successfully.")
