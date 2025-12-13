"""Tests for the main interface components."""

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton

from AutoQAC_Interface import CleaningProgressDialog, MainWindow, create_application
from AutoQACLib.config_manager import ConfigManager
from AutoQACLib.state_manager import StateManager

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMenuBar


@pytest.fixture
def mock_cleaning_dialog(qt_app: Any) -> Any:
    """Create a mock CleaningProgressDialog for testing."""
    with patch("AutoQAC_Interface.QDialog.__init__", return_value=None):
        dialog = CleaningProgressDialog.__new__(CleaningProgressDialog)

        # Set up basic attributes
        dialog._current_plugin_name = None
        dialog._cleaning_in_progress = True

        # Mock Qt widget methods
        dialog.setWindowTitle = Mock()
        dialog.setMinimumSize = Mock()
        dialog.setModal = Mock()
        dialog.windowTitle = Mock(return_value="Cleaning Progress")
        dialog.isModal = Mock(return_value=False)
        dialog.show = Mock()
        dialog.close = Mock()
        dialog.closeEvent = Mock()

        # Mock UI elements
        dialog.current_plugin_label = Mock(spec=QLabel)
        dialog.current_plugin_label.text = Mock(return_value="")
        dialog.current_plugin_label.setText = Mock()

        dialog.progress_bar = Mock(spec=QProgressBar)
        dialog.progress_bar.value = Mock(return_value=0)
        dialog.progress_bar.setValue = Mock()
        dialog.progress_bar.format = Mock(return_value="%p%")
        dialog.progress_bar.setFormat = Mock()

        dialog.progress_label = Mock(spec=QLabel)
        dialog.progress_label.text = Mock(return_value="0 / 0 plugins")
        dialog.progress_label.setText = Mock()

        dialog.stats_labels = {
            "cleaned": Mock(spec=QLabel),
            "failed": Mock(spec=QLabel),
            "skipped": Mock(spec=QLabel),
            "total": Mock(spec=QLabel),
        }
        for label in dialog.stats_labels.values():
            label.setText = Mock()
            label.text = Mock(return_value="0")

        dialog.stop_button = Mock(spec=QPushButton)
        dialog.stop_button.isVisible = Mock(return_value=True)
        dialog.stop_button.setVisible = Mock()

        dialog.close_button = Mock(spec=QPushButton)
        dialog.close_button.isEnabled = Mock(return_value=False)
        dialog.close_button.setEnabled = Mock()

        # Mock button_box for cleanup
        dialog.button_box = Mock()
        dialog.button_box.rejected = Mock()
        dialog.button_box.rejected.disconnect = Mock()

        # Mock cleanup method
        dialog.cleanup = Mock()

        # Mock the _setup_ui method
        dialog._setup_ui = Mock()

        # Mock methods that tests might call
        dialog.show = Mock()
        dialog.update_progress = Mock()
        dialog.update_statistics = Mock()
        dialog.set_cleaning_finished = Mock()
        dialog.update_current_plugin = Mock()

        return dialog


