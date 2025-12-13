"""Partial forms warning dialog for AutoQAC."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def show_partial_forms_warning(parent: QWidget) -> bool:
    """
    Show a warning dialog about partial forms cleaning.

    Args:
        parent: The parent widget for the dialog.

    Returns:
        True if the user wants to enable partial forms cleaning, False otherwise.
    """
    dialog: QDialog = QDialog(parent)
    dialog.setWindowTitle("Partial Forms Warning")
    dialog.setModal(True)
    dialog.setMinimumSize(400, 200)

    layout: QVBoxLayout = QVBoxLayout(dialog)

    # Warning message
    warning_label: QLabel = QLabel(
        "⚠️  WARNING: Partial Forms Cleaning\n\n"
        "Enabling partial forms cleaning will clean plugins that contain "
        "partial forms (records that are split across multiple plugins).\n\n"
        "This can be dangerous and may break your game if not done carefully.\n\n"
        "Only enable this if you understand the risks and have a backup "
        "of your plugins.\n\n"
        "Do you want to enable partial forms cleaning?"
    )
    warning_label.setWordWrap(True)
    layout.addWidget(warning_label)

    # Button box
    button_box: QDialogButtonBox = QDialogButtonBox()
    enable_button: QPushButton = QPushButton("Enable Partial Forms")
    enable_button.setStyleSheet("QPushButton { background-color: #ff4444; color: white; }")
    cancel_button: QPushButton = QPushButton("Cancel")
    cancel_button.setStyleSheet("QPushButton { background-color: #666666; color: white; }")

    button_box.addButton(enable_button, QDialogButtonBox.ButtonRole.AcceptRole)
    button_box.addButton(cancel_button, QDialogButtonBox.ButtonRole.RejectRole)

    layout.addWidget(button_box)

    # Connect signals
    def on_enable() -> None:
        dialog.accept()

    def on_cancel() -> None:
        dialog.reject()

    enable_button.clicked.connect(on_enable)
    cancel_button.clicked.connect(on_cancel)
    button_box.accepted.connect(on_enable)
    button_box.rejected.connect(on_cancel)

    # Show dialog and return result
    result: int = dialog.exec()
    return result == QDialog.DialogCode.Accepted
