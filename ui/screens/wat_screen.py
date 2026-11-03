"""WAT (Word Association Test) execution screen displaying 1 word at a time with 15s interval."""

import logging
from typing import List, Optional
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
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


class WATScreen(QWidget):
    """Word Association Test screen with 15-second automatic advancement and rapid response capture."""

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
        self.main_layout.setSpacing(16)

        # Top Bar: Mode, Fullscreen, Abandon
        top_bar = QHBoxLayout()
        self.mode_badge = QLabel("EXAM MODE")
        self.mode_badge.setStyleSheet(
            "background-color: #7F1D1D; color: #FEE2E2; padding: 4px 10px; border-radius: 10px; font-weight: 700; font-size: 11px;"
        )
        top_bar.addWidget(self.mode_badge)

        self.title_lbl = QLabel("Word Association Test (WAT)")
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

        # Timer Widget
        self.timer_widget = TimerWidget()
        self.timer_widget.set_theme(self.theme_name)
        self.timer_widget.pause_clicked.connect(self._on_pause)
        self.timer_widget.resume_clicked.connect(self._on_resume)
        self.timer_widget.next_clicked.connect(self._on_force_next)
        self.timer_widget.prev_clicked.connect(self._on_force_prev)
        self.main_layout.addWidget(self.timer_widget)

        # Central Word Display Card
        self.word_card = QFrame()
        self.word_card.setProperty("class", "HeroCard")
        self.word_card.setMinimumHeight(240)
        word_card_layout = QVBoxLayout(self.word_card)
        word_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        word_card_layout.setSpacing(14)

        self.prompt_sub = QLabel("ASSOCIATE SPONTANEOUSLY")
        self.prompt_sub.setProperty("class", "StatLabel")
        self.prompt_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        word_card_layout.addWidget(self.prompt_sub)

        self.word_label = QLabel("WORD")
        self.word_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        word_card_layout.addWidget(self.word_label)

        self.main_layout.addWidget(self.word_card, stretch=1)

        # Response Input Area
        input_frame = QFrame()
        input_frame.setProperty("class", "CardFrame")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(18, 14, 18, 14)
        input_layout.setSpacing(8)

        input_title = QLabel("Type your immediate thought / sentence:")
        input_title.setProperty("class", "Subtitle")
        input_layout.addWidget(input_title)

        self.response_input = QLineEdit()
        self.response_input.setPlaceholderText("Type association here... (Saved automatically)")
        self.response_input.setFont(QFont("Segoe UI", 13))
        self.response_input.returnPressed.connect(self._on_return_pressed)
        input_layout.addWidget(self.response_input)

        self.main_layout.addWidget(input_frame)

        # Engine tick poll timer
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(50)
        self.poll_timer.timeout.connect(self._poll_tick)
        self.apply_theme(self.theme_name)

    def apply_theme(self, theme_name: str) -> None:
        """Apply theme-adaptive colors to typography and sub-widgets."""
        self.theme_name = theme_name if theme_name in ("dark", "light") else "dark"
        self.timer_widget.set_theme(self.theme_name)
        if self.theme_name == "light":
            self.word_label.setStyleSheet(
                "font-size: 58px; font-weight: 900; color: #1D4ED8; letter-spacing: 3px;"
            )
            self.prompt_sub.setStyleSheet(
                "font-size: 13px; font-weight: 700; color: #475569; letter-spacing: 1.2px;"
            )
        else:
            self.word_label.setStyleSheet(
                "font-size: 58px; font-weight: 900; color: #38BDF8; letter-spacing: 3px;"
            )
            self.prompt_sub.setStyleSheet(
                "font-size: 13px; font-weight: 700; color: #94A3B8; letter-spacing: 1.2px;"
            )

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
            test_type="WAT",
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
            self.word_label.setText("GET READY")
            self.prompt_sub.setText("WORD ASSOCIATION TEST BEGINS SHORTLY...")
            self.response_input.setEnabled(False)
            self.response_input.setPlaceholderText(f"Test starts in {countdown} seconds...")
        else:
            self.response_input.setEnabled(True)
            self._load_item(0)

        self.engine.start()
        self.poll_timer.start()
        if countdown == 0:
            self.response_input.setFocus()

    def _load_item(self, index: int) -> None:
        if index < 0 or index >= len(self.items):
            return

        self._current_item_index = index
        item = self.items[index]
        self.word_label.setText(item.prompt_text.upper())
        self.prompt_sub.setText(f"WORD #{index + 1} OF {len(self.items)} • ASSOCIATE SPONTANEOUSLY")

        # Animated word pop-in
        eff = QGraphicsOpacityEffect(self.word_card)
        self.word_card.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity")
        anim.setDuration(160)
        anim.setStartValue(0.1)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: self.word_card.setGraphicsEffect(None))
        anim.start()
        self._word_anim = anim

        # Load existing response if navigating in practice mode
        self.response_input.blockSignals(True)
        if self.current_session and self.current_session.id:
            existing = self.ctx.session_repo.get_response_for_item(self.current_session.id, index)
            if existing and existing.response_text:
                self.response_input.setText(existing.response_text)
            else:
                self.response_input.clear()
        else:
            self.response_input.clear()
        self.response_input.blockSignals(False)
        self.response_input.setFocus()

    def _poll_tick(self) -> None:
        if not self.engine:
            return
        state = self.engine.poll_tick()
        self.timer_widget.update_state(state)

    def _on_phase_changed(
        self, old_phase: TestPhase, new_phase: TestPhase, item_idx: int
    ) -> None:
        if old_phase == TestPhase.WAT_SLIDE:
            self._flush_current_response()
        if new_phase == TestPhase.WAT_SLIDE:
            self.response_input.setEnabled(True)
            self.response_input.setPlaceholderText("Type association here... (Saved automatically)")
            self._load_item(item_idx)

    def _on_item_changed(self, new_idx: int) -> None:
        if self.engine and self.engine.phase == TestPhase.WAT_SLIDE:
            if new_idx != self._current_item_index:
                self._flush_current_response()
                self._load_item(new_idx)

    def _flush_current_response(self) -> None:
        if not self.current_session:
            return
        text = self.response_input.text().strip()
        time_spent = self.engine.get_state().elapsed_in_phase if self.engine else 0.0
        self.ctx.session_service.buffer_response(
            item_index=self._current_item_index,
            response_text=text,
            time_spent=time_spent,
        )
        self.ctx.session_service.flush_item_response(self._current_item_index)

    def _on_return_pressed(self) -> None:
        """Pressing Enter in practice mode can advance; in exam mode it flushes immediately."""
        self._flush_current_response()
        if self.engine and not self.engine.is_exam_mode:
            self.engine.force_next()

    def _on_session_completed(self) -> None:
        self.poll_timer.stop()
        self._flush_current_response()

        elapsed = self.engine.get_state().total_session_elapsed if self.engine else 0.0
        self.ctx.session_service.complete_session(elapsed_seconds=elapsed)

        QMessageBox.information(
            self,
            "WAT Drill Completed",
            f"You have completed all {len(self.items)} words in this session! All responses have been recorded.",
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
            "Abandon WAT Session",
            "Are you sure you want to exit? Responses recorded up to this word will be saved.",
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
