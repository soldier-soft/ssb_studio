"""Content Library manager for TAT image sets, WAT word lists, and SRT situation decks."""

import logging
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.app_context import AppContext
from database.models import ContentSet
from ui.screens.srt_preview_dialog import SRTPreviewDialog

logger = logging.getLogger(__name__)


class WATImportDialog(QDialog):
    """Word preview and editor dialog before saving a WAT set."""

    def __init__(self, raw_words: List[str], default_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Review WAT Word List — {default_name}")
        self.setMinimumSize(600, 480)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info = QLabel(
            "Review and edit the extracted words below (one word per line). "
            "Order is preserved. Empty lines are ignored."
        )
        info.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(info)

        self.editor = QPlainTextEdit()
        self.editor.setPlainText("\n".join(raw_words))
        self.editor.textChanged.connect(self._update_count)
        layout.addWidget(self.editor, stretch=1)

        self.count_lbl = QLabel(f"Total Words: {len(raw_words)}")
        self.count_lbl.setStyleSheet("color: #38BDF8; font-weight: 700;")
        layout.addWidget(self.count_lbl)

        btn_h = QHBoxLayout()
        btn_h.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_h.addWidget(btn_cancel)

        btn_save = QPushButton("Save Word Set ✔")
        btn_save.setProperty("class", "PrimaryBtn")
        btn_save.clicked.connect(self._on_save)
        btn_h.addWidget(btn_save)

        layout.addLayout(btn_h)
        self.confirmed_words: List[str] = []

    def _update_count(self) -> None:
        lines = [line.strip().upper() for line in self.editor.toPlainText().splitlines() if line.strip()]
        self.count_lbl.setText(f"Total Words: {len(lines)}")

    def _on_save(self) -> None:
        lines = [line.strip().upper() for line in self.editor.toPlainText().splitlines() if line.strip()]
        if not lines:
            QMessageBox.critical(self, "Empty", "Word list cannot be empty.")
            return
        self.confirmed_words = lines
        self.accept()


class LibraryScreen(QWidget):
    """Central repository management for TAT image series, WAT word lists, and SRT banks."""

    content_updated = Signal()

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.ctx = ctx

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(16)

        # Header
        header_h = QHBoxLayout()
        text_v = QVBoxLayout()
        text_v.setSpacing(2)

        title = QLabel("Content Library")
        title.setProperty("class", "H1")
        subtitle = QLabel("Import, organize, and inspect practice material for TAT, WAT, and SRT tests.")
        subtitle.setProperty("class", "Subtitle")

        text_v.addWidget(title)
        text_v.addWidget(subtitle)
        header_h.addLayout(text_v, stretch=1)

        btn_load_samples = QPushButton("📦 Load Default Sample Content")
        btn_load_samples.setToolTip("Reload bundled sample WAT words, SRT situations, and TAT pictures.")
        btn_load_samples.clicked.connect(self._on_reload_samples)
        header_h.addWidget(btn_load_samples)

        main_layout.addLayout(header_h)

        # Tabs for TAT, WAT, SRT
        self.tabs = QTabWidget()

        self.tat_tab = QWidget()
        self._build_tat_tab()
        self.tabs.addTab(self.tat_tab, "🖼️  TAT Image Sets")

        self.wat_tab = QWidget()
        self._build_wat_tab()
        self.tabs.addTab(self.wat_tab, "⚡  WAT Word Lists")

        self.srt_tab = QWidget()
        self._build_srt_tab()
        self.tabs.addTab(self.srt_tab, "🎯  SRT Question Banks")

        main_layout.addWidget(self.tabs, stretch=1)

    def select_tab(self, test_type: str) -> None:
        ttype = test_type.upper()
        if ttype == "TAT":
            self.tabs.setCurrentIndex(0)
        elif ttype == "WAT":
            self.tabs.setCurrentIndex(1)
        elif ttype == "SRT":
            self.tabs.setCurrentIndex(2)

    # -------------------------------------------------------------
    # TAT TAB
    # -------------------------------------------------------------
    def _build_tat_tab(self) -> None:
        layout = QVBoxLayout(self.tat_tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Action bar
        act_h = QHBoxLayout()
        lbl = QLabel("Manage TAT Image Decks")
        lbl.setProperty("class", "H3")
        act_h.addWidget(lbl, stretch=1)

        btn_import_folder = QPushButton("📁 Import Image Folder...")
        btn_import_folder.setProperty("class", "PrimaryBtn")
        btn_import_folder.clicked.connect(self._on_import_tat_folder)
        act_h.addWidget(btn_import_folder)

        btn_import_files = QPushButton("🖼️ Import Image Files...")
        btn_import_files.clicked.connect(self._on_import_tat_files)
        act_h.addWidget(btn_import_files)

        btn_delete_tat = QPushButton("🗑️ Delete Set")
        btn_delete_tat.setProperty("class", "DangerBtn")
        btn_delete_tat.clicked.connect(lambda: self._on_delete_set("TAT", self.tat_table))
        act_h.addWidget(btn_delete_tat)

        layout.addLayout(act_h)

        # Table of TAT Content Sets
        self.tat_table = QTableWidget()
        self.tat_table.setColumnCount(4)
        self.tat_table.setHorizontalHeaderLabels(["ID", "Set Name", "Pictures in Deck", "Date Created"])
        self.tat_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tat_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tat_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tat_table.itemSelectionChanged.connect(self._on_tat_set_selected)
        layout.addWidget(self.tat_table, stretch=2)

        # Items Preview List
        preview_lbl = QLabel("Images in Selected Deck (Naturally Ordered):")
        preview_lbl.setProperty("class", "StatLabel")
        layout.addWidget(preview_lbl)

        self.tat_items_list = QListWidget()
        layout.addWidget(self.tat_items_list, stretch=1)

    def _on_import_tat_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select TAT Image Folder")
        if not folder:
            return

        valid_paths, dup_paths = self.ctx.import_manager.scan_tat_images([Path(folder)])
        if not valid_paths:
            QMessageBox.warning(
                self,
                "No Images Found",
                "No supported image files (JPG, PNG, BMP, WEBP) found in the selected folder.",
            )
            return

        dup_msg = f" ({len(dup_paths)} duplicate images detected and excluded)" if dup_paths else ""

        name, ok = QInputDialog.getText(
            self,
            "Create TAT Set",
            f"Found {len(valid_paths)} pictures{dup_msg}.\nEnter a name for this TAT deck:",
            text=Path(folder).name,
        )
        if ok and name.strip():
            set_id = self.ctx.import_manager.import_tat_set(
                name=name.strip(),
                image_paths=valid_paths,
                source_label=str(folder),
            )
            QMessageBox.information(
                self,
                "TAT Set Created",
                f"Successfully imported {len(valid_paths)} images into deck '{name}'.",
            )
            self.refresh_library()

    def _on_import_tat_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select TAT Image Files",
            filter="Image Files (*.jpg *.jpeg *.png *.bmp *.webp)",
        )
        if not files:
            return

        valid_paths, dup_paths = self.ctx.import_manager.scan_tat_images([Path(f) for f in files])
        if not valid_paths:
            return

        name, ok = QInputDialog.getText(
            self,
            "Create TAT Set",
            f"Importing {len(valid_paths)} pictures.\nEnter a name for this TAT deck:",
            text="Custom TAT Series",
        )
        if ok and name.strip():
            self.ctx.import_manager.import_tat_set(
                name=name.strip(),
                image_paths=valid_paths,
                source_label="Manual file selection",
            )
            self.refresh_library()

    def _on_tat_set_selected(self) -> None:
        row = self.tat_table.currentRow()
        self.tat_items_list.clear()
        if row >= 0:
            set_id_item = self.tat_table.item(row, 0)
            if set_id_item:
                set_id = int(set_id_item.text())
                items = self.ctx.content_repo.get_tat_items(set_id)
                for it in items:
                    self.tat_items_list.addItem(f"#{it.item_order:02d} — {it.original_filename}")

    # -------------------------------------------------------------
    # WAT TAB
    # -------------------------------------------------------------
    def _build_wat_tab(self) -> None:
        layout = QVBoxLayout(self.wat_tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        act_h = QHBoxLayout()
        lbl = QLabel("Manage WAT Word Lists")
        lbl.setProperty("class", "H3")
        act_h.addWidget(lbl, stretch=1)

        btn_import_wat = QPushButton("📄 Import Words (.txt / .pdf)...")
        btn_import_wat.setProperty("class", "PrimaryBtn")
        btn_import_wat.clicked.connect(self._on_import_wat_file)
        act_h.addWidget(btn_import_wat)

        btn_delete_wat = QPushButton("🗑️ Delete Set")
        btn_delete_wat.setProperty("class", "DangerBtn")
        btn_delete_wat.clicked.connect(lambda: self._on_delete_set("WAT", self.wat_table))
        act_h.addWidget(btn_delete_wat)

        layout.addLayout(act_h)

        self.wat_table = QTableWidget()
        self.wat_table.setColumnCount(4)
        self.wat_table.setHorizontalHeaderLabels(["ID", "Set Name", "Word Count", "Date Created"])
        self.wat_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.wat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.wat_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.wat_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.wat_table.itemSelectionChanged.connect(self._on_wat_set_selected)
        layout.addWidget(self.wat_table, stretch=2)

        preview_lbl = QLabel("Words in Selected Set (Source Order):")
        preview_lbl.setProperty("class", "StatLabel")
        layout.addWidget(preview_lbl)

        self.wat_items_list = QListWidget()
        layout.addWidget(self.wat_items_list, stretch=1)

    def _on_import_wat_file(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select WAT File",
            filter="Supported Files (*.txt *.pdf);;Text Files (*.txt);;PDF Files (*.pdf)",
        )
        if not filepath:
            return

        try:
            res = self.ctx.import_manager.preview_wat_file(filepath)
            if not res.words:
                QMessageBox.warning(self, "No Words", "No valid words could be extracted from this file.")
                return

            dialog = WATImportDialog(res.words, Path(filepath).stem, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                name, ok = QInputDialog.getText(
                    self,
                    "Name WAT Set",
                    "Enter a name for this WAT word set:",
                    text=Path(filepath).stem,
                )
                if ok and name.strip():
                    self.ctx.import_manager.import_wat_set(
                        name=name.strip(),
                        words=dialog.confirmed_words,
                        source_file=str(filepath),
                    )
                    QMessageBox.information(
                        self,
                        "WAT Set Saved",
                        f"Saved {len(dialog.confirmed_words)} words to '{name}'.",
                    )
                    self.refresh_library()
        except Exception as ex:
            QMessageBox.critical(self, "Import Error", f"Failed to import WAT file: {ex}")

    def _on_wat_set_selected(self) -> None:
        row = self.wat_table.currentRow()
        self.wat_items_list.clear()
        if row >= 0:
            set_id_item = self.wat_table.item(row, 0)
            if set_id_item:
                set_id = int(set_id_item.text())
                items = self.ctx.content_repo.get_wat_items(set_id)
                for it in items:
                    self.wat_items_list.addItem(f"#{it.item_order:02d} — {it.word}")

    # -------------------------------------------------------------
    # SRT TAB
    # -------------------------------------------------------------
    def _build_srt_tab(self) -> None:
        layout = QVBoxLayout(self.srt_tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        act_h = QHBoxLayout()
        lbl = QLabel("Manage SRT Question Banks")
        lbl.setProperty("class", "H3")
        act_h.addWidget(lbl, stretch=1)

        btn_import_srt = QPushButton("📄 Import SRT (.pdf / .txt)...")
        btn_import_srt.setProperty("class", "PrimaryBtn")
        btn_import_srt.clicked.connect(self._on_import_srt_file)
        act_h.addWidget(btn_import_srt)

        btn_delete_srt = QPushButton("🗑️ Delete Bank")
        btn_delete_srt.setProperty("class", "DangerBtn")
        btn_delete_srt.clicked.connect(lambda: self._on_delete_set("SRT", self.srt_table))
        act_h.addWidget(btn_delete_srt)

        layout.addLayout(act_h)

        self.srt_table = QTableWidget()
        self.srt_table.setColumnCount(4)
        self.srt_table.setHorizontalHeaderLabels(["ID", "Bank Name", "Situations Count", "Date Created"])
        self.srt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.srt_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.srt_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.srt_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.srt_table.itemSelectionChanged.connect(self._on_srt_set_selected)
        layout.addWidget(self.srt_table, stretch=2)

        preview_lbl = QLabel("Situations in Selected Bank (Preserved Original Serials):")
        preview_lbl.setProperty("class", "StatLabel")
        layout.addWidget(preview_lbl)

        self.srt_items_list = QListWidget()
        layout.addWidget(self.srt_items_list, stretch=1)

    def _on_import_srt_file(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select SRT Document",
            filter="Supported Files (*.pdf *.txt);;PDF Files (*.pdf);;Text Files (*.txt)",
        )
        if not filepath:
            return

        try:
            res = self.ctx.import_manager.preview_srt_file(filepath)
            if not res.items:
                QMessageBox.warning(
                    self,
                    "No Situations Extracted",
                    "Could not extract standard numbered situations from this document. "
                    + ("\nWarnings: " + " ".join(res.warnings) if res.warnings else ""),
                )
                return

            dialog = SRTPreviewDialog(res, Path(filepath).stem, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                name, ok = QInputDialog.getText(
                    self,
                    "Name SRT Bank",
                    "Enter a name for this SRT question bank:",
                    text=Path(filepath).stem,
                )
                if ok and name.strip():
                    self.ctx.import_manager.import_srt_set(
                        name=name.strip(),
                        items=dialog.confirmed_items,
                        source_file=str(filepath),
                    )
                    QMessageBox.information(
                        self,
                        "SRT Bank Saved",
                        f"Saved {len(dialog.confirmed_items)} situations with original serials to '{name}'.",
                    )
                    self.refresh_library()
        except Exception as ex:
            QMessageBox.critical(self, "Import Error", f"Failed to import SRT file: {ex}")

    def _on_srt_set_selected(self) -> None:
        row = self.srt_table.currentRow()
        self.srt_items_list.clear()
        if row >= 0:
            set_id_item = self.srt_table.item(row, 0)
            if set_id_item:
                set_id = int(set_id_item.text())
                items = self.ctx.content_repo.get_srt_items(set_id)
                for it in items:
                    self.srt_items_list.addItem(f"Q#{it.original_serial}: {it.situation_text[:120]}...")

    # -------------------------------------------------------------
    # Shared Methods
    # -------------------------------------------------------------
    def refresh_library(self) -> None:
        """Reload all ContentSets from SQLite into the tables."""
        self._load_sets_into_table("TAT", self.tat_table)
        self._load_sets_into_table("WAT", self.wat_table)
        self._load_sets_into_table("SRT", self.srt_table)
        self.content_updated.emit()

    def _load_sets_into_table(self, test_type: str, table: QTableWidget) -> None:
        sets = self.ctx.content_repo.list_content_sets(test_type)
        table.setRowCount(len(sets))
        for row, s in enumerate(sets):
            table.setItem(row, 0, QTableWidgetItem(str(s.id)))
            table.setItem(row, 1, QTableWidgetItem(s.name))
            cnt_item = QTableWidgetItem(str(s.item_count))
            cnt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 2, cnt_item)
            dt_str = s.created_at[:10]
            table.setItem(row, 3, QTableWidgetItem(dt_str))

    def _on_delete_set(self, test_type: str, table: QTableWidget) -> None:
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection", "Please select a set to delete.")
            return

        set_id = int(table.item(row, 0).text())
        set_name = table.item(row, 1).text()

        reply = QMessageBox.question(
            self,
            "Delete Content Set",
            f"Are you sure you want to delete {test_type} set '{set_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.ctx.content_repo.delete_content_set(set_id)
            self.refresh_library()

    def _on_reload_samples(self) -> None:
        seeded = self.ctx.seed_sample_content_if_needed(force=True)
        self.refresh_library()
        self.content_updated.emit()
        msg = (
            f"Sample Content Loaded Successfully!\n\n"
            f"• WAT Words: {seeded.get('WAT', 0)}\n"
            f"• SRT Situations: {seeded.get('SRT', 0)}\n"
            f"• TAT Pictures: {seeded.get('TAT', 0)}"
        )
        QMessageBox.information(self, "Sample Content Loaded", msg)
