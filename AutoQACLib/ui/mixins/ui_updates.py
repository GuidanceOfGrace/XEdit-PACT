"""UI update MixIn for AutoQAC MainWindow."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QPushButton

    from AutoQACLib.state_manager import AppState, StateManager


class UIUpdateMixin:
    """MixIn class for UI update operations."""

    # Type hints for attributes from MainWindow
    state: StateManager
    _updating_ui: bool
    _update_timer: QTimer
    _update_priority: str
    load_order_button: QPushButton | None
    mo2_button: QPushButton | None
    mo2_mode_button: QPushButton | None
    partial_forms_button: QPushButton | None
    xedit_button: QPushButton | None
    start_button: QPushButton | None
    stop_button: QPushButton | None

    def _update_ui_from_state(self, priority: str = "normal") -> None:
        """Update UI elements based on current state with priority-based debouncing.

        Args:
            priority: Update priority - "immediate", "high", or "normal"
        """
        # Immediate updates bypass debouncing
        if priority == "immediate":
            self._perform_ui_update()
            return

        # Set appropriate debounce interval based on priority
        interval = 50 if priority == "high" else 200  # Longer delay for normal updates

        # Update priority if this is a higher priority update
        if priority == "high" and self._update_priority == "normal":
            self._update_priority = priority
            self._update_timer.setInterval(interval)

        # Start or restart timer with appropriate interval
        if not self._update_timer.isActive() or priority == "high":
            self._update_timer.setInterval(interval)
            self._update_timer.start()

    def _perform_ui_update(self) -> None:
        """Perform the actual UI update with debouncing."""
        if self._updating_ui:
            return  # Prevent recursive updates

        self._updating_ui = True
        self._update_priority = "normal"  # Reset priority after update
        try:
            state_snapshot: AppState = self.state.state

            # Update configuration buttons efficiently
            if self.load_order_button:
                new_text = "Load Order ✓" if state_snapshot.is_load_order_configured else "Configure Load Order"
                if self.load_order_button.text() != new_text:
                    self._update_button_state(
                        self.load_order_button,
                        state_snapshot.is_load_order_configured,
                        new_text,
                    )

            if self.mo2_button:
                new_text = "MO2 ✓" if state_snapshot.is_mo2_configured else "Configure MO2"
                if self.mo2_button.text() != new_text:
                    self._update_button_state(
                        self.mo2_button,
                        state_snapshot.is_mo2_configured,
                        new_text,
                    )

            if self.xedit_button:
                new_text = "xEdit ✓" if state_snapshot.is_xedit_configured else "Configure xEdit"
                if self.xedit_button.text() != new_text:
                    self._update_button_state(
                        self.xedit_button,
                        state_snapshot.is_xedit_configured,
                        new_text,
                    )

            # Update MO2 mode button efficiently
            if self.mo2_mode_button:
                new_checked = state_snapshot.mo2_mode
                if self.mo2_mode_button.isChecked() != new_checked:
                    self.mo2_mode_button.setChecked(new_checked)

                new_text = f"MO2 Mode: {'ON' if state_snapshot.mo2_mode else 'OFF'}"
                if self.mo2_mode_button.text() != new_text:
                    self.mo2_mode_button.setText(new_text)

            # Update Partial Forms button efficiently
            if self.partial_forms_button:
                new_checked = state_snapshot.partial_forms_enabled
                if self.partial_forms_button.isChecked() != new_checked:
                    self.partial_forms_button.setChecked(new_checked)

                new_text = f"Partial Forms: {'ON' if state_snapshot.partial_forms_enabled else 'OFF'}"
                if self.partial_forms_button.text() != new_text:
                    self.partial_forms_button.setText(new_text)

            # Update control buttons efficiently
            if self.start_button:
                new_enabled = state_snapshot.is_fully_configured and not state_snapshot.is_cleaning
                if self.start_button.isEnabled() != new_enabled:
                    self.start_button.setEnabled(new_enabled)

            if self.stop_button:
                new_enabled = state_snapshot.is_cleaning
                if self.stop_button.isEnabled() != new_enabled:
                    self.stop_button.setEnabled(new_enabled)
        finally:
            self._updating_ui = False

    @staticmethod
    def _update_button_state(button: QPushButton, configured: bool, text: str) -> None:
        """Update button appearance based on configuration state."""
        button.setText(text)
        if configured:
            button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        else:
            button.setStyleSheet("")
