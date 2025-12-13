"""Tests for the logging_config module."""

import logging
import logging.handlers
from pathlib import Path
from unittest.mock import Mock

import pytest

from AutoQACLib.logging_config import (
    LoggingConfig,
    TestLoggingConfig,
    get_logger,
    log_startup_info,
    setup_logging,
    setup_test_logging,
)


class TestLoggingConfigClass:
    """Test the LoggingConfig dataclass."""

    def test_default_values(self) -> None:
        """Test LoggingConfig default values."""
        config: LoggingConfig = LoggingConfig()

        assert config.log_dir == "logs"
        assert config.log_file == "autoqac.log"
        assert config.max_bytes == 5 * 1024 * 1024  # 5MB
        assert config.backup_count == 5
        assert config.console_level == logging.WARNING
        assert config.file_level == logging.DEBUG
        assert config.encoding == "utf-8"

    def test_custom_values(self) -> None:
        """Test LoggingConfig with custom values."""
        config: LoggingConfig = LoggingConfig(
            log_dir="custom_logs",
            log_file="custom.log",
            max_bytes=1024 * 1024,  # 1MB
            backup_count=3,
            console_level=logging.INFO,
            file_level=logging.ERROR,
            encoding="latin-1",
        )

        assert config.log_dir == "custom_logs"
        assert config.log_file == "custom.log"
        assert config.max_bytes == 1024 * 1024
        assert config.backup_count == 3
        assert config.console_level == logging.INFO
        assert config.file_level == logging.ERROR
        assert config.encoding == "latin-1"


class TestTestLoggingConfigClass:
    """Test the TestLoggingConfig dataclass."""

    def test_default_values(self) -> None:
        """Test TestLoggingConfig default values."""
        config: TestLoggingConfig = TestLoggingConfig()

        assert config.log_dir == "tests/test_output"
        assert config.log_file == "test_autoqac.log"
        assert config.max_bytes == 1 * 1024 * 1024  # 1MB
        assert config.backup_count == 3
        assert config.encoding == "utf-8"

    def test_custom_values(self) -> None:
        """Test TestLoggingConfig with custom values."""
        config: TestLoggingConfig = TestLoggingConfig(
            log_dir="test_logs",
            log_file="test_custom.log",
            max_bytes=512 * 1024,  # 512KB
            backup_count=2,
            encoding="utf-16",
        )

        assert config.log_dir == "test_logs"
        assert config.log_file == "test_custom.log"
        assert config.max_bytes == 512 * 1024
        assert config.backup_count == 2
        assert config.encoding == "utf-16"


