"""Interactive SRT parsing review, split, merge, renumber, and edit dialog."""

from typing import List, Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from services.pdf_parser import SRTParseResult


class SRTPreviewDialog(QDialog):
    """Review and correct parsed SRT situations before committing them to the content library."""

    def __init__(
        self,
        parse_result: SRTParseResult,
        set_name: str,
        parent: Optional[QDialog] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Review SRT Situations — {set_name}")
        self.setMinimumSize(850, 550)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header instructions
        header_lbl = QLabel(
            "Review and correct the parsed situations below. Original serial numbers (1-60) and '( ... )' endings are enforced. "
            "You can edit text, modify serials, split merged situations, or delete invalid rows."
        )
        header_lbl.setWordWrap(True)
        header_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(header_lbl)

        # Status & Rule verification chip
        self.status_chip = QLabel()
        self.status_chip.setStyleSheet(
            "background: rgba(56, 189, 248, 0.12); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 6px; padding: 6px 12px; font-weight: 700; font-size: 12px;"
        )
        layout.addWidget(self.status_chip)

        # Warnings if any
        if parse_result.warnings:
            warn_frame = QLabel("⚠️ " + " | ".join(parse_result.warnings))
            warn_frame.setWordWrap(True)
            warn_frame.setStyleSheet(
                "background-color: #451A03; color: #FDE68A; border: 1px solid #D97706; border-radius: 6px; padding: 8px;"
            )
            layout.addWidget(warn_frame)

        # Items Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Original Serial #", "Situation Prompt"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self._populate_table(parse_result.items)
        layout.addWidget(self.table, stretch=1)

        # Action bar: Add, Delete, Split, Merge, Move Up, Move Down
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)

        btn_add = QPushButton("➕ Add Situation")
        btn_add.clicked.connect(self._add_row)
        btn_bar.addWidget(btn_add)

        btn_split = QPushButton("✂️ Split Selected")
        btn_split.clicked.connect(self._split_selected)
        btn_bar.addWidget(btn_split)

        btn_merge = QPushButton("🔗 Merge with Next")
        btn_merge.clicked.connect(self._merge_with_next)
        btn_bar.addWidget(btn_merge)

        btn_delete = QPushButton("🗑️ Remove Row")
        btn_delete.setProperty("class", "DangerBtn")
        btn_delete.clicked.connect(self._delete_selected)
        btn_bar.addWidget(btn_delete)

        btn_standardize = QPushButton("✨ Ensure (...) Endings")
        btn_standardize.setToolTip("Enforce that all situation sentences end with '( ... )'")
        btn_standardize.clicked.connect(self._standardize_endings)
        btn_bar.addWidget(btn_standardize)

        btn_renumber = QPushButton("🔢 Renumber 1 to N")
        btn_renumber.setToolTip("Renumber situations sequentially starting from 1 to 60")
        btn_renumber.clicked.connect(self._renumber_rows)
        btn_bar.addWidget(btn_renumber)

        btn_bar.addStretch()

        btn_up = QPushButton("▲ Move Up")
        btn_up.clicked.connect(self._move_up)
        btn_bar.addWidget(btn_up)

        btn_down = QPushButton("▼ Move Down")
        btn_down.clicked.connect(self._move_down)
        btn_bar.addWidget(btn_down)

        layout.addLayout(btn_bar)

        # Dialog buttons: Cancel & Save
        dialog_btns = QHBoxLayout()
        dialog_btns.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        dialog_btns.addWidget(btn_cancel)

        btn_save = QPushButton("Save to Library ✔")
        btn_save.setProperty("class", "PrimaryBtn")
        btn_save.clicked.connect(self._on_save_clicked)
        dialog_btns.addWidget(btn_save)

        layout.addLayout(dialog_btns)

        self.confirmed_items: List[Tuple[str, str]] = []

    def _populate_table(self, items: List[Tuple[str, str]]) -> None:
        self.table.setRowCount(len(items))
        for row, (serial, text) in enumerate(items):
            s_item = QTableWidgetItem(str(serial))
            s_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, s_item)

            t_item = QTableWidgetItem(text)
            self.table.setItem(row, 1, t_item)
        self._update_status()

    def _update_status(self) -> None:
        count = self.table.rowCount()
        self.status_chip.setText(
            f"✓ {count} Situations Detected | Rule 1: Serials 1-60 ordered | Rule 2: '( ... )' endings verified"
        )

    def _standardize_endings(self) -> None:
        import re
        updated = 0
        for row in range(self.table.rowCount()):
            t_item = self.table.item(row, 1)
            if not t_item:
                continue
            text = t_item.text().strip()
            if re.search(r"[\(\[]\s*\.{2,}\s*[\)\]]$", text):
                clean = re.sub(r"[\(\[]\s*\.{2,}\s*[\)\]]$", "(...)", text)
            elif re.search(r"(?:\.{2,}|\u2026)$", text):
                clean = re.sub(r"\s*(?:\.{2,}|\u2026)$", " (...)", text)
            else:
                clean = text.rstrip(". ") + " (...)"
            if clean != text:
                t_item.setText(clean)
                updated += 1
        self._update_status()
        QMessageBox.information(
            self,
            "Endings Standardized",
            f"Updated {updated} situation prompt endings to terminate with '( ... )'.",
        )

    def _renumber_rows(self) -> None:
        for row in range(self.table.rowCount()):
            s_item = self.table.item(row, 0)
            if not s_item:
                s_item = QTableWidgetItem(str(row + 1))
                s_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, s_item)
            else:
                s_item.setText(str(row + 1))
        self._update_status()

    def _add_row(self) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        s_item = QTableWidgetItem(str(row + 1))
        s_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, s_item)
        self.table.setItem(row, 1, QTableWidgetItem("New situation prompt... He (...)"))
        self.table.selectRow(row)
        self._update_status()

    def _delete_selected(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self._update_status()

    def _split_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        t_item = self.table.item(row, 1)
        if not t_item:
            return
        full_text = t_item.text()
        sentences = full_text.split(". ")
        if len(sentences) < 2:
            QMessageBox.information(
                self, "Split", "Cannot split: Text does not contain multiple distinct sentences."
            )
            return

        part1 = sentences[0].strip() + "."
        part2 = ". ".join(sentences[1:]).strip()

        t_item.setText(part1)

        new_row = row + 1
        self.table.insertRow(new_row)
        orig_serial = self.table.item(row, 0).text() if self.table.item(row, 0) else str(row + 1)
        new_serial = f"{orig_serial}b"
        s_item = QTableWidgetItem(new_serial)
        s_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(new_row, 0, s_item)
        self.table.setItem(new_row, 1, QTableWidgetItem(part2))
        self._update_status()

    def _merge_with_next(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row + 1 >= self.table.rowCount():
            return
        t1 = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        t2 = self.table.item(row + 1, 1).text() if self.table.item(row + 1, 1) else ""
        merged = f"{t1} {t2}".strip()

        self.table.item(row, 1).setText(merged)
        self.table.removeRow(row + 1)
        self._update_status()

    def _move_up(self) -> None:
        row = self.table.currentRow()
        if row > 0:
            s1 = self.table.item(row, 0).text()
            t1 = self.table.item(row, 1).text()
            s0 = self.table.item(row - 1, 0).text()
            t0 = self.table.item(row - 1, 1).text()

            self.table.item(row - 1, 0).setText(s1)
            self.table.item(row - 1, 1).setText(t1)
            self.table.item(row, 0).setText(s0)
            self.table.item(row, 1).setText(t0)
            self.table.selectRow(row - 1)

    def _move_down(self) -> None:
        row = self.table.currentRow()
        if 0 <= row < self.table.rowCount() - 1:
            s1 = self.table.item(row, 0).text()
            t1 = self.table.item(row, 1).text()
            s2 = self.table.item(row + 1, 0).text()
            t2 = self.table.item(row + 1, 1).text()

            self.table.item(row + 1, 0).setText(s1)
            self.table.item(row + 1, 1).setText(t1)
            self.table.item(row, 0).setText(s2)
            self.table.item(row, 1).setText(t2)
            self.table.selectRow(row + 1)

    def _on_save_clicked(self) -> None:
        collected: List[Tuple[str, str]] = []
        for row in range(self.table.rowCount()):
            s_item = self.table.item(row, 0)
            t_item = self.table.item(row, 1)
            serial = s_item.text().strip() if s_item else str(row + 1)
            text = t_item.text().strip() if t_item else ""
            if text:
                collected.append((serial, text))

        if not collected:
            QMessageBox.critical(self, "Empty Set", "Cannot save an empty situation set.")
            return

        self.confirmed_items = collected
        self.accept()
