"""State event handler MixIn for AutoQAC MainWindow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Slot

if TYPE_CHECKING:
    from PySide6.QtWidgets import QPushButton

    from AutoQACLib.state_manager import StateManager
    from AutoQACLib.ui.dialogs.cleaning_progress import CleaningProgressDialog


class StateEventHandlerMixin:
    """MixIn class for handling state change events."""

    # Type hints for attributes from MainWindow
    state: StateManager
    progress_dialog: CleaningProgressDialog | None
    start_button: QPushButton | None

    # Method signatures from MainWindow
    def _log(self, message: str) -> None: ...
    def _update_status(self, message: str) -> None: ...
    def _update_ui_from_state(self, priority: str = "normal") -> None: ...
    def _on_cleaning_started(self) -> None: ...
    def _on_cleaning_finished(self) -> None: ...

    @Slot(bool)
    def _on_configuration_changed(self, is_fully_configured: bool) -> None:
        """Handle configuration changes."""
        if self.start_button is None:
            return
        self.start_button.setEnabled(is_fully_configured and not self.state.get("is_cleaning"))
        if is_fully_configured:
            self._log("All paths configured ✓")

    @Slot(int, int)
    def _on_progress_changed(self, current: int, total: int) -> None:
        """Handle progress updates."""
        if total > 0:
            percentage: float = (current / total) * 100
            self._update_status(f"Progress: {current}/{total} ({percentage:.1f}%)")

        # Update progress dialog
        if self.progress_dialog and self.progress_dialog.isVisible():
            self.progress_dialog.update_progress(current, total)
            # Update statistics
            stats: dict[str, int] = self.state.state.cleaning_stats
            self.progress_dialog.update_statistics(stats)

    @Slot(str, str, str)
    def _on_plugin_processed(self, plugin: str, status: str, message: str) -> None:
        """Handle plugin processing completion."""
        icon: str = {
            "cleaned": "✓",
            "failed": "✗",
            "skipped": "⊘",
        }.get(status, "?")

        self._log(f"{icon} {plugin}: {message}")

        # Update current plugin in progress dialog
        if self.progress_dialog and self.progress_dialog.isVisible():
            current_plugin: str | None = self.state.get("current_plugin")
            if current_plugin:
                self.progress_dialog.update_current_plugin(current_plugin)

    @Slot(dict)
    def _on_bulk_state_changed(self, changes: dict[str, object]) -> None:
        """Handle multiple state changes at once for better performance."""
        # Check if any changes require immediate update
        immediate_update = False
        high_priority_update = False

        for property_name, value in changes.items():
            if property_name == "is_cleaning":
                immediate_update = True
                if value:
                    self._on_cleaning_started()
                else:
                    self._on_cleaning_finished()
            elif property_name in ["current_plugin", "current_operation"]:
                high_priority_update = True
                if (
                    property_name == "current_plugin"
                    and self.progress_dialog
                    and self.progress_dialog.isVisible()
                    and isinstance(value, str)
                ):
                    self.progress_dialog.update_current_plugin(value)

        # Update UI with appropriate priority
        if immediate_update:
            self._update_ui_from_state("immediate")
        elif high_priority_update:
            self._update_ui_from_state("high")
        else:
            self._update_ui_from_state("normal")

    @Slot(str, object)
    def _on_state_changed(self, property_name: str, value: object) -> None:
        """Handle individual state property changes with appropriate priority."""
        # Determine update priority based on property type
        priority = "normal"

        # High priority for user-facing state changes
        if property_name == "is_cleaning":
            priority = "immediate"  # Cleaning state changes need immediate feedback
        elif property_name in ["current_plugin", "current_operation"]:
            priority = "high"  # Plugin progress updates
            # Update current plugin in progress dialog immediately
            if (
                property_name == "current_plugin"
                and self.progress_dialog
                and self.progress_dialog.isVisible()
                and isinstance(value, str)
            ):
                self.progress_dialog.update_current_plugin(value)
        elif property_name in ["mo2_mode", "partial_forms_enabled"]:
            priority = "normal"  # Settings changes

        # Update UI with appropriate priority
        if property_name in [
            "is_load_order_configured",
            "is_mo2_configured",
            "is_xedit_configured",
            "mo2_mode",
            "partial_forms_enabled",
            "is_cleaning",
        ]:
            self._update_ui_from_state(priority)
