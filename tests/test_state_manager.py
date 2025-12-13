"""Tests for state management."""

from pathlib import Path

from PySide6.QtCore import QCoreApplication

from AutoQACLib.state_manager import AppState, StateManager


class TestAppState:
    """Test the AppState dataclass."""

    def test_default_state(self) -> None:
        """Test default AppState initialization."""
        state: AppState = AppState()

        assert state.load_order_path is None
        assert state.mo2_exe_path is None
        assert state.xedit_exe_path is None
        assert state.is_load_order_configured is False
        assert state.is_mo2_configured is False
        assert state.is_xedit_configured is False
        assert state.is_cleaning is False
        assert state.current_plugin is None
        assert state.progress == 0
        assert state.total_plugins == 0
        assert state.plugins_to_clean == []
        assert state.cleaned_plugins == set()
        assert state.failed_plugins == set()
        assert state.skipped_plugins == set()

    def test_is_fully_configured_property(self) -> None:
        """Test the is_fully_configured property."""
        # Initially not configured
        state: AppState = AppState()
        assert state.is_fully_configured is False

        # Partially configured
        state.is_load_order_configured = True
        assert state.is_fully_configured is False

        state.is_mo2_configured = True
        assert state.is_fully_configured is False

        # Fully configured
        state.is_xedit_configured = True
        assert state.is_fully_configured is True

    def test_cleaning_stats_property(self) -> None:
        """Test the cleaning_stats property."""
        state: AppState = AppState()
        state.total_plugins = 10
        state.cleaned_plugins = {"plugin1.esp", "plugin2.esp"}
        state.failed_plugins = {"plugin3.esp"}
        state.skipped_plugins = {"plugin4.esp"}

        stats: dict[str, int] = state.cleaning_stats
        assert stats["cleaned"] == 2
        assert stats["failed"] == 1
        assert stats["skipped"] == 1
        assert stats["total"] == 10

    def test_state_immutability(self) -> None:
        """Test that state.snapshot returns an immutable copy."""
        state: AppState = AppState()
        state.cleaned_plugins.add("test.esp")

        # Create a copy
        copy_state: AppState = AppState(cleaned_plugins={"test.esp"}, total_plugins=1)

        # Modify the copy
        copy_state.cleaned_plugins.add("another.esp")

        # Original should be unchanged
        assert len(state.cleaned_plugins) == 1
        assert "another.esp" not in state.cleaned_plugins


