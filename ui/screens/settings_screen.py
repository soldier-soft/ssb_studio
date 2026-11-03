"""Application settings screen for theme, timings, OCR detection, audio cues, and storage paths."""

import os
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.app_context import AppContext
from app.config import (
    get_backup_dir,
    get_database_path,
    get_library_asset_dir,
    get_reports_dir,
    get_user_data_dir,
)


class SettingsScreen(QWidget):
    """Manages application-wide preferences, theme, font size, audio cues, OCR paths, and storage directories."""

    theme_change_requested = Signal(str)
    font_size_changed = Signal(int)

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
        self._build_appearance_section()
        self._build_examination_defaults_section()
        self._build_sound_section()
        self._build_ocr_section()
        self._build_storage_info_section()
        self._build_about_section()
        self._build_footer_actions()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _build_header(self) -> None:
        header_v = QVBoxLayout()
        header_v.setSpacing(2)
        title = QLabel("Settings & Preferences")
        title.setProperty("class", "H1")
        sub = QLabel("Customize appearance, default practice presets, optical character recognition paths, and storage directories.")
        sub.setProperty("class", "Subtitle")
        header_v.addWidget(title)
        header_v.addWidget(sub)
        self.main_layout.addLayout(header_v)

    def _build_appearance_section(self) -> None:
        card = QFrame()
        card.setProperty("class", "CardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        lbl = QLabel("APPEARANCE & VISUAL THEME")
        lbl.setProperty("class", "StatLabel")
        layout.addWidget(lbl)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Theme selector
        grid.addWidget(QLabel("Color Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark Navy Theme (Default)", "dark")
        self.theme_combo.addItem("Clean Light Slate Theme", "light")
        current_theme = self.ctx.get_setting("theme", "dark")
        idx = 0 if current_theme == "dark" else 1
        self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        grid.addWidget(self.theme_combo, 0, 1)

        # Font size adjuster
        grid.addWidget(QLabel("Interface Font Size (pt):"), 1, 0)
        self.spin_font = QSpinBox()
        self.spin_font.setRange(10, 20)
        self.spin_font.setValue(int(self.ctx.get_setting("font_size", 13)))
        self.spin_font.valueChanged.connect(self._on_font_size_changed)
        grid.addWidget(self.spin_font, 1, 1)

        layout.addLayout(grid)
        self.main_layout.addWidget(card)

    def _build_examination_defaults_section(self) -> None:
        card = QFrame()
        card.setProperty("class", "CardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        lbl = QLabel("DEFAULT EXAMINATION RULES & BEHAVIOR")
        lbl.setProperty("class", "StatLabel")
        layout.addWidget(lbl)

        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QLabel("Pre-Test Countdown Seconds:"), 0, 0)
        self.spin_start_countdown = QSpinBox()
        self.spin_start_countdown.setRange(0, 10)
        self.spin_start_countdown.setValue(int(self.ctx.get_setting("start_countdown", 3)))
        self.spin_start_countdown.valueChanged.connect(
            lambda val: self.ctx.set_setting("start_countdown", val)
        )
        grid.addWidget(self.spin_start_countdown, 0, 1)

        self.chk_fullscreen = QCheckBox("Default to Full-Screen Mode for Examinations")
        self.chk_fullscreen.setChecked(bool(self.ctx.get_setting("fullscreen_exam", False)))
        self.chk_fullscreen.toggled.connect(
            lambda val: self.ctx.set_setting("fullscreen_exam", val)
        )
        grid.addWidget(self.chk_fullscreen, 1, 0, 1, 2)

        layout.addLayout(grid)
        self.main_layout.addWidget(card)

    def _build_sound_section(self) -> None:
        card = QFrame()
        card.setProperty("class", "CardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        lbl = QLabel("AUDIO CUES & SOUND ALERTS")
        lbl.setProperty("class", "StatLabel")
        layout.addWidget(lbl)

        self.chk_sound = QCheckBox("Enable Sound Effects (Phase Transitions, Countdown Cues, Bells)")
        self.chk_sound.setChecked(bool(self.ctx.get_setting("sound_enabled", True)))
        self.chk_sound.toggled.connect(self._on_sound_toggled)
        layout.addWidget(self.chk_sound)

        vol_h = QHBoxLayout()
        vol_h.addWidget(QLabel("Sound Volume:"))

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(int(self.ctx.get_setting("sound_volume", 80)))
        self.vol_slider.valueChanged.connect(self._on_volume_changed)
        vol_h.addWidget(self.vol_slider)

        self.vol_val_lbl = QLabel(f"{self.vol_slider.value()}%")
        vol_h.addWidget(self.vol_val_lbl)

        btn_test_sound = QPushButton("🔔 Test Chime")
        btn_test_sound.clicked.connect(lambda: self.ctx.sound_service.play_cue("transition"))
        vol_h.addWidget(btn_test_sound)

        layout.addLayout(vol_h)
        self.main_layout.addWidget(card)

    def _build_ocr_section(self) -> None:
        card = QFrame()
        card.setProperty("class", "CardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        lbl = QLabel("TESSERACT OCR CONFIGURATION (OPTIONAL FOR SCANNED PDFS)")
        lbl.setProperty("class", "StatLabel")
        layout.addWidget(lbl)

        self.ocr_status_lbl = QLabel(self.ctx.ocr_service.get_status_message())
        self.ocr_status_lbl.setWordWrap(True)
        if self.ctx.ocr_service.is_available:
            self.ocr_status_lbl.setStyleSheet("color: #10B981; font-weight: 600;")
        else:
            self.ocr_status_lbl.setStyleSheet("color: #94A3B8;")
        layout.addWidget(self.ocr_status_lbl)

        h = QHBoxLayout()
        h.addWidget(QLabel("Tesseract Executable Path:"))
        self.ocr_path_input = QLineEdit()
        self.ocr_path_input.setPlaceholderText("Auto-detected or specify custom path to tesseract.exe")
        self.ocr_path_input.setText(self.ctx.ocr_service.executable_path or "")
        h.addWidget(self.ocr_path_input, stretch=1)

        btn_browse_ocr = QPushButton("Browse...")
        btn_browse_ocr.clicked.connect(self._on_browse_ocr)
        h.addWidget(btn_browse_ocr)

        btn_detect_ocr = QPushButton("Detect Again")
        btn_detect_ocr.clicked.connect(self._on_detect_ocr)
        h.addWidget(btn_detect_ocr)

        layout.addLayout(h)
        self.main_layout.addWidget(card)

    def _build_storage_info_section(self) -> None:
        card = QFrame()
        card.setProperty("class", "CardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        lbl = QLabel("LOCAL STORAGE & DIRECTORIES")
        lbl.setProperty("class", "StatLabel")
        layout.addWidget(lbl)

        grid = QGridLayout()
        grid.setSpacing(8)

        grid.addWidget(QLabel("User Data Directory:"), 0, 0)
        grid.addWidget(QLabel(str(get_user_data_dir())), 0, 1)

        grid.addWidget(QLabel("Active SQLite Database:"), 1, 0)
        grid.addWidget(QLabel(str(get_database_path())), 1, 1)

        grid.addWidget(QLabel("Asset Store Directory:"), 2, 0)
        grid.addWidget(QLabel(str(get_library_asset_dir())), 2, 1)

        grid.addWidget(QLabel("Backups Directory:"), 3, 0)
        grid.addWidget(QLabel(str(get_backup_dir())), 3, 1)

        grid.addWidget(QLabel("Reports Directory:"), 4, 0)
        grid.addWidget(QLabel(str(get_reports_dir())), 4, 1)

        layout.addLayout(grid)

        btn_open_folder = QPushButton("📁 Open Application Data Directory in Explorer")
        btn_open_folder.clicked.connect(self._on_open_data_folder)
        layout.addWidget(btn_open_folder, alignment=Qt.AlignmentFlag.AlignLeft)

        self.main_layout.addWidget(card)

    def _build_about_section(self) -> None:
        card = QFrame()
        card.setProperty("class", "CardFrame")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        lbl = QLabel("ABOUT & DEVELOPER CREDIT")
        lbl.setProperty("class", "StatLabel")
        layout.addWidget(lbl)

        title_lbl = QLabel("SSB Practice Studio — Officer Assessment Psychological Tests")
        title_lbl.setStyleSheet("font-weight: 700; font-size: 14px; color: #38BDF8;")
        layout.addWidget(title_lbl)

        dev_lbl = QLabel("🎖️ Designed & Developed by Lt. V. Elangovan")
        dev_lbl.setStyleSheet("font-weight: 700; font-size: 13px; color: #F1F5F9;")
        layout.addWidget(dev_lbl)

        desc_lbl = QLabel(
            "Dedicated to empowering defense aspirants preparing for Services Selection Board (SSB) Interviews "
            "(NDA, CDS, AFCAT, TGC, Army, Navy, Air Force & Coast Guard).\n"
            "Features 100% offline-first testing for Word Association Test (WAT), Situation Reaction Test (SRT), "
            "and Thematic Apperception Test (TAT)."
        )
        desc_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; line-height: 1.4;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        self.main_layout.addWidget(card)

    def _build_footer_actions(self) -> None:
        footer_h = QHBoxLayout()

        btn_reset = QPushButton("Reset All Settings to Defaults")
        btn_reset.setProperty("class", "DangerBtn")
        btn_reset.clicked.connect(self._on_reset_defaults)
        footer_h.addWidget(btn_reset)

        footer_h.addStretch()
        self.main_layout.addLayout(footer_h)

    def _on_theme_changed(self) -> None:
        theme = self.theme_combo.currentData()
        self.ctx.set_setting("theme", theme)
        self.theme_change_requested.emit(theme)

    def _on_font_size_changed(self, size: int) -> None:
        self.ctx.set_setting("font_size", size)
        self.font_size_changed.emit(size)

    def _on_sound_toggled(self, checked: bool) -> None:
        self.ctx.set_setting("sound_enabled", checked)
        self.ctx.sound_service.set_enabled(checked)

    def _on_volume_changed(self, val: int) -> None:
        self.vol_val_lbl.setText(f"{val}%")
        self.ctx.set_setting("sound_volume", val)
        self.ctx.sound_service.set_volume(val)

    def _on_browse_ocr(self) -> None:
        exe_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Tesseract Executable",
            filter="Executables (*.exe);;All Files (*.*)",
        )
        if exe_path:
            self.ocr_path_input.setText(exe_path)
            self.ctx.set_setting("tesseract_cmd", exe_path)
            self._update_ocr_display()

    def _on_detect_ocr(self) -> None:
        self.ctx.ocr_service.set_custom_path(None)
        self.ocr_path_input.setText(self.ctx.ocr_service.executable_path or "")
        self._update_ocr_display()

    def _update_ocr_display(self) -> None:
        msg = self.ctx.ocr_service.get_status_message()
        self.ocr_status_lbl.setText(msg)
        if self.ctx.ocr_service.is_available:
            self.ocr_status_lbl.setStyleSheet("color: #10B981; font-weight: 600;")
        else:
            self.ocr_status_lbl.setStyleSheet("color: #94A3B8;")

    def _on_open_data_folder(self) -> None:
        folder = str(get_user_data_dir())
        try:
            os.startfile(folder)
        except Exception as e:
            QMessageBox.information(self, "Data Directory", f"Path:\n{folder}")

    def _on_reset_defaults(self) -> None:
        reply = QMessageBox.warning(
            self,
            "Reset Settings",
            "Are you sure you want to restore all application settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.ctx.reset_settings_to_defaults()
            self.spin_start_countdown.setValue(3)
            self.chk_fullscreen.setChecked(False)
            self.chk_sound.setChecked(True)
            self.vol_slider.setValue(80)
            self.theme_combo.setCurrentIndex(0)
            self.spin_font.setValue(13)
            self._on_theme_changed()
            QMessageBox.information(self, "Reset Complete", "Settings restored to defaults.")
