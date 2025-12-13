"""Test GUI controller functionality."""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
from PySide6.QtWidgets import QWidget

from AutoQACLib.config_manager import ConfigManager
from AutoQACLib.gui_controller import GuiController
from AutoQACLib.state_manager import StateManager


@pytest.fixture
def state_manager() -> StateManager:
    """Create a state manager for testing."""
    return StateManager()


@pytest.fixture
def main_config_manager() -> ConfigManager:
    """Create a main config manager for testing."""
    return ConfigManager(Path("test_main_config.yaml"))


@pytest.fixture
def user_config_manager() -> ConfigManager:
    """Create a user config manager for testing."""
    return ConfigManager(Path("test_user_config.yaml"))


@pytest.fixture
def controller(
    state_manager: StateManager, main_config_manager: ConfigManager, user_config_manager: ConfigManager
) -> GuiController:
    """Create a GUI controller for testing."""
    return GuiController(state_manager, main_config_manager, user_config_manager)


class TestGuiController:
    """Test the GUI controller with real state manager."""

    def test_initialization(
        self, state_manager: StateManager, main_config_manager: ConfigManager, user_config_manager: ConfigManager
    ) -> None:
        """Test controller initialization."""
        controller: GuiController = GuiController(state_manager, main_config_manager, user_config_manager)
        assert controller.state == state_manager
        assert controller.main_config == main_config_manager
        assert controller.user_config == user_config_manager

    def test_configure_load_order_success(self, controller: GuiController) -> None:
        """Test successful load order configuration."""
        with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = ("/path/to/loadorder.txt", "")

            with (
                patch.object(Path, "exists", return_value=True),
                patch.object(controller.user_config, "set", return_value=True),
            ):
                result: bool = controller.configure_load_order(Mock(spec=QWidget))

                assert result is True
                assert controller.state.get("load_order_path") == Path("/path/to/loadorder.txt")

    def test_configure_load_order_cancelled(self, controller: GuiController) -> None:
        """Test cancelled load order configuration."""
        with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = ("", "")

            result: bool = controller.configure_load_order(Mock(spec=QWidget))

            assert result is False

    def test_configure_mo2_success(self, controller: GuiController) -> None:
        """Test successful MO2 configuration."""
        with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = ("/path/to/ModOrganizer.exe", "")

            with (
                patch.object(Path, "exists", return_value=True),
                patch.object(controller.user_config, "update_multiple", return_value=True),
            ):
                result: bool = controller.configure_mo2(Mock(spec=QWidget))

                assert result is True
                assert controller.state.get("mo2_exe_path") == Path("/path/to/ModOrganizer.exe")

    def test_configure_xedit_success(self, controller: GuiController) -> None:
        """Test successful xEdit configuration."""
        with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = ("/path/to/SSEEdit.exe", "")

            with (
                patch.object(Path, "exists", return_value=True),
                patch("AutoQACLib.utils.detect_xedit_game", return_value="SSE"),
                patch.object(controller.user_config, "update_multiple", return_value=True),
            ):
                result: bool = controller.configure_xedit(Mock(spec=QWidget))

                assert result is True
                assert controller.state.get("xedit_exe_path") == Path("/path/to/SSEEdit.exe")
                assert controller.state.get("game_type") == "SSE"

    def test_configure_xedit_invalid_file(self, controller: GuiController) -> None:
        """Test xEdit configuration with invalid file."""
        with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = ("/path/to/invalid.exe", "")

            with patch.object(Path, "exists", return_value=True):
                result: bool = controller.configure_xedit(Mock(spec=QWidget))

                assert result is False

    def test_toggle_mo2_mode(self, controller: GuiController) -> None:
        """Test MO2 mode toggle."""
        with patch.object(controller.user_config, "set", return_value=True):
            controller.toggle_mo2_mode(True)

            assert controller.state.get("mo2_mode") is True

    def test_get_plugins_to_clean_with_file(self, controller: GuiController) -> None:
        """Test getting plugins from load order file."""
        # Set up load order path
        controller.state.update_configuration_paths(load_order_path=Path("/path/to/loadorder.txt"))

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "open", mock_open(read_data="plugin1.esp\nplugin2.esm\n")),
        ):
            plugins: list[str] = controller.get_plugins_to_clean()

            assert plugins == ["plugin1.esp", "plugin2.esm"]

    def test_get_plugins_to_clean_no_file(self, controller: GuiController) -> None:
        """Test getting plugins when file doesn't exist."""
        # Set up load order path
        controller.state.update_configuration_paths(load_order_path=Path("/path/to/loadorder.txt"))

        with patch.object(Path, "exists", return_value=False):
            plugins: list[str] = controller.get_plugins_to_clean()

            # Should return empty list when file doesn't exist
            assert plugins == []

    def test_get_plugins_to_clean_no_path(self, controller: GuiController) -> None:
        """Test getting plugins when no path is configured."""
        plugins: list[str] = controller.get_plugins_to_clean()

        assert plugins == []

    def test_validate_plugin_line_valid(self, controller: GuiController) -> None:
        """Test validation of valid plugin lines."""
        # Test valid plugin names
        assert controller.plugin_validator._validate_plugin_line("plugin1.esp", 1, "plugin1.esp") == "plugin1.esp"  # noqa: SLF001
        assert controller.plugin_validator._validate_plugin_line("plugin2.esm", 2, "plugin2.esm") == "plugin2.esm"  # noqa: SLF001
        assert controller.plugin_validator._validate_plugin_line("plugin3.esl", 3, "plugin3.esl") == "plugin3.esl"  # noqa: SLF001

        # Test with prefix characters
        assert controller.plugin_validator._validate_plugin_line("plugin4.esp", 4, "*plugin4.esp") == "plugin4.esp"  # noqa: SLF001
        assert controller.plugin_validator._validate_plugin_line("plugin5.esm", 5, "+plugin5.esm") == "plugin5.esm"  # noqa: SLF001

    def test_validate_plugin_line_invalid_extension_position(self, controller: GuiController) -> None:
        """Test validation of plugin lines with content after extension."""
        # Test with content after extension
        result1: str | None = controller.plugin_validator._validate_plugin_line(
            "plugin1.esp,plugin2.esp", 1, "plugin1.esp,plugin2.esp"
        )  # noqa: SLF001
        assert result1 == "plugin1.esp"

        result2: str | None = controller.plugin_validator._validate_plugin_line(
            "plugin1.esm;plugin2.esm", 2, "plugin1.esm;plugin2.esm"
        )  # noqa: SLF001
        assert result2 == "plugin1.esm"

        result3: str | None = controller.plugin_validator._validate_plugin_line(  # noqa: SLF001
            "plugin1.esl extra content", 3, "plugin1.esl extra content"
        )
        assert result3 == "plugin1.esl"

    def test_validate_plugin_line_no_extension(self, controller: GuiController) -> None:
        """Test validation of lines without valid extensions."""
        # Test lines without valid extensions
        assert controller.plugin_validator._validate_plugin_line("plugin1.txt", 1, "plugin1.txt") is None  # noqa: SLF001
        assert controller.plugin_validator._validate_plugin_line("plugin1", 2, "plugin1") is None  # noqa: SLF001
        assert controller.plugin_validator._validate_plugin_line("plugin1.esp.bak", 3, "plugin1.esp.bak") is None  # noqa: SLF001

    def test_get_plugins_to_clean_with_malformed_lines(self, controller: GuiController) -> None:
        """Test getting plugins from load order file with malformed lines."""
        # Set up load order path
        controller.state.update_configuration_paths(load_order_path=Path("/path/to/loadorder.txt"))

        # Mock file content with malformed lines
        mock_content: str = """# Load order file
plugin1.esp
plugin2.esp,plugin3.esp
plugin4.esm;plugin5.esm
plugin6.esl extra content
plugin7.esp
"""

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "open", mock_open(read_data=mock_content)),
        ):
            plugins: list[str] = controller.get_plugins_to_clean()

            # Should extract valid plugin names, separating malformed lines
            expected: list[str] = ["plugin1.esp", "plugin2.esp", "plugin4.esm", "plugin6.esl", "plugin7.esp"]
            assert plugins == expected

    def test_start_cleaning_not_configured(self, controller: GuiController) -> None:
        """Test starting cleaning when not fully configured."""
        # Ensure state is not fully configured by default
        assert not controller.state.state.is_fully_configured

        controller.start_cleaning()

        # Should not create worker when not configured
        assert controller.worker is None

    def test_start_cleaning_already_running(self, controller: GuiController) -> None:
        """Test starting cleaning when already running."""
        controller.state.update(is_cleaning=True)

        controller.start_cleaning()

        # Should not create new worker when already cleaning
        assert controller.worker is None

    def test_start_cleaning_success(self, controller: GuiController) -> None:
        """Test successful cleaning start."""
        # Set up full configuration
        controller.state.update_configuration_paths(
            load_order_path=Path("/path/to/loadorder.txt"),
            mo2_exe_path=Path("/path/to/ModOrganizer.exe"),
            xedit_exe_path=Path("/path/to/SSEEdit.exe"),
        )
        controller.state.update(
            is_load_order_configured=True,
            is_mo2_configured=True,
            is_xedit_configured=True,
        )

        with (
            patch.object(controller, "get_plugins_to_clean", return_value=["test.esp"]),
            patch("AutoQACLib.gui_controller.CleaningWorker") as mock_worker_class,
        ):
            mock_worker: Mock = Mock()
            mock_worker_class.return_value = mock_worker

            controller.start_cleaning()

            # Should create and start worker
            mock_worker_class.assert_called_once()
            mock_worker.start.assert_called_once()

    def test_stop_cleaning(self, controller: GuiController) -> None:
        """Test stopping cleaning."""
        with patch("AutoQACLib.cleaning_worker.CleaningWorker") as mock_worker_class:
            mock_worker: Mock = Mock()
            mock_worker.isRunning.return_value = True
            mock_worker_class.return_value = mock_worker

            controller.worker = mock_worker
            controller.stop_cleaning()

            mock_worker.stop.assert_called_once()

    def test_stop_cleaning_no_worker(self, controller: GuiController) -> None:
        """Test stopping cleaning when no worker exists."""
        controller.stop_cleaning()

        # Should not raise any exceptions

    def test_refresh_configuration(self, controller: GuiController) -> None:
        """Test configuration refresh."""
        with patch.object(controller, "_load_configuration") as mock_load:
            controller.refresh_configuration()

            mock_load.assert_called_once()

    def test_get_state_summary(self, controller: GuiController) -> None:
        """Test getting state summary."""
        summary: str = controller.get_state_summary()

        assert isinstance(summary, str)
        assert "Configuration Status" in summary