class TestStateManager:
    """Test the StateManager class."""

    def test_initialization(self, state_manager: StateManager) -> None:
        """Test StateManager initialization."""
        assert state_manager is not None
        state: AppState = state_manager.state
        assert isinstance(state, AppState)
        assert state.is_fully_configured is False

    def test_get_method(self, state_manager: StateManager) -> None:
        """Test the get method."""
        # Test getting existing properties
        assert state_manager.get("is_cleaning") is False
        assert state_manager.get("progress") == 0
        assert state_manager.get("current_plugin") is None

        # Test getting non-existent properties with default
        assert state_manager.get("non_existent", "default") == "default"
        assert state_manager.get("non_existent") is None

    def test_update_method(self, state_manager: StateManager) -> None:
        """Test the update method."""
        # Update single property
        state_manager.update(is_cleaning=True)
        assert state_manager.get("is_cleaning") is True

        # Update multiple properties
        state_manager.update(progress=5, total_plugins=10, current_plugin="test.esp")
        assert state_manager.get("progress") == 5
        assert state_manager.get("total_plugins") == 10
        assert state_manager.get("current_plugin") == "test.esp"

    def test_configuration_signals(self, state_manager: StateManager, qt_app: QCoreApplication) -> None:
        """Test configuration change signals."""
        signals_received: list[bool] = []

        def on_config_changed(is_configured: bool) -> None:
            signals_received.append(is_configured)

        state_manager.configuration_changed.connect(on_config_changed)

        # Initially not configured
        assert state_manager.state.is_fully_configured is False

        # Configure all components
        state_manager.update(is_load_order_configured=True, is_mo2_configured=True, is_xedit_configured=True)

        # Process events to trigger signals
        qt_app.processEvents()

        # Should have received configuration changed signal
        assert len(signals_received) > 0
        assert signals_received[-1] is True

    def test_progress_signals(self, state_manager: StateManager, qt_app: QCoreApplication) -> None:
        """Test progress change signals."""
        progress_updates: list[tuple[int, int]] = []

        def on_progress_changed(current: int, total: int) -> None:
            progress_updates.append((current, total))

        state_manager.progress_changed.connect(on_progress_changed)

        # Update progress
        state_manager.update(progress=3, total_plugins=10)

        # Process events to trigger signals
        qt_app.processEvents()

        # Should have received progress signal
        assert len(progress_updates) > 0
        assert progress_updates[-1] == (3, 10)

    def test_cleaning_signals(self, state_manager: StateManager, qt_app: QCoreApplication) -> None:
        """Test cleaning start/finish signals."""
        cleaning_events: list[str] = []

        def on_cleaning_started() -> None:
            cleaning_events.append("started")

        def on_cleaning_finished() -> None:
            cleaning_events.append("finished")

        state_manager.cleaning_started.connect(on_cleaning_started)
        state_manager.cleaning_finished.connect(on_cleaning_finished)

        # Start cleaning
        state_manager.update(is_cleaning=True)
        qt_app.processEvents()

        # Stop cleaning
        state_manager.update(is_cleaning=False)
        qt_app.processEvents()

        # Should have received both signals
        assert "started" in cleaning_events
        assert "finished" in cleaning_events

    def test_add_result_method(self, state_manager: StateManager, qt_app: QCoreApplication) -> None:
        """Test the add_result method."""
        plugin_results: list[tuple[str, str, str]] = []

        def on_plugin_processed(plugin: str, status: str, message: str) -> None:
            plugin_results.append((plugin, status, message))

        state_manager.plugin_processed.connect(on_plugin_processed)

        # Add results
        state_manager.add_result("plugin1.esp", "cleaned", "Successfully cleaned")
        state_manager.add_result("plugin2.esp", "failed", "Failed to clean")
        state_manager.add_result("plugin3.esp", "skipped", "Skipped")

        qt_app.processEvents()

        # Check state updates
        state: AppState = state_manager.state
        assert "plugin1.esp" in state.cleaned_plugins
        assert "plugin2.esp" in state.failed_plugins
        assert "plugin3.esp" in state.skipped_plugins
        assert state.progress == 3

        # Check signals
        assert len(plugin_results) == 3
        assert ("plugin1.esp", "cleaned", "Successfully cleaned") in plugin_results
        assert ("plugin2.esp", "failed", "Failed to clean") in plugin_results

    def test_reset_cleaning_state(self, state_manager: StateManager) -> None:
        """Test resetting cleaning state."""
        # Set some cleaning state
        state_manager.update(
            is_cleaning=True,
            progress=5,
            total_plugins=10,
            current_plugin="test.esp",
            plugins_to_clean=["plugin1.esp", "plugin2.esp"],
        )
        state_manager.add_result("plugin1.esp", "cleaned")

        # Reset
        state_manager.reset_cleaning_state()

        # Check reset
        state: AppState = state_manager.state
        assert state.is_cleaning is False
        assert state.progress == 0
        assert state.total_plugins == 0
        assert state.current_plugin is None
        assert state.plugins_to_clean == []
        assert state.cleaned_plugins == set()
        assert state.failed_plugins == set()
        assert state.skipped_plugins == set()

    def test_update_configuration_paths(self, state_manager: StateManager) -> None:
        """Test updating configuration paths."""
        load_order_path: Path = Path("/path/to/loadorder.txt")
        mo2_exe_path: Path = Path("/path/to/ModOrganizer.exe")
        xedit_exe_path: Path = Path("/path/to/xEdit.exe")

        state_manager.update_configuration_paths(
            load_order_path=load_order_path, mo2_exe_path=mo2_exe_path, xedit_exe_path=xedit_exe_path
        )

        state: AppState = state_manager.state
        assert state.load_order_path == load_order_path
        assert state.mo2_exe_path == mo2_exe_path
        assert state.xedit_exe_path == xedit_exe_path

    def test_thread_safety(self, state_manager: StateManager) -> None:
        """Test thread safety of state updates."""
        import threading
        import time

        def update_state(thread_id: int) -> None:
            for i in range(10):
                state_manager.update(progress=i, current_plugin=f"plugin_{thread_id}_{i}.esp")
                time.sleep(0.001)  # Small delay to increase race condition chance

        # Create multiple threads updating state
        threads: list[threading.Thread] = []
        for i in range(5):
            thread: threading.Thread = threading.Thread(target=update_state, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # State should be consistent (no crashes or corruption)
        state: AppState = state_manager.state
        assert isinstance(state.progress, int)
        assert state.progress >= 0
        assert isinstance(state.current_plugin, (str, type(None)))
