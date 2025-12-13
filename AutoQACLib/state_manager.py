"""Centralized state management for AutoQAC."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QMutex, QMutexLocker, QObject, QReadLocker, QReadWriteLock, QWriteLocker, Signal

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class AppState:
    """Single source of truth for all application state."""

    # Configuration state
    load_order_path: Path | None = None
    mo2_exe_path: Path | None = None
    mo2_install_path: Path | None = None
    xedit_exe_path: Path | None = None
    xedit_install_path: Path | None = None

    # Configuration validity
    is_load_order_configured: bool = False
    is_mo2_configured: bool = False
    is_xedit_configured: bool = False

    # Runtime state
    is_cleaning: bool = False
    current_plugin: str | None = None
    current_operation: str = ""

    # Progress state
    progress: int = 0
    total_plugins: int = 0
    plugins_to_clean: list[str] = field(default_factory=list)

    # Results
    cleaned_plugins: set[str] = field(default_factory=set)
    failed_plugins: set[str] = field(default_factory=set)
    skipped_plugins: set[str] = field(default_factory=set)

    # Settings
    journal_expiration: int = 7
    cleaning_timeout: int = 300
    cpu_threshold: int = 5
    mo2_mode: bool = False
    partial_forms_enabled: bool = False
    game_type: str | None = None
    max_concurrent_subprocesses: int = 3  # Resource limit for subprocesses

    @property
    def is_fully_configured(self) -> bool:
        """Check if all required configuration is present."""
        return all([
            self.is_load_order_configured,
            self.is_mo2_configured,
            self.is_xedit_configured,
        ])

    @property
    def cleaning_stats(self) -> dict[str, int]:
        """Get current cleaning statistics."""
        return {
            "cleaned": len(self.cleaned_plugins),
            "failed": len(self.failed_plugins),
            "skipped": len(self.skipped_plugins),
            "total": self.total_plugins,
        }


class StateManager(QObject):
    """
    Manages the application's state, updating and synchronizing state attributes,
    emitting signals for changes, and handling state-related logic.

    This class provides methods for updating single or multiple state properties,
    retrieving state values, and managing the progress of processes such as plugin
    cleaning. Specialized signals are emitted to notify other components of specific
    state changes, ensuring a reactive and thread-safe environment.

    Attributes:
        state_changed (Signal): Signal emitted when individual state properties change.
            Provides the property name and its new value.
        bulk_state_changed (Signal): Signal emitted when multiple state properties
            change simultaneously. Provides a dictionary of changes.
        configuration_changed (Signal): Signal emitted when configuration changes occur,
            specifying whether full configuration is achieved.
        progress_changed (Signal): Signal emitted when process progress is updated,
            providing the current progress and total steps.
        cleaning_started (Signal): Signal emitted when the cleaning process starts.
        cleaning_finished (Signal): Signal emitted when the cleaning process finishes.
        plugin_processed (Signal): Signal emitted when a plugin is processed during
            cleaning, providing the plugin name, status, and an optional message.
    """

    # Signals for state changes
    state_changed: Signal = Signal(str, object)  # (property_name, new_value)
    bulk_state_changed: Signal = Signal(dict)  # dict of multiple state changes
    configuration_changed: Signal = Signal(bool)  # is_fully_configured
    progress_changed: Signal = Signal(int, int)  # current, total
    cleaning_started: Signal = Signal()
    cleaning_finished: Signal = Signal()
    plugin_processed: Signal = Signal(str, str, str)  # plugin, status, message

    def __init__(self) -> None:
        """Initialize the state manager."""
        super().__init__()
        self._state = AppState()
        self._rw_lock = QReadWriteLock()
        self._signal_mutex = QMutex()

    def update(self, **kwargs: Any) -> None:
        """
        Updates the internal state of the object with provided keyword arguments, emitting
        signals for state changes and handling specific state logic.

        This method uses a write lock to ensure thread-safe updates and atomic signal emission.
        It identifies changes to the state attributes and emits appropriate signals to notify
        listeners about the modifications. Aggregated signals are also emitted when certain
        related states are altered.

        Args:
            **kwargs: Arbitrary keyword arguments representing the state attributes to be
                updated and their new values. Attribute keys must correspond to existing
                keys in the object's internal state.
        """
        config_changed = False
        progress_changed = False
        state_changes: list[tuple[str, object]] = []
        cleaning_started = False
        cleaning_finished = False
        is_fully_configured = False
        current_progress = 0
        total_plugins = 0

        # Update state atomically - minimize lock time
        with QWriteLocker(self._rw_lock):
            for key, value in kwargs.items():
                if hasattr(self._state, key):
                    old_value = getattr(self._state, key)
                    if old_value != value:
                        setattr(self._state, key, value)
                        state_changes.append((key, value))

                        # Check for specific state changes
                        if key in ["is_load_order_configured", "is_mo2_configured", "is_xedit_configured"]:
                            config_changed = True
                        elif key in ["progress", "total_plugins"]:
                            progress_changed = True
                        elif key == "is_cleaning":
                            if value:
                                cleaning_started = True
                            else:
                                cleaning_finished = True

            # Capture values needed for signals while still holding lock
            if config_changed:
                is_fully_configured = self._state.is_fully_configured
            if progress_changed:
                current_progress = self._state.progress
                total_plugins = self._state.total_plugins

        # Emit signals OUTSIDE the write lock to prevent blocking
        if state_changes:
            with QMutexLocker(self._signal_mutex):
                # Use bulk signal for multiple changes to reduce overhead
                if len(state_changes) > 3:
                    # Convert to dict for bulk signal
                    changes_dict = dict(state_changes)
                    self.bulk_state_changed.emit(changes_dict)
                else:
                    # Emit individual signals for small number of changes
                    for key, value in state_changes:
                        self.state_changed.emit(key, value)

                # Emit special signals
                if cleaning_started:
                    self.cleaning_started.emit()
                elif cleaning_finished:
                    self.cleaning_finished.emit()

                # Emit aggregate signals with cached values
                if config_changed:
                    self.configuration_changed.emit(is_fully_configured)
                if progress_changed:
                    self.progress_changed.emit(current_progress, total_plugins)

    def update_multiple_properties(self, updates: dict[str, Any]) -> None:
        """
        Atomically updates multiple properties at once.

        This method ensures that all property updates happen together without
        any intermediate state being visible to other threads. This is just a
        wrapper around update() for clarity.

        Args:
            updates: Dictionary of property names and their new values.
        """
        self.update(**updates)

    def get(self, property_name: str, default: Any = None) -> Any:
        """
        Retrieves the value of a specified property from the internal state.

        This method fetches the value of a given property from the object's internal state,
        safely synchronizing access with a mutex lock to ensure thread safety. If the
        property does not exist, a default value is returned.

        Args:
            property_name (str): The name of the property whose value is to be retrieved.
            default (Any, optional): The value to be returned if the property does not
                exist. Defaults to None.

        Returns:
            Any: The value of the requested property, or the default value if the
            property does not exist.
        """
        with QReadLocker(self._rw_lock):
            return getattr(self._state, property_name, default)

    @property
    def state(self) -> AppState:
        """
        Returns a copy of the current application state.

        The property ensures thread-safe read access to the `_state` attribute
        using a read-write lock. It creates and returns a copy of the `_state`
        to preserve immutability, preventing external modifications.

        Returns:
            AppState: A copy of the application's current state.
        """
        with QReadLocker(self._rw_lock):
            return replace(self._state)

    def add_result(self, plugin: str, status: str, message: str = "") -> None:
        """
        Adds a result associated with a plugin and updates the state. This function records
        the status of a specified plugin, updates the relevant state set (e.g., cleaned,
        failed, skipped, etc.), increments the progress count, and emits related signals
        to notify about the progress and processing status.

        Args:
            plugin (str): The name of the plugin being processed.
            status (str): The status of the plugin processing. Possible values are
                'cleaned', 'failed', or 'skipped'.
            message (str, optional): A message providing additional context about the
                plugin processing. Defaults to an empty string.
        """
        # Capture values for signals - minimize lock time
        current_progress = 0
        total_plugins = 0

        # Update state atomically
        with QWriteLocker(self._rw_lock):
            if status == "cleaned":
                self._state.cleaned_plugins.add(plugin)
            elif status == "failed":
                self._state.failed_plugins.add(plugin)
            elif status == "skipped":
                self._state.skipped_plugins.add(plugin)

            self._state.progress += 1
            current_progress = self._state.progress
            total_plugins = self._state.total_plugins

        # Emit signals OUTSIDE the write lock to prevent blocking other threads
        with QMutexLocker(self._signal_mutex):
            self.plugin_processed.emit(plugin, status, message)
            self.progress_changed.emit(current_progress, total_plugins)

    def reset_cleaning_state(self) -> None:
        """
        Resets the cleaning state to its initial default values.

        This method is used to clear all data related to the current cleaning
        operation. It ensures that all relevant attributes in the state are reset
        to their initial states, effectively preparing the system for a new cleaning
        process.

        Returns:
            None
        """
        with QWriteLocker(self._rw_lock):
            self._state.is_cleaning = False
            self._state.current_plugin = None
            self._state.current_operation = ""
            self._state.progress = 0
            self._state.total_plugins = 0
            self._state.plugins_to_clean.clear()
            self._state.cleaned_plugins.clear()
            self._state.failed_plugins.clear()
            self._state.skipped_plugins.clear()

    def update_configuration_paths(
        self,
        load_order_path: Path | None = None,
        mo2_exe_path: Path | None = None,
        mo2_install_path: Path | None = None,
        xedit_exe_path: Path | None = None,
        xedit_install_path: Path | None = None,
    ) -> None:
        """
        Updates configuration paths for the specified components and verifies their
        existence if applicable. The method allows for updating paths related to load
        order, Mod Organizer 2 (MO2), and xEdit, while avoiding UI blocking checks.

        Args:
            load_order_path (Path | None): The file path for the load order configuration.
                If None, the load order path will not be updated.
            mo2_exe_path (Path | None): The file path for the Mod Organizer 2 executable.
                If None, the MO2 executable path will not be updated.
            mo2_install_path (Path | None): The file path for the Mod Organizer 2
                installation directory. If None, the MO2 installation path will not be
                updated.
            xedit_exe_path (Path | None): The file path for the xEdit executable. If None,
                the xEdit executable path will not be updated.
            xedit_install_path (Path | None): The file path for the xEdit installation
                directory. If None, the xEdit installation path will not be updated.
        """
        updates: dict[str, Any] = {}

        if load_order_path is not None:
            updates["load_order_path"] = load_order_path
            # Check file existence (synchronous - acceptable for Path.exists())
            try:
                updates["is_load_order_configured"] = load_order_path.exists()
            except (OSError, PermissionError):
                updates["is_load_order_configured"] = False

        if mo2_exe_path is not None:
            updates["mo2_exe_path"] = mo2_exe_path
            # Check file existence (synchronous - acceptable for Path.exists())
            try:
                updates["is_mo2_configured"] = mo2_exe_path.exists()
            except (OSError, PermissionError):
                updates["is_mo2_configured"] = False
            if mo2_install_path:
                updates["mo2_install_path"] = mo2_install_path

        if xedit_exe_path is not None:
            updates["xedit_exe_path"] = xedit_exe_path
            # Check file existence (synchronous - acceptable for Path.exists())
            try:
                updates["is_xedit_configured"] = xedit_exe_path.exists()
            except (OSError, PermissionError):
                updates["is_xedit_configured"] = False
            if xedit_install_path:
                updates["xedit_install_path"] = xedit_install_path

        if updates:
            self.update(**updates)
