"""Main application window hosting sidebar navigation and stacked screens."""

import logging
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from app.app_context import AppContext
from database.models import ContentSet, Preset
from ui.components.animated_stack import AnimatedStackedWidget
from ui.components.navbar import SidebarNav
from ui.screens.dashboard_screen import DashboardScreen
from ui.screens.history_screen import HistoryScreen
from ui.screens.library_screen import LibraryScreen
from ui.screens.report_screen import ReportScreen
from ui.screens.session_builder import SessionBuilderScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.srt_screen import SRTScreen
from ui.screens.tat_screen import TATScreen
from ui.screens.wat_screen import WATScreen
from ui.styles.theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main window of SSB Practice Studio."""

    def __init__(self, ctx: AppContext, theme_manager: ThemeManager) -> None:
        super().__init__()
        self.ctx = ctx
        self.theme_manager = theme_manager

        self.setWindowTitle("SSB Practice Studio — Psychological Test Preparation")
        self.setMinimumSize(1150, 720)
        self.resize(1280, 800)

        # Explicitly apply window icon
        from app.config import get_app_root
        icon_ico = get_app_root() / "assets" / "app_icon.ico"
        icon_png = get_app_root() / "assets" / "app_icon.png"
        app_icon = QIcon()
        if icon_ico.exists():
            app_icon.addFile(str(icon_ico))
        if icon_png.exists():
            app_icon.addFile(str(icon_png))
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        # Central widget and horizontal layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.root_layout = QHBoxLayout(central_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # Left Sidebar Navigation
        self.sidebar = SidebarNav()
        self.sidebar.nav_selected.connect(self.navigate_to)
        self.sidebar.theme_toggle_clicked.connect(self._toggle_theme)
        self.root_layout.addWidget(self.sidebar)

        # Stack of screens with smooth animated transitions
        self.stack = AnimatedStackedWidget()
        self.root_layout.addWidget(self.stack, stretch=1)

        # Screen instances
        self.dashboard_screen = DashboardScreen(self.ctx)
        self.builder_screen = SessionBuilderScreen(self.ctx)
        self.tat_screen = TATScreen(self.ctx)
        self.wat_screen = WATScreen(self.ctx)
        self.srt_screen = SRTScreen(self.ctx)
        self.library_screen = LibraryScreen(self.ctx)
        self.history_screen = HistoryScreen(self.ctx)
        self.report_screen = ReportScreen(self.ctx)
        self.settings_screen = SettingsScreen(self.ctx)

        # Register screens in stack
        self.screen_indices = {
            "dashboard": self.stack.addWidget(self.dashboard_screen),
            "builder": self.stack.addWidget(self.builder_screen),
            "tat": self.stack.addWidget(self.tat_screen),
            "wat": self.stack.addWidget(self.wat_screen),
            "srt": self.stack.addWidget(self.srt_screen),
            "library": self.stack.addWidget(self.library_screen),
            "history": self.stack.addWidget(self.history_screen),
            "reports": self.stack.addWidget(self.report_screen),
            "settings": self.stack.addWidget(self.settings_screen),
        }

        # Wire up inter-screen navigation and actions
        self._connect_signals()

        # Initial navigation to dashboard
        self.navigate_to("dashboard")

    def _connect_signals(self) -> None:
        # Dashboard signals
        self.dashboard_screen.navigate_requested.connect(self.navigate_to)
        self.dashboard_screen.start_test_requested.connect(self._on_dashboard_quick_start)
        self.dashboard_screen.view_session_requested.connect(self._on_view_session)

        # Builder signals
        self.builder_screen.navigate_to_library.connect(self._on_builder_to_library)
        self.builder_screen.session_ready_to_launch.connect(self._launch_session)

        # Library signals
        self.library_screen.content_updated.connect(self.builder_screen.refresh_builder)

        # Test screen finished / abandoned signals
        self.tat_screen.session_finished.connect(self._on_session_finished)
        self.tat_screen.session_abandoned.connect(self._on_session_abandoned)

        self.wat_screen.session_finished.connect(self._on_session_finished)
        self.wat_screen.session_abandoned.connect(self._on_session_abandoned)

        self.srt_screen.session_finished.connect(self._on_session_finished)
        self.srt_screen.session_abandoned.connect(self._on_session_abandoned)

        # Settings signals
        self.settings_screen.theme_change_requested.connect(
            lambda t: self.theme_manager.apply_theme(t)
        )
        self.settings_screen.font_size_changed.connect(
            lambda s: self.theme_manager.set_font_size(s)
        )

        # Broadcast theme changes across all screen components
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
        self._on_theme_changed(self.theme_manager.current_theme)

    def _on_theme_changed(self, theme_name: str) -> None:
        """Propagate theme palette updates to sidebar and test screens."""
        self.sidebar.apply_theme(theme_name)
        self.wat_screen.apply_theme(theme_name)
        self.srt_screen.apply_theme(theme_name)
        self.tat_screen.apply_theme(theme_name)

    def navigate_to(self, page_name: str) -> None:
        """Switch active view and refresh view data with animated fade."""
        if page_name in self.screen_indices:
            idx = self.screen_indices[page_name]
            self.stack.fade_to_index(idx)
            self.sidebar.select_nav(page_name)

            # Ensure sidebar is visible unless in full-screen exam
            if not self.isFullScreen():
                self.sidebar.setVisible(True)

            # Refresh targeted screen
            if page_name == "dashboard":
                self.dashboard_screen.refresh_data()
            elif page_name == "builder":
                self.builder_screen.refresh_builder()
            elif page_name == "library":
                self.library_screen.refresh_library()
            elif page_name == "history":
                self.history_screen.refresh_history()
            elif page_name == "reports":
                self.report_screen.refresh_reports_screen()

    def _toggle_theme(self) -> None:
        new_theme = self.theme_manager.toggle_theme()
        self.ctx.set_setting("theme", new_theme)

    def _on_dashboard_quick_start(self, test_type: str, preset_name: str) -> None:
        # Check if there is content available for this test type
        sets = self.ctx.content_repo.list_content_sets(test_type)
        if not sets or sets[0].item_count <= 0:
            QMessageBox.information(
                self,
                "Content Required",
                f"No practice material found for {test_type}. Opening Content Library so you can import images, words, or situations.",
            )
            self.library_screen.select_tab(test_type)
            self.navigate_to("library")
            return

        # Navigate to builder pre-configured with this preset
        self.builder_screen.refresh_builder(target_type=test_type, target_preset_name=preset_name)
        self.navigate_to("builder")

    def _on_builder_to_library(self, test_type: str) -> None:
        self.library_screen.select_tab(test_type)
        self.navigate_to("library")

    def _launch_session(self, preset: Preset, content_set: ContentSet, item_count: int) -> None:
        """Initialize session in service, switch to test view, and enter exam mode."""
        try:
            session, items = self.ctx.session_service.prepare_session(
                preset=preset,
                content_set=content_set,
                override_item_count=item_count,
            )
        except Exception as ex:
            QMessageBox.critical(self, "Session Error", f"Unable to start session: {ex}")
            return

        test_type = session.test_type.upper()

        if test_type == "TAT":
            self.tat_screen.start_session(session, items)
            self.navigate_to("tat")
        elif test_type == "WAT":
            self.wat_screen.start_session(session, items)
            self.navigate_to("wat")
        elif test_type == "SRT":
            self.srt_screen.start_session(session, items)
            self.navigate_to("srt")

        # Full-screen exam handling
        if session.is_exam_mode and self.ctx.get_setting("fullscreen_exam", False):
            self.sidebar.setVisible(False)
            self.showFullScreen()

    def _on_session_finished(self, session_id: int) -> None:
        if self.isFullScreen():
            self.showNormal()
        self.sidebar.setVisible(True)
        self.navigate_to("history")
        self.history_screen.open_session_detail(session_id)

    def _on_session_abandoned(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        self.sidebar.setVisible(True)
        self.navigate_to("dashboard")

    def _on_view_session(self, session_id: int) -> None:
        self.navigate_to("history")
        self.history_screen.open_session_detail(session_id)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Prevent data loss by checking for active tests and flushing pending writes."""
        active = self.ctx.session_service.current_session
        if active and active.status == "IN_PROGRESS":
            reply = QMessageBox.question(
                self,
                "Active Test In Progress",
                "A practice test is currently in progress. Exiting now will save all written answers and mark the test as abandoned.\nAre you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            self.ctx.session_service.abandon_session(elapsed_seconds=0.0)

        # Flush any pending state
        self.ctx.session_service.flush_responses()
        event.accept()
