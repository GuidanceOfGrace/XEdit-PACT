"""Dialog handling MixIn for AutoQAC MainWindow."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMessageBox, QWidget

from AutoQACLib import __version__

if TYPE_CHECKING:
    from PySide6.QtWidgets import QStatusBar


class DialogMixin:
    """MixIn class for dialog and message handling."""

    # Type hints for attributes from MainWindow
    status_bar: QStatusBar | None

    # Method signatures from MainWindow - removed to avoid conflicts

    @Slot(str, str)
    def _show_message(self, title: str, message: str) -> None:
        """Show an information message."""
        QMessageBox.information(cast("QWidget", self), title, message)

    @Slot(str, str)
    def _show_error(self, title: str, message: str) -> None:
        """Show an error message."""
        QMessageBox.critical(cast("QWidget", self), title, message)

    @Slot(str)
    def _update_status(self, message: str) -> None:
        """Update the status bar."""
        if self.status_bar is None:
            return
        self.status_bar.showMessage(message)

    def _log(self, message: str) -> None:
        """Add a message to the log display."""
        # Log messages are now only shown in status bar during cleaning
        if hasattr(self, "state") and hasattr(self.state, "get") and self.state.get("is_cleaning"):
            self._update_status(message)

    def _show_about(self) -> None:
        """Show the about dialog."""
        QMessageBox.about(
            cast("QWidget", self),
            "About AutoQAC",
            "AutoQAC - Automated Quick Auto Clean\n\n"
            "A PySide6 application for batch cleaning Bethesda game plugins "
            "using xEdit's Quick Auto Clean (-QAC) functionality.\n\n"
            f"Version: {__version__}\n"
            "Built with PySide6 and Python 3.12+",
        )
