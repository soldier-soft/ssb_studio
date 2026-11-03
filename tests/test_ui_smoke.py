"""Smoke test verifying GUI initialization, theme loading, and widget instantiation."""

import pytest
from PySide6.QtWidgets import QApplication

from app.app_context import AppContext
from ui.main_window import MainWindow
from ui.styles.theme_manager import ThemeManager


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_instantiation(qapp, temp_dir):
    test_db = temp_dir / "smoke_test.db"
    ctx = AppContext(db_path=test_db)
    theme_mgr = ThemeManager(current_theme="dark", font_size=13)
    theme_mgr.apply_theme("dark", qapp)

    window = MainWindow(ctx, theme_mgr)
    assert window is not None
    assert window.windowTitle() == "SSB Practice Studio — Psychological Test Preparation"

    # Verify all screens are instantiated in the stack
    assert window.dashboard_screen is not None
    assert window.builder_screen is not None
    assert window.tat_screen is not None
    assert window.wat_screen is not None
    assert window.srt_screen is not None
    assert window.library_screen is not None
    assert window.history_screen is not None
    assert window.report_screen is not None
    assert window.settings_screen is not None

    # Test screen navigation
    window.navigate_to("builder")
    assert window.stack.currentWidget() == window.builder_screen

    window.navigate_to("library")
    assert window.stack.currentWidget() == window.library_screen

    window.navigate_to("dashboard")
    assert window.stack.currentWidget() == window.dashboard_screen

    # Test theme toggle
    theme_mgr.toggle_theme(qapp)
    assert theme_mgr.current_theme == "light"
    theme_mgr.toggle_theme(qapp)
    assert theme_mgr.current_theme == "dark"

    window.close()


def test_wat_and_srt_slide_advancing_in_practice_and_exam(qapp, temp_dir):
    """Verify that WAT and SRT screens correctly advance slides in both Practice and Exam modes."""
    from database.models import Preset, ContentSet
    from services.session_service import ActiveSessionItem

    test_db = temp_dir / "timing_test.db"
    ctx = AppContext(db_path=test_db)
    theme_mgr = ThemeManager(current_theme="dark", font_size=13)
    window = MainWindow(ctx, theme_mgr)

    # 1. Practice Mode WAT: verify Next button advances slide
    wat_set = ctx.content_repo.list_content_sets("WAT")[0]
    wat_items = [
        ActiveSessionItem(index=0, identifier="COURAGE", prompt_text="COURAGE"),
        ActiveSessionItem(index=1, identifier="LEADER", prompt_text="LEADER"),
        ActiveSessionItem(index=2, identifier="DUTY", prompt_text="DUTY"),
    ]
    preset_practice = Preset(
        name="WAT Test Practice",
        test_type="WAT",
        write_duration=15.0,
        item_count=3,
        exam_mode=False,
    )
    session, _ = ctx.session_service.prepare_session(preset_practice, wat_set, override_item_count=3)

    window.wat_screen.start_session(session, wat_items)
    # Fast forward countdown
    window.wat_screen.engine._deadline = window.wat_screen.engine.clock.now() - 0.1
    window.wat_screen._poll_tick()
    assert window.wat_screen.word_label.text() == "COURAGE"

    # Type answer and press force next in practice mode
    window.wat_screen.response_input.setText("Courage overcomes all odds.")
    window.wat_screen._on_force_next()
    assert window.wat_screen._current_item_index == 1
    assert window.wat_screen.word_label.text() == "LEADER"

    # Advance again
    window.wat_screen._on_force_next()
    assert window.wat_screen._current_item_index == 2
    assert window.wat_screen.word_label.text() == "DUTY"

    # 2. SRT Practice navigation & theme adaptation
    srt_set = ctx.content_repo.list_content_sets("SRT")[0]
    srt_items = [
        ActiveSessionItem(index=0, identifier="1", prompt_text="He was going to college when a fire broke out (...)"),
        ActiveSessionItem(index=1, identifier="2", prompt_text="His commander was injured in ambush (...)"),
    ]
    preset_srt = Preset(
        name="SRT Test Practice",
        test_type="SRT",
        write_duration=30.0,
        item_count=2,
        exam_mode=False,
    )
    session_srt, _ = ctx.session_service.prepare_session(preset_srt, srt_set, override_item_count=2)

    window.srt_screen.start_session(session_srt, srt_items)
    window.srt_screen.engine._deadline = window.srt_screen.engine.clock.now() - 0.1
    window.srt_screen._poll_tick()
    assert "fire broke out" in window.srt_screen.situation_text_lbl.text()

    # Practice mode Next
    window.srt_screen._on_force_next()
    assert window.srt_screen._current_item_index == 1
    assert "ambush" in window.srt_screen.situation_text_lbl.text()

    # 3. Exam Mode WAT: verify timer expiry automatically advances slide without user click
    preset_exam = Preset(
        name="WAT Test Exam",
        test_type="WAT",
        write_duration=15.0,
        item_count=3,
        exam_mode=True,
    )
    session_exam, _ = ctx.session_service.prepare_session(preset_exam, wat_set, override_item_count=3)
    window.wat_screen.start_session(session_exam, wat_items)
    # Countdown ends
    window.wat_screen.engine._deadline = window.wat_screen.engine.clock.now() - 0.1
    window.wat_screen._poll_tick()
    assert window.wat_screen.word_label.text() == "COURAGE"
    assert window.wat_screen._current_item_index == 0

    # 15s timer for word 1 expires
    window.wat_screen.engine._deadline = window.wat_screen.engine.clock.now() - 0.1
    window.wat_screen._poll_tick()
    assert window.wat_screen._current_item_index == 1
    assert window.wat_screen.word_label.text() == "LEADER"

    # 15s timer for word 2 expires
    window.wat_screen.engine._deadline = window.wat_screen.engine.clock.now() - 0.1
    window.wat_screen._poll_tick()
    assert window.wat_screen._current_item_index == 2
    assert window.wat_screen.word_label.text() == "DUTY"

    # Toggle to White / Light theme and check no crashes
    theme_mgr.apply_theme("light", qapp)
    assert window.srt_screen.theme_name == "light"
    assert window.wat_screen.theme_name == "light"
    assert window.tat_screen.theme_name == "light"

    window.wat_screen.poll_timer.stop()
    window.srt_screen.poll_timer.stop()
    ctx.session_service.current_session = None
    window.close()

