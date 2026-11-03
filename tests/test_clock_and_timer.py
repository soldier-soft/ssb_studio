"""Tests for the monotonic clock, precision deadline timing, and single-transition guarantees."""

import pytest
from core.clock import TestClock
from core.timer_engine import TestPhase, TimerEngine


def test_test_clock_advance():
    clock = TestClock(initial_time=100.0)
    assert clock.now() == 100.0
    clock.advance(15.5)
    assert clock.now() == 115.5
    with pytest.raises(ValueError):
        clock.advance(-1.0)


def test_tat_standard_timing_transitions():
    """Verify TAT: 3s countdown -> 30s viewing -> 270s writing -> next picture."""
    clock = TestClock(initial_time=500.0)
    engine = TimerEngine(
        test_type="TAT",
        total_items=2,
        view_duration=30.0,
        write_duration=270.0,
        is_exam_mode=True,
        countdown_seconds=3,
        clock=clock,
    )

    phase_transitions = []
    sound_cues = []

    def on_phase(old_p, new_p, idx):
        phase_transitions.append((old_p, new_p, idx))

    def on_sound(cue):
        sound_cues.append(cue)

    engine.on_phase_change = on_phase
    engine.on_sound_cue = on_sound

    # Start engine
    engine.start()
    assert engine.phase == TestPhase.PRE_COUNTDOWN
    assert engine.item_index == 0

    state = engine.poll_tick()
    assert state.remaining_seconds == 3.0

    # Advance through pre-countdown (3s)
    clock.advance(3.0)
    engine.poll_tick()
    assert engine.phase == TestPhase.TAT_VIEWING
    assert engine.item_index == 0

    # Viewing phase is 30s
    state = engine.poll_tick()
    assert state.remaining_seconds == 30.0

    # Advance 15s into viewing
    clock.advance(15.0)
    state = engine.poll_tick()
    assert state.remaining_seconds == 15.0
    assert state.phase == TestPhase.TAT_VIEWING

    # Advance remaining 15s -> should switch to TAT_WRITING
    clock.advance(15.0)
    engine.poll_tick()
    assert engine.phase == TestPhase.TAT_WRITING
    assert engine.item_index == 0

    # Writing phase is 270s
    state = engine.poll_tick()
    assert state.remaining_seconds == 270.0

    # Advance 270s -> should advance to item 2 (index 1) viewing phase
    clock.advance(270.0)
    engine.poll_tick()
    assert engine.phase == TestPhase.TAT_VIEWING
    assert engine.item_index == 1

    # Item 2 viewing phase (30s) -> writing phase (270s) -> COMPLETED
    clock.advance(30.0)
    engine.poll_tick()
    assert engine.phase == TestPhase.TAT_WRITING
    assert engine.item_index == 1

    clock.advance(270.0)
    engine.poll_tick()
    assert engine.phase == TestPhase.COMPLETED

    assert "bell" in sound_cues


def test_transition_fires_only_once():
    """Verify that multiple poll ticks past deadline do NOT trigger duplicate transitions."""
    clock = TestClock(initial_time=100.0)
    engine = TimerEngine(
        test_type="WAT",
        total_items=2,
        write_duration=15.0,
        is_exam_mode=True,
        countdown_seconds=0,
        clock=clock,
    )

    transitions = []
    engine.on_phase_change = lambda o, n, idx: transitions.append((o, n, idx))

    engine.start()
    assert engine.phase == TestPhase.WAT_SLIDE
    assert engine.item_index == 0

    # Advance way past the 15s deadline (e.g. system was blocked for 25s)
    clock.advance(25.0)
    engine.poll_tick()

    assert engine.item_index == 1
    # Poll tick again without advancing clock
    engine.poll_tick()
    assert engine.item_index == 1  # Still on item 1, did not skip to completed!


def test_exam_mode_forbids_pause_and_skipping():
    clock = TestClock(initial_time=100.0)
    engine = TimerEngine(
        test_type="WAT",
        total_items=3,
        write_duration=15.0,
        is_exam_mode=True,
        countdown_seconds=0,
        clock=clock,
    )
    engine.start()

    # Pause must be rejected
    assert engine.pause() is False
    assert engine.phase == TestPhase.WAT_SLIDE

    # Force next must be rejected in exam mode
    assert engine.force_next() is False
    assert engine.item_index == 0

    # Force prev must be rejected in exam mode
    assert engine.force_prev() is False


