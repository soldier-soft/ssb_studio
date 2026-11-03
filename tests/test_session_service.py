"""Integration tests for SessionService lifecycle, debouncing, and duration estimations."""

from database.models import ContentSet, Preset
from services.session_service import SessionService


def test_prepare_wat_session_with_repeat(repos, session_service: SessionService):
    content_repo = repos["content"]

    set_id = content_repo.create_content_set("WAT", "Mini Word Deck", "deck.txt")
    words = ["DUTY", "HONOUR", "BRAVERY"]
    content_repo.add_wat_items(set_id, words)

    c_set = content_repo.get_content_set(set_id)

    preset = Preset(
        name="WAT 5-Word Drill",
        test_type="WAT",
        view_duration=0.0,
        write_duration=15.0,
        item_count=5,
        randomize=False,
        repeat=True,  # 3 items repeated to fill 5 slots
        exam_mode=True,
    )

    session, items = session_service.prepare_session(preset, c_set, override_item_count=5)

    assert session.id is not None
    assert session.total_items == 5
    assert len(items) == 5
    assert [it.identifier for it in items] == ["DUTY", "HONOUR", "BRAVERY", "DUTY", "HONOUR"]


def test_buffer_and_flush_responses(repos, session_service: SessionService):
    content_repo = repos["content"]
    session_repo = repos["session"]

    set_id = content_repo.create_content_set("SRT", "Single Situation Bank", "srt.txt")
    content_repo.add_srt_items(set_id, [("1", "There was an earthquake.")])
    c_set = content_repo.get_content_set(set_id)

    preset = Preset(
        name="SRT 1",
        test_type="SRT",
        view_duration=0.0,
        write_duration=30.0,
        item_count=1,
        exam_mode=False,
    )

    session, items = session_service.prepare_session(preset, c_set)

    # User types answer
    session_service.buffer_response(0, "Evacuated to open ground.", time_spent=12.0)
    session_service.flush_item_response(0)

    responses = session_repo.get_responses(session.id)
    assert len(responses) == 1
    assert responses[0].response_text == "Evacuated to open ground."
    assert responses[0].time_spent_seconds == 12.0


def test_calculate_estimated_duration():
    # TAT: 12 pics * (30s + 270s) + 3s countdown = 3603s (60m 3s)
    tat_dur = SessionService.calculate_estimated_duration("TAT", 12, 30.0, 270.0, 3)
    assert tat_dur == 3603.0

    # WAT: 60 words * 15s + 3s countdown = 903s (15m 3s)
    wat_dur = SessionService.calculate_estimated_duration("WAT", 60, 0.0, 15.0, 3)
    assert wat_dur == 903.0

    # SRT: 60 situations * 30s + 5s countdown = 1805s (30m 5s)
    srt_dur = SessionService.calculate_estimated_duration("SRT", 60, 0.0, 30.0, 5)
    assert srt_dur == 1805.0
