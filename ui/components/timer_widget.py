"""High-contrast, distance-readable timer widget with phase indicator and progress bar."""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from core.timer_engine import TestPhase, TimerState


class TimerWidget(QFrame):
    """Prominent countdown cockpit with phase badge, smooth multi-gradient progress, and practice controls."""

    pause_clicked = Signal()
    resume_clicked = Signal()
    next_clicked = Signal()
    prev_clicked = Signal()

    def __init__(self, parent: Optional[QFrame] = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "CardFrame")
        self.setMinimumHeight(150)
        self.theme_name: str = "dark"
        self._is_critical: Optional[bool] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 18, 24, 18)
        main_layout.setSpacing(12)

        # Top row: Phase Badge, Item Counter Pill, and Practice Controls
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self.phase_badge = QLabel("READY")
        self.phase_badge.setProperty("class", "PhaseBadge")
        top_row.addWidget(self.phase_badge)

        self.item_pill = QLabel("Item 1 / 1")
        top_row.addWidget(self.item_pill)

        top_row.addStretch()

        # Practice mode controls (hidden in Exam Mode)
        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.setToolTip("Go to previous item (Practice Mode only)")
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self.prev_clicked.emit)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setToolTip("Pause test timer (Practice Mode only)")
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.clicked.connect(self._toggle_pause)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setToolTip("Skip to next item (Practice Mode only)")
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_clicked.emit)

        top_row.addWidget(self.prev_btn)
        top_row.addWidget(self.pause_btn)
        top_row.addWidget(self.next_btn)

        main_layout.addLayout(top_row)

        # Center row: Big Timer Digits & Caption
        center_row = QVBoxLayout()
        center_row.setSpacing(0)
        center_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.digits_label = QLabel("00:00")
        self.digits_label.setProperty("class", "TimerDigits")
        self.digits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_row.addWidget(self.digits_label)

        main_layout.addLayout(center_row)

        # Bottom row: Smooth Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(1000)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        main_layout.addWidget(self.progress_bar)

        self._is_paused = False
        self._apply_theme_styling(is_critical=False)

    def set_theme(self, theme_name: str) -> None:
        """Dynamically switch widget palette between Light and Dark styles."""
        self.theme_name = theme_name if theme_name in ("dark", "light") else "dark"
        self._is_critical = None  # Force re-styling
        self._apply_theme_styling(is_critical=False)

    def _apply_theme_styling(self, is_critical: bool) -> None:
        if self._is_critical == is_critical:
            return
        self._is_critical = is_critical

        is_light = (self.theme_name == "light")

        if is_critical:
            if is_light:
                self.setStyleSheet(
                    """
                    QFrame.CardFrame {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFF1F2, stop:1 #FFE4E6);
                        border: 1.5px solid #EF4444;
                        border-radius: 14px;
                    }
                    """
                )
                self.digits_label.setStyleSheet(
                    "font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 60px; font-weight: 900; color: #DC2626; letter-spacing: 2px;"
                )
                self.progress_bar.setStyleSheet(
                    "QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:1 #EF4444); border-radius: 4px; }"
                )
            else:
                self.setStyleSheet(
                    """
                    QFrame.CardFrame {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1F1012, stop:1 #281215);
                        border: 1.5px solid #EF4444;
                        border-radius: 14px;
                    }
                    """
                )
                self.digits_label.setStyleSheet(
                    "font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 60px; font-weight: 900; color: #EF4444; letter-spacing: 2px;"
                )
                self.progress_bar.setStyleSheet(
                    "QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF4444, stop:1 #F87171); border-radius: 4px; }"
                )
        else:
            if is_light:
                self.setStyleSheet(
                    """
                    QFrame.CardFrame {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8FAFC);
                        border: 1.5px solid #CBD5E1;
                        border-radius: 14px;
                    }
                    """
                )
                self.digits_label.setStyleSheet(
                    "font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 60px; font-weight: 900; color: #1D4ED8; letter-spacing: 2px;"
                )
                self.progress_bar.setStyleSheet(
                    "QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #0284C7); border-radius: 4px; }"
                )
                self.item_pill.setStyleSheet(
                    "background-color: #EFF6FF; color: #1E40AF; padding: 5px 12px; border-radius: 12px; font-weight: 700; font-size: 11.5px; border: 1px solid #BFDBFE;"
                )
            else:
                self.setStyleSheet(
                    """
                    QFrame.CardFrame {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0F172A, stop:1 #111E36);
                        border: 1px solid #1E293B;
                        border-radius: 14px;
                    }
                    """
                )
                self.digits_label.setStyleSheet(
                    "font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 60px; font-weight: 900; color: #38BDF8; letter-spacing: 2px;"
                )
                self.progress_bar.setStyleSheet(
                    "QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #38BDF8); border-radius: 4px; }"
                )
                self.item_pill.setStyleSheet(
                    "background-color: rgba(30, 41, 59, 0.8); color: #E2E8F0; padding: 5px 12px; border-radius: 12px; font-weight: 700; font-size: 11.5px; border: 1px solid rgba(255, 255, 255, 0.08);"
                )

    def _toggle_pause(self) -> None:
        if self._is_paused:
            self.resume_clicked.emit()
        else:
            self.pause_clicked.emit()

    def update_state(self, state: TimerState) -> None:
        """Update timer digits, progress bar, and phase indicators from TimerState."""
        total_sec = int(round(state.remaining_seconds))
        mins = total_sec // 60
        secs = total_sec % 60
        self.digits_label.setText(f"{mins:02d}:{secs:02d}")

        # High-contrast critical warning when <= 5 seconds remaining
        critical = (
            state.remaining_seconds <= 5.0
            and state.phase not in (TestPhase.PAUSED, TestPhase.IDLE, TestPhase.COMPLETED, TestPhase.PRE_COUNTDOWN)
        )
        self._apply_theme_styling(is_critical=critical)

        # Progress bar (remaining fraction)
        fraction = state.progress_fraction
        remaining_units = int((1.0 - fraction) * 1000)
        self.progress_bar.setValue(max(0, min(1000, remaining_units)))

        # Item index pill
        self.item_pill.setText(f"Item {state.overall_item_number} of {state.total_items}")

        # Phase Badge label
        phase_texts = {
            TestPhase.IDLE: "READY",
            TestPhase.PRE_COUNTDOWN: "STARTING COUNTDOWN",
            TestPhase.TAT_VIEWING: "PICTURE VIEWING (30s)",
            TestPhase.TAT_WRITING: "STORY WRITING PHASE",
            TestPhase.WAT_SLIDE: "WORD ASSOCIATION",
            TestPhase.SRT_SLIDE: "SITUATION REACTION",
            TestPhase.PAUSED: "PAUSED",
            TestPhase.COMPLETED: "SESSION COMPLETED",
        }
        self.phase_badge.setText(phase_texts.get(state.phase, str(state.phase)))

        # Practice vs Exam controls visibility
        if state.is_exam_mode:
            self.prev_btn.setVisible(False)
            self.pause_btn.setVisible(False)
            self.next_btn.setVisible(False)
        else:
            self.prev_btn.setVisible(True)
            self.pause_btn.setVisible(True)
            self.next_btn.setVisible(True)
            self.prev_btn.setEnabled(state.item_index > 0)
            self.next_btn.setEnabled(state.item_index + 1 < state.total_items)

            self._is_paused = state.is_paused
            self.pause_btn.setText("▶ Resume" if state.is_paused else "⏸ Pause")
