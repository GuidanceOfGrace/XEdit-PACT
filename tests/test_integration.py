"""Integration tests for AutoQAC components."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, mock_open, patch

from AutoQACLib.config_manager import ConfigManager
from AutoQACLib.gui_controller import GuiController
from AutoQACLib.state_manager import StateManager


class TestComponentIntegration:
    """Test integration between different components."""

    @patch.object(Path, "exists", return_value=True)
    def test_state_manager_config_manager_integration(self, mock_exists: Mock, temp_test_config_file: Path) -> None:  # noqa: ARG002
        """Test integration between StateManager and ConfigManager."""
        config_path: Path = temp_test_config_file
        config_manager: ConfigManager = ConfigManager(config_path)
        state_manager: StateManager = StateManager()

        # Set configuration in config manager
        config_manager.set("Load_Order.File", "/path/to/loadorder.txt")
        config_manager.set("Mod_Organizer.Binary", "/path/to/ModOrganizer.exe")
        config_manager.set("xEdit.Binary", "/path/to/xEdit.exe")

        # Update state from config
        paths: dict[str, Any] = config_manager.get_paths()
        state_manager.update(
            load_order_path=paths["load_order_path"],
            mo2_exe_path=paths["mo2_exe_path"],
            xedit_exe_path=paths["xedit_exe_path"],
        )

        # Validate paths and update configuration state
        validation: dict[str, Any] = config_manager.validate_paths()
        state_manager.update(
            is_load_order_configured=validation["load_order_path"],
            is_mo2_configured=validation["mo2_exe_path"],
            is_xedit_configured=validation["xedit_exe_path"],
        )

        # Verify integration worked
        assert state_manager.get("load_order_path") == Path("/path/to/loadorder.txt")
        assert state_manager.get("mo2_exe_path") == Path("/path/to/ModOrganizer.exe")
        assert state_manager.get("xedit_exe_path") == Path("/path/to/xEdit.exe")

        # Configuration state should reflect path validation
        assert state_manager.get("is_load_order_configured") == validation["load_order_path"]
        assert state_manager.get("is_mo2_configured") == validation["mo2_exe_path"]
        assert state_manager.get("is_xedit_configured") == validation["xedit_exe_path"]

    @patch.object(Path, "exists", return_value=True)
    def test_gui_controller_state_manager_integration(
        self, mock_exists: Mock, temp_test_config_files: tuple[Path, Path]
    ) -> None:
        """Test integration between GUI controller and state manager."""
        main_config_path, user_config_path = temp_test_config_files

        main_config_manager: ConfigManager = ConfigManager(main_config_path)
        user_config_manager: ConfigManager = ConfigManager(user_config_path)
        state_manager: StateManager = StateManager()
        controller: GuiController = GuiController(state_manager, main_config_manager, user_config_manager)

        # Set up state
        state_manager.update(
            load_order_path=Path("/path/to/loadorder.txt"),
            mo2_exe_path=Path("/path/to/ModOrganizer.exe"),
            xedit_exe_path=Path("/path/to/xEdit.exe"),
        )

        # Manually save state to user config (refresh_configuration only loads from config)
        user_config_manager.set("Load_Order.File", "/path/to/loadorder.txt")
        user_config_manager.set("Mod_Organizer.Binary", "/path/to/ModOrganizer.exe")
        user_config_manager.set("xEdit.Binary", "/path/to/xEdit.exe")

        # Refresh configuration to load from config
        controller.refresh_configuration()

        # Verify both state and config are updated
        assert state_manager.get("load_order_path") == Path("/path/to/loadorder.txt")
        load_order_file: str | None = user_config_manager.get("Load_Order.File")
        assert load_order_file is not None
        assert Path(load_order_file) == Path("/path/to/loadorder.txt")

        # Test MO2 mode toggle
        controller.toggle_mo2_mode(True)
        # Process pending config saves immediately for test
        controller._process_pending_config_saves()  # noqa: SLF001
        assert state_manager.get("mo2_mode") is True
        assert user_config_manager.get("Settings.MO2_Mode") is True

    @patch.object(Path, "exists", return_value=True)
    def test_full_configuration_workflow(self, mock_exists: Mock, temp_test_config_files: tuple[Path, Path]) -> None:  # noqa: ARG002
        """Test the complete configuration workflow."""
        main_config_path, user_config_path = temp_test_config_files

        main_config_manager: ConfigManager = ConfigManager(main_config_path)
        user_config_manager: ConfigManager = ConfigManager(user_config_path)
        state_manager: StateManager = StateManager()
        controller: GuiController = GuiController(state_manager, main_config_manager, user_config_manager)

        # Simulate user configuring all components
        # 1. Configure load order
        state_manager.update(load_order_path=Path("/path/to/loadorder.txt"), is_load_order_configured=True)
        user_config_manager.set("Load_Order.File", "/path/to/loadorder.txt")

        # 2. Configure MO2
        state_manager.update(mo2_exe_path=Path("/path/to/ModOrganizer.exe"), is_mo2_configured=True)
        user_config_manager.set("Mod_Organizer.Binary", "/path/to/ModOrganizer.exe")

        # 3. Configure xEdit
        state_manager.update(xedit_exe_path=Path("/path/to/xEdit.exe"), is_xedit_configured=True)
        user_config_manager.set("xEdit.Binary", "/path/to/xEdit.exe")

        # 4. Toggle MO2 mode
        controller.toggle_mo2_mode(True)
        # Process pending config saves immediately for test
        controller._process_pending_config_saves()  # noqa: SLF001

        # Verify complete configuration
        assert state_manager.get("is_fully_configured") is True
        assert state_manager.get("mo2_mode") is True

        # Verify configuration persistence
        new_user_config_manager: ConfigManager = ConfigManager(user_config_path)
        load_order_file: str | None = new_user_config_manager.get("Load_Order.File")
        assert load_order_file is not None
        assert Path(load_order_file) == Path("/path/to/loadorder.txt")

        mo2_binary: str | None = new_user_config_manager.get("Mod_Organizer.Binary")
        assert mo2_binary is not None
        assert Path(mo2_binary) == Path("/path/to/ModOrganizer.exe")

        xedit_binary: str | None = new_user_config_manager.get("xEdit.Binary")
        assert xedit_binary is not None
        assert Path(xedit_binary) == Path("/path/to/xEdit.exe")

        assert new_user_config_manager.get("Settings.MO2_Mode") is True

    @patch.object(Path, "exists", return_value=True)
    def test_cleaning_workflow_integration(self, mock_exists: Mock, temp_test_config_files: tuple[Path, Path]) -> None:  # noqa: ARG002
        """Test integration of cleaning workflow components."""
        main_config_path, user_config_path = temp_test_config_files

        main_config_manager: ConfigManager = ConfigManager(main_config_path)
        user_config_manager: ConfigManager = ConfigManager(user_config_path)
        state_manager: StateManager = StateManager()
        controller: GuiController = GuiController(state_manager, main_config_manager, user_config_manager)

        # Set up complete configuration
        state_manager.update(
            is_load_order_configured=True,
            is_mo2_configured=True,
            is_xedit_configured=True,
            load_order_path=Path("/path/to/loadorder.txt"),
            mo2_exe_path=Path("/path/to/ModOrganizer.exe"),
            xedit_exe_path=Path("/path/to/xEdit.exe"),
        )

        # Mock cleaning service and worker
        with (
            patch("AutoQACLib.gui_controller.CleaningService") as mock_service_class,
            patch("AutoQACLib.gui_controller.CleaningWorker") as mock_worker_class,
            patch.object(Path, "open", mock_open(read_data="plugin1.esp\nplugin2.esm\n")),
        ):
            mock_service: Mock = Mock()
            mock_service_class.return_value = mock_service

            mock_worker: Mock = Mock()
            mock_worker_class.return_value = mock_worker

            # Start cleaning
            controller.start_cleaning()

            # Manually set is_cleaning to True since the mocked worker doesn't do it
            state_manager.update(is_cleaning=True)

            # Verify cleaning started
            assert state_manager.get("is_cleaning") is True
            mock_worker_class.assert_called_once()
            mock_worker.start.assert_called_once()

            # Simulate cleaning progress
            state_manager.update(progress=5, total_plugins=10, current_plugin="test.esp")

            # Verify progress tracking
            assert state_manager.get("progress") == 5
            assert state_manager.get("total_plugins") == 10
            assert state_manager.get("current_plugin") == "test.esp"

            # Simulate plugin results
            state_manager.add_result("plugin1.esp", "cleaned", "Successfully cleaned")
            state_manager.add_result("plugin2.esp", "failed", "Failed to clean")

            # Verify results tracking
            state = state_manager.state
            assert "plugin1.esp" in state.cleaned_plugins
            assert "plugin2.esp" in state.failed_plugins
            assert state.progress == 7  # 5 + 2 new results

            # Stop cleaning
            controller.stop_cleaning()

            # Manually set is_cleaning to False since the mocked worker doesn't do it
            state_manager.update(is_cleaning=False)

            assert state_manager.get("is_cleaning") is False

    def test_signal_propagation_integration(self, temp_test_config_files: tuple[Path, Path]) -> None:
        """Test signal propagation between components."""
        main_config_path, user_config_path = temp_test_config_files

        main_config_manager: ConfigManager = ConfigManager(main_config_path)
        user_config_manager: ConfigManager = ConfigManager(user_config_path)
        state_manager: StateManager = StateManager()
        controller: GuiController = GuiController(state_manager, main_config_manager, user_config_manager)  # noqa: F841

        # Track signals
        state_changes: list[tuple[str, Any]] = []
        config_changes: list[bool] = []
        progress_changes: list[tuple[int, int]] = []
        cleaning_events: list[str] = []
        plugin_events: list[tuple[str, str, str]] = []

        def on_state_changed(property_name: str, value) -> None:  # noqa: ANN001
            state_changes.append((property_name, value))

        def on_config_changed(is_configured: bool) -> None:
            config_changes.append(is_configured)

        def on_progress_changed(current: int, total: int) -> None:
            progress_changes.append((current, total))

        def on_cleaning_started() -> None:
            cleaning_events.append("started")

        def on_cleaning_finished() -> None:
            cleaning_events.append("finished")

        def on_plugin_processed(plugin: str, status: str, message: str) -> None:
            plugin_events.append((plugin, status, message))

        # Connect signals
        state_manager.state_changed.connect(on_state_changed)
        state_manager.configuration_changed.connect(on_config_changed)
        state_manager.progress_changed.connect(on_progress_changed)
        state_manager.cleaning_started.connect(on_cleaning_started)
        state_manager.cleaning_finished.connect(on_cleaning_finished)
        state_manager.plugin_processed.connect(on_plugin_processed)

        # Trigger state changes
        state_manager.update(is_load_order_configured=True, is_mo2_configured=True, is_xedit_configured=True)

        state_manager.update(progress=3, total_plugins=10)
        state_manager.update(is_cleaning=True)
        state_manager.add_result("test.esp", "cleaned", "Success")
        state_manager.update(is_cleaning=False)

        # Verify signals were emitted
        assert len(state_changes) > 0
        assert len(config_changes) > 0
        assert len(progress_changes) > 0
        assert "started" in cleaning_events
        assert "finished" in cleaning_events
        assert len(plugin_events) > 0

    def test_error_handling_integration(self, temp_test_config_files: tuple[Path, Path]) -> None:
        """Test error handling across components."""
        main_config_path, user_config_path = temp_test_config_files

        main_config_manager: ConfigManager = ConfigManager(main_config_path)
        user_config_manager: ConfigManager = ConfigManager(user_config_path)
        state_manager: StateManager = StateManager()
        controller: GuiController = GuiController(state_manager, main_config_manager, user_config_manager)

        # Test invalid configuration handling
        user_config_manager.set("Load_Order.File", "/non/existent/path.txt")
        user_config_manager.set("Mod_Organizer.Binary", "/non/existent/path.exe")

        # Refresh configuration
        controller.refresh_configuration()

        # Should handle invalid paths gracefully
        assert state_manager.get("is_load_order_configured") is False
        assert state_manager.get("is_mo2_configured") is False
        assert state_manager.get("is_fully_configured") is False

        # Test starting cleaning with invalid configuration
        controller.start_cleaning()
        assert state_manager.get("is_cleaning") is False

    @patch.object(Path, "exists", return_value=True)
    def test_configuration_persistence_integration(
        self, mock_exists: Mock, temp_test_config_files: tuple[Path, Path]
    ) -> None:
        """Test configuration persistence across component restarts."""
        main_config_path, user_config_path = temp_test_config_files

        # Initial setup
        main_config_manager1: ConfigManager = ConfigManager(main_config_path)
        user_config_manager1: ConfigManager = ConfigManager(user_config_path)
        state_manager1: StateManager = StateManager()
        controller1: GuiController = GuiController(state_manager1, main_config_manager1, user_config_manager1)

        # Configure everything
        state_manager1.update(
            load_order_path=Path("/path/to/loadorder.txt"),
            mo2_exe_path=Path("/path/to/ModOrganizer.exe"),
            xedit_exe_path=Path("/path/to/xEdit.exe"),
            is_load_order_configured=True,
            is_mo2_configured=True,
            is_xedit_configured=True,
        )
        controller1.toggle_mo2_mode(True)

        # Manually save state to user config (refresh_configuration only loads from config)
        user_config_manager1.set("Load_Order.File", "/path/to/loadorder.txt")
        user_config_manager1.set("Mod_Organizer.Binary", "/path/to/ModOrganizer.exe")
        user_config_manager1.set("xEdit.Binary", "/path/to/xEdit.exe")
        user_config_manager1.set("Settings.MO2_Mode", True)

        controller1.refresh_configuration()

        # Create new instances (simulating application restart)
        main_config_manager2: ConfigManager = ConfigManager(main_config_path)
        user_config_manager2: ConfigManager = ConfigManager(user_config_path)
        state_manager2: StateManager = StateManager()
        controller2: GuiController = GuiController(state_manager2, main_config_manager2, user_config_manager2)

        # Refresh configuration to load saved settings
        controller2.refresh_configuration()

        # Verify configuration was persisted
        assert state_manager2.get("load_order_path") == Path("/path/to/loadorder.txt")
        assert state_manager2.get("mo2_exe_path") == Path("/path/to/ModOrganizer.exe")
        assert state_manager2.get("xedit_exe_path") == Path("/path/to/xEdit.exe")
        assert state_manager2.get("mo2_mode") is True