class TestSetupLogging:
    """Test the setup_logging function."""

    def test_setup_logging_default_config(self, test_output_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test setup_logging with default configuration."""
        # Use temporary directory for logs
        log_dir = test_output_dir / "logs"
        monkeypatch.setattr("AutoQACLib.logging_config.Path", lambda x: log_dir if x == "logs" else Path(x))

        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Call setup_logging with default config
        setup_logging()

        # Verify logger configuration
        assert len(root_logger.handlers) == 2

        # Check file handler
        file_handler = next(
            (h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)), None
        )
        assert file_handler is not None
        assert file_handler.level == logging.DEBUG
        assert file_handler.maxBytes == 5 * 1024 * 1024  # 5MB
        assert file_handler.backupCount == 5

        # Check console handler
        console_handler = next(
            (
                h
                for h in root_logger.handlers
                if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.handlers.RotatingFileHandler)
            ),
            None,
        )
        assert console_handler is not None
        assert console_handler.level == logging.WARNING

        # Test that logging works
        test_logger = logging.getLogger("test")
        test_logger.info("Test message")

        # Verify log file was created
        log_file = log_dir / "autoqac.log"
        assert log_file.exists()
        assert "Test message" in log_file.read_text()

    def test_setup_logging_custom_config(self, test_output_dir: Path) -> None:
        """Test setup_logging with custom configuration."""
        # Create custom config
        custom_config = LoggingConfig(
            log_dir=str(test_output_dir / "custom_logs"),
            log_file="custom.log",
            file_level=logging.WARNING,
            console_level=logging.ERROR,
            max_bytes=1024 * 1024,  # 1MB
            backup_count=3,
            encoding="utf-16",
        )

        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Call setup_logging with custom config
        setup_logging(custom_config)

        # Verify custom configuration
        file_handler = next(
            (h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)), None
        )
        assert file_handler is not None
        assert file_handler.level == logging.WARNING
        assert file_handler.maxBytes == 1024 * 1024
        assert file_handler.backupCount == 3

        console_handler = next(
            (
                h
                for h in root_logger.handlers
                if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.handlers.RotatingFileHandler)
            ),
            None,
        )
        assert console_handler is not None
        assert console_handler.level == logging.ERROR

        # Verify log directory was created
        assert Path(custom_config.log_dir).exists()


class TestSetupTestLogging:
    """Test the setup_test_logging function."""

    def test_setup_test_logging_default_config(self, test_output_dir: Path) -> None:
        """Test setup_test_logging with default configuration."""
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create test config with temp directory
        test_config = TestLoggingConfig(log_dir=str(test_output_dir / "test_logs"))

        # Call setup_test_logging
        setup_test_logging(test_config)

        # Verify logger configuration
        assert len(root_logger.handlers) == 1

        # Check file handler
        file_handler = next(
            (h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)), None
        )
        assert file_handler is not None
        assert file_handler.level == logging.DEBUG
        assert file_handler.maxBytes == 1024 * 1024  # 1MB default
        assert file_handler.backupCount == 3

        # Test that logging works
        test_logger = logging.getLogger("test")
        test_logger.debug("Debug test message")
        test_logger.info("Info test message")

        # Verify log file was created
        log_file = test_output_dir / "test_logs" / "test_autoqac.log"
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Debug test message" in log_content
        assert "Info test message" in log_content

    def test_setup_test_logging_no_console_output(
        self, test_output_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that setup_test_logging doesn't create console output."""
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create test config
        test_config = TestLoggingConfig(log_dir=str(test_output_dir / "test_logs"))

        # Call setup_test_logging
        setup_test_logging(test_config)

        # Log some messages
        logger = logging.getLogger("test")
        logger.info("This should not go to console")
        logger.error("This also should not go to console")

        # Check that nothing was printed to console
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

        # But verify it was written to file
        log_file = test_output_dir / "test_logs" / "test_autoqac.log"
        log_content = log_file.read_text()
        assert "This should not go to console" in log_content
        assert "This also should not go to console" in log_content


class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger_returns_logger(self) -> None:
        """Test that get_logger returns a logger instance."""
        logger: logging.Logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_same_name_returns_same_logger(self) -> None:
        """Test that get_logger returns the same logger for the same name."""
        logger1: logging.Logger = get_logger("test_module")
        logger2: logging.Logger = get_logger("test_module")

        assert logger1 is logger2

    def test_get_logger_different_names_returns_different_loggers(self) -> None:
        """Test that get_logger returns different loggers for different names."""
        logger1: logging.Logger = get_logger("test_module_1")
        logger2: logging.Logger = get_logger("test_module_2")

        assert logger1 is not logger2
        assert logger1.name == "test_module_1"
        assert logger2.name == "test_module_2"


class TestLogStartupInfo:
    """Test the log_startup_info function."""

    def test_log_startup_info_basic(self) -> None:
        """Test log_startup_info with basic parameters."""
        logger: Mock = Mock()
        logger.handlers = []  # Empty handlers list

        log_startup_info(logger)

        # Verify separator lines were logged
        assert logger.info.call_count >= 3
        calls: list[str] = [c[0][0] for c in logger.info.call_args_list]
        assert any("=" * 60 in c for c in calls)
        assert any("AutoQAC v2.0.0 - Starting up" in c for c in calls)

    def test_log_startup_info_custom_app_name(self) -> None:
        """Test log_startup_info with custom app name."""
        logger: Mock = Mock()
        logger.handlers = []  # Empty handlers list

        log_startup_info(logger, app_name="CustomApp", version="1.0.0")

        # Verify custom app name was logged
        calls: list[str] = [c[0][0] for c in logger.info.call_args_list]
        assert any("CustomApp v1.0.0 - Starting up" in c for c in calls)

    def test_log_startup_info_with_file_handler(self) -> None:
        """Test log_startup_info when logger has a file handler."""
        logger: Mock = Mock()

        # Mock a file handler with proper type and attributes
        mock_handler: Mock = Mock(spec=logging.FileHandler)
        mock_handler.baseFilename = "/path/to/log/file.log"
        logger.handlers = [mock_handler]

        log_startup_info(logger)

        # Verify log file path was logged
        calls: list[str] = [c[0][0] for c in logger.info.call_args_list]
        assert any("Log file: /path/to/log/file.log" in c for c in calls)

    def test_log_startup_info_with_rotating_file_handler(self) -> None:
        """Test log_startup_info when logger has a rotating file handler."""
        logger: Mock = Mock()

        # Mock a rotating file handler with proper type and attributes
        mock_handler: Mock = Mock(spec=logging.handlers.RotatingFileHandler)
        mock_handler.baseFilename = "/path/to/rotating.log"
        logger.handlers = [mock_handler]

        log_startup_info(logger)

        # Verify log file path was logged
        calls: list[str] = [c[0][0] for c in logger.info.call_args_list]
        assert any("Log file: /path/to/rotating.log" in c for c in calls)

    def test_log_startup_info_no_file_handler(self) -> None:
        """Test log_startup_info when logger has no file handler."""
        logger: Mock = Mock()
        logger.handlers = []

        log_startup_info(logger)

        # Verify default log file message was logged
        calls: list[str] = [c[0][0] for c in logger.info.call_args_list]
        assert any("Log file: Not configured" in c for c in calls)

    def test_log_startup_info_log_level(self) -> None:
        """Test log_startup_info logs the effective log level."""
        logger: Mock = Mock()
        logger.handlers = []  # Empty handlers list
        logger.getEffectiveLevel.return_value = logging.INFO

        log_startup_info(logger)

        # Verify log level was logged
        calls: list[str] = [c[0][0] for c in logger.info.call_args_list]
        assert any("Log level: 20" in c for c in calls)  # INFO level is 20
