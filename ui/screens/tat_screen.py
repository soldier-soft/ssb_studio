"""TAT (Thematic Apperception Test) execution screen with 30s viewing and 270s story writing phases."""

import logging
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.app_context import AppContext
from core.timer_engine import TestPhase, TimerEngine, TimerState
from database.models import Preset, Session, SessionResponse
from services.session_service import ActiveSessionItem
from ui.components.timer_widget import TimerWidget

logger = logging.getLogger(__name__)


class TATScreen(QWidget):
    """Thematic Apperception Test screen with automated phase transitions and full-screen exam mode."""

    session_finished = Signal(int)  # Session ID
    session_abandoned = Signal()

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.engine: Optional[TimerEngine] = None
        self.items: List[ActiveSessionItem] = []
        self.current_session: Optional[Session] = None
        self.theme_name: str = ctx.get_setting("theme", "dark")

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 16, 20, 16)
        self.main_layout.setSpacing(12)

        # Top Control Bar: Emergency Exit, Mode Badge, Fullscreen Button
        top_bar = QHBoxLayout()
        self.mode_badge = QLabel("EXAM MODE")
        self.mode_badge.setStyleSheet(
            "background-color: #7F1D1D; color: #FEE2E2; padding: 4px 10px; border-radius: 10px; font-weight: 700; font-size: 11px;"
        )
        top_bar.addWidget(self.mode_badge)

        self.test_title_lbl = QLabel("Thematic Apperception Test (TAT)")
        self.test_title_lbl.setProperty("class", "H3")
        top_bar.addWidget(self.test_title_lbl, stretch=1)

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

        # Central Stack: Page 0 = Image Viewing, Page 1 = Story Writing
        self.stack = QStackedWidget()

        # Page 0: Image Viewing Widget
        self.viewing_widget = QWidget()
        view_layout = QVBoxLayout(self.viewing_widget)
        view_layout.setContentsMargins(0, 0, 0, 0)
        view_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        view_layout.addWidget(self.image_label)

        self.stack.addWidget(self.viewing_widget)

        # Page 1: Story Writing Widget
        self.writing_widget = QWidget()
        write_layout = QVBoxLayout(self.writing_widget)
        write_layout.setContentsMargins(0, 0, 0, 0)
        write_layout.setSpacing(8)

        self.guidance_lbl = QLabel(
            "Write your story: Describe what led to the situation, what is happening at the moment, the characters' feelings/thoughts, and the final outcome."
        )
        self.guidance_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; font-style: italic;")
        write_layout.addWidget(self.guidance_lbl)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Type your story here... (Responses are automatically saved)")
        self.editor.setFont(QFont("Segoe UI", 12))
        self.editor.textChanged.connect(self._on_editor_text_changed)
        write_layout.addWidget(self.editor, stretch=1)

        # Word count & Character count footer
        stats_h = QHBoxLayout()
        self.word_count_lbl = QLabel("Words: 0 | Characters: 0")
        self.word_count_lbl.setStyleSheet("color: #64748B; font-weight: 500; font-size: 11px;")
        stats_h.addWidget(self.word_count_lbl)
        stats_h.addStretch()

        self.autosave_status_lbl = QLabel("Autosave: Active")
        self.autosave_status_lbl.setStyleSheet("color: #10B981; font-weight: 600; font-size: 11px;")
        stats_h.addWidget(self.autosave_status_lbl)

        write_layout.addLayout(stats_h)
        self.stack.addWidget(self.writing_widget)

        self.main_layout.addWidget(self.stack, stretch=1)

        # Polling Timer for precise monotonic time derivation
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(50)  # 20 ticks per second
        self.poll_timer.timeout.connect(self._poll_tick)

        # Autosave debounce timer (1500 ms)
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(1500)
        self.debounce_timer.timeout.connect(self._on_debounce_flush)

        self._current_item_index: int = 0
        self._current_pixmap: Optional[QPixmap] = None
        self.apply_theme(self.theme_name)

    def apply_theme(self, theme_name: str) -> None:
        """Apply theme-adaptive styling."""
        self.theme_name = theme_name if theme_name in ("dark", "light") else "dark"
        self.timer_widget.set_theme(self.theme_name)
        if self.theme_name == "light":
            self.image_label.setStyleSheet("background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 8px; color: #0F172A; font-size: 16px; font-weight: 600;")
            self.guidance_lbl.setStyleSheet("color: #475569; font-size: 12px; font-style: italic;")
        else:
            self.image_label.setStyleSheet("background-color: #030712; border: 1px solid #1E293B; border-radius: 8px; color: #E2E8F0; font-size: 16px; font-weight: 600;")
            self.guidance_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; font-style: italic;")

    def start_session(
        self,
        session: Session,
        items: List[ActiveSessionItem],
    ) -> None:
        """Start the TAT test session with verified items and timing engine."""
        self.current_session = session
        self.items = items
        self._current_item_index = 0
        self.theme_name = self.ctx.get_setting("theme", "dark")
        self.apply_theme(self.theme_name)

        # Update mode badge
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
            test_type="TAT",
            total_items=len(items),
            view_duration=session.view_duration,
            write_duration=session.write_duration,
            is_exam_mode=session.is_exam_mode,
            countdown_seconds=countdown,
        )

        self.engine.on_phase_change = self._on_phase_changed
        self.engine.on_item_change = self._on_item_changed
        self.engine.on_session_complete = self._on_session_completed
        self.engine.on_sound_cue = self._play_sound_cue

        if countdown > 0:
            self.image_label.setText(
                f"GET READY\n\nThematic Apperception Test begins in {countdown} seconds...\nPicture #1 viewing starts automatically."
            )
            self.stack.setCurrentIndex(0)
        else:
            self._load_item(0)

        self.engine.start()
        self.poll_timer.start()

    def _on_item_changed(self, new_idx: int) -> None:
        if new_idx != self._current_item_index:
            self._load_item(new_idx)

    def _load_item(self, index: int) -> None:
        """Load image and draft answer for the specified item index."""
        if index < 0 or index >= len(self.items):
            return

        self._current_item_index = index
        item = self.items[index]

        # Load image pixmap
        img_path = Path(item.prompt_text)
        if img_path.exists():
            self._current_pixmap = QPixmap(str(img_path))
            self._update_scaled_image()
        else:
            self.image_label.setText(f"[Image file not found: {img_path.name}]")

        # Load existing response from session service if navigating in practice mode
        self.editor.blockSignals(True)
        if self.current_session and self.current_session.id:
            existing = self.ctx.session_repo.get_response_for_item(self.current_session.id, index)
            if existing and existing.response_text:
                self.editor.setPlainText(existing.response_text)
            else:
                self.editor.setPlainText("")
        else:
            self.editor.setPlainText("")
        self.editor.blockSignals(False)
        self._update_counts()

    def _update_scaled_image(self) -> None:
        if self._current_pixmap and not self._current_pixmap.isNull():
            target_size = self.viewing_widget.size()
            if target_size.width() > 100 and target_size.height() > 100:
                scaled = self._current_pixmap.scaled(
                    target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.image_label.setPixmap(scaled)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_scaled_image()

    def _poll_tick(self) -> None:
        if not self.engine:
            return
        state = self.engine.poll_tick()
        self.timer_widget.update_state(state)

    def _on_phase_changed(
        self, old_phase: TestPhase, new_phase: TestPhase, item_idx: int
    ) -> None:
        """Handle transition between Viewing, Writing, and Next Image."""
        # 1. Flush response for current item before leaving writing phase
        if old_phase == TestPhase.TAT_WRITING:
            self._flush_current_response()

        # 2. Switch visual stack page
        if new_phase == TestPhase.TAT_VIEWING:
            self._load_item(item_idx)
            self.stack.setCurrentIndex(0)  # Image viewing page
        elif new_phase == TestPhase.TAT_WRITING:
            if item_idx != self._current_item_index:
                self._load_item(item_idx)
            self.stack.setCurrentIndex(1)  # Story editor page
            self.editor.setFocus()
        elif new_phase == TestPhase.PRE_COUNTDOWN:
            self.stack.setCurrentIndex(0)

    def _on_editor_text_changed(self) -> None:
        self._update_counts()
        self.debounce_timer.start()

    def _update_counts(self) -> None:
        text = self.editor.toPlainText().strip()
        words = len(text.split()) if text else 0
        chars = len(text)
        self.word_count_lbl.setText(f"Words: {words} | Characters: {chars}")

    def _on_debounce_flush(self) -> None:
        self._flush_current_response()

    def _flush_current_response(self) -> None:
        if not self.current_session:
            return
        text = self.editor.toPlainText().strip()
        self.ctx.session_service.buffer_response(
            item_index=self._current_item_index,
            response_text=text,
            time_spent=self.engine.get_state().elapsed_in_phase if self.engine else 0.0,
        )
        self.ctx.session_service.flush_item_response(self._current_item_index)

    def _on_session_completed(self) -> None:
        self.poll_timer.stop()
        self._flush_current_response()

        elapsed = self.engine.get_state().total_session_elapsed if self.engine else 0.0
        self.ctx.session_service.complete_session(elapsed_seconds=elapsed)

        QMessageBox.information(
            self,
            "TAT Test Completed",
            "Congratulations! You have completed all Thematic Apperception Test pictures. All responses have been saved.",
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
            "Abandon TAT Session",
            "Are you sure you want to exit? All stories written so far will be saved to your session history.",
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
