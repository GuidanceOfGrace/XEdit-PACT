"""Controller to mediate between GUI and business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QMutex, QMutexLocker, QObject, QTimer, Signal

from AutoQACLib.cleaning_service import CleaningService
from AutoQACLib.cleaning_worker import CleaningWorker
from AutoQACLib.configuration_dialogs import ConfigurationDialogs
from AutoQACLib.logging_config import get_logger
from AutoQACLib.plugin_validator import PluginValidator

if TYPE_CHECKING:
    from pathlib import Path

    from PySide6.QtWidgets import QWidget

    from AutoQACLib.config_manager import ConfigManager
    from AutoQACLib.state_manager import AppState, StateManager

logger = get_logger(__name__)


class GuiController(QObject):
    """Mediates between GUI and business logic."""

    # Signals for GUI updates
    show_message: Signal = Signal(str, str)  # title, message
    show_error: Signal = Signal(str, str)  # title, message
    update_status: Signal = Signal(str)  # status message

    def __init__(
        self,
        state: StateManager,
        main_config: ConfigManager,
        user_config: ConfigManager,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the GUI controller."""
        super().__init__(parent)
        self.state: StateManager = state
        self.main_config: ConfigManager = main_config  # For skip lists and game configs
        self.user_config: ConfigManager = user_config  # For user settings
        self.worker: CleaningWorker | None = None
        self._cleaning_finished_handled: bool = False  # Flag to prevent duplicate dialogs

        # Deferred configuration saves to avoid deadlocks
        self._pending_config_saves: list[tuple[str, Any]] = []
        self._pending_saves_mutex = QMutex()  # Mutex to protect the pending saves list
        self._config_save_timer = QTimer(self)
        self._config_save_timer.setSingleShot(True)
        self._config_save_timer.timeout.connect(self._process_pending_config_saves)
        self._config_save_timer.setInterval(100)  # 100ms delay

        # Create cleaning service with both config managers
        self.service: CleaningService = CleaningService(main_config, user_config, state)

        # Create helper instances
        self.config_dialogs = ConfigurationDialogs(self)
        self.plugin_validator = PluginValidator(state)

        # Load initial configuration
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from file into state."""
        # Load paths from user config
        paths: dict[str, Path | None] = self.user_config.get_paths()
        self.state.update_configuration_paths(
            load_order_path=paths.get("load_order_path"),
            mo2_exe_path=paths.get("mo2_exe_path"),
            mo2_install_path=paths.get("mo2_install_path"),
            xedit_exe_path=paths.get("xedit_exe_path"),
            xedit_install_path=paths.get("xedit_install_path"),
        )

        # Load settings from user config
        settings: dict[str, Any] = self.user_config.get_settings()

        # Load specific settings
        partial_forms_enabled = self.user_config.get("Settings.Partial_Forms", False)
        mo2_mode = self.user_config.get("Settings.MO2_Mode", False)

        settings["partial_forms_enabled"] = partial_forms_enabled
        settings["mo2_mode"] = mo2_mode

        self.state.update(**settings)

    def configure_load_order(self, parent_widget: QWidget) -> bool:
        """Delegate to configuration dialogs handler."""
        return self.config_dialogs.configure_load_order(parent_widget)

    def configure_mo2(self, parent_widget: QWidget) -> bool:
        """Delegate to configuration dialogs handler."""
        return self.config_dialogs.configure_mo2(parent_widget)

    def configure_xedit(self, parent_widget: QWidget) -> bool:
        """Delegate to configuration dialogs handler."""
        return self.config_dialogs.configure_xedit(parent_widget)

    def toggle_mo2_mode(self, enabled: bool) -> None:
        """Delegate to configuration dialogs handler."""
        self.config_dialogs.toggle_mo2_mode(enabled)

    def toggle_partial_forms(self, enabled: bool) -> None:
        """Delegate to configuration dialogs handler."""
        self.config_dialogs.toggle_partial_forms(enabled)

    def get_plugins_to_clean(self) -> list[str]:
        """Delegate to plugin validator."""
        return self.plugin_validator.get_plugins_to_clean()

    def start_cleaning(self) -> None:
        """
        Starts the cleaning process if all prerequisites are met and no other cleaning is in progress.

        This method checks whether cleaning is already in progress. If cleaning is currently being performed,
        it logs a warning message and exits. It ensures the system is fully configured before proceeding;
        otherwise, it prompts the user with an error message to configure all necessary paths.
        The method identifies the plugins to clean and validates their existence. If no plugins are available,
        it displays an appropriate error message.

        After validation and preparation, this method resets the previous cleaning state and initializes the
        cleaning worker with the appropriate services, state, and plugins. It sets up the necessary signal
        connections for tracking cleaning progress, handling errors, and managing the cleaning completion process.
        Finally, the cleaning process is started, and the status is updated to reflect the initiation of cleaning.

        Raises:
            None
        """
        try:
            if self.state.get("is_cleaning"):
                logger.warning("Cleaning already in progress")
                return

            # Validate configuration
            if not self.state.state.is_fully_configured:
                self.show_error.emit(
                    "Configuration Required",
                    "Please configure all paths before starting",
                )
                return

            # Get plugins to clean
            plugins: list[str] | None = self.get_plugins_to_clean()
            if not plugins:
                self.show_error.emit("No Plugins", "No plugins found in load order")
                return

            logger.info(f"Starting cleaning process for {len(plugins)} plugins")

            # Reset previous results
            self.state.reset_cleaning_state()
            self._cleaning_finished_handled = False  # Reset flag for new cleaning session

            # Create and start worker
            self.worker = CleaningWorker(self.service, self.state, plugins)
            self.worker.setParent(self)  # Set parent for proper Qt object management

            # Connect signals
            self.worker.plugin_started.connect(lambda p: self.update_status.emit(f"Cleaning: {p}"))
            self.worker.plugin_completed.connect(self._on_plugin_completed)
            self.worker.finished.connect(self._on_cleaning_finished)
            self.worker.error.connect(lambda e: self.show_error.emit("Cleaning Error", e))

            # Start cleaning
            self.worker.start()
            self.update_status.emit("Starting cleaning process...")

        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error in start_cleaning: {e}")
            self.show_error.emit("Error", f"Failed to start cleaning: {e}")

    def stop_cleaning(self) -> None:
        """
        Stops the cleaning process if it is currently running.

        This method checks whether a cleaning worker process is active, and if so,
        stops it. Once the cleaning process is halted, it emits a status update
        signal indicating that the stopping process has begun.

        Raises:
            None
        """
        if self.worker and self.worker.isRunning():
            logger.info("Stopping cleaning process")
            self.worker.stop()
            self.update_status.emit("Stopping cleaning...")

    def cleanup(self) -> None:
        """
        Performs comprehensive cleanup of all resources and threads.

        This method ensures that:
        - All worker threads are properly stopped and joined
        - Signal connections are disconnected
        - Resources are freed
        - State is properly reset

        This should be called during application shutdown.
        """
        logger.info("Starting GuiController cleanup")

        # Stop config save timer and process any pending saves
        if self._config_save_timer.isActive():
            self._config_save_timer.stop()
        self._process_pending_config_saves()

        # Stop any running cleaning process
        if self.worker is not None:
            if self.worker.isRunning():
                logger.info("Stopping cleaning worker thread")
                self.worker.stop()

                # Wait for worker to finish (max 15 seconds)
                if not self.worker.wait(15000):
                    logger.error("Cleaning worker did not stop gracefully within 15 seconds")
                    # Don't use terminate() - it's dangerous and can leave resources in inconsistent state
                    # The worker should eventually finish on its own after stop() was called
                    # Mark it for cleanup but don't forcefully terminate
                    self.worker.setParent(None)

            # Disconnect all worker signals safely
            try:
                self.worker.progress.disconnect()
                self.worker.plugin_started.disconnect()
                self.worker.plugin_completed.disconnect()
                self.worker.plugin_progress.disconnect()
                self.worker.log_output.disconnect()
                self.worker.error.disconnect()
                self.worker.finished.disconnect()
            except (RuntimeError, TypeError):
                # Signal might not be connected or already disconnected, that's okay
                pass

            # Schedule the worker for deletion
            self.worker.deleteLater()
            # Process events to ensure deletion happens
            from PySide6.QtCore import QCoreApplication

            QCoreApplication.processEvents()
            self.worker = None

        # Reset cleaning state
        self.state.reset_cleaning_state()

        # Disconnect our own signals
        try:
            self.show_message.disconnect()
            self.show_error.disconnect()
            self.update_status.disconnect()
        except RuntimeError:
            # Signals might not be connected
            pass

        logger.info("GuiController cleanup completed")

    def defer_config_save(self, key: str, value: Any) -> None:
        """
        Defers a configuration save to avoid holding locks across StateManager and ConfigManager.

        This method queues configuration updates and processes them after a short delay,
        ensuring that state locks are released before config file operations occur.

        Args:
            key: Configuration key to save
            value: Value to save
        """
        with QMutexLocker(self._pending_saves_mutex):
            self._pending_config_saves.append((key, value))
        self._config_save_timer.start()

    def _process_pending_config_saves(self) -> None:
        """
        Processes all pending configuration saves.

        This method is called by a timer after state updates are complete,
        avoiding potential deadlocks between StateManager and ConfigManager.
        """
        # Get pending saves under mutex protection
        with QMutexLocker(self._pending_saves_mutex):
            if not self._pending_config_saves:
                return

            # Copy and clear the list under mutex protection
            saves_to_process = self._pending_config_saves.copy()
            self._pending_config_saves.clear()

        # Process saves outside the mutex to avoid holding lock during I/O
        errors = []
        try:
            for key, value in saves_to_process:
                if not self.user_config.set(key, value):
                    errors.append(f"Failed to save config key: {key}")
        except (OSError, ValueError, TypeError) as e:
            # If we get an exception during the loop, log it and stop processing
            logger.error(f"Error during config save processing: {e}")
            return

        # Log all errors after the loop
        for error in errors:
            logger.error(error)

    @staticmethod
    def _on_plugin_completed(plugin: str, success: bool, message: str) -> None:
        """Handle plugin completion."""
        logger.info(f"Plugin {plugin}: {'Success' if success else 'Failed'} - {message}")

    def _on_cleaning_finished(self) -> None:
        """Handle cleaning completion."""
        if self.worker is not None and not self._cleaning_finished_handled:
            summary: str = self.worker.get_summary()
            self.show_message.emit("Cleaning Complete", summary)
            self.update_status.emit("Cleaning complete")
            self.worker = None
            self._cleaning_finished_handled = True

    def refresh_configuration(self) -> None:
        """
        Refreshes the application configuration by reloading it and updates the user interface
        to reflect the new configuration status. If an error occurs during the refreshing
        process, it is logged, and an error message is emitted to notify the user.

        Raises:
            OSError: Raised if there is an issue accessing the configuration file.
            ValueError: Raised if the configuration file contains invalid values.
            TypeError: Raised if there is an unexpected type in the configuration file.
        """
        try:
            self._load_configuration()
            self.update_status.emit("Configuration refreshed")
        except (OSError, ValueError, TypeError) as e:
            logger.error(f"Error refreshing configuration: {e}")
            self.show_error.emit("Error", f"Failed to refresh configuration: {e}")

    def get_state_summary(self) -> str:
        """
        Generates a textual summary of the current application state configuration, providing
        information on the load order, Mod Organizer 2 (MO2) configuration, xEdit configuration,
        MO2 operational mode, and game type.

        Returns:
            str: A formatted string summarizing the state configuration status.
        """
        state: AppState = self.state.state
        return (
            f"Configuration Status:\n"
            f"  Load Order: {'✓' if state.is_load_order_configured else '✗'}\n"
            f"  MO2: {'✓' if state.is_mo2_configured else '✗'}\n"
            f"  xEdit: {'✓' if state.is_xedit_configured else '✗'}\n"
            f"  MO2 Mode: {'Enabled' if state.mo2_mode else 'Disabled'}\n"
            f"  Partial Forms: {'Enabled' if state.partial_forms_enabled else 'Disabled'}\n"
            f"  Game Type: {state.game_type or 'Not detected'}"
        )
