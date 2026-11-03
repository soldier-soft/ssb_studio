"""Data access repositories for content sets, presets, sessions, responses, analytics, and settings."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database.connection import DatabaseConnection
from database.models import (
    ContentSet,
    Preset,
    Session,
    SessionResponse,
    SRTItem,
    TATItem,
    UserGoal,
    WATItem,
)


class ContentSetRepository:
    """Manages content sets (TAT image decks, WAT word lists, SRT question banks)."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db

    def create_content_set(
        self,
        test_type: str,
        name: str,
        source_file: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        now = datetime.now().isoformat()
        metadata_str = json.dumps(metadata or {})
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO content_sets (test_type, name, source_file, item_count, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, 0, ?, ?, ?)
                """,
                (test_type, name, source_file, now, now, metadata_str),
            )
            return int(cur.lastrowid)

    def add_tat_items(self, set_id: int, items: List[Tuple[int, str, str, str]]) -> None:
        """items: List of (item_order, file_path, original_filename, title)"""
        with self.db.transaction() as conn:
            conn.executemany(
                """
                INSERT INTO tat_items (set_id, item_order, file_path, original_filename, title)
                VALUES (?, ?, ?, ?, ?)
                """,
                [(set_id, order, path, orig_name, title) for order, path, orig_name, title in items],
            )
            conn.execute(
                "UPDATE content_sets SET item_count = (SELECT COUNT(*) FROM tat_items WHERE set_id = ?), updated_at = ? WHERE id = ?",
                (set_id, datetime.now().isoformat(), set_id),
            )

    def add_wat_items(self, set_id: int, words: List[str]) -> None:
        """words: List of words in source order"""
        with self.db.transaction() as conn:
            conn.executemany(
                """
                INSERT INTO wat_items (set_id, item_order, word)
                VALUES (?, ?, ?)
                """,
                [(set_id, idx + 1, word.strip()) for idx, word in enumerate(words) if word.strip()],
            )
            conn.execute(
                "UPDATE content_sets SET item_count = (SELECT COUNT(*) FROM wat_items WHERE set_id = ?), updated_at = ? WHERE id = ?",
                (set_id, datetime.now().isoformat(), set_id),
            )

    def add_srt_items(self, set_id: int, items: List[Tuple[str, str]]) -> None:
        """items: List of (original_serial, situation_text)"""
        with self.db.transaction() as conn:
            conn.executemany(
                """
                INSERT INTO srt_items (set_id, item_order, original_serial, situation_text)
                VALUES (?, ?, ?, ?)
                """,
                [(set_id, idx + 1, serial.strip(), text.strip()) for idx, (serial, text) in enumerate(items)],
            )
            conn.execute(
                "UPDATE content_sets SET item_count = (SELECT COUNT(*) FROM srt_items WHERE set_id = ?), updated_at = ? WHERE id = ?",
                (set_id, datetime.now().isoformat(), set_id),
            )

    def get_content_set(self, set_id: int) -> Optional[ContentSet]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM content_sets WHERE id = ?", (set_id,))
            row = cur.fetchone()
            if not row:
                return None
            return ContentSet(
                id=row["id"],
                test_type=row["test_type"],
                name=row["name"],
                source_file=row["source_file"],
                item_count=row["item_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata_json=row["metadata_json"],
            )

    def list_content_sets(self, test_type: Optional[str] = None) -> List[ContentSet]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            if test_type:
                cur.execute(
                    "SELECT * FROM content_sets WHERE test_type = ? ORDER BY id DESC",
                    (test_type,),
                )
            else:
                cur.execute("SELECT * FROM content_sets ORDER BY id DESC")
            rows = cur.fetchall()
            return [
                ContentSet(
                    id=r["id"],
                    test_type=r["test_type"],
                    name=r["name"],
                    source_file=r["source_file"],
                    item_count=r["item_count"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    metadata_json=r["metadata_json"],
                )
                for r in rows
            ]

    def get_tat_items(self, set_id: int) -> List[TATItem]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM tat_items WHERE set_id = ? ORDER BY item_order ASC",
                (set_id,),
            )
            return [
                TATItem(
                    id=r["id"],
                    set_id=r["set_id"],
                    item_order=r["item_order"],
                    file_path=r["file_path"],
                    original_filename=r["original_filename"],
                    title=r["title"],
                )
                for r in cur.fetchall()
            ]

    def get_wat_items(self, set_id: int) -> List[WATItem]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM wat_items WHERE set_id = ? ORDER BY item_order ASC",
                (set_id,),
            )
            return [
                WATItem(
                    id=r["id"],
                    set_id=r["set_id"],
                    item_order=r["item_order"],
                    word=r["word"],
                )
                for r in cur.fetchall()
            ]

    def get_srt_items(self, set_id: int) -> List[SRTItem]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM srt_items WHERE set_id = ? ORDER BY item_order ASC",
                (set_id,),
            )
            return [
                SRTItem(
                    id=r["id"],
                    set_id=r["set_id"],
                    item_order=r["item_order"],
                    original_serial=r["original_serial"],
                    situation_text=r["situation_text"],
                )
                for r in cur.fetchall()
            ]

    def delete_content_set(self, set_id: int) -> bool:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM content_sets WHERE id = ?", (set_id,))
            return cur.rowcount > 0

    def update_content_set_name(self, set_id: int, new_name: str) -> bool:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE content_sets SET name = ?, updated_at = ? WHERE id = ?",
                (new_name, datetime.now().isoformat(), set_id),
            )
            return cur.rowcount > 0


class PresetRepository:
    """Manages test presets for TAT, WAT, and SRT."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db

    def create_preset(self, preset: Preset) -> int:
        now = datetime.now().isoformat()
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO presets (
                    name, test_type, view_duration, write_duration, item_count,
                    randomize, repeat, countdown_seconds, sound_enabled, exam_mode,
                    is_builtin, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    preset.name,
                    preset.test_type,
                    preset.view_duration,
                    preset.write_duration,
                    preset.item_count,
                    1 if preset.randomize else 0,
                    1 if preset.repeat else 0,
                    preset.countdown_seconds,
                    1 if preset.sound_enabled else 0,
                    1 if preset.exam_mode else 0,
                    1 if preset.is_builtin else 0,
                    now,
                ),
            )
            return int(cur.lastrowid)

    def get_preset(self, preset_id: int) -> Optional[Preset]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM presets WHERE id = ?", (preset_id,))
            r = cur.fetchone()
            if not r:
                return None
            return Preset(
                id=r["id"],
                name=r["name"],
                test_type=r["test_type"],
                view_duration=float(r["view_duration"]),
                write_duration=float(r["write_duration"]),
                item_count=int(r["item_count"]),
                randomize=bool(r["randomize"]),
                repeat=bool(r["repeat"]),
                countdown_seconds=int(r["countdown_seconds"]),
                sound_enabled=bool(r["sound_enabled"]),
                exam_mode=bool(r["exam_mode"]),
                is_builtin=bool(r["is_builtin"]),
                created_at=r["created_at"],
            )

    def list_presets(self, test_type: Optional[str] = None) -> List[Preset]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            if test_type:
                cur.execute(
                    "SELECT * FROM presets WHERE test_type = ? ORDER BY is_builtin DESC, id ASC",
                    (test_type,),
                )
            else:
                cur.execute("SELECT * FROM presets ORDER BY test_type, is_builtin DESC, id ASC")
            rows = cur.fetchall()
            return [
                Preset(
                    id=r["id"],
                    name=r["name"],
                    test_type=r["test_type"],
                    view_duration=float(r["view_duration"]),
                    write_duration=float(r["write_duration"]),
                    item_count=int(r["item_count"]),
                    randomize=bool(r["randomize"]),
                    repeat=bool(r["repeat"]),
                    countdown_seconds=int(r["countdown_seconds"]),
                    sound_enabled=bool(r["sound_enabled"]),
                    exam_mode=bool(r["exam_mode"]),
                    is_builtin=bool(r["is_builtin"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def update_preset(self, preset: Preset) -> bool:
        if preset.id is None:
            return False
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE presets SET
                    name = ?, test_type = ?, view_duration = ?, write_duration = ?,
                    item_count = ?, randomize = ?, repeat = ?, countdown_seconds = ?,
                    sound_enabled = ?, exam_mode = ?
                WHERE id = ? AND is_builtin = 0
                """,
                (
                    preset.name,
                    preset.test_type,
                    preset.view_duration,
                    preset.write_duration,
                    preset.item_count,
                    1 if preset.randomize else 0,
                    1 if preset.repeat else 0,
                    preset.countdown_seconds,
                    1 if preset.sound_enabled else 0,
                    1 if preset.exam_mode else 0,
                    preset.id,
                ),
            )
            return cur.rowcount > 0

    def delete_preset(self, preset_id: int) -> bool:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM presets WHERE id = ? AND is_builtin = 0", (preset_id,))
            return cur.rowcount > 0

    def duplicate_preset(self, preset_id: int, new_name: str) -> Optional[int]:
        original = self.get_preset(preset_id)
        if not original:
            return None
        original.id = None
        original.name = new_name
        original.is_builtin = False
        return self.create_preset(original)


class SessionRepository:
    """Manages examination & practice sessions and responses."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db

    def create_session(self, session: Session) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO sessions (
                    preset_id, test_type, preset_name, content_set_id, content_set_name,
                    total_items, completed_items, is_exam_mode, view_duration, write_duration,
                    status, start_time, end_time, elapsed_seconds, evaluator_notes, user_rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.preset_id,
                    session.test_type,
                    session.preset_name,
                    session.content_set_id,
                    session.content_set_name,
                    session.total_items,
                    session.completed_items,
                    1 if session.is_exam_mode else 0,
                    session.view_duration,
                    session.write_duration,
                    session.status,
                    session.start_time,
                    session.end_time,
                    session.elapsed_seconds,
                    session.evaluator_notes,
                    session.user_rating,
                ),
            )
            return int(cur.lastrowid)

    def get_session(self, session_id: int) -> Optional[Session]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            r = cur.fetchone()
            if not r:
                return None
            return Session(
                id=r["id"],
                preset_id=r["preset_id"],
                test_type=r["test_type"],
                preset_name=r["preset_name"],
                content_set_id=r["content_set_id"],
                content_set_name=r["content_set_name"],
                total_items=int(r["total_items"]),
                completed_items=int(r["completed_items"]),
                is_exam_mode=bool(r["is_exam_mode"]),
                view_duration=float(r["view_duration"]),
                write_duration=float(r["write_duration"]),
                status=r["status"],
                start_time=r["start_time"],
                end_time=r["end_time"],
                elapsed_seconds=float(r["elapsed_seconds"]),
                evaluator_notes=r["evaluator_notes"] or "",
                user_rating=r["user_rating"],
            )

    def list_sessions(
        self,
        test_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        search_query: Optional[str] = None,
    ) -> List[Session]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM sessions WHERE 1=1"
            params: List[Any] = []

            if test_type and test_type != "ALL":
                query += " AND test_type = ?"
                params.append(test_type)

            if search_query:
                query += " AND (preset_name LIKE ? OR content_set_name LIKE ? OR evaluator_notes LIKE ?)"
                like_term = f"%{search_query.strip()}%"
                params.extend([like_term, like_term, like_term])

            query += " ORDER BY id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            return [
                Session(
                    id=r["id"],
                    preset_id=r["preset_id"],
                    test_type=r["test_type"],
                    preset_name=r["preset_name"],
                    content_set_id=r["content_set_id"],
                    content_set_name=r["content_set_name"],
                    total_items=int(r["total_items"]),
                    completed_items=int(r["completed_items"]),
                    is_exam_mode=bool(r["is_exam_mode"]),
                    view_duration=float(r["view_duration"]),
                    write_duration=float(r["write_duration"]),
                    status=r["status"],
                    start_time=r["start_time"],
                    end_time=r["end_time"],
                    elapsed_seconds=float(r["elapsed_seconds"]),
                    evaluator_notes=r["evaluator_notes"] or "",
                    user_rating=r["user_rating"],
                )
                for r in rows
            ]

    def update_session_status(
        self,
        session_id: int,
        status: str,
        completed_items: int,
        elapsed_seconds: float,
        end_time: Optional[str] = None,
    ) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                UPDATE sessions SET
                    status = ?, completed_items = ?, elapsed_seconds = ?, end_time = ?
                WHERE id = ?
                """,
                (status, completed_items, elapsed_seconds, end_time, session_id),
            )

    def update_evaluator_notes(
        self, session_id: int, notes: str, rating: Optional[int] = None
    ) -> None:
        with self.db.transaction() as conn:
            if rating is not None:
                conn.execute(
                    "UPDATE sessions SET evaluator_notes = ?, user_rating = ? WHERE id = ?",
                    (notes, rating, session_id),
                )
            else:
                conn.execute(
                    "UPDATE sessions SET evaluator_notes = ? WHERE id = ?",
                    (notes, session_id),
                )

    def save_response(self, resp: SessionResponse) -> int:
        """Upsert response by session_id and item_index."""
        now = datetime.now().isoformat()
        length = len(resp.response_text.strip())
        is_completed = 1 if length > 0 else 0

        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM session_responses WHERE session_id = ? AND item_index = ?",
                (resp.session_id, resp.item_index),
            )
            existing = cur.fetchone()

            if existing:
                resp_id = existing["id"]
                cur.execute(
                    """
                    UPDATE session_responses SET
                        item_identifier = ?, prompt_text = ?, response_text = ?,
                        response_length = ?, time_spent_seconds = ?, is_completed = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        resp.item_identifier,
                        resp.prompt_text,
                        resp.response_text,
                        length,
                        resp.time_spent_seconds,
                        is_completed,
                        now,
                        resp_id,
                    ),
                )
                return resp_id
            else:
                cur.execute(
                    """
                    INSERT INTO session_responses (
                        session_id, item_index, item_identifier, prompt_text, response_text,
                        response_length, time_spent_seconds, is_completed, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        resp.session_id,
                        resp.item_index,
                        resp.item_identifier,
                        resp.prompt_text,
                        resp.response_text,
                        length,
                        resp.time_spent_seconds,
                        is_completed,
                        now,
                        now,
                    ),
                )
                return int(cur.lastrowid)

    def get_responses(self, session_id: int) -> List[SessionResponse]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM session_responses WHERE session_id = ? ORDER BY item_index ASC",
                (session_id,),
            )
            rows = cur.fetchall()
            return [
                SessionResponse(
                    id=r["id"],
                    session_id=r["session_id"],
                    item_index=int(r["item_index"]),
                    item_identifier=r["item_identifier"],
                    prompt_text=r["prompt_text"],
                    response_text=r["response_text"] or "",
                    response_length=int(r["response_length"]),
                    time_spent_seconds=float(r["time_spent_seconds"]),
                    is_completed=bool(r["is_completed"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def get_response_for_item(
        self, session_id: int, item_index: int
    ) -> Optional[SessionResponse]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM session_responses WHERE session_id = ? AND item_index = ?",
                (session_id, item_index),
            )
            r = cur.fetchone()
            if not r:
                return None
            return SessionResponse(
                id=r["id"],
                session_id=r["session_id"],
                item_index=int(r["item_index"]),
                item_identifier=r["item_identifier"],
                prompt_text=r["prompt_text"],
                response_text=r["response_text"] or "",
                response_length=int(r["response_length"]),
                time_spent_seconds=float(r["time_spent_seconds"]),
                is_completed=bool(r["is_completed"]),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

    def delete_session(self, session_id: int) -> bool:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return cur.rowcount > 0

    def get_uncompleted_session(self) -> Optional[Session]:
        """Check for interrupted in-progress sessions for crash recovery."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM sessions WHERE status = 'IN_PROGRESS' ORDER BY id DESC LIMIT 1"
            )
            r = cur.fetchone()
            if not r:
                return None
            return Session(
                id=r["id"],
                preset_id=r["preset_id"],
                test_type=r["test_type"],
                preset_name=r["preset_name"],
                content_set_id=r["content_set_id"],
                content_set_name=r["content_set_name"],
                total_items=int(r["total_items"]),
                completed_items=int(r["completed_items"]),
                is_exam_mode=bool(r["is_exam_mode"]),
                view_duration=float(r["view_duration"]),
                write_duration=float(r["write_duration"]),
                status=r["status"],
                start_time=r["start_time"],
                end_time=r["end_time"],
                elapsed_seconds=float(r["elapsed_seconds"]),
                evaluator_notes=r["evaluator_notes"] or "",
                user_rating=r["user_rating"],
            )


