"""Shared, high-precision monotonic timing engine for SSB tests (TAT, WAT, SRT)."""

from enum import Enum
from typing import Callable, List, Optional

from core.clock import Clock, SystemClock


class TestPhase(str, Enum):
    __test__ = False
    IDLE = "IDLE"
    PRE_COUNTDOWN = "PRE_COUNTDOWN"
    TAT_VIEWING = "TAT_VIEWING"
    TAT_WRITING = "TAT_WRITING"
    WAT_SLIDE = "WAT_SLIDE"
    SRT_SLIDE = "SRT_SLIDE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class TimerState:
    """Snapshot of current timer engine state."""

    def __init__(
        self,
        phase: TestPhase,
        item_index: int,
        total_items: int,
        remaining_seconds: float,
        phase_duration: float,
        elapsed_in_phase: float,
        total_session_elapsed: float,
        is_paused: bool,
        is_exam_mode: bool,
    ) -> None:
        self.phase = phase
        self.item_index = item_index
        self.total_items = total_items
        self.remaining_seconds = max(0.0, remaining_seconds)
        self.phase_duration = phase_duration
        self.elapsed_in_phase = elapsed_in_phase
        self.total_session_elapsed = total_session_elapsed
        self.is_paused = is_paused
        self.is_exam_mode = is_exam_mode

    @property
    def progress_fraction(self) -> float:
        """Fraction of current phase completed (0.0 to 1.0)."""
        if self.phase_duration <= 0:
            return 1.0
        return min(1.0, max(0.0, self.elapsed_in_phase / self.phase_duration))

    @property
    def overall_item_number(self) -> int:
        """1-based item number for display."""
        return self.item_index + 1


