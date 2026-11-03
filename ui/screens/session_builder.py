"""Session Builder screen for customizing test presets, selecting content sets, and validating runs."""

from typing import Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.app_context import AppContext
from database.models import ContentSet, Preset
from services.session_service import SessionService


class SessionBuilderScreen(QWidget):
    """Configures and validates test runs: preset selection, content library, durations, and exam/practice mode."""

    session_ready_to_launch = Signal(Preset, ContentSet, int)  # (preset, content_set, item_count)
    navigate_to_library = Signal(str)  # test_type

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.ctx = ctx

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(30, 24, 30, 24)
        self.main_layout.setSpacing(20)

        self._build_header()
        self._build_test_type_selector()
        self._build_preset_management()
        self._build_content_selector()
        self._build_timing_and_rules()
        self._build_duration_and_launch_bar()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _build_header(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(4)
        title = QLabel("Test Session Builder")
        title.setProperty("class", "H1")
        subtitle = QLabel("Configure examination rules, select authentic content sets, adjust timings, and preview estimated duration.")
        subtitle.setProperty("class", "Subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.main_layout.addLayout(layout)

    def _build_test_type_selector(self) -> None:
        frame = QFrame()
        frame.setProperty("class", "CardFrame")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        lbl = QLabel("1. SELECT TEST TYPE")
        lbl.setProperty("class", "StatLabel")
        layout.addWidget(lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        self.btn_tat = QRadioButton("🖼️  Thematic Apperception Test (TAT)")
        self.btn_wat = QRadioButton("⚡  Word Association Test (WAT)")
        self.btn_srt = QRadioButton("🎯  Situation Reaction Test (SRT)")

        self.btn_tat.setChecked(True)
        self.btn_tat.toggled.connect(self._on_test_type_changed)
        self.btn_wat.toggled.connect(self._on_test_type_changed)
        self.btn_srt.toggled.connect(self._on_test_type_changed)

        btn_row.addWidget(self.btn_tat)
        btn_row.addWidget(self.btn_wat)
        btn_row.addWidget(self.btn_srt)
        btn_row.addStretch()

        layout.addLayout(btn_row)
        self.main_layout.addWidget(frame)

    def _build_preset_management(self) -> None:
        frame = QFrame()
        frame.setProperty("class", "CardFrame")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        lbl = QLabel("2. PRESET TEMPLATE")
        lbl.setProperty("class", "StatLabel")
        layout.addWidget(lbl)

        h = QHBoxLayout()
        h.setSpacing(10)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(320)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        h.addWidget(self.preset_combo)

        self.btn_new_preset = QPushButton("Save as New Preset")
        self.btn_new_preset.clicked.connect(self._on_save_new_preset)
        h.addWidget(self.btn_new_preset)

        self.btn_dup_preset = QPushButton("Duplicate")
        self.btn_dup_preset.clicked.connect(self._on_duplicate_preset)
        h.addWidget(self.btn_dup_preset)

        self.btn_del_preset = QPushButton("Delete")
        self.btn_del_preset.setProperty("class", "DangerBtn")
        self.btn_del_preset.clicked.connect(self._on_delete_preset)
        h.addWidget(self.btn_del_preset)

        h.addStretch()
        layout.addLayout(h)
        self.main_layout.addWidget(frame)

    def _build_content_selector(self) -> None:
        frame = QFrame()
        frame.setProperty("class", "CardFrame")
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        lbl = QLabel("3. CONTENT DECK / SOURCE BANK")
        lbl.setProperty("class", "StatLabel")
        layout.addWidget(lbl)

        h = QHBoxLayout()
        h.setSpacing(10)

        self.content_combo = QComboBox()
        self.content_combo.setMinimumWidth(320)
        self.content_combo.currentIndexChanged.connect(self._on_content_selected)
        h.addWidget(self.content_combo)

        self.content_info_lbl = QLabel("(0 items available)")
        self.content_info_lbl.setStyleSheet("color: #94A3B8; font-weight: 500;")
        h.addWidget(self.content_info_lbl)

        btn_import = QPushButton("Import / Manage in Library →")
        btn_import.clicked.connect(lambda: self.navigate_to_library.emit(self.current_test_type))
        h.addWidget(btn_import)

        h.addStretch()
        layout.addLayout(h)

        self.content_warning_lbl = QLabel("")
        self.content_warning_lbl.setStyleSheet("color: #EF4444; font-weight: 600; font-size: 12px;")
        layout.addWidget(self.content_warning_lbl)

        self.main_layout.addWidget(frame)

    def _build_timing_and_rules(self) -> None:
        frame = QFrame()
        frame.setProperty("class", "CardFrame")
        layout = QVBoxLayout(frame)
        layout.setSpacing(16)

        lbl = QLabel("4. TIMINGS & EXAMINATION RULES")
        lbl.setProperty("class", "StatLabel")
        layout.addWidget(lbl)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(12)

        # Mode: Exam vs Practice
        grid.addWidget(QLabel("Testing Mode:"), 0, 0)
        mode_h = QHBoxLayout()
        self.radio_exam = QRadioButton("Exam Mode (Strict no pause, no skip, full immersion)")
        self.radio_practice = QRadioButton("Practice Mode (Pause, review, manual next enabled)")
        self.radio_exam.setChecked(True)
        mode_h.addWidget(self.radio_exam)
        mode_h.addWidget(self.radio_practice)
        grid.addLayout(mode_h, 0, 1)

        # Item count
        grid.addWidget(QLabel("Number of Items to Practice:"), 1, 0)
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 500)
        self.spin_count.setValue(12)
        self.spin_count.valueChanged.connect(self._recalculate_estimate)
        grid.addWidget(self.spin_count, 1, 1)

        # TAT Viewing duration
        self.lbl_view_dur = QLabel("Image Viewing Duration (seconds):")
        grid.addWidget(self.lbl_view_dur, 2, 0)
        self.spin_view_dur = QDoubleSpinBox()
        self.spin_view_dur.setRange(0.0, 300.0)
        self.spin_view_dur.setValue(30.0)
        self.spin_view_dur.setSingleStep(5.0)
        self.spin_view_dur.valueChanged.connect(self._recalculate_estimate)
        grid.addWidget(self.spin_view_dur, 2, 1)

        # Writing / reaction duration
        self.lbl_write_dur = QLabel("Response Writing Duration (seconds):")
        grid.addWidget(self.lbl_write_dur, 3, 0)
        self.spin_write_dur = QDoubleSpinBox()
        self.spin_write_dur.setRange(5.0, 600.0)
        self.spin_write_dur.setValue(270.0)
        self.spin_write_dur.setSingleStep(5.0)
        self.spin_write_dur.valueChanged.connect(self._recalculate_estimate)
        grid.addWidget(self.spin_write_dur, 3, 1)

        # Pre-test countdown
        grid.addWidget(QLabel("Pre-Start Countdown (seconds):"), 4, 0)
        self.spin_countdown = QSpinBox()
        self.spin_countdown.setRange(0, 10)
        self.spin_countdown.setValue(3)
        self.spin_countdown.valueChanged.connect(self._recalculate_estimate)
        grid.addWidget(self.spin_countdown, 4, 1)

        # Checkboxes: Randomize, Repeat, Sound
        chk_layout = QHBoxLayout()
        self.chk_randomize = QCheckBox("Shuffle / Randomize Order")
        self.chk_repeat = QCheckBox("Allow Repeat if Deck < Requested Items")
        self.chk_sound = QCheckBox("Audio Alerts on Phase Transitions")
        self.chk_sound.setChecked(True)

        chk_layout.addWidget(self.chk_randomize)
        chk_layout.addWidget(self.chk_repeat)
        chk_layout.addWidget(self.chk_sound)
        grid.addLayout(chk_layout, 5, 0, 1, 2)

        layout.addLayout(grid)
        self.main_layout.addWidget(frame)

    def _build_duration_and_launch_bar(self) -> None:
        frame = QFrame()
        frame.setStyleSheet(
            "background-color: #0F172A; border: 1px solid #1E3A8A; border-radius: 12px; padding: 16px;"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)

        dur_v = QVBoxLayout()
        dur_v.setSpacing(2)
        dur_lbl = QLabel("ESTIMATED TOTAL TEST DURATION")
        dur_lbl.setProperty("class", "StatLabel")
        self.est_duration_display = QLabel("00m 00s")
        self.est_duration_display.setStyleSheet("font-size: 24px; font-weight: 800; color: #38BDF8;")
        dur_v.addWidget(dur_lbl)
        dur_v.addWidget(self.est_duration_display)
        layout.addLayout(dur_v, stretch=1)

        self.btn_start = QPushButton("START TEST SESSION ▶")
        self.btn_start.setProperty("class", "PrimaryBtn")
        self.btn_start.setStyleSheet(
            "font-size: 15px; font-weight: 700; padding: 12px 28px; background-color: #2563EB; border-radius: 8px;"
        )
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.btn_start)

        self.main_layout.addWidget(frame)

    @property
    def current_test_type(self) -> str:
        if self.btn_wat.isChecked():
            return "WAT"
        if self.btn_srt.isChecked():
            return "SRT"
        return "TAT"

    def refresh_builder(self, target_type: Optional[str] = None, target_preset_name: Optional[str] = None) -> None:
        """Reload presets and content sets from SQLite for current selection."""
        if target_type:
            if target_type == "TAT":
                self.btn_tat.setChecked(True)
            elif target_type == "WAT":
                self.btn_wat.setChecked(True)
            elif target_type == "SRT":
                self.btn_srt.setChecked(True)

        self._populate_presets(target_preset_name)
        self._populate_content_sets()
        self._update_visibility_by_type()
        self._recalculate_estimate()

    def _on_test_type_changed(self) -> None:
        self._populate_presets()
        self._populate_content_sets()
        self._update_visibility_by_type()
        self._recalculate_estimate()

    def _update_visibility_by_type(self) -> None:
        ttype = self.current_test_type
        if ttype == "TAT":
            self.lbl_view_dur.setVisible(True)
            self.spin_view_dur.setVisible(True)
            self.lbl_write_dur.setText("Story Writing Duration (seconds):")
        elif ttype == "WAT":
            self.lbl_view_dur.setVisible(False)
            self.spin_view_dur.setVisible(False)
            self.lbl_write_dur.setText("Word Slide Duration (seconds):")
        elif ttype == "SRT":
            self.lbl_view_dur.setVisible(False)
            self.spin_view_dur.setVisible(False)
            self.lbl_write_dur.setText("Situation Slide Duration (seconds):")

    def _populate_presets(self, select_name: Optional[str] = None) -> None:
        ttype = self.current_test_type
        presets = self.ctx.preset_repo.list_presets(ttype)

        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        target_idx = 0

        for idx, p in enumerate(presets):
            self.preset_combo.addItem(p.name, p)
            if select_name and p.name == select_name:
                target_idx = idx

        self.preset_combo.blockSignals(False)
        if presets:
            self.preset_combo.setCurrentIndex(target_idx)
            self._load_preset_to_form(presets[target_idx])

    def _load_preset_to_form(self, p: Preset) -> None:
        self.spin_count.setValue(p.item_count)
        self.spin_view_dur.setValue(p.view_duration)
        self.spin_write_dur.setValue(p.write_duration)
        self.spin_countdown.setValue(p.countdown_seconds)
        self.chk_randomize.setChecked(p.randomize)
        self.chk_repeat.setChecked(p.repeat)
        self.chk_sound.setChecked(p.sound_enabled)
        if p.exam_mode:
            self.radio_exam.setChecked(True)
        else:
            self.radio_practice.setChecked(True)

        self.btn_del_preset.setEnabled(not p.is_builtin)
        self._recalculate_estimate()

    def _on_preset_selected(self, index: int) -> None:
        p = self.preset_combo.currentData()
        if p:
            self._load_preset_to_form(p)

    def _populate_content_sets(self) -> None:
        ttype = self.current_test_type
        sets = self.ctx.content_repo.list_content_sets(ttype)

        self.content_combo.blockSignals(True)
        self.content_combo.clear()

        for s in sets:
            self.content_combo.addItem(f"{s.name} ({s.item_count} items)", s)

        self.content_combo.blockSignals(False)

        if not sets:
            self.content_info_lbl.setText("(No content available in library)")
            self.content_warning_lbl.setText(
                f"⚠️ No {ttype} content found. Please import content into the library before starting."
            )
            self.btn_start.setEnabled(False)
        else:
            self.content_warning_lbl.setText("")
            self.btn_start.setEnabled(True)
            self._on_content_selected(0)

    def _on_content_selected(self, index: int) -> None:
        content_set: Optional[ContentSet] = self.content_combo.currentData()
        if content_set:
            self.content_info_lbl.setText(f"({content_set.item_count} items available in deck)")
            # Suggest count if user hasn't touched it
            if self.spin_count.value() > content_set.item_count and content_set.item_count > 0:
                self.content_warning_lbl.setText(
                    f"Notice: Requested items ({self.spin_count.value()}) exceeds deck size ({content_set.item_count}). Enable 'Allow Repeat' or adjust count."
                )
            else:
                self.content_warning_lbl.setText("")
        self._recalculate_estimate()

    def _recalculate_estimate(self) -> None:
        total_sec = SessionService.calculate_estimated_duration(
            test_type=self.current_test_type,
            item_count=self.spin_count.value(),
            view_duration=self.spin_view_dur.value() if self.current_test_type == "TAT" else 0.0,
            write_duration=self.spin_write_dur.value(),
            countdown_seconds=self.spin_countdown.value(),
        )
        mins = int(total_sec // 60)
        secs = int(total_sec % 60)
        self.est_duration_display.setText(f"{mins}m {secs:02d}s")

    def _on_save_new_preset(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(
            self, "Save Preset", "Enter a name for the custom preset:"
        )
        if ok and name.strip():
            p = Preset(
                name=name.strip(),
                test_type=self.current_test_type,
                view_duration=self.spin_view_dur.value() if self.current_test_type == "TAT" else 0.0,
                write_duration=self.spin_write_dur.value(),
                item_count=self.spin_count.value(),
                randomize=self.chk_randomize.isChecked(),
                repeat=self.chk_repeat.isChecked(),
                countdown_seconds=self.spin_countdown.value(),
                sound_enabled=self.chk_sound.isChecked(),
                exam_mode=self.radio_exam.isChecked(),
                is_builtin=False,
            )
            p_id = self.ctx.preset_repo.create_preset(p)
            self._populate_presets(select_name=name.strip())

    def _on_duplicate_preset(self) -> None:
        p: Optional[Preset] = self.preset_combo.currentData()
        if not p or p.id is None:
            return
        new_name = f"{p.name} (Custom Copy)"
        self.ctx.preset_repo.duplicate_preset(p.id, new_name)
        self._populate_presets(select_name=new_name)

    def _on_delete_preset(self) -> None:
        p: Optional[Preset] = self.preset_combo.currentData()
        if not p or p.is_builtin or p.id is None:
            return

        reply = QMessageBox.question(
            self,
            "Delete Preset",
            f"Are you sure you want to delete preset '{p.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.ctx.preset_repo.delete_preset(p.id)
            self._populate_presets()

    def _on_start_clicked(self) -> None:
        content_set: Optional[ContentSet] = self.content_combo.currentData()
        if not content_set or content_set.item_count <= 0:
            QMessageBox.critical(
                self,
                "No Content Available",
                f"Cannot start session: Selected content set is empty. Please import valid {self.current_test_type} items into the library first.",
            )
            return

        # Build current configured Preset object
        active_preset = Preset(
            name=self.preset_combo.currentText(),
            test_type=self.current_test_type,
            view_duration=self.spin_view_dur.value() if self.current_test_type == "TAT" else 0.0,
            write_duration=self.spin_write_dur.value(),
            item_count=self.spin_count.value(),
            randomize=self.chk_randomize.isChecked(),
            repeat=self.chk_repeat.isChecked(),
            countdown_seconds=self.spin_countdown.value(),
            sound_enabled=self.chk_sound.isChecked(),
            exam_mode=self.radio_exam.isChecked(),
        )

        self.session_ready_to_launch.emit(active_preset, content_set, self.spin_count.value())
