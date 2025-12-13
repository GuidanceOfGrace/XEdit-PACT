"""Cleaning progress dialog for AutoQAC."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from PySide6.QtGui import QCloseEvent


class CleaningProgressDialog(QDialog):
    """Dialog that shows cleaning progress and statistics."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the cleaning progress dialog."""
        super().__init__(parent)
        self._current_plugin_name: str | None = None
        self.setWindowTitle("Cleaning Progress")
        self.setMinimumSize(450, 300)
        self.setModal(False)  # Non-modal so user can interact with main window

        # Track if cleaning is in progress
        self._cleaning_in_progress: bool = True

        # Create UI elements
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout: QVBoxLayout = QVBoxLayout(self)

        # Progress section
        progress_group: QGroupBox = QGroupBox("Progress")
        progress_layout: QVBoxLayout = QVBoxLayout()

        # Current plugin label
        self.current_plugin_label: QLabel = QLabel("Waiting to start...")
        self.current_plugin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.current_plugin_label.font()
        font.setPointSize(font.pointSize() + 2)
        self.current_plugin_label.setFont(font)
        progress_layout.addWidget(self.current_plugin_label)

        # Progress bar
        self.progress_bar: QProgressBar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        progress_layout.addWidget(self.progress_bar)

        # Progress text
        self.progress_label: QLabel = QLabel("0 / 0 plugins")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Statistics section
        stats_group: QGroupBox = QGroupBox("Statistics")
        stats_layout: QVBoxLayout = QVBoxLayout()

        # Create statistics labels
        self.stats_labels: dict[str, QLabel] = {}
        stats_items: list[tuple[str, str]] = [
            ("cleaned", "✓ Cleaned:"),
            ("failed", "✗ Failed:"),
            ("skipped", "⊘ Skipped:"),
            ("total", "Total:"),
        ]

        for key, label_text in stats_items:
            row_layout: QHBoxLayout = QHBoxLayout()
            label: QLabel = QLabel(label_text)
            label.setMinimumWidth(150)
            row_layout.addWidget(label)

            value_label: QLabel = QLabel("0")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.stats_labels[key] = value_label
            row_layout.addWidget(value_label)
            row_layout.addStretch()

            stats_layout.addLayout(row_layout)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()

        # Button box
        self.button_box: QDialogButtonBox = QDialogButtonBox()

        # Stop button (only shown during cleaning)
        self.stop_button: QPushButton = QPushButton("Stop Cleaning")
        self.stop_button.setStyleSheet("QPushButton { background-color: #ff4444; color: white; }")
        self.button_box.addButton(self.stop_button, QDialogButtonBox.ButtonRole.ActionRole)

        # Close button (only enabled after cleaning)
        self.close_button: QPushButton = self.button_box.addButton(QDialogButtonBox.StandardButton.Close)
        self.close_button.setEnabled(False)

        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def update_progress(self, current: int, total: int) -> None:
        """
        Updates the progress of a progress bar and its associated label based on the current and total values.

        This method calculates the progress percentage, updates the progress bar's value, and sets the text of
        the progress label to indicate the current and total progress. If a `_current_plugin_name` attribute
        is present and non-empty, it incorporates the plugin name into the progress bar's displayed format.
        If the total is zero, it resets the progress bar and label to their initial states.

        Args:
            current (int): The current progress count of the operation.
            total (int): The total progress count for the operation.
        """
        if total > 0:
            percentage: int = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_label.setText(f"{current} / {total} plugins")

            # Update progress bar format to show current plugin and percentage
            if hasattr(self, "_current_plugin_name") and self._current_plugin_name:
                self.progress_bar.setFormat(f"{self._current_plugin_name} / {percentage}%")
            else:
                self.progress_bar.setFormat("%p%")
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText("0 / 0 plugins")
            self.progress_bar.setFormat("%p%")

    def update_current_plugin(self, plugin_name: str) -> None:
        """
        Updates the current plugin label and manages the progress bar display.

        This function sets the label text to reflect the name of the currently processing
        plugin. It additionally formats and updates the progress bar display if a progress
        value greater than zero is present.

        Args:
            plugin_name: The name of the plugin to be set as the current processing plugin.
        """
        self.current_plugin_label.setText(f"Processing: {plugin_name}")
        self._current_plugin_name = plugin_name

        # Update progress bar format
        if self.progress_bar.value() > 0:
            self.progress_bar.setFormat(f"{plugin_name} / {self.progress_bar.value()}%")

    def update_statistics(self, stats: dict[str, int]) -> None:
        """
        Updates the statistics display for the user interface.

        This method iterates through the provided statistics dictionary and updates the
        associated labels in the user interface with the corresponding values. The keys
        in the given `stats` dictionary must match the keys defined in `self.stats_labels`
        for the display to be updated.

        Args:
            stats: A dictionary where the keys are strings representing statistical
                categories, and the values are integers representing the statistics
                to be displayed.
        """
        for key, label in self.stats_labels.items():
            if key in stats:
                label.setText(str(stats[key]))

    def set_cleaning_finished(self) -> None:
        """
        Marks the completion of the cleaning process and updates the UI components accordingly.

        This method ensures the cleaning process is visually finalized by changing the UI elements.
        It updates the text displayed on a label, hides the stop button, enables the close button,
        and adjusts the progress bar format depending on the state of completion.

        Returns:
            None
        """
        self._cleaning_in_progress = False
        self.current_plugin_label.setText("Cleaning completed!")
        self.stop_button.setVisible(False)
        self.close_button.setEnabled(True)

        # Update progress bar format to show completion
        if self.progress_bar.value() == 100:
            self.progress_bar.setFormat("Completed - 100%")
        else:
            self.progress_bar.setFormat(f"Stopped - {self.progress_bar.value()}%")

    def cleanup(self) -> None:
        """Clean up signal connections."""
        with suppress(RuntimeError):
            self.button_box.rejected.disconnect()
        with suppress(RuntimeError):
            self.stop_button.clicked.disconnect()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle close event."""
        if self._cleaning_in_progress:
            reply: QMessageBox.StandardButton = QMessageBox.question(
                self,
                "Cleaning in Progress",
                "Cleaning is still in progress. Are you sure you want to close this dialog?\n\n"
                "Note: Closing this dialog will not stop the cleaning process.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        self.cleanup()
        event.accept()
