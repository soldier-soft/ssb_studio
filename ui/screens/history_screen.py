"""Session History and Detailed Answer Review with candidate evaluator notes and export options."""

from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.app_context import AppContext
from database.models import Session, SessionResponse


class SessionDetailDialog(QDialog):
    """Detailed view of a single session's questions, candidate answers, and evaluator notes."""

    def __init__(self, ctx: AppContext, session_id: int, parent=None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.session_id = session_id

        self.session: Optional[Session] = self.ctx.session_repo.get_session(session_id)
        if not self.session:
            raise ValueError(f"Session #{session_id} not found.")

        self.responses: List[SessionResponse] = self.ctx.session_repo.get_responses(session_id)

        self.setWindowTitle(f"Session #{self.session.id} — {self.session.test_type} ({self.session.preset_name})")
        self.setMinimumSize(900, 650)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(14)

        # Header Info Card
        meta_card = QFrame()
        meta_card.setProperty("class", "CardFrame")
        meta_layout = QHBoxLayout(meta_card)

        col1 = QVBoxLayout()
        col1.addWidget(QLabel(f"<b>Test Type:</b> {self.session.test_type}"))
        col1.addWidget(QLabel(f"<b>Preset:</b> {self.session.preset_name}"))
        col1.addWidget(QLabel(f"<b>Mode:</b> {'Exam' if self.session.is_exam_mode else 'Practice'}"))
        meta_layout.addLayout(col1)

        col2 = QVBoxLayout()
        dt_str = self.session.start_time[:19].replace("T", " ")
        col2.addWidget(QLabel(f"<b>Date:</b> {dt_str}"))
        mins = int(self.session.elapsed_seconds // 60)
        secs = int(self.session.elapsed_seconds % 60)
        col2.addWidget(QLabel(f"<b>Duration:</b> {mins}m {secs}s"))
        col2.addWidget(QLabel(f"<b>Completed:</b> {self.session.completed_items} / {self.session.total_items}"))
        meta_layout.addLayout(col2)

        meta_layout.addStretch()

        # Export Buttons inside detail dialog
        btn_v = QVBoxLayout()
        btn_pdf = QPushButton("📄 Export PDF Report")
        btn_pdf.setProperty("class", "PrimaryBtn")
        btn_pdf.clicked.connect(self._export_pdf)
        btn_v.addWidget(btn_pdf)

        btn_csv = QPushButton("📊 Export CSV")
        btn_csv.clicked.connect(self._export_csv)
        btn_v.addWidget(btn_csv)

        meta_layout.addLayout(btn_v)
        main_layout.addWidget(meta_card)

        # Responses Table
        tbl_lbl = QLabel("Candidate Responses & Answers Log:")
        tbl_lbl.setProperty("class", "StatLabel")
        main_layout.addWidget(tbl_lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "#", "Prompt / Identifier", "Response Text", "Chars", "Time Spent"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self._populate_responses()
        main_layout.addWidget(self.table, stretch=2)

        # Evaluator / Self-Assessment Notes & Rating Area
        notes_card = QFrame()
        notes_card.setProperty("class", "CardFrame")
        notes_layout = QVBoxLayout(notes_card)
        notes_layout.setSpacing(8)

        n_top = QHBoxLayout()
        n_lbl = QLabel("Evaluator Assessment & Improvement Goals:")
        n_lbl.setProperty("class", "H3")
        n_top.addWidget(n_lbl, stretch=1)

        rating_lbl = QLabel("Candidate Rating (1-5):")
        n_top.addWidget(rating_lbl)
        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(1, 5)
        self.rating_spin.setValue(self.session.user_rating or 4)
        n_top.addWidget(self.rating_spin)

        btn_save_notes = QPushButton("Save Assessment")
        btn_save_notes.setProperty("class", "PrimaryBtn")
        btn_save_notes.clicked.connect(self._save_notes)
        n_top.addWidget(btn_save_notes)

        notes_layout.addLayout(n_top)

        self.notes_editor = QPlainTextEdit()
        self.notes_editor.setPlaceholderText("Write observations on themes, qualities shown, speed, initiative, or areas for improvement...")
        self.notes_editor.setPlainText(self.session.evaluator_notes)
        self.notes_editor.setMaximumHeight(90)
        notes_layout.addWidget(self.notes_editor)

        main_layout.addWidget(notes_card, stretch=1)

        # Close button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        main_layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def _populate_responses(self) -> None:
        self.table.setRowCount(len(self.responses))
        for row, r in enumerate(self.responses):
            idx_item = QTableWidgetItem(str(r.item_index + 1))
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, idx_item)

            ident_item = QTableWidgetItem(r.item_identifier)
            self.table.setItem(row, 1, ident_item)

            resp_item = QTableWidgetItem(r.response_text if r.response_text else "(No answer)")
            self.table.setItem(row, 2, resp_item)

            len_item = QTableWidgetItem(str(r.response_length))
            len_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, len_item)

            time_item = QTableWidgetItem(f"{r.time_spent_seconds:.1f}s")
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, time_item)

    def _save_notes(self) -> None:
        notes = self.notes_editor.toPlainText().strip()
        rating = self.rating_spin.value()
        self.ctx.session_repo.update_evaluator_notes(self.session_id, notes, rating)
        QMessageBox.information(self, "Notes Saved", "Evaluator notes and rating successfully saved.")

    def _export_pdf(self) -> None:
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Report",
            filter="PDF Files (*.pdf)",
            dir=f"session_{self.session_id}_report.pdf",
        )
        if out_path:
            self.ctx.report_service.generate_pdf_report(
                self.session, self.responses, out_path
            )
            QMessageBox.information(
                self, "Export Successful", f"PDF report generated at:\n{out_path}"
            )

    def _export_csv(self) -> None:
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV Export",
            filter="CSV Files (*.csv)",
            dir=f"session_{self.session_id}_export.csv",
        )
        if out_path:
            self.ctx.report_service.export_session_to_csv(
                self.session, self.responses, out_path
            )
            QMessageBox.information(
                self, "Export Successful", f"CSV file exported to:\n{out_path}"
            )


