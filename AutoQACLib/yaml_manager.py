"""Thread-safe YAML file management with caching capabilities."""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

import ruamel.yaml
from PySide6.QtCore import QMutex, QMutexLocker

from AutoQACLib.logging_config import get_logger

if TYPE_CHECKING:
    from logging import Logger


logger: Logger = get_logger(__name__)


class YAMLLockTimeoutError(Exception):
    """Raised when a YAML file lock cannot be acquired within the timeout period."""


# Timeout constant for YAML file locks
YAML_LOCK_TIMEOUT_MS = 5000  # 5 second timeout


class YamlManager:
    """Thread-safe YAML file manager with caching capabilities using Qt threading."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self._cache_mtimes: dict[str, float] = {}  # Track file modification times
        self._cache_mutex = QMutex()
        self._file_mutexes: dict[str, QMutex] = {}
        self._file_mutexes_mutex = QMutex()
        self._yaml = ruamel.yaml.YAML()
        self._yaml.indent(offset=2)
        self._yaml.width = 300

    def _get_file_mutex(self, yaml_path: str) -> QMutex:
        """Get or create a mutex for the specified file path."""
        with QMutexLocker(self._file_mutexes_mutex):
            if yaml_path not in self._file_mutexes:
                self._file_mutexes[yaml_path] = QMutex()
            return self._file_mutexes[yaml_path]

    def get_value(self, yaml_path: str, key_path: str | list[str]) -> Any:
        """
        Retrieves a value from a specified YAML file at a given key path.

        This method reads a YAML file, locks it to prevent concurrent modifications,
        and navigates through its structure based on the key path to return the desired
        value. If the key path cannot be fully resolved, the method returns None.

        Args:
            yaml_path: Path to the YAML file from which the value is to be retrieved.
            key_path: A string or a list of strings representing the hierarchical key path
                to the desired value within the YAML structure.

        Returns:
            The value at the specified key path within the YAML file. If the key path
            does not exist or cannot be resolved, returns None.
        """
        file_mutex: QMutex = self._get_file_mutex(yaml_path)

        # Use Qt mutex with timeout to prevent deadlocks
        if not file_mutex.tryLock(YAML_LOCK_TIMEOUT_MS):
            error_msg = f"Timeout acquiring lock for file: {yaml_path}"
            logger.error(error_msg)
            raise YAMLLockTimeoutError(error_msg)

        try:
            data = self._load_yaml(yaml_path)
            keys: list[str] = self._parse_key_path(key_path)

            # Traverse the YAML structure
            value: Any = data
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None

            return value
        finally:
            file_mutex.unlock()

    def set_value(self, yaml_path: str, key_path: str | list[str], new_value: Any) -> None:
        """
        Sets a new value in a YAML file at the specified key path. The method ensures thread-safety using
        a file-level mutex to serialize access. If the specified key path does not exist, intermediate
        keys are created as dictionaries to facilitate value assignment.

        Args:
            yaml_path (str): Path to the YAML file to be modified.
            key_path (str | list[str]): The path of the key where the value is to be set. It can be
                a dot-separated string or a list of keys representing nested paths.
            new_value (Any): The new value to set at the specified key path.

        """
        file_mutex: QMutex = self._get_file_mutex(yaml_path)

        # Use Qt mutex with timeout to prevent deadlocks
        if not file_mutex.tryLock(YAML_LOCK_TIMEOUT_MS):
            error_msg = f"Timeout acquiring lock for file: {yaml_path}"
            logger.error(error_msg)
            raise YAMLLockTimeoutError(error_msg)

        try:
            data: Any = self._load_yaml(yaml_path)
            keys: list[str] = self._parse_key_path(key_path)

            # Navigate to the parent of the final key
            current: Any = data
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Set the value at the final key
            current[keys[-1]] = new_value

            # Save changes back to file
            self._save_yaml(yaml_path, data)
        finally:
            file_mutex.unlock()

    def write_full_file(self, yaml_path: str, data: Any) -> None:
        """
        Write full file contents and update cache atomically.

        This method replaces the entire YAML file with the provided data,
        properly updating both the cache and modification time tracking.

        Args:
            yaml_path: Path to the YAML file to write.
            data: The complete data structure to write to the file.
        """
        self._save_yaml(yaml_path, data)

    @staticmethod
    def _parse_key_path(key_path: str | list[str]) -> list[str]:
        """Convert a dot-separated string path to list of keys."""
        return key_path.split(".") if isinstance(key_path, str) else key_path

    def _load_yaml(self, yaml_path: str) -> Any:
        """Load YAML file with intelligent caching based on modification time."""
        path = Path(yaml_path)

        # Quick cache check with modification time validation
        with QMutexLocker(self._cache_mutex):
            if yaml_path in self._cache:
                # Check if file has been modified since cached
                try:
                    current_mtime = path.stat().st_mtime if path.exists() else 0
                    cached_mtime = self._cache_mtimes.get(yaml_path, 0)
                    if cached_mtime >= current_mtime:
                        # Cache is still valid
                        return self._cache[yaml_path]
                except OSError:
                    # Fall through to reload on error
                    pass

        # Load file outside of cache mutex to minimize lock time
        warning_msg = None
        error_msg = None
        data: dict[str, Any] = {}
        file_mtime: float = 0

        try:
            if not path.exists():
                warning_msg = f"YAML file not found: {yaml_path}"
            else:
                # Get modification time for cache tracking
                file_mtime = path.stat().st_mtime

                with path.open(encoding="utf-8") as yaml_file:
                    content: str = yaml_file.read().strip()
                    # Handle empty file
                    data = {} if not content else self._yaml.load(content) or {}
        except (OSError, ruamel.yaml.YAMLError, ValueError) as e:
            error_msg = f"Failed to load YAML file '{yaml_path}': {e}"
            data = {}

        # Update cache with loaded data and modification time
        with QMutexLocker(self._cache_mutex):
            self._cache[yaml_path] = data
            if file_mtime > 0:
                self._cache_mtimes[yaml_path] = file_mtime

        # Log messages outside of mutex
        if warning_msg:
            logger.warning(warning_msg)
        if error_msg:
            logger.error(error_msg)

        return data

    def _save_yaml(self, yaml_path: str, data: Any) -> None:
        """Save data to YAML file with atomic write and cache update."""
        try:
            path: Path = Path(yaml_path)
            temp_path: Path = path.with_suffix(".tmp")

            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file
            with temp_path.open("w", encoding="utf-8") as temp_file:
                self._yaml.dump(data, temp_file)

            # Atomic rename
            temp_path.replace(path)

            # Get new modification time after save
            file_mtime = path.stat().st_mtime

            # Update cache with new data and modification time
            with QMutexLocker(self._cache_mutex):
                self._cache[yaml_path] = data
                self._cache_mtimes[yaml_path] = file_mtime
        except (OSError, ruamel.yaml.YAMLError, ValueError) as e:
            logger.error(f"Failed to save YAML file '{yaml_path}': {e}")
            # Clean up temp file if it exists
            with contextlib.suppress(OSError):
                Path(yaml_path).with_suffix(".tmp").unlink(missing_ok=True)


# Create singleton instance
_yaml_manager: YamlManager = YamlManager()