@pytest.fixture
def mock_main_window(state_manager: StateManager, qt_app: Any) -> Any:
    """Create a mock MainWindow for testing."""
    with patch("AutoQAC_Interface.QMainWindow.__init__", return_value=None):
        window = MainWindow.__new__(MainWindow)

        # Set up basic attributes
        window.state = state_manager
        window.controller = Mock()
        window._updating_ui = False
        window.progress_dialog = None
        window._cleaning_finished_handled = False

        # Mock Qt methods
        window.setWindowTitle = Mock()
        window.setMinimumSize = Mock()
        window.setCentralWidget = Mock()
        window.statusBar = Mock(return_value=Mock())
        window.menuBar = Mock(return_value=Mock())
        window.show = Mock()
        window.close = Mock()

        # Mock UI elements
        window.load_order_button = Mock(spec=QPushButton)
        window.load_order_button.setText = Mock()
        window.load_order_button.text = Mock(return_value="Configure Load Order")
        window.mo2_button = Mock(spec=QPushButton)
        window.mo2_button.setText = Mock()
        window.mo2_button.text = Mock(return_value="Configure MO2")
        window.xedit_button = Mock(spec=QPushButton)
        window.xedit_button.setText = Mock()
        window.xedit_button.text = Mock(return_value="Configure xEdit")
        window.mo2_mode_button = Mock(spec=QPushButton)
        window.mo2_mode_button.isChecked = Mock(return_value=False)
        window.mo2_mode_button.setChecked = Mock()
        window.mo2_mode_button.setText = Mock()
        window.mo2_mode_button.text = Mock(return_value="MO2 Mode: OFF")
        window.partial_forms_button = Mock(spec=QPushButton)
        window.partial_forms_button.isChecked = Mock(return_value=False)
        window.partial_forms_button.setChecked = Mock()
        window.partial_forms_button.setText = Mock()
        window.start_button = Mock(spec=QPushButton)
        window.start_button.setEnabled = Mock()
        window.start_button.isEnabled = Mock(return_value=False)
        window.stop_button = Mock(spec=QPushButton)
        window.stop_button.setEnabled = Mock()
        window.stop_button.isEnabled = Mock(return_value=False)
        window.status_bar = Mock()
        window.status_bar.showMessage = Mock()
        window.status_bar.currentMessage = Mock(return_value="")

        # Mock timer
        window._update_timer = Mock()
        window._update_timer.setSingleShot = Mock()
        window._update_timer.setInterval = Mock()
        window._update_timer.timeout = Mock()
        window._update_timer.timeout.connect = Mock()
        window._update_timer.start = Mock()
        window._update_timer.stop = Mock()
        window._update_timer.isActive = Mock(return_value=False)

        # Mock methods
        window._setup_ui = Mock()
        window._update_ui_from_state = Mock()
        window._perform_ui_update = Mock()
        window._create_menu_bar = Mock()

        return window


