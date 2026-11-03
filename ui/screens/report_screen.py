"""Reports Center for generating PDF reports, exporting CSV files, and managing database backups."""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.app_context import AppContext
from app.config import get_backup_dir, get_reports_dir
from database.models import Session


class ReportScreen(QWidget):
    """Generates ReportLab PDF reports, CSV data files, and performs atomic SQLite backups."""

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.ctx = ctx

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(20)

        # Header
        header_v = QVBoxLayout()
        header_v.setSpacing(2)
        title = QLabel("Reports & Data Export Center")
        title.setProperty("class", "H1")
        sub = QLabel("Export polished PDF reports with candidate answers, generate CSV spreadsheets, and manage local database backups.")
        sub.setProperty("class", "Subtitle")
        header_v.addWidget(title)
        header_v.addWidget(sub)
        main_layout.addLayout(header_v)

        # Section 1: Session Report Generator
        card1 = QFrame()
        card1.setProperty("class", "CardFrame")
        c1_layout = QVBoxLayout(card1)
        c1_layout.setSpacing(14)

        sec1_title = QLabel("📄 Export Candidate Session Report")
        sec1_title.setProperty("class", "H2")
        c1_layout.addWidget(sec1_title)

        c1_sub = QLabel("Select a completed or past session to produce an official evaluation report or CSV spreadsheet.")
        c1_sub.setProperty("class", "Subtitle")
        c1_layout.addWidget(c1_sub)

        row_h = QHBoxLayout()
        row_h.addWidget(QLabel("Select Session:"))
        self.session_combo = QComboBox()
        self.session_combo.setMinimumWidth(380)
        self.session_combo.currentIndexChanged.connect(self._on_session_selection_changed)
        row_h.addWidget(self.session_combo)
        row_h.addStretch()
        c1_layout.addLayout(row_h)

        self.session_info_lbl = QLabel("")
        self.session_info_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 500;")
        c1_layout.addWidget(self.session_info_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_export_pdf = QPushButton("📄 Generate Polished PDF Report")
        self.btn_export_pdf.setProperty("class", "PrimaryBtn")
        self.btn_export_pdf.clicked.connect(self._on_generate_pdf)
        btn_row.addWidget(self.btn_export_pdf)

        self.btn_export_csv = QPushButton("📊 Export CSV Spreadsheet")
        self.btn_export_csv.clicked.connect(self._on_export_csv)
        btn_row.addWidget(self.btn_export_csv)

        btn_row.addStretch()
        c1_layout.addLayout(btn_row)

        main_layout.addWidget(card1)

        # Section 2: Database Backup & Maintenance
        card2 = QFrame()
        card2.setProperty("class", "CardFrame")
        c2_layout = QVBoxLayout(card2)
        c2_layout.setSpacing(14)

        sec2_title = QLabel("💾 Local Database Management & Backups")
        sec2_title.setProperty("class", "H2")
        c2_layout.addWidget(sec2_title)

        c2_sub = QLabel(
            "All sessions, custom presets, content sets, and answers are stored locally on your machine in SQLite. "
            "Create non-blocking atomic backups or restore from an earlier backup file."
        )
        c2_sub.setProperty("class", "Subtitle")
        c2_layout.addWidget(c2_sub)

        self.db_stats_lbl = QLabel("Database Path: ... | Size: ...")
        self.db_stats_lbl.setStyleSheet("color: #64748B; font-family: monospace; font-size: 11px;")
        c2_layout.addWidget(self.db_stats_lbl)

        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(10)

        btn_backup = QPushButton("📦 Backup Database Now")
        btn_backup.setProperty("class", "PrimaryBtn")
        btn_backup.clicked.connect(self._on_backup_db)
        btn_row2.addWidget(btn_backup)

        btn_restore = QPushButton("🔄 Restore Database from Backup...")
        btn_restore.setProperty("class", "DangerBtn")
        btn_restore.clicked.connect(self._on_restore_db)
        btn_row2.addWidget(btn_restore)

        btn_open_backup_folder = QPushButton("📁 Open Backup Folder")
        btn_open_backup_folder.clicked.connect(self._on_open_backup_folder)
        btn_row2.addWidget(btn_open_backup_folder)

        btn_row2.addStretch()
        c2_layout.addLayout(btn_row2)

        main_layout.addWidget(card2)
        main_layout.addStretch()

    def refresh_reports_screen(self) -> None:
        """Reload sessions and database stats."""
        sessions = self.ctx.session_repo.list_sessions(limit=100)

        self.session_combo.blockSignals(True)
        self.session_combo.clear()

        for s in sessions:
            dt = s.start_time[:16].replace("T", " ")
            lbl = f"#{s.id:03d} — {s.test_type} ({s.preset_name}) • {s.completed_items}/{s.total_items} items • {dt}"
            self.session_combo.addItem(lbl, s)

        self.session_combo.blockSignals(False)

        if sessions:
            self._on_session_selection_changed(0)
            self.btn_export_pdf.setEnabled(True)
            self.btn_export_csv.setEnabled(True)
        else:
            self.session_info_lbl.setText("No sessions available to export.")
            self.btn_export_pdf.setEnabled(False)
            self.btn_export_csv.setEnabled(False)

        # Update DB stats
        db_path = self.ctx.db_path
        if db_path.exists():
            size_kb = db_path.stat().st_size / 1024.0
            self.db_stats_lbl.setText(
                f"Active SQLite File: {db_path} ({size_kb:.1f} KB)\nBackup Location: {get_backup_dir()}"
            )

    def _on_session_selection_changed(self, idx: int) -> None:
        s: Optional[Session] = self.session_combo.currentData()
        if s:
            mins = int(s.elapsed_seconds // 60)
            secs = int(s.elapsed_seconds % 60)
            self.session_info_lbl.setText(
                f"Session #{s.id} | Mode: {'Exam' if s.is_exam_mode else 'Practice'} | "
                f"Duration: {mins}m {secs}s | Status: {s.status} | Content: {s.content_set_name or 'Default'}"
            )

    def _on_generate_pdf(self) -> None:
        s: Optional[Session] = self.session_combo.currentData()
        if not s or not s.id:
            return

        default_name = f"ssb_{s.test_type.lower()}_session_{s.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        default_path = get_reports_dir() / default_name

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Report",
            dir=str(default_path),
            filter="PDF Files (*.pdf)",
        )
        if not out_path:
            return

        try:
            responses = self.ctx.session_repo.get_responses(s.id)
            self.ctx.report_service.generate_pdf_report(s, responses, out_path)
            QMessageBox.information(
                self,
                "Report Generated",
                f"PDF session report successfully created at:\n{out_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to generate PDF report: {e}")

    def _on_export_csv(self) -> None:
        s: Optional[Session] = self.session_combo.currentData()
        if not s or not s.id:
            return

        default_name = f"ssb_{s.test_type.lower()}_session_{s.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        default_path = get_reports_dir() / default_name

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV Export",
            dir=str(default_path),
            filter="CSV Files (*.csv)",
        )
        if not out_path:
            return

        try:
            responses = self.ctx.session_repo.get_responses(s.id)
            self.ctx.report_service.export_session_to_csv(s, responses, out_path)
            QMessageBox.information(
                self,
                "CSV Exported",
                f"CSV data file successfully saved to:\n{out_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export CSV: {e}")

    def _on_backup_db(self) -> None:
        backup_name = f"ssb_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        target_path = get_backup_dir() / backup_name
        try:
            self.ctx.report_service.backup_database(self.ctx.db_path, target_path)
            QMessageBox.information(
                self,
                "Backup Successful",
                f"Atomic database backup created at:\n{target_path}",
            )
            self.refresh_reports_screen()
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Database backup failed: {e}")

    def _on_restore_db(self) -> None:
        backup_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database Backup to Restore",
            dir=str(get_backup_dir()),
            filter="Database Backups (*.db);;All Files (*.*)",
        )
        if not backup_file:
            return

        reply = QMessageBox.warning(
            self,
            "Confirm Database Restore",
            "Restoring will overwrite current database records with the selected backup file.\nAre you sure you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.ctx.report_service.restore_database(backup_file, self.ctx.db_path)
                QMessageBox.information(
                    self,
                    "Restore Completed",
                    "Database successfully restored from backup! The application will refresh records.",
                )
                self.refresh_reports_screen()
            except Exception as e:
                QMessageBox.critical(self, "Restore Failed", f"Database restore failed: {e}")

    def _on_open_backup_folder(self) -> None:
        folder = str(get_backup_dir())
        try:
            os.startfile(folder)
        except Exception as e:
            QMessageBox.information(self, "Backup Folder", f"Backup folder path:\n{folder}")
