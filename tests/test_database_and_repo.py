"""Tests for SQLite database schema, repositories, sessions, responses, and real analytics calculations."""

from database.models import Preset, Session, SessionResponse


def test_migrations_and_builtin_presets(repos):
    preset_repo = repos["preset"]
    presets = preset_repo.list_presets()
    assert len(presets) >= 7

    builtins = [p.name for p in presets if p.is_builtin]
    assert "TAT Standard Exam (12 Pics)" in builtins
    assert "WAT 60-Word Official Standard" in builtins
    assert "SRT 60-Situation Official Exam" in builtins


def test_custom_preset_crud(repos):
    preset_repo = repos["preset"]
    new_p = Preset(
        name="My Custom WAT 45",
        test_type="WAT",
        view_duration=0.0,
        write_duration=12.0,
        item_count=45,
        randomize=True,
        repeat=False,
        countdown_seconds=5,
        sound_enabled=True,
        exam_mode=True,
    )
    p_id = preset_repo.create_preset(new_p)
    assert p_id > 0

    fetched = preset_repo.get_preset(p_id)
    assert fetched is not None
    assert fetched.name == "My Custom WAT 45"
    assert fetched.write_duration == 12.0
    assert fetched.item_count == 45
    assert fetched.randomize is True

    # Duplicate preset
    dup_id = preset_repo.duplicate_preset(p_id, "My Custom WAT 45 (Copy)")
    assert dup_id is not None
    assert dup_id != p_id
    dup = preset_repo.get_preset(dup_id)
    assert dup.name == "My Custom WAT 45 (Copy)"

    # Delete custom preset
    assert preset_repo.delete_preset(dup_id) is True
    assert preset_repo.get_preset(dup_id) is None


def test_content_sets_and_items(repos):
    content_repo = repos["content"]

    # WAT set
    wat_set_id = content_repo.create_content_set("WAT", "Official Set A", "words.txt")
    words = ["COURAGE", "DUTY", "HONOUR", "ALERT", "DISCIPLINE"]
    content_repo.add_wat_items(wat_set_id, words)

    wat_set = content_repo.get_content_set(wat_set_id)
    assert wat_set.item_count == 5
    wat_items = content_repo.get_wat_items(wat_set_id)
    assert len(wat_items) == 5
    assert [w.word for w in wat_items] == words

    # SRT set
    srt_set_id = content_repo.create_content_set("SRT", "Sample SRT Bank", "srt.pdf")
    srt_tuples = [
        ("1", "He saw a fire."),
        ("2", "His comrade fell in battle."),
        ("7", "A bridge collapsed."),
    ]
    content_repo.add_srt_items(srt_set_id, srt_tuples)

    srt_items = content_repo.get_srt_items(srt_set_id)
    assert len(srt_items) == 3
    assert [s.original_serial for s in srt_items] == ["1", "2", "7"]


def test_session_lifecycle_and_responses(repos):
    session_repo = repos["session"]

    session = Session(
        preset_name="WAT Standard",
        test_type="WAT",
        content_set_name="Word Deck 1",
        total_items=10,
        completed_items=0,
        is_exam_mode=True,
        view_duration=0.0,
        write_duration=15.0,
        status="IN_PROGRESS",
    )
    s_id = session_repo.create_session(session)
    assert s_id > 0

    # Save answers for items
    r1 = SessionResponse(
        session_id=s_id,
        item_index=0,
        item_identifier="COURAGE",
        prompt_text="COURAGE",
        response_text="Courage is indispensable for a commander.",
        time_spent_seconds=8.5,
    )
    session_repo.save_response(r1)

    r2 = SessionResponse(
        session_id=s_id,
        item_index=1,
        item_identifier="DUTY",
        prompt_text="DUTY",
        response_text="Duty comes before comfort.",
        time_spent_seconds=7.0,
    )
    session_repo.save_response(r2)

    responses = session_repo.get_responses(s_id)
    assert len(responses) == 2
    assert responses[0].response_text == "Courage is indispensable for a commander."
    assert responses[0].is_completed is True
    assert responses[0].response_length == len("Courage is indispensable for a commander.")

    # Update session status
    session_repo.update_session_status(
        session_id=s_id,
        status="COMPLETED",
        completed_items=2,
        elapsed_seconds=15.5,
        end_time="2026-11-02T12:00:00",
    )

    completed_session = session_repo.get_session(s_id)
    assert completed_session.status == "COMPLETED"
    assert completed_session.completed_items == 2


def test_real_analytics_aggregation(repos):
    """Verify statistics are computed from real database records, not mock constants!"""
    session_repo = repos["session"]
    analytics_repo = repos["analytics"]

    # Initial stats should be 0
    stats_empty = analytics_repo.get_dashboard_stats()
    assert stats_empty["total_completed"] == 0
    assert stats_empty["completion_rate"] == 0.0

    # Insert a completed session
    s1 = Session(
        test_type="TAT",
        preset_name="TAT Exam",
        content_set_name="TAT Images",
        total_items=5,
        completed_items=5,
        is_exam_mode=True,
        view_duration=30.0,
        write_duration=270.0,
        status="COMPLETED",
        elapsed_seconds=1500.0,
    )
    s1_id = session_repo.create_session(s1)

    # Insert responses
    for i in range(5):
        session_repo.save_response(
            SessionResponse(
                session_id=s1_id,
                item_index=i,
                item_identifier=f"pic_{i}.jpg",
                prompt_text=f"pic_{i}.jpg",
                response_text="A leader steps forward during the crisis and leads the team to safety.",
                time_spent_seconds=250.0,
            )
        )

    # Re-check stats
    stats = analytics_repo.get_dashboard_stats()
    assert stats["total_completed"] == 1
    assert stats["tat_tests"] == 1
    assert stats["tat_stories_written"] == 5
    assert stats["completion_rate"] == 100.0
    assert stats["total_practice_seconds"] == 1500.0
    assert stats["avg_response_length"] > 0
