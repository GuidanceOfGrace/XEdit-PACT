"""Main window for AutoQAC application using MixIn classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from AutoQACLib.logging_config import get_logger
from AutoQACLib.ui.mixins import (
    CleaningControlMixin,
    ConfigurationMixin,
    DialogMixin,
    SignalConnectionMixin,
    StateEventHandlerMixin,
    UIUpdateMixin,
)

if TYPE_CHECKING:
    from logging import Logger

    from AutoQACLib.gui_controller import GuiController
    from AutoQACLib.state_manager import StateManager
    from AutoQACLib.ui.dialogs.cleaning_progress import CleaningProgressDialog

logger: Logger = get_logger(__name__)


class MainWindow(
    QMainWindow,
    ConfigurationMixin,
    SignalConnectionMixin,
    UIUpdateMixin,
    CleaningControlMixin,
    DialogMixin,
    StateEventHandlerMixin,
):
    """Main application window with refactored state management using MixIn classes."""

    def __init__(self, state: StateManager, controller: GuiController) -> None:
        """Initialize the main window."""
        super().__init__()
        self.state: StateManager = state
        self.controller: GuiController = controller
        self._updating_ui: bool = False  # Flag to prevent recursive updates
        self._update_timer: QTimer = QTimer(self)  # Timer for debouncing UI updates
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(50)  # 50ms delay
        self._update_timer.timeout.connect(self._perform_ui_update)
        self._update_priority: str = "normal"  # Track update priority

        # UI elements
        self.progress_dialog: CleaningProgressDialog | None = None
        self.load_order_button: QPushButton | None = None
        self.mo2_button: QPushButton | None = None
        self.mo2_mode_button: QPushButton | None = None
        self.partial_forms_button: QPushButton | None = None
        self.xedit_button: QPushButton | None = None
        self.start_button: QPushButton | None = None
        self.stop_button: QPushButton | None = None

        # Connect controller signals
        self._connect_controller_signals()

        # Connect state signals
        self._connect_state_signals()

        # Setup UI
        self._setup_ui()

        # Update initial state
        self._update_ui_from_state()

    def _setup_ui(self) -> None:
        """Setup the main window UI."""
        self.setWindowTitle("AutoQAC")
        self.setMinimumSize(600, 400)

        # Create central widget
        central_widget: QWidget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout: QVBoxLayout = QVBoxLayout(central_widget)

        # Create configuration group
        config_group: QGroupBox = self._create_configuration_group()
        main_layout.addWidget(config_group)

        # Create control group
        control_group: QGroupBox = self._create_control_group()
        main_layout.addWidget(control_group)

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Initial UI update
        self._update_ui_from_state()

    def _create_control_group(self) -> QGroupBox:
        """Create the control section."""
        group: QGroupBox = QGroupBox("Controls")
        layout: QHBoxLayout = QHBoxLayout()

        self.start_button = QPushButton("Start Cleaning")
        self.start_button.clicked.connect(self._start_cleaning)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._stop_cleaning)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        layout.addStretch()

        group.setLayout(layout)
        return group

    def _create_menu_bar(self) -> None:
        """Create the menu bar."""
        menubar: QMenuBar = self.menuBar()

        # File menu
        file_menu: QMenu = menubar.addMenu("&File")

        refresh_action: QAction = QAction("&Refresh Configuration", self)
        refresh_action.triggered.connect(self.controller.refresh_configuration)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action: QAction = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu: QMenu = menubar.addMenu("&Help")

        about_action: QAction = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event with proper cleanup."""
        # If cleaning is in progress, ask user for confirmation
        if self.state.get("is_cleaning"):
            reply: QMessageBox.StandardButton = QMessageBox.question(
                self,
                "Cleaning in Progress",
                "Cleaning is currently in progress. Are you sure you want to close the application?\n\n"
                "This will stop the cleaning process.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        # Stop update timer
        if self._update_timer.isActive():
            self._update_timer.stop()

        # Disconnect all signals
        self._disconnect_all_signals()

        # Close progress dialog if open
        if self.progress_dialog:
            if self.progress_dialog.isVisible():
                self.progress_dialog.close()
            self.progress_dialog.cleanup()
            self.progress_dialog.deleteLater()
            self.progress_dialog = None

        # Perform comprehensive cleanup
        logger.info("Shutting down application")
        self.controller.cleanup()

        # Ensure all events are processed
        QCoreApplication.processEvents()

        event.accept()
        logger.info("Application shutdown complete")