def test_practice_mode_permits_pause_and_navigation():
    clock = TestClock(initial_time=100.0)
    engine = TimerEngine(
        test_type="SRT",
        total_items=3,
        write_duration=30.0,
        is_exam_mode=False,
        countdown_seconds=0,
        clock=clock,
    )
    engine.start()

    clock.advance(10.0)
    state = engine.poll_tick()
    assert state.remaining_seconds == 20.0

    # Pause
    assert engine.pause() is True
    assert engine.phase == TestPhase.PAUSED

    # Time passes while paused
    clock.advance(100.0)
    state = engine.poll_tick()
    assert state.remaining_seconds == 20.0  # Time frozen during pause

    # Resume
    assert engine.resume() is True
    assert engine.phase == TestPhase.SRT_SLIDE

    clock.advance(5.0)
    state = engine.poll_tick()
    assert state.remaining_seconds == 15.0

    # Manual navigation in practice mode
    assert engine.force_next() is True
    assert engine.item_index == 1

    assert engine.force_prev() is True
    assert engine.item_index == 0


def test_tat_zero_second_viewing():
    """Verify zero-second viewing config directly starts writing phase."""
    clock = TestClock(initial_time=100.0)
    engine = TimerEngine(
        test_type="TAT",
        total_items=1,
        view_duration=0.0,
        write_duration=200.0,
        is_exam_mode=True,
        countdown_seconds=0,
        clock=clock,
    )
    engine.start()
    assert engine.phase == TestPhase.TAT_WRITING
    state = engine.poll_tick()
    assert state.remaining_seconds == 200.0


def test_wat_sequential_slide_advancing_fires_notifications():
    """Verify that WAT item transitions (same phase WAT_SLIDE) trigger notifications so UI updates."""
    clock = TestClock(initial_time=100.0)
    engine = TimerEngine(
        test_type="WAT",
        total_items=3,
        write_duration=15.0,
        is_exam_mode=True,
        countdown_seconds=0,
        clock=clock,
    )

    phases_recorded = []
    items_recorded = []
    engine.on_phase_change = lambda o, n, idx: phases_recorded.append((o, n, idx))
    engine.on_item_change = lambda idx: items_recorded.append(idx)

    engine.start()
    assert engine.item_index == 0
    assert len(phases_recorded) == 1
    assert phases_recorded[-1] == (TestPhase.IDLE, TestPhase.WAT_SLIDE, 0)
    assert items_recorded == [0]

    # Advance clock by 15s -> should advance to item 1 and notify
    clock.advance(15.0)
    engine.poll_tick()

    assert engine.item_index == 1
    assert len(phases_recorded) == 2
    assert phases_recorded[-1] == (TestPhase.WAT_SLIDE, TestPhase.WAT_SLIDE, 1)
    assert items_recorded == [0, 1]

    # Advance clock another 15s -> should advance to item 2 and notify
    clock.advance(15.0)
    engine.poll_tick()

    assert engine.item_index == 2
    assert len(phases_recorded) == 3
    assert phases_recorded[-1] == (TestPhase.WAT_SLIDE, TestPhase.WAT_SLIDE, 2)
    assert items_recorded == [0, 1, 2]

    # Advance clock another 15s -> session completed
    clock.advance(15.0)
    engine.poll_tick()
    assert engine.phase == TestPhase.COMPLETED


def test_srt_practice_navigation_fires_notifications():
    """Verify that SRT Practice mode next/prev correctly notifies item transitions."""
    clock = TestClock(initial_time=100.0)
    engine = TimerEngine(
        test_type="SRT",
        total_items=3,
        write_duration=30.0,
        is_exam_mode=False,
        countdown_seconds=0,
        clock=clock,
    )

    items_recorded = []
    engine.on_item_change = lambda idx: items_recorded.append(idx)

    engine.start()
    assert engine.item_index == 0
    assert items_recorded == [0]

    # Practice mode Next
    assert engine.force_next() is True
    assert engine.item_index == 1
    assert items_recorded == [0, 1]

    # Practice mode Next again
    assert engine.force_next() is True
    assert engine.item_index == 2
    assert items_recorded == [0, 1, 2]

    # Practice mode Prev
    assert engine.force_prev() is True
    assert engine.item_index == 1
    assert items_recorded == [0, 1, 2, 1]

