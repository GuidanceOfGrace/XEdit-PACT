"""Signal connection MixIn for AutoQAC MainWindow."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QPushButton

    from AutoQACLib.gui_controller import GuiController
    from AutoQACLib.state_manager import StateManager


class SignalConnectionMixin:
    """MixIn class for signal connection management."""

    # Type hints for attributes from MainWindow
    state: StateManager
    controller: GuiController
    _update_timer: QTimer
    load_order_button: QPushButton | None
    mo2_button: QPushButton | None
    mo2_mode_button: QPushButton | None
    xedit_button: QPushButton | None
    partial_forms_button: QPushButton | None
    start_button: QPushButton | None
    stop_button: QPushButton | None

    # Method signatures from MainWindow
    def _show_message(self, title: str, message: str) -> None: ...
    def _show_error(self, title: str, message: str) -> None: ...
    def _update_status(self, message: str) -> None: ...
    def _on_configuration_changed(self, is_fully_configured: bool) -> None: ...
    def _on_progress_changed(self, current: int, total: int) -> None: ...
    def _on_cleaning_started(self) -> None: ...
    def _on_cleaning_finished(self) -> None: ...
    def _on_plugin_processed(self, plugin: str, status: str, message: str) -> None: ...
    def _on_state_changed(self, property_name: str, value: object) -> None: ...
    def _on_bulk_state_changed(self, changes: dict[str, object]) -> None: ...
    def _perform_ui_update(self) -> None: ...

    def _connect_controller_signals(self) -> None:
        """Connect controller signals to UI updates."""
        self.controller.show_message.connect(self._show_message)
        self.controller.show_error.connect(self._show_error)
        self.controller.update_status.connect(self._update_status)

    def _connect_state_signals(self) -> None:
        """Connect state signals to UI updates."""
        self.state.configuration_changed.connect(self._on_configuration_changed)
        self.state.progress_changed.connect(self._on_progress_changed)
        self.state.cleaning_started.connect(self._on_cleaning_started)
        self.state.cleaning_finished.connect(self._on_cleaning_finished)
        self.state.plugin_processed.connect(self._on_plugin_processed)
        self.state.state_changed.connect(self._on_state_changed)
        self.state.bulk_state_changed.connect(self._on_bulk_state_changed)

    def _disconnect_all_signals(self) -> None:
        """Disconnect all signal connections to prevent memory leaks."""
        # Disconnect controller signals
        try:
            self.controller.show_message.disconnect(self._show_message)
            self.controller.show_error.disconnect(self._show_error)
            self.controller.update_status.disconnect(self._update_status)
        except RuntimeError:
            pass  # Already disconnected

        # Disconnect state signals
        try:
            self.state.configuration_changed.disconnect(self._on_configuration_changed)
            self.state.progress_changed.disconnect(self._on_progress_changed)
            self.state.cleaning_started.disconnect(self._on_cleaning_started)
            self.state.cleaning_finished.disconnect(self._on_cleaning_finished)
            self.state.plugin_processed.disconnect(self._on_plugin_processed)
            self.state.state_changed.disconnect(self._on_state_changed)
            self.state.bulk_state_changed.disconnect(self._on_bulk_state_changed)
        except RuntimeError:
            pass  # Already disconnected

        # Disconnect button signals
        if self.load_order_button:
            with suppress(RuntimeError):
                self.load_order_button.clicked.disconnect()
        if self.mo2_button:
            with suppress(RuntimeError):
                self.mo2_button.clicked.disconnect()
        if self.mo2_mode_button:
            with suppress(RuntimeError):
                self.mo2_mode_button.clicked.disconnect()
        if self.xedit_button:
            with suppress(RuntimeError):
                self.xedit_button.clicked.disconnect()
        if self.partial_forms_button:
            with suppress(RuntimeError):
                self.partial_forms_button.clicked.disconnect()
        if self.start_button:
            with suppress(RuntimeError):
                self.start_button.clicked.disconnect()
        if self.stop_button:
            with suppress(RuntimeError):
                self.stop_button.clicked.disconnect()

        # Disconnect timer
        with suppress(RuntimeError):
            self._update_timer.timeout.disconnect()