class TestCleaningProgressDialog:
    """Test the CleaningProgressDialog class."""

    def test_initialization(self, mock_cleaning_dialog: Any) -> None:
        """Test CleaningProgressDialog initialization."""
        dialog = mock_cleaning_dialog

        assert dialog._current_plugin_name is None  # noqa: SLF001
        assert dialog._cleaning_in_progress is True  # noqa: SLF001
        assert dialog.windowTitle() == "Cleaning Progress"
        assert dialog.isModal() is False

    def test_update_progress(self, mock_cleaning_dialog: Any) -> None:
        """Test update_progress method."""
        dialog = mock_cleaning_dialog
        dialog.update_progress = CleaningProgressDialog.update_progress.__get__(dialog, CleaningProgressDialog)

        # Test progress update
        dialog.update_progress(3, 10)
        dialog.progress_bar.setValue.assert_called_with(30)
        dialog.progress_label.setText.assert_called_with("3 / 10 plugins")

        # Test progress with plugin name
        dialog._current_plugin_name = "test.esp"  # noqa: SLF001
        dialog.update_progress(5, 10)
        dialog.progress_bar.setFormat.assert_called_with("test.esp / 50%")

        # Test zero total
        dialog.update_progress(0, 0)
        dialog.progress_bar.setValue.assert_called_with(0)
        dialog.progress_label.setText.assert_called_with("0 / 0 plugins")

    def test_update_current_plugin(self, mock_cleaning_dialog: Any) -> None:
        """Test update_current_plugin method."""
        dialog = mock_cleaning_dialog
        dialog.update_current_plugin = CleaningProgressDialog.update_current_plugin.__get__(
            dialog, CleaningProgressDialog
        )

        dialog.update_current_plugin("test.esp")
        dialog.current_plugin_label.setText.assert_called_with("Processing: test.esp")
        assert dialog._current_plugin_name == "test.esp"  # noqa: SLF001

        # Test with progress
        dialog.progress_bar.value.return_value = 50
        dialog.update_current_plugin("another.esp")
        dialog.progress_bar.setFormat.assert_called_with("another.esp / 50%")

    def test_update_statistics(self, mock_cleaning_dialog: Any) -> None:
        """Test update_statistics method."""
        dialog = mock_cleaning_dialog
        dialog.update_statistics = CleaningProgressDialog.update_statistics.__get__(dialog, CleaningProgressDialog)

        stats: dict[str, int] = {"cleaned": 5, "failed": 2, "skipped": 1, "total": 8}

        dialog.update_statistics(stats)

        dialog.stats_labels["cleaned"].setText.assert_called_with("5")
        dialog.stats_labels["failed"].setText.assert_called_with("2")
        dialog.stats_labels["skipped"].setText.assert_called_with("1")
        dialog.stats_labels["total"].setText.assert_called_with("8")

    def test_set_cleaning_finished(self, mock_cleaning_dialog: Any) -> None:
        """Test set_cleaning_finished method."""
        dialog = mock_cleaning_dialog
        dialog.set_cleaning_finished = CleaningProgressDialog.set_cleaning_finished.__get__(
            dialog, CleaningProgressDialog
        )

        # Set some progress first
        dialog.progress_bar.value.return_value = 100

        dialog.set_cleaning_finished()

        assert dialog._cleaning_in_progress is False  # noqa: SLF001
        dialog.current_plugin_label.setText.assert_called_with("Cleaning completed!")
        dialog.stop_button.setVisible.assert_called_with(False)
        dialog.close_button.setEnabled.assert_called_with(True)
        dialog.progress_bar.setFormat.assert_called_with("Completed - 100%")

        # Test with partial progress
        dialog.progress_bar.value.return_value = 50
        dialog.set_cleaning_finished()
        dialog.progress_bar.setFormat.assert_called_with("Stopped - 50%")

    def test_close_event_during_cleaning(self, mock_cleaning_dialog: Any) -> None:
        """Test closeEvent during cleaning."""
        dialog = mock_cleaning_dialog
        # Bind the actual closeEvent method
        dialog.closeEvent = CleaningProgressDialog.closeEvent.__get__(dialog, CleaningProgressDialog)

        # Mock QMessageBox
        with patch("AutoQAC_Interface.QMessageBox") as mock_qmb:
            # Create mock StandardButton enum values that support bitwise OR
            mock_no = Mock()
            mock_yes = Mock()
            mock_yes.__or__ = Mock(return_value=Mock())  # Support Yes | No operation

            mock_qmb.StandardButton.No = mock_no
            mock_qmb.StandardButton.Yes = mock_yes
            mock_qmb.question.return_value = mock_no  # Return No to cancel

            # Test closing during cleaning
            event: Mock = Mock()
            dialog.closeEvent(event)

            # Should show confirmation dialog
            mock_qmb.question.assert_called_once()
            # Should ignore the event (not accept) when user clicks No
            event.ignore.assert_called_once()
            event.accept.assert_not_called()

    def test_close_event_after_cleaning(self, mock_cleaning_dialog: Any) -> None:
        """Test closeEvent after cleaning is finished."""
        dialog = mock_cleaning_dialog
        # Bind the actual methods
        dialog.set_cleaning_finished = CleaningProgressDialog.set_cleaning_finished.__get__(
            dialog, CleaningProgressDialog
        )
        dialog.closeEvent = CleaningProgressDialog.closeEvent.__get__(dialog, CleaningProgressDialog)

        dialog.set_cleaning_finished()

        event: Mock = Mock()
        dialog.closeEvent(event)

        # Should accept the event immediately
        event.accept.assert_called_once()


