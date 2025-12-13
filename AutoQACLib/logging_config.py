"""Centralized logging configuration for AutoQAC."""

from __future__ import annotations

import logging
import logging.handlers
import sys
from dataclasses import dataclass
from logging import Formatter, Logger, StreamHandler
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO

if TYPE_CHECKING:
    from logging.handlers import RotatingFileHandler


@dataclass
class LoggingConfig:
    """Configuration for logging setup."""

    log_dir: Path | str = "logs"
    log_file: str = "autoqac.log"
    max_bytes: int = 5 * 1024 * 1024  # 5MB
    backup_count: int = 5
    console_level: int = logging.WARNING
    file_level: int = logging.DEBUG
    encoding: str = "utf-8"


def setup_logging(config: LoggingConfig | None = None) -> None:
    """
    Setup logging with rotating file handler and optional console output.

    Args:
        config: Logging configuration object. If None, uses default configuration.
    """
    if config is None:
        config = LoggingConfig()

    log_path: Path = Path(config.log_dir)
    log_path.mkdir(exist_ok=True)

    # Create formatter
    formatter: Formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create rotating file handler
    file_handler: RotatingFileHandler = logging.handlers.RotatingFileHandler(
        log_path / config.log_file, maxBytes=config.max_bytes, backupCount=config.backup_count, encoding=config.encoding
    )
    file_handler.setLevel(config.file_level)
    file_handler.setFormatter(formatter)

    # Create console handler
    console_handler: StreamHandler[TextIO | Any] = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.console_level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger: Logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


@dataclass
class TestLoggingConfig:
    """Configuration for test logging setup."""

    log_dir: Path | str = "tests/test_output"
    log_file: str = "test_autoqac.log"
    max_bytes: int = 1 * 1024 * 1024  # 1MB for tests
    backup_count: int = 3
    encoding: str = "utf-8"


def setup_test_logging(config: TestLoggingConfig | None = None) -> None:
    """
    Setup logging specifically for tests.

    Args:
        config: Test logging configuration object. If None, uses default configuration.
    """
    if config is None:
        config = TestLoggingConfig()

    log_path: Path = Path(config.log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter: Formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create test log file handler
    file_handler: RotatingFileHandler = logging.handlers.RotatingFileHandler(
        log_path / config.log_file, maxBytes=config.max_bytes, backupCount=config.backup_count, encoding=config.encoding
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Configure root logger for tests
    root_logger: Logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add test file handler only (no console output for tests)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_startup_info(logger: logging.Logger, app_name: str = "AutoQAC", version: str | None = None) -> None:
    """Log startup information."""
    if version is None:
        from AutoQACLib import __version__

        version = __version__
    separator = "=" * 60
    logger.info(separator)
    logger.info(f"{app_name} v{version} - Starting up")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Working directory: {Path.cwd()}")

    # Log file information
    log_file = "Not configured"
    for handler in logger.handlers:
        if isinstance(handler, (logging.FileHandler, logging.handlers.RotatingFileHandler)):
            log_file = handler.baseFilename
            break

    logger.info(f"Log file: {log_file}")
    logger.info(f"Log level: {logger.getEffectiveLevel()}")
    logger.info(separator)
