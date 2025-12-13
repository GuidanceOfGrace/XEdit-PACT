#!/usr/bin/env python3
"""AutoQAC Main Interface - Slim entry point with refactored components."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

from AutoQACLib.config_manager import ConfigManager
from AutoQACLib.gui_controller import GuiController
from AutoQACLib.logging_config import get_logger, log_startup_info, setup_logging
from AutoQACLib.migration import run_all_migrations
from AutoQACLib.state_manager import StateManager
from AutoQACLib.ui.main_window import MainWindow

if TYPE_CHECKING:
    from logging import Logger

# Constants
AUTOQAC_DATA_PATH: Path = Path("AutoQAC Data")
AUTOQAC_YAML_PATH: Path = AUTOQAC_DATA_PATH / "AutoQAC Main.yaml"
AUTOQAC_CONFIG_PATH: Path = AUTOQAC_DATA_PATH / "AutoQAC Config.yaml"  # New config file

# Setup logging
setup_logging()
logger: Logger = get_logger(__name__)
log_startup_info(logger)


def create_application() -> tuple[QApplication, MainWindow]:
    """Create and configure the application and main window."""
    # Create application
    app: QApplication = QApplication(sys.argv)
    app.setApplicationName("AutoQAC")

    # Run legacy configuration migrations
    migration_results = run_all_migrations()
    if any(migration_results.values()):
        logger.info(f"Migration results: {migration_results}")

    # Create config managers
    main_config: ConfigManager = ConfigManager(AUTOQAC_YAML_PATH)  # For skip lists and game configs
    user_config: ConfigManager = ConfigManager(AUTOQAC_CONFIG_PATH)  # For user settings

    # Create state manager and controller
    state: StateManager = StateManager()
    controller: GuiController = GuiController(state, main_config, user_config)

    # Create main window
    window: MainWindow = MainWindow(state, controller)

    return app, window


def main() -> None:
    """
    Main entry point for the application.

    This function initializes the application, displays the main window, and handles any
    fatal errors that may occur during execution. If an error is encountered, it logs the
    error details and terminates the application with a non-zero exit code.

    Raises:
        OSError: If an operating system-related error is encountered.
        RuntimeError: If a runtime error occurs during application execution.
        ValueError: If an invalid value is encountered, causing the application to fail.

    Returns:
        None
    """
    try:
        app, window = create_application()
        window.show()
        sys.exit(app.exec())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except (OSError, RuntimeError, ValueError) as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    except (TypeError, AttributeError, ImportError) as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