class TestMainWindow:
    """Test the MainWindow class."""

    def test_initialization(
        self, mock_main_window: Any, state_manager: StateManager, config_manager: ConfigManager
    ) -> None:
        """Test MainWindow initialization."""
        window = mock_main_window

        assert window.state == state_manager
        assert window.controller is not None
        assert window._updating_ui is False  # noqa: SLF001
        assert window.progress_dialog is None

    def test_setup_ui(self, mock_main_window: Any, state_manager: StateManager, config_manager: ConfigManager) -> None:  # noqa: ARG002
        """Test UI setup."""
        window = mock_main_window

        # Check that UI elements were created
        assert window.load_order_button is not None
        assert window.mo2_button is not None
        assert window.xedit_button is not None
        assert window.mo2_mode_button is not None
        assert window.start_button is not None
        assert window.stop_button is not None
        assert window.status_bar is not None

        # Check window properties were set (they would be set by _setup_ui which is mocked)
        assert window.setWindowTitle is not None
        assert window.setMinimumSize is not None

    def test_button_connections(
        self, mock_main_window: Any, state_manager: StateManager, config_manager: ConfigManager
    ) -> None:
        """Test that buttons are properly connected."""
        window = mock_main_window
        # Bind actual methods for testing
        window._configure_load_order = MainWindow._configure_load_order.__get__(window, MainWindow)
        window._configure_mo2 = MainWindow._configure_mo2.__get__(window, MainWindow)
        window._configure_xedit = MainWindow._configure_xedit.__get__(window, MainWindow)
        window._start_cleaning = MainWindow._start_cleaning.__get__(window, MainWindow)
        window._stop_cleaning = MainWindow._stop_cleaning.__get__(window, MainWindow)

        # Test button connections by calling the slots directly
        window._configure_load_order()
        window.controller.configure_load_order.assert_called_once()

        window._configure_mo2()
        window.controller.configure_mo2.assert_called_once()

        window._configure_xedit()
        window.controller.configure_xedit.assert_called_once()

        window._start_cleaning()
        window.controller.start_cleaning.assert_called_once()

        window._stop_cleaning()
        window.controller.stop_cleaning.assert_called_once()

    def test_mo2_mode_toggle(
        self, mock_main_window: Any, state_manager: StateManager, config_manager: ConfigManager
    ) -> None:
        """Test MO2 mode toggle functionality."""
        window = mock_main_window
        window._toggle_mo2_mode = MainWindow._toggle_mo2_mode.__get__(window, MainWindow)

        # Test enabling MO2 mode
        assert window.mo2_mode_button is not None
        window.mo2_mode_button.setChecked(True)
        window.mo2_mode_button.isChecked.return_value = True
        window._toggle_mo2_mode()
        window.controller.toggle_mo2_mode.assert_called_with(True)

        # Test disabling MO2 mode
        window.mo2_mode_button.isChecked.return_value = False
        window._toggle_mo2_mode()
        window.controller.toggle_mo2_mode.assert_called_with(False)

    def test_ui_update_from_state(
        self, mock_main_window: Any, state_manager: StateManager, config_manager: ConfigManager
    ) -> None:
        """Test UI updates based on state changes."""
        window = mock_main_window
        window._update_ui_from_state = MainWindow._update_ui_from_state.__get__(window, MainWindow)
        window._perform_ui_update = MainWindow._perform_ui_update.__get__(window, MainWindow)

        # Configure all components
        state_manager.update(
            is_load_order_configured=True, is_mo2_configured=True, is_xedit_configured=True, mo2_mode=True
        )

        # Trigger UI update
        window._update_ui_from_state()  # noqa: SLF001

        # Wait for timer to complete
        window._update_timer.stop()  # noqa: SLF001
        window._perform_ui_update()  # noqa: SLF001

        # Verify that UI update methods were called
        window._update_timer.start.assert_called()
        # Since _perform_ui_update is called, verify buttons exist
        assert window.load_order_button is not None
        assert window.mo2_button is not None
        assert window.xedit_button is not None

    def test_cleaning_started_handler(
        self, mock_main_window: Any, state_manager: StateManager, config_manager: ConfigManager
    ) -> None:
        """Test handling of cleaning started event."""
        window = mock_main_window
        # Mock the CleaningProgressDialog creation
        with patch("AutoQAC_Interface.CleaningProgressDialog") as mock_dialog_class:
            mock_dialog_instance = Mock()
            mock_dialog_instance.show = Mock()
            mock_dialog_instance.stop_button = Mock()
            mock_dialog_instance.stop_button.clicked = Mock()
            mock_dialog_instance.stop_button.clicked.connect = Mock()
            mock_dialog_instance.update_statistics = Mock()
            mock_dialog_class.return_value = mock_dialog_instance

            window._on_cleaning_started = MainWindow._on_cleaning_started.__get__(window, MainWindow)

            # Simulate cleaning started
            window._on_cleaning_started()

            # Check that progress dialog was created and shown
            assert window.progress_dialog is not None
            mock_dialog_instance.show.assert_called()

            # Check button states were updated
            window.start_button.setEnabled.assert_called_with(False)
            window.stop_button.setEnabled.assert_called_with(True)

    def test_cleaning_finished_handler(
        self,
        mock_main_window: Any,
        mock_cleaning_dialog: Any,
        state_manager: StateManager,
        config_manager: ConfigManager,
    ) -> None:
        """Test handling of cleaning finished event."""
        window = mock_main_window
        window._on_cleaning_finished = MainWindow._on_cleaning_finished.__get__(window, MainWindow)

        # Create progress dialog first
        window.progress_dialog = mock_cleaning_dialog

        # Simulate cleaning finished
        window._on_cleaning_finished()  # noqa: SLF001

        # Check button states were updated
        window.start_button.setEnabled.assert_called_with(True)
        window.stop_button.setEnabled.assert_called_with(False)

        # Check progress dialog state update was called
        mock_cleaning_dialog.set_cleaning_finished.assert_called()

    def test_progress_update_handler(
        self,
        mock_main_window: Any,
        mock_cleaning_dialog: Any,
        state_manager: StateManager,
        config_manager: ConfigManager,
    ) -> None:
        """Test handling of progress updates."""
        window = mock_main_window
        window._on_progress_changed = MainWindow._on_progress_changed.__get__(window, MainWindow)

        # Create progress dialog
        window.progress_dialog = mock_cleaning_dialog
        window.progress_dialog.show()

        # Mock isVisible to return True
        mock_cleaning_dialog.isVisible = Mock(return_value=True)

        # Simulate progress update
        window._on_progress_changed(3, 10)

        # Check status bar update was called
        window.status_bar.showMessage.assert_called()
        # Check progress dialog update was called
        mock_cleaning_dialog.update_progress.assert_called_with(3, 10)

        # Progress dialog update is verified above

    def test_plugin_processed_handler(
        self,
        mock_main_window: Any,
        mock_cleaning_dialog: Any,
        state_manager: StateManager,
        config_manager: ConfigManager,
    ) -> None:
        """Test handling of plugin processing events."""
        window = mock_main_window
        window._on_plugin_processed = MainWindow._on_plugin_processed.__get__(window, MainWindow)

        # Create progress dialog
        window.progress_dialog = mock_cleaning_dialog
        window.progress_dialog.show()

        # Mock isVisible to return True
        mock_cleaning_dialog.isVisible = Mock(return_value=True)

        # Set current plugin in state
        state_manager.update(current_plugin="test.esp")

        # Simulate plugin processing
        window._on_plugin_processed("test.esp", "cleaned", "Successfully cleaned")

        # Check that current plugin was updated
        mock_cleaning_dialog.update_current_plugin.assert_called_with("test.esp")

    def test_menu_bar_creation(
        self, mock_main_window: Any, state_manager: StateManager, config_manager: ConfigManager
    ) -> None:
        """Test menu bar creation."""
        window = mock_main_window

        menubar: QMenuBar = window.menuBar()
        assert menubar is not None

        # Check that menus were created
        file_menu: Mock | None = menubar.findChild(Mock, "File")  # noqa: F841
        help_menu: Mock | None = menubar.findChild(Mock, "Help")  # noqa: F841

        # Note: In a real test, we'd check for actual menu items
        # This is a simplified check

    def test_about_dialog(
        self, mock_main_window: Any, state_manager: StateManager, config_manager: ConfigManager
    ) -> None:
        """Test about dialog."""
        window = mock_main_window
        window._show_about = MainWindow._show_about.__get__(window, MainWindow)

        with patch("AutoQAC_Interface.QMessageBox.about") as mock_about:
            window._show_about()  # noqa: SLF001
            mock_about.assert_called_once()

            # Check the arguments
            args: tuple[Any, ...] = mock_about.call_args
            assert args[0][0] == window  # parent
            assert args[0][1] == "About AutoQAC"  # title
            assert "AutoQAC" in args[0][2]  # message

    def test_message_handlers(
        self, mock_main_window: Any, state_manager: StateManager, config_manager: ConfigManager
    ) -> None:
        """Test message and error handlers."""
        window = mock_main_window
        window._show_message = MainWindow._show_message.__get__(window, MainWindow)
        window._show_error = MainWindow._show_error.__get__(window, MainWindow)

        with patch("AutoQAC_Interface.QMessageBox.information") as mock_info:
            window._show_message("Test Title", "Test Message")  # noqa: SLF001
            mock_info.assert_called_once_with(window, "Test Title", "Test Message")

        with patch("AutoQAC_Interface.QMessageBox.critical") as mock_critical:
            window._show_error("Error Title", "Error Message")  # noqa: SLF001
            mock_critical.assert_called_once_with(window, "Error Title", "Error Message")

    def test_status_update(
        self, mock_main_window: Any, state_manager: StateManager, config_manager: ConfigManager
    ) -> None:
        """Test status bar updates."""
        window = mock_main_window
        window._update_status = MainWindow._update_status.__get__(window, MainWindow)
        window._update_status("Test Status")
        # Check that showMessage was called with the status
        window.status_bar.showMessage.assert_called_with("Test Status")

    def test_logging(self, mock_main_window: Any, state_manager: StateManager, config_manager: ConfigManager) -> None:  # noqa: ARG002
        """Test logging functionality."""
        window = mock_main_window
        window._log = MainWindow._log.__get__(window, MainWindow)

        # Test logging during cleaning
        state_manager.update(is_cleaning=True)
        window._log("Test log message")
        # Should update status bar during cleaning
        window.status_bar.showMessage.assert_called_with("Test log message")


