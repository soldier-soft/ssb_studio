"""Main Dashboard cockpit displaying real SQLite statistics, module launcher cards, and recent sessions."""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.app_context import AppContext
from ui.components.stat_card import StatCard


class DashboardScreen(QWidget):
    """Cockpit view showing real metrics from SQLite, module launcher cards, and recent history."""

    start_test_requested = Signal(str, str)  # (test_type, preset_name)
    navigate_requested = Signal(str)  # Target view key
    view_session_requested = Signal(int)  # Session ID

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.ctx = ctx

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        self.main_layout = QVBoxLayout(content_widget)
        self.main_layout.setContentsMargins(28, 24, 28, 24)
        self.main_layout.setSpacing(22)

        self._build_hero_header()
        self._build_crash_recovery_banner()
        self._build_kpi_cards()
        self._build_test_cards()
        self._build_recent_sessions_section()

        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)

    def _build_hero_header(self) -> None:
        hero_card = QFrame()
        hero_card.setProperty("class", "HeroCard")
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(24, 20, 24, 20)
        hero_layout.setSpacing(20)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)

        badge_h = QHBoxLayout()
        badge_lbl = QLabel("OFFICER LIKE QUALITIES (OLQ) TRAINING COCKPIT")
        badge_lbl.setStyleSheet(
            "background: rgba(59, 130, 246, 0.18); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.35); padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 10px; letter-spacing: 0.8px;"
        )
        badge_h.addWidget(badge_lbl)
        badge_h.addStretch()
        text_layout.addLayout(badge_h)

        title = QLabel("Candidate Practice Dashboard")
        title.setProperty("class", "H1")
        title.setStyleSheet("font-size: 26px; font-weight: 900; color: #F8FAFC;")

        subtitle = QLabel("Full-fidelity offline examination simulators for TAT picture analysis, WAT rapid association, and SRT crisis reaction.")
        subtitle.setProperty("class", "Subtitle")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 13px; line-height: 1.4;")

        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        hero_layout.addLayout(text_layout, stretch=1)

        # Quick action buttons in hero
        act_v = QVBoxLayout()
        act_v.setSpacing(8)
        act_v.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        import_btn = QPushButton("📁  Import Content")
        import_btn.setProperty("class", "PrimaryBtn")
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(lambda: self.navigate_requested.emit("library"))
        act_v.addWidget(import_btn)

        new_sess_btn = QPushButton("🚀  New Custom Session")
        new_sess_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_sess_btn.clicked.connect(lambda: self.navigate_requested.emit("builder"))
        act_v.addWidget(new_sess_btn)

        hero_layout.addLayout(act_v)
        self.main_layout.addWidget(hero_card)

    def _build_crash_recovery_banner(self) -> None:
        self.recovery_banner = QFrame()
        self.recovery_banner.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #450A0A, stop:1 #1C1917); border: 1px solid #EF4444; border-radius: 10px; padding: 12px 16px;"
        )
        banner_layout = QHBoxLayout(self.recovery_banner)

        self.recovery_label = QLabel("⚠️ An uncompleted session from a previous run was detected.")
        self.recovery_label.setStyleSheet("color: #FCA5A5; font-weight: 600; font-size: 12.5px;")
        banner_layout.addWidget(self.recovery_label, stretch=1)

        view_rec_btn = QPushButton("Review Session Responses →")
        view_rec_btn.setProperty("class", "DangerBtn")
        view_rec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_rec_btn.clicked.connect(self._on_view_recovery_clicked)
        banner_layout.addWidget(view_rec_btn)

        self.recovery_banner.setVisible(False)
        self.main_layout.addWidget(self.recovery_banner)

    def _build_kpi_cards(self) -> None:
        grid = QGridLayout()
        grid.setSpacing(14)

        self.stat_completed = StatCard("Tests Completed", "0", "Full simulated exams", "🏆", "#38BDF8")
        self.stat_practice_time = StatCard("Practice Time", "0m", "Active test duration", "⏱️", "#34D399")
        self.stat_completion_rate = StatCard("Answer Rate", "0.0%", "Questions attempted", "📈", "#FBBF24")
        self.stat_total_responses = StatCard("Responses Logged", "0", "Saved answers", "✍️", "#A78BFA")

        grid.addWidget(self.stat_completed, 0, 0)
        grid.addWidget(self.stat_practice_time, 0, 1)
        grid.addWidget(self.stat_completion_rate, 0, 2)
        grid.addWidget(self.stat_total_responses, 0, 3)

        self.main_layout.addLayout(grid)

    def _build_test_cards(self) -> None:
        lbl_h = QHBoxLayout()
        section_lbl = QLabel("Psychological Test Modules")
        section_lbl.setProperty("class", "H2")
        lbl_h.addWidget(section_lbl)
        lbl_h.addStretch()
        self.main_layout.addLayout(lbl_h)

        grid = QGridLayout()
        grid.setSpacing(16)

        # 1. TAT Card
        tat_card = self._create_module_card(
            title="TAT — Thematic Apperception",
            icon="🖼️",
            desc="Examine ambiguous picture slides. 30 seconds viewing phase followed by 4 minutes 30 seconds story writing phase per picture.",
            badge="12 PICTURES • 54 MINS",
            test_type="TAT",
            preset_name="TAT Standard Exam (12 Pics)",
            accent_color="#3B82F6",
        )
        grid.addWidget(tat_card, 0, 0)

        # 2. WAT Card
        wat_card = self._create_module_card(
            title="WAT — Word Association",
            icon="⚡",
            desc="Spontaneous thought reaction slides. Displays 1 word at a time with a strict 15-second interval and auto-advancement.",
            badge="60 WORDS • 15 MINS",
            test_type="WAT",
            preset_name="WAT 60-Word Official Standard",
            accent_color="#10B981",
        )
        grid.addWidget(wat_card, 0, 1)

        # 3. SRT Card
        srt_card = self._create_module_card(
            title="SRT — Situation Reaction",
            icon="🎯",
            desc="Realistic crisis scenarios. 30 seconds per slide to record prompt, constructive solutions with numbering gap preservation.",
            badge="60 SITUATIONS • 30 MINS",
            test_type="SRT",
            preset_name="SRT 60-Situation Official Exam",
            accent_color="#F59E0B",
        )
        grid.addWidget(srt_card, 0, 2)

        self.main_layout.addLayout(grid)

    def _create_module_card(
        self,
        title: str,
        icon: str,
        desc: str,
        badge: str,
        test_type: str,
        preset_name: str,
        accent_color: str,
    ) -> QFrame:
        card = QFrame()
        card.setProperty("class", "CardFrame")
        card.setStyleSheet(
            f"""
            QFrame.CardFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #111827, stop:1 #131E33);
                border: 1px solid #1F2937;
                border-top: 3px solid {accent_color};
                border-radius: 12px;
            }}
            QFrame.CardFrame:hover {{
                border-color: {accent_color};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #131C30, stop:1 #17243F);
            }}
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # Top icon + title + badge
        top_h = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 26px; padding: 6px; background-color: rgba(255, 255, 255, 0.05); border-radius: 8px;")
        top_h.addWidget(icon_lbl)

        card_title = QLabel(title)
        card_title.setStyleSheet(f"color: {accent_color}; font-size: 15px; font-weight: 800;")
        top_h.addWidget(card_title, stretch=1)
        layout.addLayout(top_h)

        # Badge pill
        badge_lbl = QLabel(badge)
        badge_lbl.setStyleSheet(
            f"background-color: rgba(255, 255, 255, 0.06); color: #94A3B8; font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.5px;"
        )
        layout.addWidget(badge_lbl, alignment=Qt.AlignmentFlag.AlignLeft)

        # Description
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; line-height: 1.45;")
        layout.addWidget(desc_lbl)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        custom_btn = QPushButton("Custom Setup")
        custom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        custom_btn.clicked.connect(lambda: self.navigate_requested.emit("builder"))
        btn_layout.addWidget(custom_btn)

        start_btn = QPushButton("Quick Start ▶")
        start_btn.setProperty("class", "PrimaryBtn")
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.clicked.connect(lambda: self.start_test_requested.emit(test_type, preset_name))
        btn_layout.addWidget(start_btn)

        layout.addLayout(btn_layout)
        return card

    def _build_recent_sessions_section(self) -> None:
        header_h = QHBoxLayout()
        title = QLabel("Recent Practice Sessions")
        title.setProperty("class", "H2")
        header_h.addWidget(title, stretch=1)

        view_all_btn = QPushButton("View Full History →")
        view_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_all_btn.clicked.connect(lambda: self.navigate_requested.emit("history"))
        header_h.addWidget(view_all_btn)

        self.main_layout.addLayout(header_h)

        # Empty state message
        self.empty_history_frame = QFrame()
        self.empty_history_frame.setProperty("class", "CardFrame")
        empty_layout = QVBoxLayout(self.empty_history_frame)
        empty_layout.setContentsMargins(36, 36, 36, 36)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(10)

        empty_icon = QLabel("📝")
        empty_icon.setStyleSheet("font-size: 40px;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)

        empty_txt = QLabel("No test sessions recorded yet.")
        empty_txt.setProperty("class", "H3")
        empty_txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_txt)

        empty_sub = QLabel("Select a test module above or click Quick Start to begin your first SSB practice drill.")
        empty_sub.setProperty("class", "Subtitle")
        empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_sub)

        self.main_layout.addWidget(self.empty_history_frame)

        # Table for populated sessions
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Date & Time", "Type", "Preset / Title", "Items Attempted", "Duration", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(240)
        self.table.doubleClicked.connect(self._on_row_double_clicked)

        self.main_layout.addWidget(self.table)

    def refresh_data(self) -> None:
        """Query SQLite and reload all dashboard KPIs and recent sessions."""
        stats = self.ctx.analytics_repo.get_dashboard_stats()

        self.stat_completed.set_value(str(stats["total_completed"]))

        total_sec = stats["total_practice_seconds"]
        hrs = int(total_sec // 3600)
        mins = int((total_sec % 3600) // 60)
        time_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins}m"
        self.stat_practice_time.set_value(time_str)

        self.stat_completion_rate.set_value(f"{stats['completion_rate']}%")

        resp_text = f"{stats['completed_responses']} / {stats['total_responses']}"
        sub_text = f"TAT: {stats['tat_stories_written']} | WAT: {stats['wat_words_attempted']} | SRT: {stats['srt_reactions_attempted']}"
        self.stat_total_responses.set_value(resp_text, sub_text)

        # Check crash recovery
        uncompleted = self.ctx.session_service.check_crash_recovery()
        if uncompleted:
            self._uncompleted_session_id = uncompleted.id
            self.recovery_label.setText(
                f"⚠️ Interrupted {uncompleted.test_type} session #{uncompleted.id} ('{uncompleted.preset_name}') detected from {uncompleted.start_time[:19].replace('T', ' ')}. All responses are saved."
            )
            self.recovery_banner.setVisible(True)
        else:
            self.recovery_banner.setVisible(False)

        # Populate Recent Sessions
        recent = self.ctx.analytics_repo.get_recent_sessions(limit=6)
        if not recent:
            self.empty_history_frame.setVisible(True)
            self.table.setVisible(False)
        else:
            self.empty_history_frame.setVisible(False)
            self.table.setVisible(True)
            self.table.setRowCount(len(recent))

            for row_idx, sess in enumerate(recent):
                self.table.setItem(row_idx, 0, QTableWidgetItem(f"#{sess.id:03d}"))
                dt_str = sess.start_time[:16].replace("T", " ")
                self.table.setItem(row_idx, 1, QTableWidgetItem(dt_str))

                type_item = QTableWidgetItem(sess.test_type)
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_idx, 2, type_item)

                self.table.setItem(row_idx, 3, QTableWidgetItem(sess.preset_name))

                comp_str = f"{sess.completed_items} / {sess.total_items}"
                self.table.setItem(row_idx, 4, QTableWidgetItem(comp_str))

                dur_mins = int(sess.elapsed_seconds // 60)
                dur_secs = int(sess.elapsed_seconds % 60)
                dur_str = f"{dur_mins}m {dur_secs:02d}s"
                self.table.setItem(row_idx, 5, QTableWidgetItem(dur_str))

                status_item = QTableWidgetItem(f" {sess.status} ")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if sess.status == "COMPLETED":
                    status_item.setForeground(Qt.GlobalColor.green)
                elif sess.status == "ABANDONED":
                    status_item.setForeground(Qt.GlobalColor.yellow)
                self.table.setItem(row_idx, 6, status_item)

    def _on_row_double_clicked(self) -> None:
        current_row = self.table.currentRow()
        if current_row >= 0:
            id_item = self.table.item(current_row, 0)
            if id_item:
                sess_id = int(id_item.text().replace("#", ""))
                self.view_session_requested.emit(sess_id)

    def _on_view_recovery_clicked(self) -> None:
        if hasattr(self, "_uncompleted_session_id"):
            self.view_session_requested.emit(self._uncompleted_session_id)
