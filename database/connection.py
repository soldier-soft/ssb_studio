"""SQLite connection management with WAL mode, foreign keys, and transaction support."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Union


class DatabaseConnection:
    """Manages SQLite connections and ensures proper PRAGMAs and transactional safety."""

    def __init__(self, db_path: Union[str, Path]) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def create_raw_connection(self) -> sqlite3.Connection:
        """Create and configure a new SQLite connection with foreign keys and WAL mode."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
        except sqlite3.OperationalError:
            pass
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing an auto-closing SQLite connection."""
        conn = self.create_raw_connection()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing an atomic transaction block with auto-commit/rollback and close."""
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    @contextmanager
    def cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager providing an atomic transaction block with a cursor."""
        with self.transaction() as conn:
            cur = conn.cursor()
            try:
                yield cur
            finally:
                cur.close()