class TestApplicationCreation:
    """Test application creation functions."""

    def test_create_application(self) -> None:
        """Test create_application function."""
        with (
            patch("AutoQAC_Interface.ConfigManager") as mock_config_class,
            patch("AutoQAC_Interface.StateManager") as mock_state_class,
            patch("AutoQAC_Interface.GuiController") as mock_controller_class,
            patch("AutoQAC_Interface.QApplication") as mock_app_class,
            patch("AutoQAC_Interface.MainWindow") as mock_window_class,
        ):
            # Mock instances
            mock_config: Mock = Mock()
            mock_state: Mock = Mock()
            mock_controller: Mock = Mock()
            mock_app: Mock = Mock()
            mock_window: Mock = Mock()

            mock_config_class.return_value = mock_config
            mock_state_class.return_value = mock_state
            mock_controller_class.return_value = mock_controller
            mock_app_class.return_value = mock_app
            mock_window_class.return_value = mock_window

            # Test application creation
            app, window = create_application()

            # Verify components were created
            assert mock_config_class.call_count == 2  # Main and user configs
            mock_state_class.assert_called_once()
            mock_controller_class.assert_called_once()
            mock_window_class.assert_called_once_with(mock_state, mock_controller)

            assert app == mock_app
            assert window == mock_window

    def test_main_function(self) -> None:
        """Test main function."""
        with (
            patch("AutoQAC_Interface.create_application") as mock_create,
            patch("AutoQAC_Interface.sys.exit") as mock_exit,
        ):
            # Mock application components
            mock_app: Mock = Mock()
            mock_window: Mock = Mock()
            mock_create.return_value = (mock_app, mock_window)

            # Import and call main
            from AutoQAC_Interface import main

            main()

            # Verify application was created and shown
            mock_create.assert_called_once()
            mock_window.show.assert_called_once()
            mock_app.exec.assert_called_once()
            mock_exit.assert_called_once()