class TimerEngine:
    """
    Precision monotonic timer engine.
    Derives all remaining times from an absolute monotonic deadline.
    Prevents drift, double transitions, negative durations, and unauthorized skipping.
    """

    def __init__(
        self,
        test_type: str,  # "TAT", "WAT", "SRT"
        total_items: int,
        view_duration: float = 0.0,  # TAT view time in seconds (0 allowed if configured)
        write_duration: float = 15.0,  # Write/response time in seconds
        is_exam_mode: bool = True,
        countdown_seconds: int = 3,
        clock: Optional[Clock] = None,
    ) -> None:
        if total_items <= 0:
            raise ValueError("total_items must be at least 1")

        self.test_type = test_type.upper()
        self.total_items = total_items
        self.view_duration = float(view_duration)
        self.write_duration = float(write_duration)
        self.is_exam_mode = is_exam_mode
        self.countdown_seconds = int(countdown_seconds)
        self.clock: Clock = clock if clock is not None else SystemClock()

        # State tracking
        self.phase: TestPhase = TestPhase.IDLE
        self.item_index: int = 0
        self._deadline: float = 0.0
        self._phase_duration: float = 0.0
        self._phase_start_time: float = 0.0
        self._session_start_time: float = 0.0
        self._total_session_elapsed: float = 0.0
        self._paused_remaining: float = 0.0
        self._pre_pause_phase: TestPhase = TestPhase.IDLE

        # Transition concurrency guard to guarantee single transition
        self._transitioning: bool = False

        # Callbacks
        self.on_tick: Optional[Callable[[TimerState], None]] = None
        self.on_phase_change: Optional[
            Callable[[TestPhase, TestPhase, int], None]
        ] = None  # (old_phase, new_phase, item_index)
        self.on_item_change: Optional[Callable[[int], None]] = None  # (new_item_index)
        self.on_session_complete: Optional[Callable[[], None]] = None
        self.on_sound_cue: Optional[Callable[[str], None]] = None  # "countdown", "transition", "bell"

    def start(self) -> None:
        """Initiate the timer engine from beginning."""
        now = self.clock.now()
        self._session_start_time = now
        self._total_session_elapsed = 0.0
        self.item_index = 0

        if self.countdown_seconds > 0:
            self._set_phase(TestPhase.PRE_COUNTDOWN, float(self.countdown_seconds), force_notify=True)
            if self.on_sound_cue:
                self.on_sound_cue("countdown")
        else:
            self._start_first_item_phase()

    def _start_first_item_phase(self) -> None:
        if self.test_type == "TAT":
            if self.view_duration > 0:
                self._set_phase(TestPhase.TAT_VIEWING, self.view_duration, force_notify=True)
                if self.on_sound_cue:
                    self.on_sound_cue("transition")
            else:
                self._set_phase(TestPhase.TAT_WRITING, self.write_duration, force_notify=True)
                if self.on_sound_cue:
                    self.on_sound_cue("transition")
        elif self.test_type == "WAT":
            self._set_phase(TestPhase.WAT_SLIDE, self.write_duration, force_notify=True)
            if self.on_sound_cue:
                self.on_sound_cue("transition")
        elif self.test_type == "SRT":
            self._set_phase(TestPhase.SRT_SLIDE, self.write_duration, force_notify=True)
            if self.on_sound_cue:
                self.on_sound_cue("transition")
        else:
            raise ValueError(f"Unknown test type: {self.test_type}")

        if self.on_item_change:
            self.on_item_change(self.item_index)

    def _set_phase(self, new_phase: TestPhase, duration: float, force_notify: bool = False) -> None:
        old_phase = self.phase
        now = self.clock.now()
        self.phase = new_phase
        self._phase_duration = float(duration)
        self._phase_start_time = now
        self._deadline = now + self._phase_duration

        if self.on_phase_change and (old_phase != new_phase or force_notify):
            self.on_phase_change(old_phase, new_phase, self.item_index)

    def pause(self) -> bool:
        """Pause the timer. Forbidden in Exam Mode to preserve strict exam integrity."""
        if self.is_exam_mode:
            return False  # Exam mode strictly disallows pausing
        if self.phase in (TestPhase.IDLE, TestPhase.PAUSED, TestPhase.COMPLETED):
            return False

        now = self.clock.now()
        self._paused_remaining = max(0.0, self._deadline - now)
        self._pre_pause_phase = self.phase
        self.phase = TestPhase.PAUSED
        if self.on_phase_change:
            self.on_phase_change(self._pre_pause_phase, TestPhase.PAUSED, self.item_index)
        return True

    def resume(self) -> bool:
        """Resume timer from paused state in Practice Mode."""
        if self.phase != TestPhase.PAUSED:
            return False

        now = self.clock.now()
        self.phase = self._pre_pause_phase
        self._deadline = now + self._paused_remaining
        self._phase_start_time = now - (self._phase_duration - self._paused_remaining)

        if self.on_phase_change:
            self.on_phase_change(TestPhase.PAUSED, self.phase, self.item_index)
        return True

    def poll_tick(self) -> TimerState:
        """
        Poll monotonic clock, calculate exact drift-free remaining time,
        and trigger phase expiry transition if deadline has passed.
        """
        if self.phase in (TestPhase.IDLE, TestPhase.COMPLETED):
            return self.get_state()

        if self.phase == TestPhase.PAUSED:
            return self.get_state()

        now = self.clock.now()
        remaining = self._deadline - now

        if remaining <= 0.0:
            self._handle_deadline_expired()
            # Re-fetch state after transition
            return self.get_state()

        state = self.get_state()
        if self.on_tick:
            self.on_tick(state)
        return state

    def _handle_deadline_expired(self) -> None:
        """Guaranteed single-transition handler."""
        if self._transitioning:
            return
        self._transitioning = True

        try:
            current_phase = self.phase

            if current_phase == TestPhase.PRE_COUNTDOWN:
                self._start_first_item_phase()

            elif current_phase == TestPhase.TAT_VIEWING:
                # Transition viewing -> writing phase for the same TAT image
                if self.on_sound_cue:
                    self.on_sound_cue("transition")
                self._set_phase(TestPhase.TAT_WRITING, self.write_duration)

            elif current_phase == TestPhase.TAT_WRITING:
                # Writing phase ended: advance to next image
                self._advance_item()

            elif current_phase in (TestPhase.WAT_SLIDE, TestPhase.SRT_SLIDE):
                # Word or situation ended: advance to next item
                self._advance_item()

        finally:
            self._transitioning = False

    def _advance_item(self) -> None:
        """Advance to next item or finish test."""
        if self.item_index + 1 >= self.total_items:
            self._complete_session()
            return

        self.item_index += 1
        if self.test_type == "TAT":
            if self.view_duration > 0:
                self._set_phase(TestPhase.TAT_VIEWING, self.view_duration, force_notify=True)
            else:
                self._set_phase(TestPhase.TAT_WRITING, self.write_duration, force_notify=True)
        elif self.test_type == "WAT":
            self._set_phase(TestPhase.WAT_SLIDE, self.write_duration, force_notify=True)
        elif self.test_type == "SRT":
            self._set_phase(TestPhase.SRT_SLIDE, self.write_duration, force_notify=True)

        if self.on_item_change:
            self.on_item_change(self.item_index)

        if self.on_sound_cue:
            self.on_sound_cue("transition")

    def _complete_session(self) -> None:
        """Mark session completed."""
        old_phase = self.phase
        self.phase = TestPhase.COMPLETED
        self._deadline = self.clock.now()
        if self.on_sound_cue:
            self.on_sound_cue("bell")
        if self.on_phase_change:
            self.on_phase_change(old_phase, TestPhase.COMPLETED, self.item_index)
        if self.on_session_complete:
            self.on_session_complete()

    def force_next(self) -> bool:
        """
        Manually trigger next item. Only permitted in Practice Mode.
        In Exam Mode, manual advancement is rejected to preserve strict exam integrity.
        """
        if self.is_exam_mode:
            return False
        if self.phase in (TestPhase.IDLE, TestPhase.COMPLETED, TestPhase.PRE_COUNTDOWN):
            return False

        if self.phase == TestPhase.TAT_VIEWING:
            self._set_phase(TestPhase.TAT_WRITING, self.write_duration, force_notify=True)
            return True
        else:
            self._advance_item()
            return True

    def force_prev(self) -> bool:
        """
        Navigate to previous item. Only allowed in Practice Mode.
        Strictly disallowed in Exam Mode.
        """
        if self.is_exam_mode:
            return False
        if self.phase in (TestPhase.IDLE, TestPhase.COMPLETED, TestPhase.PRE_COUNTDOWN):
            return False
        if self.item_index <= 0:
            return False

        self.item_index -= 1
        if self.test_type == "TAT":
            if self.view_duration > 0:
                self._set_phase(TestPhase.TAT_VIEWING, self.view_duration, force_notify=True)
            else:
                self._set_phase(TestPhase.TAT_WRITING, self.write_duration, force_notify=True)
        elif self.test_type == "WAT":
            self._set_phase(TestPhase.WAT_SLIDE, self.write_duration, force_notify=True)
        elif self.test_type == "SRT":
            self._set_phase(TestPhase.SRT_SLIDE, self.write_duration, force_notify=True)

        if self.on_item_change:
            self.on_item_change(self.item_index)

        return True

    def force_expire_current_phase(self) -> None:
        """Expire the current phase immediately (used by test suites and manual triggers)."""
        if self.phase not in (TestPhase.IDLE, TestPhase.COMPLETED):
            self._deadline = self.clock.now() - 0.001
            self._handle_deadline_expired()

    def abandon(self) -> None:
        """Abandon the session gracefully."""
        self.phase = TestPhase.IDLE
        self._deadline = 0.0

    def get_state(self) -> TimerState:
        now = self.clock.now()
        if self.phase == TestPhase.PAUSED:
            remaining = self._paused_remaining
            elapsed_in_phase = self._phase_duration - remaining
        elif self.phase in (TestPhase.IDLE, TestPhase.COMPLETED):
            remaining = 0.0
            elapsed_in_phase = self._phase_duration
        else:
            remaining = max(0.0, self._deadline - now)
            elapsed_in_phase = max(0.0, self._phase_duration - remaining)

        total_elapsed = (now - self._session_start_time) if self._session_start_time > 0 else 0.0

        return TimerState(
            phase=self.phase,
            item_index=self.item_index,
            total_items=self.total_items,
            remaining_seconds=remaining,
            phase_duration=self._phase_duration,
            elapsed_in_phase=elapsed_in_phase,
            total_session_elapsed=max(0.0, total_elapsed),
            is_paused=(self.phase == TestPhase.PAUSED),
            is_exam_mode=self.is_exam_mode,
        )