class AnalyticsRepository:
    """Calculates all statistics and metrics directly from SQLite records."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db

    def get_dashboard_stats(self) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Total tests completed
            cur.execute("SELECT COUNT(*) FROM sessions WHERE status = 'COMPLETED'")
            total_completed = cur.fetchone()[0] or 0

            # Total tests attempted (all sessions)
            cur.execute("SELECT COUNT(*) FROM sessions")
            total_sessions = cur.fetchone()[0] or 0

            # Total practice duration (sum of elapsed_seconds)
            cur.execute("SELECT SUM(elapsed_seconds) FROM sessions")
            total_elapsed_seconds = cur.fetchone()[0] or 0.0

            # Overall item completion percentage
            cur.execute("SELECT SUM(completed_items), SUM(total_items) FROM sessions")
            row = cur.fetchone()
            sum_completed = row[0] or 0
            sum_total = row[1] or 0
            completion_rate = (
                (sum_completed / sum_total * 100.0) if sum_total > 0 else 0.0
            )

            # Tests by test_type
            cur.execute(
                "SELECT test_type, COUNT(*) FROM sessions WHERE status = 'COMPLETED' GROUP BY test_type"
            )
            type_counts = {r[0]: r[1] for r in cur.fetchall()}

            # Total responses written and non-empty responses
            cur.execute(
                "SELECT COUNT(*), SUM(is_completed), AVG(response_length) FROM session_responses"
            )
            r_row = cur.fetchone()
            total_responses = r_row[0] or 0
            completed_responses = r_row[1] or 0
            avg_response_len = round(float(r_row[2] or 0.0), 1)

            # TAT stories written
            cur.execute(
                """
                SELECT COUNT(*) FROM session_responses sr
                JOIN sessions s ON sr.session_id = s.id
                WHERE s.test_type = 'TAT' AND sr.is_completed = 1
                """
            )
            tat_stories = cur.fetchone()[0] or 0

            # WAT words attempted
            cur.execute(
                """
                SELECT COUNT(*) FROM session_responses sr
                JOIN sessions s ON sr.session_id = s.id
                WHERE s.test_type = 'WAT' AND sr.is_completed = 1
                """
            )
            wat_words = cur.fetchone()[0] or 0

            # SRT reactions attempted
            cur.execute(
                """
                SELECT COUNT(*) FROM session_responses sr
                JOIN sessions s ON sr.session_id = s.id
                WHERE s.test_type = 'SRT' AND sr.is_completed = 1
                """
            )
            srt_reactions = cur.fetchone()[0] or 0

            return {
                "total_completed": total_completed,
                "total_sessions": total_sessions,
                "total_practice_seconds": total_elapsed_seconds,
                "completion_rate": round(completion_rate, 1),
                "tat_tests": type_counts.get("TAT", 0),
                "wat_tests": type_counts.get("WAT", 0),
                "srt_tests": type_counts.get("SRT", 0),
                "total_responses": total_responses,
                "completed_responses": completed_responses,
                "avg_response_length": avg_response_len,
                "tat_stories_written": tat_stories,
                "wat_words_attempted": wat_words,
                "srt_reactions_attempted": srt_reactions,
            }

    def get_recent_sessions(self, limit: int = 5) -> List[Session]:
        session_repo = SessionRepository(self.db)
        return session_repo.list_sessions(limit=limit)

    def get_type_analytics(self, test_type: str) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*), SUM(elapsed_seconds), AVG(completed_items * 100.0 / CASE WHEN total_items=0 THEN 1 ELSE total_items END)
                FROM sessions WHERE test_type = ? AND status = 'COMPLETED'
                """,
                (test_type,),
            )
            row = cur.fetchone()
            count = row[0] or 0
            total_sec = row[1] or 0.0
            avg_comp = round(float(row[2] or 0.0), 1)

            cur.execute(
                """
                SELECT AVG(sr.response_length), AVG(sr.time_spent_seconds)
                FROM session_responses sr
                JOIN sessions s ON sr.session_id = s.id
                WHERE s.test_type = ? AND sr.is_completed = 1
                """,
                (test_type,),
            )
            r_row = cur.fetchone()
            avg_chars = round(float(r_row[0] or 0.0), 1)
            avg_time = round(float(r_row[1] or 0.0), 1)

            return {
                "test_type": test_type,
                "completed_count": count,
                "total_seconds": total_sec,
                "avg_completion_rate": avg_comp,
                "avg_chars_per_response": avg_chars,
                "avg_seconds_per_response": avg_time,
            }


