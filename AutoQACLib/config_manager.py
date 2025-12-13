"""Configuration management for AutoQAC."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel import yaml
from ruamel.yaml import YAML

from AutoQACLib.game_detection import yaml_settings, yaml_settings_write
from AutoQACLib.logging_config import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Single source for all configuration."""

    def __init__(self, config_path: Path) -> None:
        """Initialize the configuration manager."""
        self._path: Path = config_path
        self._ensure_config_exists()

    def _ensure_config_exists(self) -> None:
        """Ensure the configuration file and directory exist."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            logger.info(f"Creating configuration file: {self._path}")
            self._path.touch()
            yaml_settings_write(str(self._path), {})
        else:
            # Check if file is empty and initialize it
            try:
                with self._path.open(encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        logger.info(f"Initializing empty configuration file: {self._path}")
                        yaml_settings_write(str(self._path), {})
            except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError) as e:
                logger.error(f"Error checking configuration file: {e}")
                # Recreate the file if there's an issue
                self._path.unlink(missing_ok=True)
                self._path.touch()
                yaml_settings_write(str(self._path), {})

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves the value associated with the specified configuration key from a YAML
        file. If the key is not found or an error occurs during the file reading process,
        returns a default value.

        Handles potential errors caused by YAML parsing issues, missing files, or
        inadequate permissions.

        Args:
            key (str): The configuration key to retrieve from the YAML file.
            default (Any): The default value to return if the key is not found or an error
                occurs during the file reading process.

        Returns:
            Any: The value associated with the given key if found and accessible; otherwise,
                 the provided default value.
        """
        try:
            value = yaml_settings(str(self._path), key)
        except (yaml.YAMLError, FileNotFoundError, PermissionError) as e:
            logger.error(f"Error reading config key '{key}': {e}")
            return default
        else:
            return value if value is not None else default

    def set(self, key: str, value: Any) -> bool:
        """
        Writes a key-value pair to a YAML configuration file in a thread-safe manner.

        This method attempts to write the provided key and value to the YAML configuration
        file located at the path specified by the instance. If the operation fails due to
        a YAML parsing error, missing file, permission issues, or an OS error, the method
        logs the error and returns False.

        Args:
            key (str): The configuration key to be written to the YAML file.
            value (Any): The value associated with the key to be written.

        Returns:
            bool: True if the write operation is successful; False otherwise.
        """
        try:
            # Use the thread-safe YAML manager directly instead of creating a separate thread
            yaml_settings_write(str(self._path), value, key)
        except (yaml.YAMLError, FileNotFoundError, PermissionError, OSError) as e:
            logger.error(f"Error writing config key '{key}': {e}")
            return False
        else:
            return True

    def get_all(self) -> dict[str, Any]:
        """
        Retrieves all configurations from the YAML file.

        This method attempts to read and parse a YAML configuration file. If the file
        does not exist, has insufficient permissions, contains invalid YAML, or another
        I/O-related error occurs, an empty dictionary is returned.

        Returns:
            dict[str, Any]: A dictionary containing the parsed configurations from the
            YAML file. If the file is empty or an error occurs, an empty dictionary is
            returned.

        Raises:
            yaml.YAMLError: If there is an error while parsing the YAML content.
            FileNotFoundError: If the configuration file does not exist.
            PermissionError: If there is no permission to read the file.
            OSError: If an operating system-related error occurs during file access.
        """
        try:
            yaml_loader: YAML = YAML(typ="safe", pure=True)
            with self._path.open(encoding="utf-8") as f:
                return yaml_loader.load(f) or {}
        except (yaml.YAMLError, FileNotFoundError, PermissionError, OSError) as e:
            logger.error(f"Error reading configuration file: {e}")
            return {}

    def update_multiple(self, updates: dict[str, Any]) -> bool:
        """
        Updates multiple configuration keys and their values.

        This method iterates over a dictionary of updates, setting each key-value pair
        using the `set` method. If any update fails, the method logs an error but
        continues processing the remaining updates. In case of an exception during
        execution, it logs the exception and stops further updates.

        Args:
            updates (dict[str, Any]): A dictionary where keys are configuration keys
                to update and values are the corresponding new configuration values.

        Returns:
            bool: True if all updates succeed, False otherwise. If an exception is
                encountered, False is returned, and the exception is logged.
        """
        try:
            success = True
            for key, value in updates.items():
                if not self.set(key, value):
                    success = False
                    logger.error(f"Failed to update config key: {key}")
        except (yaml.YAMLError, FileNotFoundError, PermissionError, OSError, ValueError) as e:
            logger.error(f"Error in update_multiple: {e}")
            return False
        else:
            return success

    def get_game_config(self, game_type: str) -> dict[str, Any]:
        """
        Retrieves the game configuration for the specified game type.

        This method fetches configuration details for the given game type,
        including the xedit list, skip list, and quickauto-clean list.

        Args:
            game_type: The type of the game for which configuration is to
                be retrieved.

        Returns:
            A dictionary containing configuration details with keys:
            - "xedit_list": The list of items related to xedit for the
              specified game type.
            - "skip_list": The list of items to be skipped for the
              specified game type.
        """
        # Get skip list from the correct key in AutoQAC Main.yaml
        skip_list = self.get(f"AutoQAC_Data.Skip_Lists.{game_type}", [])

        return {
            "skip_list": skip_list,
            "xedit_list": self.get(f"AutoQAC_Data.XEdit_Lists.{game_type}", []),
        }

    def get_paths(self) -> dict[str, Path | None]:
        """
        Retrieves and constructs a dictionary of file and directory paths based on specific
        keys from a settings source. The function processes a predefined list of keys, checks
        their existence in the settings, and transforms the keys into a standardized format for
        use in the returned dictionary.

        Returns:
            dict[str, Path | None]: A dictionary where keys are standardized names derived
            from a settings source's hierarchical keys, and values are either `Path`
            objects or `None` if the corresponding key does not exist or has no value.

        Raises:
            None
        """
        # Map config keys to output keys as expected by the tests
        key_map = {
            "Load_Order.File": "load_order_path",
            "Mod_Organizer.Binary": "mo2_exe_path",
            "Mod_Organizer.Install_Path": "mo2_install_path",
            "xEdit.Binary": "xedit_exe_path",
            "xEdit.Install_Path": "xedit_install_path",
        }
        paths: dict[str, Path | None] = {}
        for config_key, output_key in key_map.items():
            value = self.get(config_key)
            if value:
                paths[output_key] = Path(value)
            else:
                paths[output_key] = None
        return paths

    def get_settings(self) -> dict[str, Any]:
        """
        Retrieves configuration settings.

        This method fetches specific application configuration settings and returns
        them as a dictionary. It pulls data using predefined keys and defaults to
        specific values if settings are not available.

        Returns:
            dict[str, Any]: A dictionary containing configuration settings:
                - "journal_expiration" (int): Number of days before journals expire.
                - "cleaning_timeout" (int): Timeout duration in seconds for cleaning
                  operations.
                - "cpu_threshold" (int): CPU usage threshold percentage.
                - "mo2_mode" (bool): Mode of operation flag for MO2.

        """
        return {
            "journal_expiration": self.get("AutoQAC_Settings.Journal_Expiration", 7),
            "cleaning_timeout": self.get("AutoQAC_Settings.Cleaning_Timeout", 300),
            "cpu_threshold": self.get("AutoQAC_Settings.CPU_Threshold", 5),
            "mo2_mode": self.get("AutoQAC_Settings.MO2Mode", False),
            "max_concurrent_subprocesses": self.get("AutoQAC_Settings.Max_Concurrent_Subprocesses", 3),
        }

    def validate_paths(self) -> dict[str, bool]:
        """
        Validates the existence of file paths provided by the `get_paths` method.

        This method iterates through the paths returned by the `get_paths` method
        and checks whether each path exists on the filesystem. If a path exists,
        it returns `True` for the corresponding key; otherwise, it returns `False`.
        If a path is `None`, it is treated as non-existent (`False`).

        Returns:
            dict[str, bool]: A dictionary where keys are path names and values are
            booleans indicating whether the corresponding path exists.
        """
        paths: dict[str, Path | None] = self.get_paths()
        return {name: path.exists() if path else False for name, path in paths.items()}
