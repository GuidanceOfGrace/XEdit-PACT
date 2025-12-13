"""Configuration dialog handlers for AutoQAC GUI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog, QWidget

from AutoQACLib.game_detection import detect_xedit_game
from AutoQACLib.logging_config import get_logger

if TYPE_CHECKING:
    from AutoQACLib.gui_controller import GuiController

logger = get_logger(__name__)


class ConfigurationDialogs:
    """Handles configuration dialogs for the GUI controller."""

    def __init__(self, controller: GuiController) -> None:
        """Initialize with reference to the GUI controller."""
        self.controller = controller
        self.state = controller.state
        self.user_config = controller.user_config

    def configure_load_order(self, parent_widget: QWidget) -> bool:
        """
        Configures the load order file by allowing the user to select a file via a dialog,
        and updates the application state and configuration accordingly.

        The method ensures a responsive UI by avoiding blocking file checks, deferring
        error handling to signals, and performing asynchronous state updates. It verifies
        the file's existence, updates configurations, and handles errors during the save
        process. If successful, it emits a status update signal.

        Args:
            parent_widget: The QWidget that serves as the parent for the file selection dialog.

        Returns:
            bool: True if the load order configuration is successfully updated and saved,
            otherwise False.
        """
        try:
            current_path: Path | None = self.state.get("load_order_path")
            initial_dir: str | None = str(current_path.parent) if current_path else ""

            # Use non-blocking file dialog options
            file_path, _ = QFileDialog.getOpenFileName(
                parent_widget, "Select Load Order File", initial_dir or "", "Text Files (*.txt);;All Files (*.*)"
            )

            if file_path:
                path: Path = Path(file_path)
                # Defer file existence check to avoid blocking
                if path.exists():
                    # Update state immediately for responsive UI
                    self.state.update_configuration_paths(load_order_path=path)

                    # Defer config save to avoid deadlock
                    self.controller.defer_config_save("Load_Order.File", str(path))

                    self.controller.update_status.emit(f"Load order configured: {path.name}")
                    return True
                else:  # noqa: RET505
                    self.controller.show_error.emit("Error", "Selected file does not exist")
                    return False
        except (OSError, ValueError, TypeError) as e:
            logger.error(f"Error in configure_load_order: {e}")
            self.controller.show_error.emit("Error", f"Unexpected error: {e}")
            return False
        else:
            return False

    def configure_mo2(self, parent_widget: QWidget) -> bool:
        """
        Configures Mod Organizer 2 (MO2) by allowing the user to select the `ModOrganizer.exe` file
        through a file dialog. Updates the internal state, configuration, and provides feedback
        on the process. Ensures the selected file is valid and saves configuration changes
        asynchronously. Emits updates related to configuration status or errors.

        Args:
            parent_widget (QWidget): The parent widget for the file dialog.

        Returns:
            bool: True if the configuration was successfully updated, False otherwise.
        """
        try:
            current_path: Path | None = self.state.get("mo2_exe_path")
            initial_dir: str | None = str(current_path.parent) if current_path else ""

            # Use non-blocking file dialog options
            file_path, _ = QFileDialog.getOpenFileName(
                parent_widget, "Select ModOrganizer.exe", initial_dir or "", "Executable Files (*.exe);;All Files (*.*)"
            )

            if file_path:
                path: Path = Path(file_path)
                # Defer file existence check to avoid blocking
                if path.exists() and path.name.lower() == "modorganizer.exe":
                    # Update state immediately for responsive UI
                    install_path: Path = path.parent
                    self.state.update_configuration_paths(
                        mo2_exe_path=path,
                        mo2_install_path=install_path,
                    )

                    # Defer config saves to avoid deadlock
                    self.controller.defer_config_save("Mod_Organizer.Binary", str(path))
                    self.controller.defer_config_save("Mod_Organizer.Install_Path", str(install_path))

                    self.controller.update_status.emit("Mod Organizer 2 configured")
                    return True
                else:  # noqa: RET505
                    self.controller.show_error.emit("Error", "Please select ModOrganizer.exe")
                    return False
        except (OSError, ValueError, TypeError) as e:
            logger.error(f"Error in configure_mo2: {e}")
            self.controller.show_error.emit("Error", f"Unexpected error: {e}")
            return False
        else:
            return False

    def configure_xedit(self, parent_widget: QWidget) -> bool:
        """
        Configures the xEdit executable for the application, updating its state and saving
        the configuration. Validates the selected file to ensure it corresponds to a valid
        xEdit executable.

        Args:
            parent_widget (QWidget): The parent widget used for file dialog. Serves as
                the context for the dialog.

        Returns:
            bool: True if the xEdit executable was successfully configured and saved,
                False otherwise.

        Raises:
            OSError: Raised when there is an error accessing the filesystem.
            ValueError: Raised when invalid values are encountered during processing.
            TypeError: Raised when arguments or data types are invalid.
        """
        try:
            current_path: Path | None = self.state.get("xedit_exe_path")
            initial_dir: str | None = str(current_path.parent) if current_path else ""

            file_path, _ = QFileDialog.getOpenFileName(
                parent_widget, "Select xEdit Executable", initial_dir or "", "Executable Files (*.exe);;All Files (*.*)"
            )

            if file_path:
                path: Path = Path(file_path)
                if path.exists():
                    # Validate it's an xEdit executable
                    valid_names: list[str] = [
                        "fo3edit",
                        "fnvedit",
                        "fo4edit",
                        "sseedit",
                        "tes5edit",
                        "xedit",
                        "xedit64",
                    ]
                    if not any(name in path.name.lower() for name in valid_names):
                        self.controller.show_error.emit(
                            "Error",
                            "Selected file does not appear to be an xEdit executable",
                        )
                        return False

                    # Update state immediately for responsive UI
                    install_path: Path = path.parent
                    self.state.update_configuration_paths(
                        xedit_exe_path=path,
                        xedit_install_path=install_path,
                    )

                    # Detect game type from xEdit executable
                    game_type: str | None = detect_xedit_game(str(path), self.state.get("load_order_path"))
                    if game_type:
                        self.state.update(game_type=game_type)
                        logger.info(f"Detected game type: {game_type}")

                    # Defer config saves to avoid deadlock
                    self.controller.defer_config_save("xEdit.Binary", str(path))
                    self.controller.defer_config_save("xEdit.Install_Path", str(install_path))

                    self.controller.update_status.emit(f"xEdit configured: {path.name}")
                    return True
                else:  # noqa: RET505
                    self.controller.show_error.emit("Error", "Selected file does not exist")
                    return False
        except (OSError, ValueError, TypeError) as e:
            logger.error(f"Error in configure_xedit: {e}")
            self.controller.show_error.emit("Error", f"Unexpected error: {e}")
            return False
        else:
            return False

    def toggle_mo2_mode(self, enabled: bool) -> None:
        """
        Toggles the MO2 mode setting by updating the application state, configuration, and UI.

        This method modifies the internal state of the application to either enable or disable
        MO2 mode, updates the corresponding configuration setting, and emits a status update
        signal to reflect the current state. In case of an error during these operations,
        it logs the error and emits an error signal to notify the user.

        Args:
            enabled (bool): Specifies whether to enable or disable MO2 mode.
        """
        try:
            # Update state immediately
            self.state.update(mo2_mode=enabled)
            # Defer config save to avoid deadlock
            self.controller.defer_config_save("Settings.MO2_Mode", enabled)
            self.controller.update_status.emit(f"MO2 Mode {'enabled' if enabled else 'disabled'}")
        except (OSError, ValueError, TypeError) as e:
            logger.error(f"Error toggling MO2 mode: {e}")
            self.controller.show_error.emit("Error", f"Failed to update MO2 mode: {e}")

    def toggle_partial_forms(self, enabled: bool) -> None:
        """
        Toggles the Partial Forms feature. The UI is responsible for confirmation and warning.

        Args:
            enabled (bool): Specifies whether to enable or disable Partial Forms.
        """
        try:
            # Update state immediately
            self.state.update(partial_forms_enabled=enabled)
            # Defer config save to avoid deadlock (consistent with other toggle methods)
            self.controller.defer_config_save("Settings.Partial_Forms", enabled)
            self.controller.update_status.emit(f"Partial Forms {'enabled' if enabled else 'disabled'}")
        except (OSError, ValueError, TypeError) as e:
            logger.error(f"Error toggling Partial Forms: {e}")
            self.controller.show_error.emit("Error", f"Failed to update Partial Forms setting: {e}")
