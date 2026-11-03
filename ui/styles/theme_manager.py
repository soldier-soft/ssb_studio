"""Theme loader and dynamic application style switcher."""

import logging
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    """Manages switching between dark navy and light visual themes."""

    theme_changed = Signal(str)

    def __init__(self, current_theme: str = "dark", font_size: int = 13) -> None:
        super().__init__()
        self.current_theme = current_theme if current_theme in ("dark", "light") else "dark"
        self.font_size = font_size
        self._styles_dir = Path(__file__).parent

    def apply_theme(self, theme_name: str, app: Optional[QApplication] = None) -> None:
        """Apply the chosen theme stylesheet to the active QApplication."""
        if app is None:
            app = QApplication.instance()
            if app is None:
                return

        self.current_theme = theme_name if theme_name in ("dark", "light") else "dark"
        qss_filename = f"{self.current_theme}_theme.qss"
        qss_file = self._styles_dir / qss_filename

        if qss_file.exists():
            stylesheet = qss_file.read_text(encoding="utf-8")
            # Apply user font size
            font = app.font()
            font.setPointSize(self.font_size)
            app.setFont(font)

            app.setStyleSheet(stylesheet)
            self.theme_changed.emit(self.current_theme)
            logger.info(f"Applied {self.current_theme} theme successfully.")
        else:
            logger.warning(f"Stylesheet not found: {qss_file}")

    def set_font_size(self, size_pt: int, app: Optional[QApplication] = None) -> None:
        self.font_size = max(10, min(24, int(size_pt)))
        if app is None:
            app = QApplication.instance()
        if app:
            font = app.font()
            font.setPointSize(self.font_size)
            app.setFont(font)

    def toggle_theme(self, app: Optional[QApplication] = None) -> str:
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme(new_theme, app)
        return new_theme