class SettingsRepository:
    """Stores key-value application settings in SQLite."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            r = cur.fetchone()
            if not r:
                return default
            try:
                return json.loads(r["value"])
            except (json.JSONDecodeError, TypeError):
                return r["value"]

    def set_setting(self, key: str, value: Any) -> None:
        val_str = json.dumps(value)
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO app_settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, val_str),
            )

    def get_all_settings(self) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT key, value FROM app_settings")
            result = {}
            for r in cur.fetchall():
                try:
                    result[r["key"]] = json.loads(r["value"])
                except Exception:
                    result[r["key"]] = r["value"]
            return result


class UserGoalRepository:
    """Manages custom user goals and targets."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db

    def add_goal(
        self,
        test_type: str,
        goal_text: str,
        target_count: int = 0,
        target_date: Optional[str] = None,
    ) -> int:
        now = datetime.now().isoformat()
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO user_goals (test_type, goal_text, target_count, target_date, is_achieved, created_at)
                VALUES (?, ?, ?, ?, 0, ?)
                """,
                (test_type, goal_text, target_count, target_date, now),
            )
            return int(cur.lastrowid)

    def list_goals(self) -> List[UserGoal]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM user_goals ORDER BY is_achieved ASC, id DESC")
            return [
                UserGoal(
                    id=r["id"],
                    test_type=r["test_type"],
                    goal_text=r["goal_text"],
                    target_count=int(r["target_count"]),
                    target_date=r["target_date"],
                    is_achieved=bool(r["is_achieved"]),
                    created_at=r["created_at"],
                )
                for r in cur.fetchall()
            ]

    def toggle_goal(self, goal_id: int) -> bool:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE user_goals SET is_achieved = CASE WHEN is_achieved=1 THEN 0 ELSE 1 END WHERE id = ?",
                (goal_id,),
            )
            return cur.rowcount > 0

    def delete_goal(self, goal_id: int) -> bool:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM user_goals WHERE id = ?", (goal_id,))
            return cur.rowcount > 0
