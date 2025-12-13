"""Cleaning control MixIn for AutoQAC MainWindow."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import Slot

from AutoQACLib.logging_config import get_logger

if TYPE_CHECKING:
    from logging import Logger

    from PySide6.QtWidgets import QPushButton, QWidget

    from AutoQACLib.gui_controller import GuiController
    from AutoQACLib.state_manager import StateManager
    from AutoQACLib.ui.dialogs.cleaning_progress import CleaningProgressDialog

logger: Logger = get_logger(__name__)


class CleaningControlMixin:
    """MixIn class for cleaning process control."""

    # Type hints for attributes from MainWindow
    state: StateManager
    controller: GuiController
    progress_dialog: CleaningProgressDialog | None
    start_button: QPushButton | None
    stop_button: QPushButton | None

    # Method signatures from MainWindow
    def _show_error(self, title: str, message: str) -> None: ...
    def _log(self, message: str) -> None: ...

    @Slot()
    def _start_cleaning(self) -> None:
        """Start the cleaning process."""
        try:
            logger.info("Starting cleaning process...")
            self.controller.start_cleaning()
        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Error starting cleaning: {e}")
            self._show_error("Error", f"Failed to start cleaning: {e}")

    @Slot()
    def _stop_cleaning(self) -> None:
        """Stop the cleaning process."""
        self.controller.stop_cleaning()

    @Slot()
    def _on_cleaning_started(self) -> None:
        """Handle cleaning start."""
        if self.start_button is None or self.stop_button is None:
            return

        # Import here to avoid circular dependency
        from AutoQACLib.ui.dialogs.cleaning_progress import CleaningProgressDialog

        # Create and show progress dialog
        self.progress_dialog = CleaningProgressDialog(cast("QWidget", self))
        self.progress_dialog.stop_button.clicked.connect(self._stop_cleaning)

        # Update progress with current state
        stats: dict[str, int] = self.state.state.cleaning_stats
        self.progress_dialog.update_statistics(stats)
        self.progress_dialog.update_progress(self.state.get("progress", 0), self.state.get("total_plugins", 0))

        self.progress_dialog.show()
        self._log("Cleaning started...")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    @Slot()
    def _on_cleaning_finished(self) -> None:
        """Handle cleaning completion."""
        if self.start_button is None or self.stop_button is None:
            return

        self._log("Cleaning finished!")

        # Update progress dialog
        if self.progress_dialog:
            self.progress_dialog.set_cleaning_finished()
            # Update final statistics
            stats: dict[str, int] = self.state.state.cleaning_stats
            self.progress_dialog.update_statistics(stats)

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
