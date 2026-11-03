"""SRT (Situation Reaction Test) execution screen with original serial preservation and 30s slides."""

import logging
from typing import List, Optional
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.app_context import AppContext
from core.timer_engine import TestPhase, TimerEngine, TimerState
from database.models import Session
from services.session_service import ActiveSessionItem
from ui.components.timer_widget import TimerWidget

logger = logging.getLogger(__name__)


class SRTScreen(QWidget):
    """Situation Reaction Test screen displaying situations with preserved serials and 30-second pacing."""

    session_finished = Signal(int)
    session_abandoned = Signal()

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.engine: Optional[TimerEngine] = None
        self.items: List[ActiveSessionItem] = []
        self.current_session: Optional[Session] = None
        self._current_item_index: int = 0
        self.theme_name: str = ctx.get_setting("theme", "dark")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 16, 20, 16)
        self.main_layout.setSpacing(14)

        # Top Bar
        top_bar = QHBoxLayout()
        self.mode_badge = QLabel("EXAM MODE")
        self.mode_badge.setStyleSheet(
            "background-color: #7F1D1D; color: #FEE2E2; padding: 4px 10px; border-radius: 10px; font-weight: 700; font-size: 11px;"
        )
        top_bar.addWidget(self.mode_badge)

        self.title_lbl = QLabel("Situation Reaction Test (SRT)")
        self.title_lbl.setProperty("class", "H3")
        top_bar.addWidget(self.title_lbl, stretch=1)

        self.btn_fullscreen = QPushButton("⛶ Fullscreen")
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        top_bar.addWidget(self.btn_fullscreen)

        self.btn_abandon = QPushButton("✕ Exit Test")
        self.btn_abandon.setProperty("class", "DangerBtn")
        self.btn_abandon.clicked.connect(self._confirm_abandon)
        top_bar.addWidget(self.btn_abandon)

        self.main_layout.addLayout(top_bar)

        # Timer Component
        self.timer_widget = TimerWidget()
        self.timer_widget.set_theme(self.theme_name)
        self.timer_widget.pause_clicked.connect(self._on_pause)
        self.timer_widget.resume_clicked.connect(self._on_resume)
        self.timer_widget.next_clicked.connect(self._on_force_next)
        self.timer_widget.prev_clicked.connect(self._on_force_prev)
        self.main_layout.addWidget(self.timer_widget)

        # Situation Prompt Card with Glow
        self.situation_card = QFrame()
        self.situation_card.setProperty("class", "HeroCard")
        situation_layout = QVBoxLayout(self.situation_card)
        situation_layout.setContentsMargins(24, 20, 24, 20)
        situation_layout.setSpacing(12)

        self.serial_badge = QLabel("SITUATION #1")
        situation_layout.addWidget(self.serial_badge, alignment=Qt.AlignmentFlag.AlignLeft)

        self.situation_text_lbl = QLabel("Situation prompt text goes here...")
        self.situation_text_lbl.setWordWrap(True)
        situation_layout.addWidget(self.situation_text_lbl)

        self.main_layout.addWidget(self.situation_card)

        # Response Reaction Editor
        reaction_card = QFrame()
        reaction_card.setProperty("class", "CardFrame")
        reaction_layout = QVBoxLayout(reaction_card)
        reaction_layout.setContentsMargins(18, 14, 18, 14)
        reaction_layout.setSpacing(8)

        reaction_header = QLabel("Your immediate reaction / resolution:")
        reaction_header.setProperty("class", "Subtitle")
        reaction_layout.addWidget(reaction_header)

        self.reaction_editor = QPlainTextEdit()
        self.reaction_editor.setPlaceholderText("State your decisive action and outcome... (Auto-advances in 30 seconds)")
        self.reaction_editor.setFont(QFont("Segoe UI", 12))
        reaction_layout.addWidget(self.reaction_editor, stretch=1)

        char_stats_h = QHBoxLayout()
        self.char_count_lbl = QLabel("Characters: 0")
        self.char_count_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        char_stats_h.addWidget(self.char_count_lbl)
        char_stats_h.addStretch()

        autosave_lbl = QLabel("Autosave: Active against original serial")
        autosave_lbl.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 600;")
        char_stats_h.addWidget(autosave_lbl)
        reaction_layout.addLayout(char_stats_h)

        self.main_layout.addWidget(reaction_card, stretch=1)

        # Engine tick poll timer
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(50)
        self.poll_timer.timeout.connect(self._poll_tick)

        self.reaction_editor.textChanged.connect(self._on_text_changed)
        self.apply_theme(self.theme_name)

    def apply_theme(self, theme_name: str) -> None:
        """Apply theme-adaptive colors to typography, badges, and sub-widgets."""
        self.theme_name = theme_name if theme_name in ("dark", "light") else "dark"
        self.timer_widget.set_theme(self.theme_name)
        if self.theme_name == "light":
            self.situation_text_lbl.setStyleSheet(
                "font-size: 19px; font-weight: 600; color: #0F172A; line-height: 1.6;"
            )
            self.serial_badge.setStyleSheet(
                "background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; padding: 5px 14px; border-radius: 12px; font-weight: 800; font-size: 12px; letter-spacing: 0.5px;"
            )
        else:
            self.situation_text_lbl.setStyleSheet(
                "font-size: 19px; font-weight: 600; color: #F8FAFC; line-height: 1.6;"
            )
            self.serial_badge.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E3A8A, stop:1 #2563EB); "
                "color: #93C5FD; border: 1px solid #3B82F6; padding: 5px 14px; border-radius: 12px; font-weight: 800; font-size: 12px; letter-spacing: 0.5px;"
            )

        if self.items and 0 <= self._current_item_index < len(self.items):
            self._render_situation_text(self.items[self._current_item_index].prompt_text)

    def _render_situation_text(self, prompt: str) -> None:
        """Render situation text with high-contrast, theme-aware (...) highlight."""
        if "(...)" in prompt:
            if self.theme_name == "light":
                badge_style = "color: #1D4ED8; font-weight: 800; background: #DBEAFE; padding: 2px 8px; border-radius: 6px; border: 1px solid #93C5FD;"
            else:
                badge_style = "color: #38BDF8; font-weight: 800; background: rgba(56, 189, 248, 0.16); padding: 2px 8px; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.35);"
            formatted_prompt = prompt.replace(
                "(...)",
                f"<span style='{badge_style}'> (...) </span>",
            )
            self.situation_text_lbl.setTextFormat(Qt.TextFormat.RichText)
            self.situation_text_lbl.setText(formatted_prompt)
        else:
            self.situation_text_lbl.setTextFormat(Qt.TextFormat.PlainText)
            self.situation_text_lbl.setText(prompt)

    def start_session(
        self,
        session: Session,
        items: List[ActiveSessionItem],
    ) -> None:
        self.current_session = session
        self.items = items
        self._current_item_index = 0
        self.theme_name = self.ctx.get_setting("theme", "dark")
        self.apply_theme(self.theme_name)

        if session.is_exam_mode:
            self.mode_badge.setText("EXAM MODE")
            self.mode_badge.setStyleSheet(
                "background-color: #7F1D1D; color: #FEE2E2; padding: 4px 10px; border-radius: 10px; font-weight: 700; font-size: 11px;"
            )
        else:
            self.mode_badge.setText("PRACTICE MODE")
            self.mode_badge.setStyleSheet(
                "background-color: #065F46; color: #D1FAE5; padding: 4px 10px; border-radius: 10px; font-weight: 700; font-size: 11px;"
            )

        countdown = self.ctx.get_setting("start_countdown", 3)
        self.engine = TimerEngine(
            test_type="SRT",
            total_items=len(items),
            view_duration=0.0,
            write_duration=session.write_duration,
            is_exam_mode=session.is_exam_mode,
            countdown_seconds=countdown,
        )

        self.engine.on_phase_change = self._on_phase_changed
        self.engine.on_item_change = self._on_item_changed
        self.engine.on_session_complete = self._on_session_completed
        self.engine.on_sound_cue = self._play_sound_cue

        if countdown > 0:
            self.serial_badge.setText("GET READY")
            self.situation_text_lbl.setText(
                f"Situation Reaction Test starting in {countdown} seconds...\nRead each situation attentively and record your instantaneous reaction."
            )
            self.reaction_editor.setEnabled(False)
            self.reaction_editor.setPlaceholderText(f"Test starts in {countdown} seconds...")
        else:
            self.reaction_editor.setEnabled(True)
            self._load_item(0)

        self.engine.start()
        self.poll_timer.start()
        if countdown == 0:
            self.reaction_editor.setFocus()

    def _load_item(self, index: int) -> None:
        if index < 0 or index >= len(self.items):
            return

        self._current_item_index = index
        item = self.items[index]

        self.serial_badge.setText(f"SITUATION #{item.identifier} OF {len(self.items)}")
        self._render_situation_text(item.prompt_text)

        # Smooth card fade-in animation
        eff = QGraphicsOpacityEffect(self.situation_card)
        self.situation_card.setGraphicsEffect(eff)
        self._card_anim = QPropertyAnimation(eff, b"opacity")
        self._card_anim.setDuration(180)
        self._card_anim.setStartValue(0.15)
        self._card_anim.setEndValue(1.0)
        self._card_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._card_anim.finished.connect(lambda: self.situation_card.setGraphicsEffect(None))
        self._card_anim.start()

        # Load existing response if navigating in practice mode
        self.reaction_editor.blockSignals(True)
        if self.current_session and self.current_session.id:
            existing = self.ctx.session_repo.get_response_for_item(self.current_session.id, index)
            if existing and existing.response_text:
                self.reaction_editor.setPlainText(existing.response_text)
            else:
                self.reaction_editor.clear()
        else:
            self.reaction_editor.clear()
        self.reaction_editor.blockSignals(False)
        self._on_text_changed()
        self.reaction_editor.setFocus()

    def _poll_tick(self) -> None:
        if not self.engine:
            return
        state = self.engine.poll_tick()
        self.timer_widget.update_state(state)

    def _on_phase_changed(
        self, old_phase: TestPhase, new_phase: TestPhase, item_idx: int
    ) -> None:
        if old_phase == TestPhase.SRT_SLIDE:
            self._flush_current_response()
        if new_phase == TestPhase.SRT_SLIDE:
            self.reaction_editor.setEnabled(True)
            self.reaction_editor.setPlaceholderText("State your decisive action and outcome... (Auto-advances in 30 seconds)")
            self._load_item(item_idx)

    def _on_item_changed(self, new_idx: int) -> None:
        if self.engine and self.engine.phase == TestPhase.SRT_SLIDE:
            if new_idx != self._current_item_index:
                self._flush_current_response()
                self._load_item(new_idx)

    def _on_text_changed(self) -> None:
        raw_text = self.reaction_editor.toPlainText().strip()
        words = len(raw_text.split()) if raw_text else 0
        chars = len(raw_text)
        self.char_count_lbl.setText(f"Words: {words}  |  Characters: {chars}")

    def keyPressEvent(self, event) -> None:
        # Ctrl+Enter to advance
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            self._on_force_next()
            event.accept()
            return
        super().keyPressEvent(event)

    def _flush_current_response(self) -> None:
        if not self.current_session:
            return
        text = self.reaction_editor.toPlainText().strip()
        time_spent = self.engine.get_state().elapsed_in_phase if self.engine else 0.0
        self.ctx.session_service.buffer_response(
            item_index=self._current_item_index,
            response_text=text,
            time_spent=time_spent,
        )
        self.ctx.session_service.flush_item_response(self._current_item_index)

    def _on_session_completed(self) -> None:
        self.poll_timer.stop()
        self._flush_current_response()

        elapsed = self.engine.get_state().total_session_elapsed if self.engine else 0.0
        self.ctx.session_service.complete_session(elapsed_seconds=elapsed)

        QMessageBox.information(
            self,
            "SRT Drill Completed",
            f"You have completed all {len(self.items)} situations in this session! All responses have been saved.",
        )
        if self.current_session and self.current_session.id:
            self.session_finished.emit(self.current_session.id)

    def _on_pause(self) -> None:
        if self.engine:
            self.engine.pause()

    def _on_resume(self) -> None:
        if self.engine:
            self.engine.resume()

    def _on_force_next(self) -> None:
        if self.engine:
            self._flush_current_response()
            self.engine.force_next()

    def _on_force_prev(self) -> None:
        if self.engine:
            self._flush_current_response()
            self.engine.force_prev()

    def _play_sound_cue(self, cue_name: str) -> None:
        self.ctx.sound_service.play_cue(cue_name)

    def _toggle_fullscreen(self) -> None:
        win = self.window()
        if win.isFullScreen():
            win.showNormal()
            self.btn_fullscreen.setText("⛶ Fullscreen")
        else:
            win.showFullScreen()
            self.btn_fullscreen.setText("⛶ Exit Fullscreen")

    def _confirm_abandon(self) -> None:
        reply = QMessageBox.question(
            self,
            "Abandon SRT Session",
            "Are you sure you want to exit? Responses recorded up to this point will be saved.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.poll_timer.stop()
            self._flush_current_response()
            elapsed = self.engine.get_state().total_session_elapsed if self.engine else 0.0
            self.ctx.session_service.abandon_session(elapsed_seconds=elapsed)
            if self.window().isFullScreen():
                self.window().showNormal()
            self.session_abandoned.emit()