class TestGuiControllerPartialForms:
    """Test GUI controller with partial forms functionality using mocks."""

    @pytest.fixture
    def mock_state(self) -> Mock:
        """Create a mock state manager."""
        state: Mock = Mock(spec=StateManager)
        state.state.partial_forms_enabled = False
        state.state.mo2_mode = False
        state.state.is_fully_configured = True
        state.state.is_cleaning = False
        state.state.game_type = "SSE"
        state.state.xedit_exe_path = None
        state.state.mo2_exe_path = None
        state.state.load_order_path = None
        state.state.is_load_order_configured = False
        state.state.is_mo2_configured = False
        state.state.is_xedit_configured = False
        return state

    @pytest.fixture
    def mock_main_config(self) -> Mock:
        """Create a mock main config manager."""
        config: Mock = Mock(spec=ConfigManager)
        config.get_game_config.return_value = {"xedit_list": [], "skip_list": []}
        config.get.return_value = []
        return config

    @pytest.fixture
    def mock_user_config(self) -> Mock:
        """Create a mock user config manager."""
        config: Mock = Mock(spec=ConfigManager)
        config.get.return_value = False
        config.set.return_value = True
        config.update_multiple.return_value = True
        config.get_paths.return_value = {}
        config.get_settings.return_value = {}
        return config

    @pytest.fixture
    def partial_forms_controller(
        self, mock_state: Mock, mock_main_config: Mock, mock_user_config: Mock
    ) -> GuiController:
        """Create a GuiController instance for testing."""
        return GuiController(mock_state, mock_main_config, mock_user_config)

    def test_toggle_partial_forms_first_time(
        self, partial_forms_controller: GuiController, mock_user_config: Mock, mock_state: Mock
    ) -> None:
        """Test enabling Partial Forms for the first time shows warning."""
        # Patch defer_config_save to track calls
        with patch.object(partial_forms_controller, "defer_config_save") as mock_defer:
            # Enable Partial Forms
            partial_forms_controller.toggle_partial_forms(True)

            # Verify state was updated
            mock_state.update.assert_called_with(partial_forms_enabled=True)
            # Verify deferred config save was called (consistent with other toggle methods)
            mock_defer.assert_called_with("Settings.Partial_Forms", True)

    def test_toggle_partial_forms_subsequent_time(
        self, partial_forms_controller: GuiController, mock_user_config: Mock, mock_state: Mock
    ) -> None:
        """Test enabling Partial Forms after warning has been shown."""
        # Mock that warning has been shown before
        mock_user_config.get.return_value = True

        # Patch defer_config_save to track calls
        with patch.object(partial_forms_controller, "defer_config_save") as mock_defer:
            # Enable Partial Forms
            partial_forms_controller.toggle_partial_forms(True)

            # Verify state was updated
            mock_state.update.assert_called_with(partial_forms_enabled=True)
            # Verify deferred config save was called (consistent with other toggle methods)
            mock_defer.assert_called_with("Settings.Partial_Forms", True)

    def test_toggle_partial_forms_disable(
        self, partial_forms_controller: GuiController, mock_user_config: Mock, mock_state: Mock
    ) -> None:
        """Test disabling Partial Forms."""
        # Patch defer_config_save to track calls
        with patch.object(partial_forms_controller, "defer_config_save") as mock_defer:
            # Disable Partial Forms
            partial_forms_controller.toggle_partial_forms(False)

            # Verify state was updated
            mock_state.update.assert_called_with(partial_forms_enabled=False)
            # Verify deferred config save was called (consistent with other toggle methods)
            mock_defer.assert_called_with("Settings.Partial_Forms", False)

    def test_toggle_partial_forms_error_handling(
        self, partial_forms_controller: GuiController, mock_user_config: Mock, mock_state: Mock
    ) -> None:
        """Test error handling in Partial Forms toggle."""
        # Mock an error during deferred config save
        with patch.object(
            partial_forms_controller, "defer_config_save", side_effect=OSError("Test error")
        ):
            # Try to enable Partial Forms
            partial_forms_controller.toggle_partial_forms(True)

            # Verify error was handled (state update was attempted)
            mock_state.update.assert_called_with(partial_forms_enabled=True)
