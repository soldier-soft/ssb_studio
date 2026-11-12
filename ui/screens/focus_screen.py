"""Officer Focus Screen with full-screen mode, 5-minute pre-completion warning alarm, and scratchpad."""

import logging
from typing import Optional
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.app_context import AppContext

logger = logging.getLogger(__name__)


class FocusScreen(QWidget):
    """Full-screen focus countdown timer with 5-minute audio warning bell and scratchpad."""

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.total_seconds = 25 * 60
        self.time_remaining = 25 * 60
        self.is_running = False
        self.five_min_alarm_played = False
        self.theme_name = ctx.get_setting("theme", "dark")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(28, 20, 28, 20)
        self.main_layout.setSpacing(16)

        self._build_top_bar()
        self._build_warning_banner()
        self._build_clock_card()
        self._build_controls_and_presets()
        self._build_scratchpad()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        # 1-second countdown timer
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_tick)

        self.apply_theme(self.theme_name)

    def _build_top_bar(self) -> None:
        bar = QHBoxLayout()
        badge = QLabel("OFFICER FOCUS DRILL")
        badge.setStyleSheet(
            "background: rgba(245, 158, 11, 0.18); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.35); padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 11px;"
        )
        bar.addWidget(badge)

        sub = QLabel("5-Min Warning Bell &bull; Full-Screen Immersion")
        sub.setStyleSheet("color: #94A3B8; font-size: 12px;")
        bar.addWidget(sub)
        bar.addStretch()

        self.btn_fs = QPushButton("⛶ Toggle Fullscreen")
        self.btn_fs.clicked.connect(self._toggle_fullscreen)
        bar.addWidget(self.btn_fs)

        self.main_layout.addLayout(bar)

    def _build_warning_banner(self) -> None:
        self.warning_banner = QFrame()
        self.warning_banner.setStyleSheet(
            "background: rgba(245, 158, 11, 0.2); border: 1.5px solid #F59E0B; border-radius: 8px; padding: 10px;"
        )
        layout = QHBoxLayout(self.warning_banner)
        lbl = QLabel("🔔 5 MINUTES REMAINING — WRAP UP FINAL THOUGHTS & REVISIONS")
        lbl.setStyleSheet("color: #FBBF24; font-weight: 800; font-size: 12.5px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        self.warning_banner.setVisible(False)
        self.main_layout.addWidget(self.warning_banner)

    def _build_clock_card(self) -> None:
        self.clock_card = QFrame()
        self.clock_card.setProperty("class", "HeroCard")
        layout = QVBoxLayout(self.clock_card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(24, 28, 24, 28)
        layout.setSpacing(8)

        self.status_caption = QLabel("STANDBY READY")
        self.status_caption.setProperty("class", "StatLabel")
        self.status_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_caption)

        self.digits_lbl = QLabel("25:00")
        self.digits_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.digits_lbl.setStyleSheet("font-size: 72px; font-weight: 900; font-family: 'Consolas', monospace; color: #38BDF8;")
        layout.addWidget(self.digits_lbl)

        self.progress_caption = QLabel("0% elapsed of 25m drill")
        self.progress_caption.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.progress_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_caption)

        self.main_layout.addWidget(self.clock_card)

    def _build_controls_and_presets(self) -> None:
        act_h = QHBoxLayout()
        act_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        act_h.setSpacing(12)

        self.btn_play = QPushButton("▶  Start Focus Drill")
        self.btn_play.setProperty("class", "PrimaryBtn")
        self.btn_play.setMinimumHeight(44)
        self.btn_play.setStyleSheet("font-size: 14px; font-weight: 700; padding: 10px 24px;")
        self.btn_play.clicked.connect(self._toggle_run)
        act_h.addWidget(self.btn_play)

        self.btn_reset = QPushButton("↺  Reset")
        self.btn_reset.setMinimumHeight(44)
        self.btn_reset.clicked.connect(self._reset_timer)
        act_h.addWidget(self.btn_reset)

        self.main_layout.addLayout(act_h)

        # Presets row
        preset_h = QHBoxLayout()
        preset_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preset_h.setSpacing(8)

        for mins, label in [(15, "15m Drill"), (25, "25m Pomodoro"), (45, "45m Mock"), (60, "60m Full"), (90, "90m Deep")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked=False, m=mins: self._set_preset(m))
            preset_h.addWidget(btn)

        self.main_layout.addLayout(preset_h)

        # Custom minutes input
        custom_h = QHBoxLayout()
        custom_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        custom_h.setSpacing(8)

        lbl = QLabel("Custom Minutes:")
        lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        custom_h.addWidget(lbl)

        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("e.g. 30")
        self.custom_input.setFixedWidth(80)
        custom_h.addWidget(self.custom_input)

        set_btn = QPushButton("Set Time")
        set_btn.clicked.connect(self._on_set_custom)
        custom_h.addWidget(set_btn)

        self.main_layout.addLayout(custom_h)

    def _build_scratchpad(self) -> None:
        card = QFrame()
        card.setProperty("class", "CardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(6)

        header_h = QHBoxLayout()
        lbl = QLabel("📝 Candidate Focus Scratchpad")
        lbl.setStyleSheet("font-weight: 700; font-size: 13px; color: #F1F5F9;")
        header_h.addWidget(lbl)
        header_h.addStretch()

        autosave_lbl = QLabel("Autosaved locally")
        autosave_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        header_h.addWidget(autosave_lbl)
        layout.addLayout(header_h)

        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setPlaceholderText("Jot down quick thoughts, story keywords, or tactical notes during your drill...")
        self.notes_edit.setFont(QFont("Segoe UI", 12))
        self.notes_edit.setMinimumHeight(120)

        # Load existing notes
        saved_notes = self.ctx.get_setting("focus_scratchpad_notes", "")
        self.notes_edit.setPlainText(saved_notes)
        self.notes_edit.textChanged.connect(self._save_notes)
        layout.addWidget(self.notes_edit)

        self.main_layout.addWidget(card)

    def _save_notes(self) -> None:
        self.ctx.set_setting("focus_scratchpad_notes", self.notes_edit.toPlainText())

    def _set_preset(self, minutes: int) -> None:
        self.ctx.sound_service.play_cue("click")
        self.total_seconds = minutes * 60
        self.time_remaining = self.total_seconds
        self.is_running = False
        self.timer.stop()
        self.five_min_alarm_played = False
        self.warning_banner.setVisible(False)
        self.btn_play.setText("▶  Start Focus Drill")
        self._update_display()

    def _on_set_custom(self) -> None:
        try:
            val = int(self.custom_input.text().strip())
            if 1 <= val <= 360:
                self._set_preset(val)
                self.custom_input.clear()
        except ValueError:
            pass

    def _toggle_run(self) -> None:
        self.ctx.sound_service.play_cue("click")
        if self.is_running:
            self.is_running = False
            self.timer.stop()
            self.btn_play.setText("▶  Resume Focus Drill")
            self.status_caption.setText("PAUSED")
        else:
            self.is_running = True
            self.timer.start()
            self.btn_play.setText("⏸  Pause Focus Drill")
            self.status_caption.setText("ACTIVE STUDY DRILL")

    def _reset_timer(self) -> None:
        self.ctx.sound_service.play_cue("click")
        self.is_running = False
        self.timer.stop()
        self.time_remaining = self.total_seconds
        self.five_min_alarm_played = False
        self.warning_banner.setVisible(False)
        self.btn_play.setText("▶  Start Focus Drill")
        self.status_caption.setText("STANDBY READY")
        self._update_display()

    def _on_tick(self) -> None:
        if self.time_remaining > 0:
            self.time_remaining -= 1

            # 5-minute warning check (300 seconds)
            if self.time_remaining == 300 and self.total_seconds > 300 and not self.five_min_alarm_played:
                self.five_min_alarm_played = True
                self.warning_banner.setVisible(True)
                self.ctx.sound_service.play_cue("focus_5min_warning")

            if self.time_remaining <= 0:
                self.is_running = False
                self.timer.stop()
                self.status_caption.setText("MISSION COMPLETED")
                self.ctx.sound_service.play_cue("completion")
                QMessageBox.information(
                    self,
                    "Focus Session Complete",
                    "Session complete! Outstanding dedication, officer.",
                )
            self._update_display()

    def _update_display(self) -> None:
        mins = self.time_remaining // 60
        secs = self.time_remaining % 60
        self.digits_lbl.setText(f"{mins:02d}:{secs:02d}")

        if self.total_seconds > 0:
            elapsed = self.total_seconds - self.time_remaining
            pct = int((elapsed / self.total_seconds) * 100)
            self.progress_caption.setText(f"{pct}% elapsed of {self.total_seconds // 60}m drill")

        if self.time_remaining <= 300 and self.time_remaining > 0 and self.total_seconds > 300:
            self.digits_lbl.setStyleSheet("font-size: 72px; font-weight: 900; font-family: 'Consolas', monospace; color: #F59E0B;")
        elif self.time_remaining <= 0:
            self.digits_lbl.setStyleSheet("font-size: 72px; font-weight: 900; font-family: 'Consolas', monospace; color: #10B981;")
        else:
            color = "#1D4ED8" if self.theme_name == "light" else "#38BDF8"
            self.digits_lbl.setStyleSheet(f"font-size: 72px; font-weight: 900; font-family: 'Consolas', monospace; color: {color};")

    def _toggle_fullscreen(self) -> None:
        top_window = self.window()
        if top_window.isFullScreen():
            top_window.showNormal()
            self.btn_fs.setText("⛶ Toggle Fullscreen")
        else:
            top_window.showFullScreen()
            self.btn_fs.setText("✕ Exit Fullscreen")

    def apply_theme(self, theme_name: str) -> None:
        self.theme_name = theme_name if theme_name in ("dark", "light") else "dark"
        self._update_display()

