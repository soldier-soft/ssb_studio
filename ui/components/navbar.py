"""Sidebar navigation bar with app icon, candidate status chip, active state highlighting, and theme toggle."""

from pathlib import Path
from typing import Dict, Optional
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.config import get_app_root


class SidebarNav(QFrame):
    """Vertical sidebar navigation frame with rich visual branding and navigation routes."""

    nav_selected = Signal(str)
    theme_toggle_clicked = Signal()

    NAV_ITEMS = [
        ("dashboard", "🏠  Dashboard"),
        ("builder", "🚀  Start Session"),
        ("tat", "🖼️  TAT Practice"),
        ("wat", "⚡  WAT Practice"),
        ("srt", "🎯  SRT Practice"),
        ("library", "📚  Content Library"),
        ("history", "📜  Session History"),
        ("reports", "📄  Reports & Export"),
        ("settings", "⚙️  Settings"),
    ]

    def __init__(self, parent: Optional[QFrame] = None) -> None:
        super().__init__(parent)
        self.setObjectName("SidebarFrame")
        self.setFixedWidth(240)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 18, 14, 18)
        main_layout.setSpacing(6)

        # Brand Header with Icon
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)

        # Load icon if available
        icon_path = get_app_root() / "assets" / "app_icon.png"
        icon_lbl = QLabel()
        if icon_path.exists():
            pix = QPixmap(str(icon_path)).scaled(
                36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            icon_lbl.setPixmap(pix)
        else:
            icon_lbl.setText("🎖️")
            icon_lbl.setStyleSheet("font-size: 24px;")
        brand_row.addWidget(icon_lbl)

        brand_text_v = QVBoxLayout()
        brand_text_v.setSpacing(1)

        app_title = QLabel("SSB STUDIO")
        app_title.setStyleSheet("font-size: 15px; font-weight: 900; color: #60A5FA; letter-spacing: 0.8px;")

        app_sub = QLabel("Officer Assessment")
        app_sub.setStyleSheet("font-size: 10.5px; color: #94A3B8; font-weight: 500;")

        brand_text_v.addWidget(app_title)
        brand_text_v.addWidget(app_sub)
        brand_row.addLayout(brand_text_v)
        brand_row.addStretch()

        main_layout.addLayout(brand_row)

        # Candidate Status Chip
        self.status_card = QFrame()
        status_h = QHBoxLayout(self.status_card)
        status_h.setContentsMargins(4, 2, 4, 2)
        status_h.setSpacing(8)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #10B981; font-size: 10px;")
        status_h.addWidget(self.status_dot)

        self.status_text = QLabel("CADET READY • LOCAL")
        status_h.addWidget(self.status_text)
        status_h.addStretch()

        # Animated breathing pulse for status dot
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(900)
        self._pulse_state = False

        def on_pulse():
            self._pulse_state = not self._pulse_state
            if self._pulse_state:
                self.status_dot.setStyleSheet("color: #34D399; font-size: 11px;")
            else:
                self.status_dot.setStyleSheet("color: #059669; font-size: 10px;")

        self._pulse_timer.timeout.connect(on_pulse)
        self._pulse_timer.start()

        main_layout.addSpacing(6)
        main_layout.addWidget(self.status_card)
        main_layout.addSpacing(10)

        # Nav Buttons Group
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self.nav_buttons: Dict[str, QPushButton] = {}

        for key, label in self.NAV_ITEMS:
            btn = QPushButton(label)
            btn.setProperty("class", "NavBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, k=key: self.nav_selected.emit(k))
            self.btn_group.addButton(btn)
            self.nav_buttons[key] = btn
            main_layout.addWidget(btn)

        if "dashboard" in self.nav_buttons:
            self.nav_buttons["dashboard"].setChecked(True)

        main_layout.addStretch()

        # Bottom section: Theme toggle button
        self.theme_btn = QPushButton("🌓  Toggle Theme")
        self.theme_btn.setProperty("class", "NavBtn")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self.theme_toggle_clicked.emit)
        main_layout.addWidget(self.theme_btn)

        # Version & Offline status footer
        footer_lbl = QLabel("SSB Studio v1.0 • Offline-First")
        footer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_lbl.setStyleSheet("font-size: 9.5px; color: #64748B; padding-top: 4px;")
        main_layout.addWidget(footer_lbl)
        self.apply_theme("dark")

    def apply_theme(self, theme_name: str) -> None:
        """Update navbar accents for light/dark theme."""
        if theme_name == "light":
            self.status_card.setStyleSheet(
                "background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 8px; padding: 6px 10px;"
            )
            self.status_text.setStyleSheet(
                "color: #475569; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;"
            )
            self.theme_btn.setText("☀️  Light Theme")
        else:
            self.status_card.setStyleSheet(
                "background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 8px; padding: 6px 10px;"
            )
            self.status_text.setStyleSheet(
                "color: #94A3B8; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;"
            )
            self.theme_btn.setText("🌙  Dark Theme")

    def select_nav(self, page_name: str) -> None:
        """Programmatically highlight the active navigation button."""
        if page_name in self.nav_buttons:
            self.nav_buttons[page_name].setChecked(True)
