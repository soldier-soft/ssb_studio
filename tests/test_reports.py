"""Tests for ReportLab PDF report generation, CSV export, and database backup/restore."""

from pathlib import Path
from database.connection import DatabaseConnection
from database.models import Session, SessionResponse
from services.report_service import ReportService


def test_export_session_to_csv(temp_dir: Path, report_service: ReportService):
    session = Session(
        id=42,
        preset_name="WAT Rapid Drill",
        test_type="WAT",
        content_set_name="Drill Set A",
        total_items=2,
        completed_items=2,
        is_exam_mode=True,
        view_duration=0.0,
        write_duration=15.0,
        status="COMPLETED",
        start_time="2026-11-02T10:00:00",
        elapsed_seconds=30.0,
    )

    responses = [
        SessionResponse(
            session_id=42,
            item_index=0,
            item_identifier="COURAGE",
            prompt_text="COURAGE",
            response_text="Courage conquers all obstacles.",
            response_length=31,
            time_spent_seconds=12.0,
            is_completed=True,
        ),
        SessionResponse(
            session_id=42,
            item_index=1,
            item_identifier="LOYALTY",
            prompt_text="LOYALTY",
            response_text="Loyalty binds soldiers together.",
            response_length=32,
            time_spent_seconds=10.0,
            is_completed=True,
        ),
    ]

    csv_path = temp_dir / "test_session_42.csv"
    res = report_service.export_session_to_csv(session, responses, csv_path)

    assert res.exists()
    content = csv_path.read_text(encoding="utf-8-sig")
    assert "WAT Rapid Drill" in content
    assert "COURAGE" in content
    assert "Courage conquers all obstacles." in content
    assert "Loyalty binds soldiers together." in content


def test_generate_pdf_report(temp_dir: Path, report_service: ReportService):
    session = Session(
        id=101,
        preset_name="SRT Full Exam",
        test_type="SRT",
        content_set_name="Official Situation Bank",
        total_items=2,
        completed_items=2,
        is_exam_mode=True,
        view_duration=0.0,
        write_duration=30.0,
        status="COMPLETED",
        start_time="2026-11-02T14:30:00",
        elapsed_seconds=60.0,
        evaluator_notes="Good decisive answers showing initiative.",
    )

    responses = [
        SessionResponse(
            session_id=101,
            item_index=0,
            item_identifier="1",
            prompt_text="He was in a train compartment when a thief snatched a lady's bag and jumped off. He...",
            response_text="Pulled the emergency chain, noted the thief's direction, and pursued him with co-passengers.",
            response_length=90,
            time_spent_seconds=22.0,
            is_completed=True,
        ),
        SessionResponse(
            session_id=101,
            item_index=1,
            item_identifier="2",
            prompt_text="During an expedition, the food supplies got washed away. He...",
            response_text="Rationed available emergency supplies, located edible forest resources, and continued the mission.",
            response_length=95,
            time_spent_seconds=25.0,
            is_completed=True,
        ),
    ]

    pdf_path = temp_dir / "report_101.pdf"
    res = report_service.generate_pdf_report(session, responses, pdf_path)

    assert res.exists()
    assert pdf_path.stat().st_size > 1000  # Valid generated PDF file size


def test_sqlite_backup_and_restore(temp_dir: Path, db_conn: DatabaseConnection, report_service: ReportService):
    # Insert some data into active db
    with db_conn.transaction() as conn:
        conn.execute("INSERT INTO app_settings (key, value) VALUES ('test_key', '\"test_val\"');")

    backup_path = temp_dir / "backup_test.db"
    report_service.backup_database(db_conn.db_path, backup_path)
    assert backup_path.exists()

    # Modify active db
    with db_conn.transaction() as conn:
        conn.execute("UPDATE app_settings SET value = '\"modified\"' WHERE key = 'test_key';")

    # Restore from backup
    assert report_service.restore_database(backup_path, db_conn.db_path) is True

    # Verify active db has restored value
    with db_conn.transaction() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM app_settings WHERE key = 'test_key';")
        val = cur.fetchone()[0]
        assert val == '"test_val"'
