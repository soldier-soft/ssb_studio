"""Enhanced modern metric KPI card widget for the dashboard."""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class StatCard(QFrame):
    """Modern card displaying a performance KPI with glowing icon badge, bold typography, and status chip."""

    def __init__(
        self,
        label: str,
        value: str,
        subtitle: str = "",
        icon_text: str = "📊",
        accent_color: str = "#38BDF8",
        parent: Optional[QFrame] = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("class", "CardFrame")
        self.setMinimumHeight(115)
        self.accent_color = accent_color
        self.icon_text = icon_text
        self.theme_name = "dark"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Left Column: label, large value, and subtitle
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.label_widget = QLabel(label.upper())
        self.label_widget.setProperty("class", "StatLabel")

        self.value_widget = QLabel(value)

        self.sub_widget = QLabel(subtitle)

        text_layout.addWidget(self.label_widget)
        text_layout.addWidget(self.value_widget)
        if subtitle:
            text_layout.addWidget(self.sub_widget)

        layout.addLayout(text_layout, stretch=1)

        # Right Column: Ambient Glow Icon Badge
        self.icon_badge = QLabel(icon_text) if icon_text else None
        if self.icon_badge:
            self.icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.icon_badge, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.set_theme("dark")

    def set_theme(self, theme_name: str) -> None:
        """Update styling to match dark or light theme seamlessly."""
        self.theme_name = theme_name if theme_name in ("dark", "light") else "dark"

        if self.theme_name == "light":
            self.setStyleSheet(
                f"""
                QFrame.CardFrame {{
                    background-color: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-top: 3.5px solid {self.accent_color};
                    border-radius: 12px;
                }}
                QFrame.CardFrame:hover {{
                    border-color: {self.accent_color};
                    background-color: #F8FAFC;
                }}
                """
            )
            self.label_widget.setStyleSheet("color: #475569; font-weight: 700; font-size: 11px; letter-spacing: 0.8px;")
            self.value_widget.setStyleSheet(
                f"font-size: 30px; font-weight: 900; color: {self.accent_color}; letter-spacing: -0.5px;"
            )
            self.sub_widget.setStyleSheet("color: #64748B; font-size: 11.5px; font-weight: 500;")
            if self.icon_badge:
                self.icon_badge.setStyleSheet(
                    f"""
                    QLabel {{
                        font-size: 26px;
                        background-color: #EFF6FF;
                        border: 1px solid #BFDBFE;
                        border-radius: 25px;
                        min-width: 50px;
                        min-height: 50px;
                        max-width: 50px;
                        max-height: 50px;
                    }}
                    """
                )
        else:
            self.setStyleSheet(
                f"""
                QFrame.CardFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #111827, stop:1 #131E33);
                    border: 1px solid #1F2937;
                    border-top: 3.5px solid {self.accent_color};
                    border-radius: 12px;
                }}
                QFrame.CardFrame:hover {{
                    border-color: {self.accent_color};
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #131C30, stop:1 #17243F);
                }}
                """
            )
            self.label_widget.setStyleSheet("color: #94A3B8; font-weight: 700; font-size: 11px; letter-spacing: 0.8px;")
            self.value_widget.setStyleSheet(
                f"font-size: 30px; font-weight: 900; color: {self.accent_color}; letter-spacing: -0.5px;"
            )
            self.sub_widget.setStyleSheet("color: #94A3B8; font-size: 11.5px; font-weight: 500;")
            if self.icon_badge:
                self.icon_badge.setStyleSheet(
                    f"""
                    QLabel {{
                        font-size: 26px;
                        background-color: rgba(56, 189, 248, 0.08);
                        border: 1px solid rgba(56, 189, 248, 0.2);
                        border-radius: 25px;
                        min-width: 50px;
                        min-height: 50px;
                        max-width: 50px;
                        max-height: 50px;
                    }}
                    """
                )

    def set_value(self, value: str, subtitle: Optional[str] = None) -> None:
        self.value_widget.setText(value)
        if subtitle is not None:
            self.sub_widget.setText(subtitle)