class HistoryScreen(QWidget):
    """Past sessions browser with filtering, searching, answer review, and bulk exports."""

    view_session_requested = Signal(int)

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.ctx = ctx

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(16)

        # Header
        header_v = QVBoxLayout()
        header_v.setSpacing(2)
        title = QLabel("Session History & Detailed Analytics")
        title.setProperty("class", "H1")
        sub = QLabel("Filter and inspect your previous psychological practice sessions, evaluate candidate answers, and export reports.")
        sub.setProperty("class", "Subtitle")
        header_v.addWidget(title)
        header_v.addWidget(sub)
        main_layout.addLayout(header_v)

        # Search & Filter Bar
        filter_card = QFrame()
        filter_card.setProperty("class", "CardFrame")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setSpacing(12)

        filter_layout.addWidget(QLabel("Filter Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["ALL", "TAT", "WAT", "SRT"])
        self.type_combo.currentIndexChanged.connect(self.refresh_history)
        filter_layout.addWidget(self.type_combo)

        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search preset, content deck, or notes...")
        self.search_input.textChanged.connect(self.refresh_history)
        filter_layout.addWidget(self.search_input, stretch=1)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self.refresh_history)
        filter_layout.addWidget(btn_refresh)

        main_layout.addWidget(filter_card)

        # Sessions Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Date & Time", "Test Type", "Preset / Title", "Deck Source", "Attempted", "Duration", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_view_selected)
        main_layout.addWidget(self.table, stretch=1)

        # Action bar at bottom
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        btn_view = QPushButton("🔍 Review Answers & Evaluator Notes")
        btn_view.setProperty("class", "PrimaryBtn")
        btn_view.clicked.connect(self._on_view_selected)
        bottom_bar.addWidget(btn_view)

        btn_delete = QPushButton("🗑️ Delete Session")
        btn_delete.setProperty("class", "DangerBtn")
        btn_delete.clicked.connect(self._on_delete_selected)
        bottom_bar.addWidget(btn_delete)

        bottom_bar.addStretch()
        main_layout.addLayout(bottom_bar)

    def refresh_history(self) -> None:
        """Fetch filtered sessions from SQLite repository."""
        ttype = self.type_combo.currentText()
        search = self.search_input.text().strip() or None

        sessions = self.ctx.session_repo.list_sessions(
            test_type=ttype, limit=100, search_query=search
        )

        self.table.setRowCount(len(sessions))
        for row, s in enumerate(sessions):
            self.table.setItem(row, 0, QTableWidgetItem(str(s.id)))
            dt = s.start_time[:16].replace("T", " ")
            self.table.setItem(row, 1, QTableWidgetItem(dt))

            type_it = QTableWidgetItem(s.test_type)
            type_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, type_it)

            self.table.setItem(row, 3, QTableWidgetItem(s.preset_name))
            self.table.setItem(row, 4, QTableWidgetItem(s.content_set_name or "Default"))

            comp_it = QTableWidgetItem(f"{s.completed_items} / {s.total_items}")
            comp_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, comp_it)

            dur_m = int(s.elapsed_seconds // 60)
            dur_s = int(s.elapsed_seconds % 60)
            self.table.setItem(row, 6, QTableWidgetItem(f"{dur_m}m {dur_s}s"))

            stat_it = QTableWidgetItem(s.status)
            stat_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if s.status == "COMPLETED":
                stat_it.setForeground(Qt.GlobalColor.green)
            elif s.status == "ABANDONED":
                stat_it.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 7, stat_it)

    def open_session_detail(self, session_id: int) -> None:
        """Open the detailed answer review modal for a specific session."""
        try:
            dlg = SessionDetailDialog(self.ctx, session_id, parent=self)
            dlg.exec()
            self.refresh_history()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load session #{session_id}: {e}")

    def _on_view_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection", "Please select a session row to review.")
            return
        id_item = self.table.item(row, 0)
        if id_item:
            sess_id = int(id_item.text())
            self.open_session_detail(sess_id)

    def _on_delete_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection", "Please select a session to delete.")
            return

        sess_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(
            self,
            "Delete Session",
            f"Are you sure you want to permanently delete session #{sess_id}? Responses and records will be removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.ctx.session_repo.delete_session(sess_id)
            self.refresh_history()
