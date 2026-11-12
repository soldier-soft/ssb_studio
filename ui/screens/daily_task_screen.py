"""Daily Officer Task Screen running a unified curriculum: 2 TAT, 15 WAT, 15 SRT.
Guaranteed difference from last 2 days' practice items with non-repeater auto-shuffle.
Developed by Lt. V. Elangovan
"""

import logging
from typing import Any, Dict, List, Optional
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
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.app_context import AppContext
from services.item_pool_service import ItemPoolService

logger = logging.getLogger(__name__)


class DailyTaskScreen(QWidget):
    """Executes the daily officer routine with 2 TAT, 15 WAT, and 15 SRT."""

    mission_finished = Signal()

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.pool_service = ItemPoolService(ctx)
        self.theme_name = ctx.get_setting("theme", "dark")

        self.task_data: Optional[Dict[str, Any]] = None
        self.phase: str = "briefing"  # briefing, tat, wat, srt, completed

        # TAT state
        self.tat_idx = 0
        self.tat_subphase = "view"  # view (30s) or write (240s)
        self.tat_timer = 30
        self.tat_stories: Dict[str, str] = {}

        # WAT state
        self.wat_idx = 0
        self.wat_timer = 15
        self.wat_responses: Dict[str, str] = {}

        # SRT state
        self.srt_idx = 0
        self.srt_timer = 30
        self.srt_responses: Dict[str, str] = {}

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(28, 20, 28, 20)
        self.main_layout.setSpacing(16)

        # Build stack of stages
        self.stack = QStackedWidget()
        self._build_briefing_page()
        self._build_tat_page()
        self._build_wat_page()
        self._build_srt_page()
        self._build_completed_page()

        self.main_layout.addWidget(self.stack)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        # Active countdown loop
        self.tick_timer = QTimer(self)
        self.tick_timer.setInterval(1000)
        self.tick_timer.timeout.connect(self._on_tick)

        self.load_daily_task()

    def load_daily_task(self) -> None:
        self.task_data = self.pool_service.get_daily_task()
        self.stack.setCurrentIndex(0)
        self.streak_lbl.setText(f"{self.pool_service.get_streak()} Days Streak")

    # -------------------------------------------------------------
    # PAGE 0: Briefing
    # -------------------------------------------------------------
    def _build_briefing_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        card = QFrame()
        card.setProperty("class", "HeroCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(24, 20, 24, 20)
        c_layout.setSpacing(12)

        badge_h = QHBoxLayout()
        badge = QLabel("DAILY OFFICER WORKOUT ROUTINE")
        badge.setStyleSheet("background: rgba(245, 158, 11, 0.18); color: #F59E0B; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 11px;")
        badge_h.addWidget(badge)
        badge_h.addStretch()

        self.streak_lbl = QLabel("0 Days Streak")
        self.streak_lbl.setStyleSheet("color: #FBBF24; font-weight: 800; font-size: 13px;")
        badge_h.addWidget(self.streak_lbl)
        c_layout.addLayout(badge_h)

        self.briefing_title = QLabel("Today's Tactical Psychological Routine")
        self.briefing_title.setProperty("class", "H1")
        self.briefing_title.setStyleSheet("font-size: 24px; font-weight: 900;")
        c_layout.addWidget(self.briefing_title)

        self.briefing_desc = QLabel(
            "Curated daily set: 2 TAT Pictures, 15 WAT Words, and 15 SRT Situations.\n"
            "Guaranteed non-repeating and filtered to provide the difference of your last 2 days' sets."
        )
        self.briefing_desc.setStyleSheet("color: #94A3B8; font-size: 13px; line-height: 1.5;")
        c_layout.addWidget(self.briefing_desc)

        dev_credit = QLabel("🎖️ Curated & Designed by Lt. V. Elangovan")
        dev_credit.setStyleSheet("color: #38BDF8; font-weight: 700; font-size: 11.5px;")
        c_layout.addWidget(dev_credit)

        layout.addWidget(card)

        # 3 Phase Summary Cards
        row_h = QHBoxLayout()
        row_h.setSpacing(14)

        for icon, title_txt, items_txt in [
            ("🖼️", "Phase 1: TAT", "2 Picture Stories (30s view + 4m write)"),
            ("⚡", "Phase 2: WAT", "15 Words (15-second automatic progression)"),
            ("🎯", "Phase 3: SRT", "15 Situations (30-second decisive reactions)"),
        ]:
            f = QFrame()
            f.setProperty("class", "CardFrame")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(16, 14, 16, 14)
            fl.addWidget(QLabel(f"<span style='font-size: 20px;'>{icon}</span> <b>{title_txt}</b>"))
            fl.addWidget(QLabel(items_txt))
            row_h.addWidget(f)

        layout.addLayout(row_h)

        start_btn = QPushButton("🚀  Commence Today's Routine")
        start_btn.setProperty("class", "PrimaryBtn")
        start_btn.setMinimumHeight(44)
        start_btn.setStyleSheet("font-size: 15px; font-weight: 700;")
        start_btn.clicked.connect(self._start_daily_workout)
        layout.addWidget(start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(page)

    # -------------------------------------------------------------
    # PAGE 1: TAT Phase
    # -------------------------------------------------------------
    def _build_tat_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        top_h = QHBoxLayout()
        self.tat_header_lbl = QLabel("Phase 1: TAT Picture 1 of 2")
        self.tat_header_lbl.setStyleSheet("font-weight: 700; font-size: 14px; color: #38BDF8;")
        top_h.addWidget(self.tat_header_lbl)
        top_h.addStretch()

        self.tat_timer_lbl = QLabel("00:30")
        self.tat_timer_lbl.setStyleSheet("font-size: 28px; font-weight: 900; font-family: 'Consolas', monospace; color: #38BDF8;")
        top_h.addWidget(self.tat_timer_lbl)
        layout.addLayout(top_h)

        self.tat_scene_card = QFrame()
        self.tat_scene_card.setProperty("class", "HeroCard")
        sc_layout = QVBoxLayout(self.tat_scene_card)
        sc_layout.setContentsMargins(20, 16, 20, 16)

        self.tat_scene_title = QLabel("Tactical Map Conference")
        self.tat_scene_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #F8FAFC;")
        sc_layout.addWidget(self.tat_scene_title)

        self.tat_scene_desc = QLabel("Description...")
        self.tat_scene_desc.setWordWrap(True)
        self.tat_scene_desc.setStyleSheet("color: #94A3B8; font-size: 13px;")
        sc_layout.addWidget(self.tat_scene_desc)

        layout.addWidget(self.tat_scene_card)

        self.tat_story_edit = QPlainTextEdit()
        self.tat_story_edit.setPlaceholderText("Write your structured story here (Unlocked during 4-minute writing phase)...")
        self.tat_story_edit.setFont(QFont("Segoe UI", 12))
        self.tat_story_edit.setMinimumHeight(130)
        layout.addWidget(self.tat_story_edit)

        btn_adv = QPushButton("Advance to Next &rarr;")
        btn_adv.clicked.connect(self._advance_tat_manually)
        layout.addWidget(btn_adv, alignment=Qt.AlignmentFlag.AlignRight)

        self.stack.addWidget(page)

    # -------------------------------------------------------------
    # PAGE 2: WAT Phase
    # -------------------------------------------------------------
    def _build_wat_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        top_h = QHBoxLayout()
        self.wat_header_lbl = QLabel("Phase 2: WAT Word 1 of 15")
        self.wat_header_lbl.setStyleSheet("font-weight: 700; font-size: 14px; color: #3B82F6;")
        top_h.addWidget(self.wat_header_lbl)
        top_h.addStretch()

        self.wat_timer_lbl = QLabel("00:15")
        self.wat_timer_lbl.setStyleSheet("font-size: 32px; font-weight: 900; font-family: 'Consolas', monospace; color: #3B82F6;")
        top_h.addWidget(self.wat_timer_lbl)
        layout.addLayout(top_h)

        self.wat_card = QFrame()
        self.wat_card.setProperty("class", "HeroCard")
        wc_layout = QVBoxLayout(self.wat_card)
        wc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wc_layout.setContentsMargins(20, 24, 20, 24)

        self.wat_word_lbl = QLabel("COURAGE")
        self.wat_word_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wat_word_lbl.setStyleSheet("font-size: 52px; font-weight: 900; color: #38BDF8; letter-spacing: 2px;")
        wc_layout.addWidget(self.wat_word_lbl)
        layout.addWidget(self.wat_card)

        self.wat_input = QLineEdit()
        self.wat_input.setPlaceholderText("Type your spontaneous reaction and press Enter...")
        self.wat_input.setFont(QFont("Segoe UI", 13))
        self.wat_input.setMinimumHeight(44)
        self.wat_input.returnPressed.connect(self._advance_wat_manually)
        layout.addWidget(self.wat_input)

        self.stack.addWidget(page)

    # -------------------------------------------------------------
    # PAGE 3: SRT Phase
    # -------------------------------------------------------------
    def _build_srt_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        top_h = QHBoxLayout()
        self.srt_header_lbl = QLabel("Phase 3: SRT Situation 1 of 15")
        self.srt_header_lbl.setStyleSheet("font-weight: 700; font-size: 14px; color: #10B981;")
        top_h.addWidget(self.srt_header_lbl)
        top_h.addStretch()

        self.srt_timer_lbl = QLabel("00:30")
        self.srt_timer_lbl.setStyleSheet("font-size: 32px; font-weight: 900; font-family: 'Consolas', monospace; color: #10B981;")
        top_h.addWidget(self.srt_timer_lbl)
        layout.addLayout(top_h)

        self.srt_card = QFrame()
        self.srt_card.setProperty("class", "HeroCard")
        sc_layout = QVBoxLayout(self.srt_card)
        sc_layout.setContentsMargins(20, 16, 20, 16)

        self.srt_text_lbl = QLabel("Situation text...")
        self.srt_text_lbl.setWordWrap(True)
        self.srt_text_lbl.setStyleSheet("font-size: 17px; font-weight: 600; color: #F8FAFC;")
        sc_layout.addWidget(self.srt_text_lbl)
        layout.addWidget(self.srt_card)

        self.srt_edit = QPlainTextEdit()
        self.srt_edit.setPlaceholderText("Type your decisive reaction and press Submit...")
        self.srt_edit.setFont(QFont("Segoe UI", 12))
        self.srt_edit.setMinimumHeight(100)
        layout.addWidget(self.srt_edit)

        sub_btn = QPushButton("Submit Reaction &rarr;")
        sub_btn.setProperty("class", "PrimaryBtn")
        sub_btn.clicked.connect(self._advance_srt_manually)
        layout.addWidget(sub_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.stack.addWidget(page)

    # -------------------------------------------------------------
    # PAGE 4: Completed
    # -------------------------------------------------------------
    def _build_completed_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        lbl_trophy = QLabel("🏆")
        lbl_trophy.setStyleSheet("font-size: 64px;")
        lbl_trophy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_trophy)

        title = QLabel("DAILY OFFICER MISSION COMPLETED!")
        title.setProperty("class", "H1")
        title.setStyleSheet("font-size: 26px; font-weight: 900; color: #10B981;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.complete_desc = QLabel("Your daily streak is now 1 day. Excellent readiness!")
        self.complete_desc.setStyleSheet("color: #94A3B8; font-size: 14px;")
        self.complete_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.complete_desc)

        btn_ret = QPushButton("Return to Dashboard")
        btn_ret.setProperty("class", "PrimaryBtn")
        btn_ret.setMinimumHeight(44)
        btn_ret.clicked.connect(lambda: self.mission_finished.emit())
        layout.addWidget(btn_ret, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(page)

    # -------------------------------------------------------------
    # RUNNER & LOGIC
    # -------------------------------------------------------------
    def _start_daily_workout(self) -> None:
        self.ctx.sound_service.play_cue("countdown")
        self.phase = "tat"
        self.tat_idx = 0
        self.tat_subphase = "view"
        self.tat_timer = 30
        self.stack.setCurrentIndex(1)
        self._load_current_tat()
        self.tick_timer.start()

    def _load_current_tat(self) -> None:
        scenes = self.task_data.get("tat", [])
        if 0 <= self.tat_idx < len(scenes):
            sc = scenes[self.tat_idx]
            self.tat_header_lbl.setText(f"Phase 1: TAT Picture {self.tat_idx + 1} of {len(scenes)}")
            self.tat_scene_title.setText(sc.get("title", ""))
            self.tat_scene_desc.setText(sc.get("desc", ""))
            self.tat_story_edit.setPlainText(self.tat_stories.get(sc.get("id"), ""))
            self.tat_story_edit.setEnabled(self.tat_subphase == "write")
            self.tat_timer_lbl.setText(f"00:{self.tat_timer:02d}")

    def _advance_tat_manually(self) -> None:
        scenes = self.task_data.get("tat", [])
        if 0 <= self.tat_idx < len(scenes):
            sc = scenes[self.tat_idx]
            self.tat_stories[sc.get("id")] = self.tat_story_edit.toPlainText().strip()

        self.ctx.sound_service.play_cue("transition")
        if self.tat_subphase == "view":
            self.tat_subphase = "write"
            self.tat_timer = 240
            self._load_current_tat()
        else:
            if self.tat_idx + 1 < len(scenes):
                self.tat_idx += 1
                self.tat_subphase = "view"
                self.tat_timer = 30
                self._load_current_tat()
            else:
                # Switch to WAT
                self.phase = "wat"
                self.wat_idx = 0
                self.wat_timer = 15
                self.stack.setCurrentIndex(2)
                self._load_current_wat()

    def _load_current_wat(self) -> None:
        words = self.task_data.get("wat", [])
        if 0 <= self.wat_idx < len(words):
            w = words[self.wat_idx]
            self.wat_header_lbl.setText(f"Phase 2: WAT Word {self.wat_idx + 1} of {len(words)}")
            self.wat_word_lbl.setText(w.get("word", ""))
            self.wat_input.clear()
            self.wat_timer_lbl.setText(f"00:{self.wat_timer:02d}")
            self.wat_input.setFocus()

    def _advance_wat_manually(self) -> None:
        words = self.task_data.get("wat", [])
        if 0 <= self.wat_idx < len(words):
            w = words[self.wat_idx]
            self.wat_responses[w.get("id")] = self.wat_input.text().strip() or "(No reaction)"

        self.ctx.sound_service.play_cue("transition")
        if self.wat_idx + 1 < len(words):
            self.wat_idx += 1
            self.wat_timer = 15
            self._load_current_wat()
        else:
            # Switch to SRT
            self.phase = "srt"
            self.srt_idx = 0
            self.srt_timer = 30
            self.stack.setCurrentIndex(3)
            self._load_current_srt()

    def _load_current_srt(self) -> None:
        sits = self.task_data.get("srt", [])
        if 0 <= self.srt_idx < len(sits):
            s = sits[self.srt_idx]
            self.srt_header_lbl.setText(f"Phase 3: SRT Situation {self.srt_idx + 1} of {len(sits)}")
            self.srt_text_lbl.setText(s.get("text", ""))
            self.srt_edit.clear()
            self.srt_timer_lbl.setText(f"00:{self.srt_timer:02d}")
            self.srt_edit.setFocus()

    def _advance_srt_manually(self) -> None:
        sits = self.task_data.get("srt", [])
        if 0 <= self.srt_idx < len(sits):
            s = sits[self.srt_idx]
            self.srt_responses[s.get("id")] = self.srt_edit.toPlainText().strip() or "(No reaction)"

        self.ctx.sound_service.play_cue("transition")
        if self.srt_idx + 1 < len(sits):
            self.srt_idx += 1
            self.srt_timer = 30
            self._load_current_srt()
        else:
            # Mission Complete!
            self.tick_timer.stop()
            self.phase = "completed"
            new_streak = self.pool_service.record_daily_completion()
            self.complete_desc.setText(f"Your daily streak is now {new_streak} days. Outstanding readiness!")
            self.ctx.sound_service.play_cue("completion")
            self.stack.setCurrentIndex(4)

    def _on_tick(self) -> None:
        if self.phase == "tat":
            if self.tat_timer > 1:
                self.tat_timer -= 1
                self.tat_timer_lbl.setText(f"00:{self.tat_timer:02d}")
                if self.tat_timer <= 5 and self.tat_subphase == "view":
                    self.ctx.sound_service.play_cue("hurry")
            else:
                self._advance_tat_manually()

        elif self.phase == "wat":
            if self.wat_timer > 1:
                self.wat_timer -= 1
                self.wat_timer_lbl.setText(f"00:{self.wat_timer:02d}")
                if self.wat_timer <= 5:
                    self.ctx.sound_service.play_cue("hurry")
            else:
                self._advance_wat_manually()

        elif self.phase == "srt":
            if self.srt_timer > 1:
                self.srt_timer -= 1
                self.srt_timer_lbl.setText(f"00:{self.srt_timer:02d}")
                if self.srt_timer <= 5:
                    self.ctx.sound_service.play_cue("hurry")
            else:
                self._advance_srt_manually()

    def apply_theme(self, theme_name: str) -> None:
        """Update dynamic colors for dark and light theme consistency."""
        self.theme_name = theme_name if theme_name in ("dark", "light") else "dark"
        is_light = self.theme_name == "light"
        heading_color = "#0F172A" if is_light else "#F8FAFC"
        text_color = "#334155" if is_light else "#E2E8F0"
        sub_color = "#475569" if is_light else "#94A3B8"

        self.briefing_title.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {heading_color};")
        self.briefing_desc.setStyleSheet(f"color: {sub_color}; font-size: 13px; line-height: 1.5;")
        self.tat_scene_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {heading_color};")
        self.tat_scene_desc.setStyleSheet(f"color: {sub_color}; font-size: 13px;")
        self.srt_text_lbl.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {heading_color};")
