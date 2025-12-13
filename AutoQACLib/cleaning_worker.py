"""Worker thread for plugin cleaning operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QThread, Signal

from AutoQACLib.logging_config import get_logger
from AutoQACLib.process_utils import set_max_concurrent_subprocesses

if TYPE_CHECKING:
    from AutoQACLib.cleaning_service import CleaningService, CleanResult
    from AutoQACLib.state_manager import StateManager

logger = get_logger(__name__)


class CleaningWorker(QThread):
    """Worker thread for cleaning plugins with clear signals."""

    # Signals
    progress: Signal = Signal(int, int)  # current, total
    plugin_started: Signal = Signal(str)  # plugin name
    plugin_completed: Signal = Signal(str, bool, str)  # plugin, success, message
    plugin_progress: Signal = Signal(dict)  # real-time progress info from cleaning
    log_output: Signal = Signal(str)  # real-time log output from xEdit
    error: Signal = Signal(str)  # error message

    def __init__(
        self,
        service: CleaningService,
        state: StateManager,
        plugins: list[str],
    ) -> None:
        """Initialize the cleaning worker."""
        super().__init__()
        self.service: CleaningService = service
        self.state: StateManager = state
        self.plugins: list[str] = plugins
        self._should_stop = False

    def run(self) -> None:
        """
        Executes the cleaning process for a list of plugins while providing real-time
        progress and log updates. This method validates the environment, processes
        each plugin sequentially, and supports stopping based on a user command.

        Raises:
            OSError: If an OS-level error occurs during the cleaning process.
            RuntimeError: If a runtime error is encountered during the execution.
            ValueError: If the provided values or parameters are invalid.

        Returns:
            None
        """
        try:
            # Validate environment first
            valid, message = self.service.validate_environment()
            if not valid:
                self.error.emit(message)
                return

            # Set subprocess resource limit from state
            state_snapshot = self.state.state
            set_max_concurrent_subprocesses(state_snapshot.max_concurrent_subprocesses)
            logger.info(f"Set max concurrent subprocesses to {state_snapshot.max_concurrent_subprocesses}")

            # Set up real-time callbacks for the cleaning service
            self.service.set_progress_callback(self._on_cleaning_progress)
            self.service.set_log_callback(self._on_log_output)

            # Update state
            self.state.update(
                is_cleaning=True,
                total_plugins=len(self.plugins),
                plugins_to_clean=self.plugins.copy(),
                progress=0,
            )

            # Process each plugin
            for i, plugin in enumerate(self.plugins):
                if self._should_stop or self.isInterruptionRequested():
                    logger.info("Cleaning stopped by user")
                    break

                # Update current plugin
                self.state.update(current_plugin=plugin)
                self.plugin_started.emit(plugin)

                try:
                    # Clean the plugin with real-time monitoring
                    result: CleanResult = self.service.clean_plugin(plugin)

                    # Update results
                    self.state.add_result(plugin, result.status, result.message)
                    self.plugin_completed.emit(plugin, result.success, result.message)
                    self.progress.emit(i + 1, len(self.plugins))

                    logger.info(f"Processed {plugin}: {result.status} ({result.duration:.1f}s) - {result.message}")

                except (OSError, RuntimeError, ValueError) as e:
                    logger.error(f"Error processing plugin {plugin}: {e}")
                    # Mark plugin as failed
                    self.state.add_result(plugin, "failed", f"Error: {e}")
                    self.plugin_completed.emit(plugin, False, f"Error: {e}")
                    self.progress.emit(i + 1, len(self.plugins))

        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error in cleaning worker: {e}")
            self.error.emit(str(e))
        except KeyboardInterrupt:
            logger.info("Cleaning worker interrupted by user")
            self.error.emit("Cleaning process was interrupted by user")
        except (TypeError, AttributeError) as e:
            logger.error(f"Unexpected error in cleaning worker: {e}")
            self.error.emit(f"Unexpected error: {e}")
        finally:
            # Reset cleaning state
            self.state.update(is_cleaning=False, current_plugin=None)
            self.finished.emit()

    def stop(self) -> None:
        """
        Stops the process by setting a flag and requesting interruption.

        This method sets an internal flag to indicate that the process should
        stop, attempts to stop any running subprocess through the service,
        and waits for the thread to complete gracefully.

        Returns:
            None
        """
        logger.info("Stopping cleaning worker...")
        self._should_stop = True
        self.requestInterruption()

        # First try to stop any running subprocess through the service
        if hasattr(self, "service") and self.service:
            try:
                self.service.stop_current_operation()
            except (AttributeError, RuntimeError) as e:
                logger.error(f"Error stopping service operation: {e}")

        # Wait for the thread to finish gracefully
        if self.isRunning() and not self.wait(10000):  # Wait up to 10 seconds
            logger.error("Cleaning worker did not stop gracefully after 10 seconds")
            # Don't use terminate() - it's dangerous and can leave resources in inconsistent state
            # Let the thread continue running or wait for it to finish on its own
            # The stop flag and service stop should cause it to exit soon

    def _on_cleaning_progress(self, progress_info: dict) -> None:
        """Handle real-time progress updates from cleaning service."""
        # Emit the progress signal with detailed information
        self.plugin_progress.emit(progress_info)

    def _on_log_output(self, log_line: str) -> None:
        """Handle real-time log output from xEdit process."""
        # Emit the log output signal
        self.log_output.emit(log_line)

    def get_summary(self) -> str:
        """
        Generates a summary of the cleaning statistics.

        This method retrieves the cleaning statistics from the current state
        and formats a detailed summary string, including the number of
        cleaned, failed, skipped items, and the total count.

        Returns:
            str: A formatted string summarizing the cleaning statistics.
        """
        stats = self.state.state.cleaning_stats
        return (
            f"Cleaning complete:\n"
            f"  Cleaned: {stats['cleaned']}\n"
            f"  Failed: {stats['failed']}\n"
            f"  Skipped: {stats['skipped']}\n"
            f"  Total: {stats['total']}"
        )
