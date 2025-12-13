"""Configuration UI MixIn for AutoQAC MainWindow."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from AutoQACLib.ui.dialogs.partial_forms import show_partial_forms_warning

if TYPE_CHECKING:
    from AutoQACLib.gui_controller import GuiController
    from AutoQACLib.state_manager import StateManager


class ConfigurationMixin:
    """MixIn class for configuration UI elements and handling."""

    # Type hints for attributes from MainWindow
    state: StateManager
    controller: GuiController
    load_order_button: QPushButton | None
    mo2_button: QPushButton | None
    mo2_mode_button: QPushButton | None
    partial_forms_button: QPushButton | None
    xedit_button: QPushButton | None

    def _create_configuration_group(self) -> QGroupBox:
        """Create the configuration section."""
        group: QGroupBox = QGroupBox("Configuration")
        layout: QVBoxLayout = QVBoxLayout()

        # Load Order
        lo_layout: QHBoxLayout = QHBoxLayout()
        self.load_order_button = QPushButton("Configure Load Order")
        self.load_order_button.clicked.connect(self._configure_load_order)
        lo_layout.addWidget(self.load_order_button)
        lo_layout.addStretch()
        layout.addLayout(lo_layout)

        # MO2
        mo2_layout: QHBoxLayout = QHBoxLayout()
        self.mo2_button = QPushButton("Configure MO2")
        self.mo2_button.clicked.connect(self._configure_mo2)
        mo2_layout.addWidget(self.mo2_button)

        self.mo2_mode_button = QPushButton("MO2 Mode: OFF")
        self.mo2_mode_button.setCheckable(True)
        self.mo2_mode_button.clicked.connect(self._toggle_mo2_mode)
        mo2_layout.addWidget(self.mo2_mode_button)
        mo2_layout.addStretch()
        layout.addLayout(mo2_layout)

        # xEdit
        xedit_layout: QHBoxLayout = QHBoxLayout()
        self.xedit_button = QPushButton("Configure xEdit")
        self.xedit_button.clicked.connect(self._configure_xedit)
        xedit_layout.addWidget(self.xedit_button)
        xedit_layout.addStretch()
        layout.addLayout(xedit_layout)

        # Partial Forms (Experimental Feature)
        partial_forms_layout: QHBoxLayout = QHBoxLayout()
        self.partial_forms_button = QPushButton("Partial Forms: OFF")
        self.partial_forms_button.setCheckable(True)
        self.partial_forms_button.setToolTip("Enable experimental Partial Forms feature (requires xEdit >= 4.1.5b)")
        self.partial_forms_button.clicked.connect(self._toggle_partial_forms)
        partial_forms_layout.addWidget(self.partial_forms_button)
        partial_forms_layout.addStretch()
        layout.addLayout(partial_forms_layout)

        group.setLayout(layout)
        return group

    @Slot()
    def _configure_load_order(self) -> None:
        """Configure load order file."""
        self.controller.configure_load_order(cast("QWidget", self))

    @Slot()
    def _configure_mo2(self) -> None:
        """Configure MO2."""
        self.controller.configure_mo2(cast("QWidget", self))

    @Slot()
    def _configure_xedit(self) -> None:
        """Configure xEdit."""
        self.controller.configure_xedit(cast("QWidget", self))

    @Slot()
    def _toggle_mo2_mode(self) -> None:
        """Toggle MO2 mode."""
        if self.mo2_mode_button is None:
            return
        enabled: bool = self.mo2_mode_button.isChecked()
        self.controller.toggle_mo2_mode(enabled)

    @Slot()
    def _toggle_partial_forms(self) -> None:
        """Toggle partial forms cleaning."""
        if self.partial_forms_button is None:
            return
        enabled: bool = self.partial_forms_button.isChecked()
        if enabled:
            # Show warning dialog if enabling
            confirmed: bool = show_partial_forms_warning(cast("QWidget", self))
            if not confirmed:
                # User cancelled or closed dialog, revert button
                self.partial_forms_button.setChecked(False)
                return
        self.controller.toggle_partial_forms(enabled)
