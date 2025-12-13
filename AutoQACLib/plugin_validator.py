"""Plugin validation and extraction from load order files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from AutoQACLib.logging_config import get_logger

if TYPE_CHECKING:
    from AutoQACLib.state_manager import AppState, StateManager

logger = get_logger(__name__)

# Pre-compiled patterns for efficient plugin parsing
PLUGIN_EXTENSIONS = frozenset([".esp", ".esm", ".esl"])
PREFIX_CHARS = frozenset(["*", "+", "-"])
SEPARATOR_CHARS = frozenset([",", ";"])


class PluginValidator:
    """Handles plugin validation and extraction from load order files."""

    def __init__(self, state: StateManager) -> None:
        """Initialize with reference to the state manager."""
        self.state = state

    def get_plugins_to_clean(self) -> list[str]:
        """
        Retrieves a list of plugin filenames to clean based on the load order file.

        This function reads the load order file specified in the application state and extracts
        plugin filenames that are active in the load order. It filters out any lines that are
        comments or do not represent valid plugin files with specific file extensions. The function
        also accounts for prefixes in the load order entries and removes them before adding the
        plugin filenames to the result.

        The function validates that plugin extensions (.esp, .esm, .esl) are at the end of the line.
        If content is found after the extension, it separates the plugin name and logs a warning.

        Returns:
            list[str]: A list of plugin filenames extracted from the load order file. If the load
            order file is not found or an error occurs during reading, an empty list is returned.

        Raises:
            None
        """
        state_snapshot: AppState = self.state.state

        if not state_snapshot.load_order_path:
            logger.error("Load order path not configured")
            return []

        if not state_snapshot.load_order_path.exists():
            logger.error("Load order file not found")
            return []

        try:
            # Read load order file
            plugins: list[str] = []
            with state_snapshot.load_order_path.open(encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    # Fast skip empty lines and comments
                    if not line or line[0] == "#":
                        continue

                    original_line = line.strip()
                    if not original_line:
                        continue

                    # Optimized prefix removal
                    line = original_line[1:].strip() if original_line[0] in PREFIX_CHARS else original_line

                    # Fast extension check using set membership
                    line_lower = line.lower()
                    has_plugin_ext = False
                    for ext in PLUGIN_EXTENSIONS:
                        if ext in line_lower:
                            has_plugin_ext = True
                            break

                    if has_plugin_ext:
                        # Validate plugin line and extract clean plugin name
                        plugin_name = self._validate_plugin_line(line, line_num, original_line)
                        if plugin_name:
                            plugins.append(plugin_name)

            logger.info(f"Found {len(plugins)} plugins in load order")
        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error reading load order: {e}")
            return []
        else:
            return plugins

    def _validate_plugin_line(self, line: str, line_num: int, original_line: str) -> str | None:
        """
        Validates a plugin line to ensure the extension is at the end.

        Args:
            line: The processed line (with prefix removed)
            line_num: The line number in the file
            original_line: The original line from the file

        Returns:
            str | None: The validated plugin name, or None if invalid
        """
        # Check if the line contains separators that would indicate multiple plugins
        has_separator = any(sep in line for sep in SEPARATOR_CHARS)

        if has_separator:
            # Line contains separators, extract the first plugin
            for ext in PLUGIN_EXTENSIONS:
                ext_pos: int = line.lower().find(ext)
                if ext_pos != -1:
                    # Check what comes after the extension
                    after_ext: str = line[ext_pos + len(ext) :]

                    # Check if it's followed by common separators (comma, semicolon)
                    if after_ext and after_ext[0] in [",", ";"]:
                        plugin_name: str = line[: ext_pos + len(ext)]
                        remaining_content: str = after_ext.strip()
                        if remaining_content:  # There's meaningful content after the extension
                            logger.warning(
                                f"Line {line_num}: Plugin extension not at end of line. "
                                f"Original: '{original_line}' -> Using: '{plugin_name}' "
                                f"(ignored: '{remaining_content}')"
                            )
                        return plugin_name

        # Check if the line ends with a valid extension (clean case)
        for ext in PLUGIN_EXTENSIONS:
            if line.lower().endswith(ext):
                # This is a clean plugin line
                return line

        # Check if the line contains a valid extension followed by space or other content (not other extensions)
        for ext in PLUGIN_EXTENSIONS:
            ext_pos = line.lower().find(ext)
            if ext_pos != -1:
                after_ext = line[ext_pos + len(ext) :]
                # Check if there's space or whitespace after the extension (not other extensions)
                if after_ext and after_ext[0] in [" ", "\t"]:
                    plugin_name = line[: ext_pos + len(ext)]
                    remaining_content = after_ext.strip()
                    if remaining_content:  # There's meaningful content after the extension
                        logger.warning(
                            f"Line {line_num}: Plugin extension not at end of line. "
                            f"Original: '{original_line}' -> Using: '{plugin_name}' "
                            f"(ignored: '{remaining_content}')"
                        )
                    return plugin_name

        # No valid extension found or extension not properly positioned
        return None
