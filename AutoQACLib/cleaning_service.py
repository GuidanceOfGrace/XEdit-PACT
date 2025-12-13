"""Business logic for plugin cleaning operations."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from AutoQACLib.game_detection import detect_xedit_game
from AutoQACLib.logging_config import get_logger
from AutoQACLib.process_utils import run_process_with_realtime_output

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger
    from re import Pattern

    from AutoQACLib.config_manager import ConfigManager
    from AutoQACLib.state_manager import AppState, StateManager


logger: Logger = get_logger(__name__)


@dataclass
class CleanResult:
    """Result of a plugin cleaning operation."""

    success: bool
    message: str
    status: str  # "cleaned", "failed", "skipped"
    duration: float = 0.0


class CleaningService:
    """Pure business logic for plugin cleaning - no Qt dependencies."""

    def __init__(self, main_config: ConfigManager, user_config: ConfigManager, state: StateManager) -> None:
        """Initialize the cleaning service."""
        self.main_config = main_config  # For skip lists and game configs
        self.user_config = user_config  # For user settings
        self.state = state
        self.progress_callback: Callable[[dict[str, Any]], None] | None = None
        self.log_callback: Callable[[str], None] | None = None
        self._current_process: Any = None  # Track current subprocess for cleanup
        self._stop_requested: bool = False  # Flag to indicate stop was requested

    def set_progress_callback(self, callback: Callable[[dict[str, Any]], None] | None) -> None:
        """
        Sets the progress callback to monitor or handle progress updates during an operation.
        The callback function will be called whenever progress changes.

        Args:
            callback: A function to handle progress updates. Takes a dict with progress
                information (plugin, action, line, stats). If None, no progress updates
                will be processed.
        """
        self.progress_callback = callback

    def set_log_callback(self, callback: Callable[[str], None] | None) -> None:
        """
        Sets a callback function for logging events.

        This method allows the user to set a callable function that will be used for
        logging purposes. If no callback is provided or if `None` is passed, the
        logging callback will be disabled.

        Args:
            callback: A callable function to handle logging events (takes a string),
                or `None` to disable the logging callback.
        """
        self.log_callback = callback

    def stop_current_operation(self) -> None:
        """
        Stop the currently running cleaning operation gracefully.

        This method sets a flag to request stopping and attempts to terminate
        the current subprocess if one is running.
        """
        logger.info("Requesting stop of current cleaning operation")
        self._stop_requested = True

        if self._current_process:
            try:
                # Attempt to terminate the subprocess gracefully
                logger.info("Terminating current subprocess")
                self._current_process.terminate()
                # Give it a moment to terminate
                time.sleep(0.5)

                # If still running, kill it
                if self._current_process.poll() is None:
                    logger.warning("Subprocess did not terminate gracefully, killing")
                    self._current_process.kill()
            except (OSError, AttributeError) as e:
                logger.error(f"Error stopping subprocess: {e}")
            finally:
                self._current_process = None

    def clean_plugin(self, plugin_name: str) -> CleanResult:
        """
        Cleans a specified plugin by always performing Quick Auto Clean (QAC).
        Args:
            plugin_name: The name of the plugin to be cleaned.
        Returns:
            CleanResult: An object representing the result of the cleaning operation.
        """
        start_time: float = time.time()

        # Reset stop flag at the beginning of each cleaning operation
        self._stop_requested = False
        self._current_process = None

        try:
            # Check if stop was requested before starting
            if self._stop_requested:
                return CleanResult(
                    success=False,
                    message=f"Cleaning of {plugin_name} was cancelled",
                    status="failed",
                    duration=time.time() - start_time,
                )
            # Get current state
            state_snapshot: AppState = self.state.state

            # Check if plugin should be skipped
            if self._should_skip_plugin(plugin_name, state_snapshot.game_type):
                return CleanResult(
                    success=True,
                    message=f"Skipped {plugin_name} (in skip list)",
                    status="skipped",
                    duration=time.time() - start_time,
                )

            # Ensure environment is validated and game type is detected
            if not state_snapshot.game_type:
                # Try to detect game type
                game_type: str | None = detect_xedit_game(
                    str(state_snapshot.xedit_exe_path), state_snapshot.load_order_path
                )
                if game_type:
                    self.state.update(game_type=game_type)
                    logger.info(f"Detected game type: {game_type}")
                    # Get updated state
                    state_snapshot = self.state.state
                # For universal xEdit executables, try to detect from load order
                elif state_snapshot.load_order_path and state_snapshot.load_order_path.exists():
                    from AutoQACLib.game_detection import detect_game_from_load_order

                    game_type = detect_game_from_load_order(state_snapshot.load_order_path)
                    if game_type:
                        self.state.update(game_type=game_type)
                        logger.info(f"Detected game type from load order: {game_type}")
                        state_snapshot = self.state.state

            # Always run Quick Auto Clean
            command: str = self._build_cleaning_command(plugin_name, state_snapshot)
            if not command:
                return CleanResult(
                    success=False,
                    message=f"Failed to build cleaning command for {plugin_name}",
                    status="failed",
                    duration=time.time() - start_time,
                )

            result: CleanResult = self._execute_cleaning_command(command, plugin_name, state_snapshot.cleaning_timeout)

            if result.success:
                result.status = "cleaned"

        except (OSError, RuntimeError, ValueError, KeyError) as e:
            logger.error(f"Error cleaning {plugin_name}: {e}")
            return CleanResult(
                success=False,
                message=f"Error cleaning {plugin_name}: {e!s}",
                status="failed",
                duration=time.time() - start_time,
            )
        else:
            return result

    def _should_skip_plugin(self, plugin_name: str, game_type: str | None) -> bool:
        """Check if plugin should be skipped."""
        if not game_type:
            return False

        game_config: dict[str, Any] = self.main_config.get_game_config(game_type)
        skip_list: list[str] = game_config.get("skip_list", [])

        # Special case: TTW plugins are listed under FNV in the skip list
        if game_type == "TTW":
            fnv_config: dict[str, Any] = self.main_config.get_game_config("FNV")
            fnv_skip_list: list[str] = fnv_config.get("skip_list", [])
            skip_list.extend(fnv_skip_list)

        # Also check universal skip list
        universal_skip: list[str] = self.main_config.get("AutoQAC_Data.Skip_Lists.Universal", [])

        return plugin_name.lower() in [p.lower() for p in skip_list + universal_skip]

    @staticmethod
    def _build_cleaning_command(plugin_name: str, state_snapshot: AppState) -> str:
        """Build the command to clean a plugin using -QAC."""

        # Check if xEdit executable path is set
        if not state_snapshot.xedit_exe_path:
            logger.error("xEdit executable path not set")
            return ""

        # Determine if xEdit executable is specific or universal
        xedit_exe_name: str = state_snapshot.xedit_exe_path.name.lower()

        # Specific xEdit executables (game-specific)
        specific_xedit_list: list[str] = [
            "fo3edit.exe",
            "fo3edit64.exe",
            "fnvedit.exe",
            "fnvedit64.exe",
            "fo4edit.exe",
            "fo4edit64.exe",
            "sseedit.exe",
            "sseedit64.exe",
            "fo4vredit.exe",
            "fo4vredit64.exe",
            "tes5vredit.exe",
        ]

        # Universal xEdit executables
        universal_xedit_list: list[str] = ["xedit.exe", "xedit64.exe", "xfoedit.exe", "xfoedit64.exe"]

        is_specific_xedit: bool = xedit_exe_name in specific_xedit_list
        is_universal_xedit: bool = xedit_exe_name in universal_xedit_list

        if not is_specific_xedit and not is_universal_xedit:
            logger.error(f"Invalid xEdit executable: {xedit_exe_name}")
            return ""

        # Always use -QAC for cleaning
        cleaning_flag = "-QAC"

        # Add Partial Forms options if enabled
        partial_forms_options: str = ""
        if state_snapshot.partial_forms_enabled:
            partial_forms_options = " -iknowwhatimdoing -allowmakepartial"
            logger.info("Partial Forms feature enabled - adding experimental command line options")

        # Build command based on MO2 mode and xEdit type
        if state_snapshot.mo2_mode and state_snapshot.mo2_exe_path:
            mo2_path: str = str(state_snapshot.mo2_exe_path)
            xedit_path: str = str(state_snapshot.xedit_exe_path)

            if is_specific_xedit:
                args: str = f'{cleaning_flag} -autoexit -autoload{partial_forms_options} "{plugin_name}"'
            elif state_snapshot.game_type:
                args = f'-{state_snapshot.game_type} {cleaning_flag} -autoexit -autoload{partial_forms_options} "{plugin_name}"'
            else:
                logger.error("Game type not set for universal xEdit executable")
                return ""

            # MO2 requires special quoting for arguments
            return f'"{mo2_path}" run "{xedit_path}" -a "{args}"'

        xedit_path = str(state_snapshot.xedit_exe_path)

        # Build command based on xEdit type
        if is_specific_xedit:
            return f'"{xedit_path}" {cleaning_flag} -autoexit -autoload{partial_forms_options} "{plugin_name}"'
        if state_snapshot.game_type:
            return f'"{xedit_path}" -{state_snapshot.game_type} {cleaning_flag} -autoexit -autoload{partial_forms_options} "{plugin_name}"'
        logger.error("Game type not set for universal xEdit executable")
        return ""

    def _execute_cleaning_command(self, command: str, plugin_name: str, timeout: int) -> CleanResult:
        """Execute the cleaning command with real-time monitoring.

        Note: This method uses instance variables (_cleaning_stats, _current_plugin)
        that are not thread-synchronized. CleaningService is designed to be called
        sequentially by a single CleaningWorker thread. Do not call this method
        from multiple threads concurrently.
        """
        start_time: float = time.time()

        try:
            # Prepare progress tracking variables
            self._current_plugin = plugin_name
            self._cleaning_stats = {
                "undeleted": 0,
                "removed": 0,
                "skipped": 0,
                "partial_forms": 0,
                "total_processed": 0,
            }

            # Create output callback for real-time monitoring
            def on_output_line(line: str) -> None:
                """Handle real-time output from xEdit process."""
                if self.log_callback:
                    self.log_callback(line)

                # Parse line for cleaning statistics and progress
                self._parse_cleaning_output(line, plugin_name)

            # Execute command with real-time monitoring
            logger.info(f"Executing command: {command}")
            exit_code, _, stderr = run_process_with_realtime_output(
                command=command, output_callback=on_output_line, timeout=timeout, working_dir=None
            )

            duration: float = time.time() - start_time

            # Check result
            if exit_code == 0:
                stats_summary: str = self._get_cleaning_summary()
                return CleanResult(
                    success=True,
                    message=f"Successfully cleaned {plugin_name}{stats_summary}",
                    status="cleaned",
                    duration=duration,
                )
            if exit_code == -1:
                # Timeout or other error
                timeout_error_msg: str = stderr.strip() if stderr else "Process failed or timed out"
                return CleanResult(
                    success=False,
                    message=f"Failed to clean {plugin_name}: {timeout_error_msg}",
                    status="failed",
                    duration=duration,
                )
            # Non-zero exit code
            exit_error_msg: str = stderr.strip() if stderr else f"Process exited with code {exit_code}"
            return CleanResult(
                success=False,
                message=f"Failed to clean {plugin_name}: {exit_error_msg}",
                status="failed",
                duration=duration,
            )

        except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError) as e:
            logger.error(f"Error executing cleaning command for {plugin_name}: {e}")
            return CleanResult(
                success=False,
                message=f"Error cleaning {plugin_name}: {e!s}",
                status="failed",
                duration=time.time() - start_time,
            )

    def _parse_cleaning_output(self, line: str, plugin_name: str) -> None:
        """Parse xEdit output line for cleaning statistics and progress."""
        import re

        # Pattern matching for xEdit cleaning operations
        patterns: dict[str, Pattern[str]] = {
            "undeleted": re.compile(r"Undeleting:\s*(.*)", re.IGNORECASE),
            "removed": re.compile(r"Removing:\s*(.*)", re.IGNORECASE),
            "skipped": re.compile(r"Skipping:\s*(.*)", re.IGNORECASE),
            "partial_forms": re.compile(r"Making Partial Form:\s*(.*)", re.IGNORECASE),
        }

        # Check each pattern and update stats
        for stat_type, pattern in patterns.items():
            if pattern.search(line):
                self._cleaning_stats[stat_type] += 1
                self._cleaning_stats["total_processed"] += 1

                # Emit progress update if callback is set
                if self.progress_callback:
                    progress_info: dict[str, Any] = {
                        "plugin": plugin_name,
                        "action": stat_type,
                        "line": line.strip(),
                        "stats": self._cleaning_stats.copy(),
                    }
                    self.progress_callback(progress_info)
                break

        # Check for completion indicators
        if ("Done." in line or "Cleaning completed" in line) and self.progress_callback:
            completion_info: dict[str, Any] = {
                "plugin": plugin_name,
                "action": "completed",
                "line": line.strip(),
                "stats": self._cleaning_stats.copy(),
            }
            self.progress_callback(completion_info)

    def _get_cleaning_summary(self) -> str:
        """Generate a summary of cleaning statistics."""
        stats: dict[str, int] = self._cleaning_stats
        if stats["total_processed"] == 0:
            return ""

        summary_parts: list[Any] = []
        if stats["undeleted"] > 0:
            summary_parts.append(f"{stats['undeleted']} undeleted")
        if stats["removed"] > 0:
            summary_parts.append(f"{stats['removed']} removed")
        if stats["skipped"] > 0:
            summary_parts.append(f"{stats['skipped']} skipped")
        if stats["partial_forms"] > 0:
            summary_parts.append(f"{stats['partial_forms']} partial forms")

        if summary_parts:
            return f" ({', '.join(summary_parts)})"
        return f" ({stats['total_processed']} items processed)"

    def validate_environment(self) -> tuple[bool, str]:
        """
        Validates the application environment, ensuring all paths, required executables,
        and configurations are appropriately set. This function performs the following checks:

        1. Verifies that all required paths are configured.
        2. Ensures the xEdit executable exists and is properly set.
        3. Attempts to auto-detect the game type if not already specified.
        4. Confirms the presence of the MO2 executable if operating in MO2 mode.

        Returns a tuple indicating the validation status and an associated message.

        Returns:
            tuple[bool, str]: A tuple where the first element signifies the success
                (True for valid environment, False otherwise) and the second element
                contains a detailed message explaining the result of the validation.
        """
        state_snapshot: AppState = self.state.state

        # Check configuration
        if not state_snapshot.is_fully_configured:
            return False, "Not all paths are configured"

        # Check xEdit executable
        if not state_snapshot.xedit_exe_path or not state_snapshot.xedit_exe_path.exists():
            return False, "xEdit executable not found"

        # Detect game type if not set
        if not state_snapshot.game_type:
            game_type: str | None = detect_xedit_game(
                str(state_snapshot.xedit_exe_path), state_snapshot.load_order_path
            )
            if game_type:
                self.state.update(game_type=game_type)
                logger.info(f"Detected game type: {game_type}")
            else:
                # For generic xEdit executables (xEdit.exe, xEdit64.exe),
                # we can't auto-detect game type, but we can still proceed
                logger.warning(
                    "Could not auto-detect game type from xEdit executable or load order file. "
                    "For generic xEdit executables, game type may need to be set manually."
                )

        # Check MO2 if in MO2 mode
        if state_snapshot.mo2_mode and (not state_snapshot.mo2_exe_path or not state_snapshot.mo2_exe_path.exists()):
            return False, "MO2 executable not found (required in MO2 mode)"

        return True, "Environment validated successfully"
