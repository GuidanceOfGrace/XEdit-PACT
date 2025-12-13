"""Game detection and YAML helper functions."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QThread

from AutoQACLib.logging_config import get_logger
from AutoQACLib.yaml_manager import _yaml_manager

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger

logger: Logger = get_logger(__name__)


def yaml_settings(yaml_path: str | Path, key_path: str | list[str]) -> Any:
    """
    Retrieves a value from a YAML file based on the specified key path using the YAML manager.

    This function uses the `_yaml_manager` to fetch a value from the given YAML file
    defined by `yaml_path`. The specific value to retrieve is determined by the
    provided `key_path`, which can either be a string or a list of strings representing
    the hierarchical path to the desired key within the YAML file.

    Args:
        yaml_path: A string or `Path` object that specifies the path to the YAML file.
        key_path: A string or list of strings used to define the hierarchical
            path to the target key in the YAML file.

    Returns:
        The value associated with the specified key path in the YAML file.

    Raises:
        Any exceptions raised during the loading or retrieval of the YAML data.
    """
    return _yaml_manager.get_value(str(yaml_path), key_path)


def yaml_settings_write(yaml_path: str | Path, new_value: Any, key_path: str | list[str] | None = None) -> None:
    """
    Writes or updates a YAML file with provided values. This function either writes the entire YAML file from scratch with
    the given content or updates a specific key path with a new value, depending on the `key_path` argument.

    Args:
        yaml_path (str | Path): Path to the YAML file to be written or updated.
        new_value (Any): The value to be written to the YAML file. If `key_path` is None, this is the entire content of
            the YAML file. Otherwise, this value is assigned to the specified key path.
        key_path (str | list[str] | None): The key path to update within the YAML file. If this is None, the entire
            YAML file is rewritten with `new_value`. Otherwise, the provided key(s) are updated with the value.

    Returns:
        None
    """
    if key_path is None:
        # Write entire file using the public API
        _yaml_manager.write_full_file(str(yaml_path), new_value)
    else:
        _yaml_manager.set_value(str(yaml_path), key_path, new_value)


def detect_game_from_load_order(load_order_path: Path) -> str | None:
    """
    Detects the game type by reading the load order file and looking for specific game master files.

    This function reads the load order file line by line to determine the game mode
    by checking for specific game master files in the first few lines.

    Args:
        load_order_path: The path to the load order file.

    Returns:
        The game type abbreviation (e.g., "SSE", "FO3", "FNV", "FO4") if detected,
        or None if no game type could be determined.

    Raises:
        FileNotFoundError: If the load order file is not found.
        OSError: If there is an error reading the load order file.
    """
    try:
        with load_order_path.open("r", encoding="utf-8", errors="ignore") as lo_check:
            for line in lo_check:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Remove any prefix characters (*, +, etc.)
                    if line[0] in ["*", "+", "-"]:
                        line = line[1:].strip()

                    if "Skyrim.esm" in line:
                        return "SSE"
                    if "Fallout3.esm" in line:
                        return "FO3"
                    if "FalloutNV.esm" in line:
                        return "FNV"
                    if "Fallout4.esm" in line:
                        return "FO4"
    except FileNotFoundError:
        logger.error(f"Load order file not found: {load_order_path}")
        raise
    except (OSError, ValueError, UnicodeDecodeError) as e:
        logger.error(f"Error reading load order file: {load_order_path}, error: {e!s}")
        raise

    return None


def detect_xedit_game(xedit_path: str, load_order_path: Path | None = None) -> str | None:
    """
    Detects the game type associated with a given xEdit executable based on its file
    name, and optionally from the load order file if the executable detection fails.

    The function first attempts to identify the game by checking for specific keywords in the
    xEdit executable filename. If that fails and a load order path is provided, it will
    attempt to detect the game type by reading the load order file and looking for specific
    game master files.

    Args:
        xedit_path: The file path to the xEdit executable.
        load_order_path: Optional path to the load order file for fallback detection.

    Returns:
        The abbreviation of the detected game (e.g., "FO3", "FNV", "FO4", "SSE", "TTW") if a
        match is found, or None if no match is identified.
    """
    filename: str = Path(xedit_path).stem.lower()

    game_map: dict[str, str] = {
        "fo3edit": "FO3",
        "fnvedit": "FNV",
        "ttwedit": "TTW",
        "fo4edit": "FO4",
        "fo4vredit": "FO4",
        "sseedit": "SSE",
        "tes5edit": "SSE",
        "skyrimvredit": "SSE",
    }

    # First try to detect from xEdit executable name
    for key, game in game_map.items():
        if key in filename:
            return game

    # If xEdit detection failed and load order path is provided, try load order detection
    if load_order_path and load_order_path.exists():
        try:
            return detect_game_from_load_order(load_order_path)
        except (FileNotFoundError, OSError) as e:
            logger.warning(f"Could not detect game type from load order file: {e}")
            return None

    return None


def monitor_log_file(
    log_file_path: str | Path,
    line_callback: Callable[[str], None],
    stop_event: Any,  # Changed from threading.Event to Any for Qt compatibility
    poll_interval: float = 0.1,
) -> None:
    """
    Monitors a log file for new lines in real-time and executes a callback function
    for each new line. If the file does not yet exist, it waits until the file is
    created. Continuously checks the file until a stop event is set.

    Args:
        log_file_path: Path to the log file to be monitored.
        line_callback: Callback function to handle each new line read
            from the log file.
        stop_event: An event object used to signal the function to stop
            monitoring the file. Can be any object with an `is_set` method.
        poll_interval: Interval in seconds at which to check for new lines
            in the log file or the existence of the file. Defaults to 0.1.
    """

    log_path: Path = Path(log_file_path)

    try:
        # Wait for file to exist
        while not log_path.exists() and not stop_event.is_set():
            QThread.msleep(int(poll_interval * 1000))

        if stop_event.is_set():
            return

        with log_path.open("r", encoding="utf-8", errors="ignore") as f:
            # Start from end of existing file
            f.seek(0, 2)

            while not stop_event.is_set():
                line: str = f.readline()
                if line:
                    line_callback(line.rstrip("\n\r"))
                else:
                    QThread.msleep(int(poll_interval * 1000))

    except (OSError, ValueError) as e:
        logger.error(f"Error monitoring log file '{log_file_path}': {e}")
