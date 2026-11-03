"""Application entry point for SSB Practice Studio."""

import sys
# Suppress optional PyMuPDF ONNX layout models to prevent runtime crash in packaged environments
if "pymupdf.layout" not in sys.modules:
    sys.modules["pymupdf.layout"] = None

import logging
import traceback
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from app.app_context import AppContext
from app.config import APP_NAME, APP_VERSION, ORG_NAME
from ui.main_window import MainWindow
from ui.styles.theme_manager import ThemeManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("SSBPracticeStudio")


def exception_hook(exc_type, exc_value, exc_traceback):
    """Global unhandled exception handler to notify user gracefully without silent crash."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Unhandled exception:\n{err_msg}")

    # If QApplication is running, show error dialog
    app = QApplication.instance()
    if app:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Application Error")
        msg_box.setText("An unexpected error occurred.")
        msg_box.setInformativeText(str(exc_value))
        msg_box.setDetailedText(err_msg)
        msg_box.exec()


def main() -> int:
    """Initialize and run SSB Practice Studio."""
    sys.excepthook = exception_hook

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORG_NAME)

    # Windows taskbar AppUserModelID for dedicated taskbar grouping and icon display
    if sys.platform == "win32":
        try:
            import ctypes
            app_id = f"defense.ssb.practicestudio.{APP_VERSION}"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass

    # Load and apply application icon (both .ico and .png for optimal resolution)
    from app.config import get_app_root
    from PySide6.QtGui import QIcon
    icon_ico = get_app_root() / "assets" / "app_icon.ico"
    icon_png = get_app_root() / "assets" / "app_icon.png"
    app_icon = QIcon()
    if icon_ico.exists():
        app_icon.addFile(str(icon_ico))
    if icon_png.exists():
        app_icon.addFile(str(icon_png))
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # Initialize app context (database, repositories, services)
    ctx = AppContext()

    # Initialize theme manager and apply user's saved theme
    theme_name = ctx.get_setting("theme", "dark")
    font_size = int(ctx.get_setting("font_size", 13))
    theme_mgr = ThemeManager(current_theme=theme_name, font_size=font_size)
    theme_mgr.apply_theme(theme_name, app)

    # Launch Main Window
    window = MainWindow(ctx, theme_mgr)
    window.show()
    window.raise_()
    window.activateWindow()

    logger.info(f"{APP_NAME} v{APP_VERSION} launched successfully.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
