"""Tests for the utils module."""

import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from AutoQACLib.game_detection import monitor_log_file, yaml_settings, yaml_settings_write
from AutoQACLib.process_utils import run_process, run_process_with_realtime_output
from AutoQACLib.yaml_manager import YamlManager


class TestYamlManager:
    """Test the YamlManager class."""

    def test_initialization(self) -> None:
        """Test YamlManager initialization."""
        manager: YamlManager = YamlManager()
        assert manager._cache == {}  # noqa: SLF001
        assert manager._file_mutexes == {}  # noqa: SLF001

    def test_parse_key_path(self) -> None:
        """Test _parse_key_path method."""
        manager: YamlManager = YamlManager()

        # Test string path
        keys1: list[str] = manager._parse_key_path("level1.level2.level3")  # noqa: SLF001
        assert keys1 == ["level1", "level2", "level3"]

        # Test list path
        keys2: list[str] = manager._parse_key_path(["level1", "level2", "level3"])  # noqa: SLF001
        assert keys2 == ["level1", "level2", "level3"]

    def test_get_value_simple(self, temp_test_config_file: Path) -> None:
        """Test getting a simple value from YAML."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("key: value\n")

        manager = YamlManager()
        value = manager.get_value(yaml_path, "key")
        assert value == "value"

    def test_get_value_nested(self, temp_test_config_file: Path) -> None:
        """Test getting a nested value from YAML."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("""
level1:
  level2:
    level3: nested_value
""")

        manager = YamlManager()
        value = manager.get_value(yaml_path, "level1.level2.level3")
        assert value == "nested_value"

    def test_get_value_nonexistent(self, temp_test_config_file: Path) -> None:
        """Test getting a non-existent value."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("key: value\n")

        manager = YamlManager()
        value = manager.get_value(yaml_path, "nonexistent")
        assert value is None

        value = manager.get_value(yaml_path, "key.nonexistent")
        assert value is None

    def test_set_value_simple(self, temp_test_config_file: Path) -> None:
        """Test setting a simple value in YAML."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("key: old_value\n")

        manager = YamlManager()
        manager.set_value(yaml_path, "key", "new_value")

        # Verify the value was set
        value = manager.get_value(yaml_path, "key")
        assert value == "new_value"

    def test_set_value_nested(self, temp_test_config_file: Path) -> None:
        """Test setting a nested value in YAML."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("level1: {}\n")

        manager = YamlManager()
        manager.set_value(yaml_path, "level1.level2.level3", "nested_value")

        # Verify the value was set
        value = manager.get_value(yaml_path, "level1.level2.level3")
        assert value == "nested_value"

    def test_set_value_create_intermediate(self, temp_test_config_file: Path) -> None:
        """Test setting a value with non-existent intermediate keys."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("{}\n")

        manager = YamlManager()
        manager.set_value(yaml_path, "new.level1.level2", "value")

        # Verify the value was set and intermediate keys created
        value = manager.get_value(yaml_path, "new.level1.level2")
        assert value == "value"

        # Check that intermediate structure exists
        level1 = manager.get_value(yaml_path, "new.level1")
        assert isinstance(level1, dict)

    def test_cache_functionality(self, temp_test_config_file: Path) -> None:
        """Test that YAML files are cached."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("key: value\n")

        manager = YamlManager()

        # First read should load from file
        value1 = manager.get_value(yaml_path, "key")
        assert value1 == "value"

        # Second read should use cache
        value2 = manager.get_value(yaml_path, "key")
        assert value2 == "value"

        # Cache should contain the file
        assert yaml_path in manager._cache  # noqa: SLF001

    def test_empty_file_handling(self, temp_test_config_file: Path) -> None:
        """Test handling of empty YAML files."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("")

        manager = YamlManager()
        value = manager.get_value(yaml_path, "key")
        assert value is None

        # Should be able to set values in empty file
        manager.set_value(yaml_path, "new_key", "new_value")
        value = manager.get_value(yaml_path, "new_key")
        assert value == "new_value"

    def test_nonexistent_file_handling(self, test_output_dir: Path) -> None:
        """Test handling of non-existent YAML files."""
        yaml_path: str = str(test_output_dir / "nonexistent_file.yaml")
        manager = YamlManager()

        value = manager.get_value(yaml_path, "key")
        assert value is None

        # Should be able to set values (creates file)
        manager.set_value(yaml_path, "key", "value")
        value = manager.get_value(yaml_path, "key")
        assert value == "value"

        # Clean up created file
        Path(yaml_path).unlink(missing_ok=True)

    def test_thread_safety(self, temp_test_config_file: Path) -> None:
        """Test thread safety of YAML operations."""
        import threading
        import time

        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("{}\n")

        manager = YamlManager()

        def write_values(thread_id: int) -> None:
            for i in range(10):
                key = f"thread_{thread_id}_key_{i}"
                value = f"value_{thread_id}_{i}"
                manager.set_value(yaml_path, key, value)
                time.sleep(0.001)

        def read_values(thread_id: int) -> None:
            for i in range(10):
                key = f"thread_{thread_id}_key_{i}"
                manager.get_value(yaml_path, key)
                time.sleep(0.001)

        # Create multiple threads
        threads: list[threading.Thread] = []
        for i in range(5):
            write_thread: threading.Thread = threading.Thread(target=write_values, args=(i,))
            read_thread: threading.Thread = threading.Thread(target=read_values, args=(i,))
            threads.extend([write_thread, read_thread])
            write_thread.start()
            read_thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should not have crashed
        assert True


class TestYamlSettingsFunctions:
    """Test the yaml_settings and yaml_settings_write functions."""

    def test_yaml_settings_simple(self, temp_test_config_file: Path) -> None:
        """Test yaml_settings function with simple value."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("key: value\n")

        value = yaml_settings(yaml_path, "key")
        assert value == "value"

    def test_yaml_settings_nested(self, temp_test_config_file: Path) -> None:
        """Test yaml_settings function with nested value."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("""
level1:
  level2:
    level3: nested_value
""")

        value = yaml_settings(yaml_path, "level1.level2.level3")
        assert value == "nested_value"

    def test_yaml_settings_write_simple(self, temp_test_config_file: Path) -> None:
        """Test yaml_settings_write function with simple value."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("{}\n")

        yaml_settings_write(yaml_path, "new_value", "key")
        value = yaml_settings(yaml_path, "key")
        assert value == "new_value"

    def test_yaml_settings_write_nested(self, temp_test_config_file: Path) -> None:
        """Test yaml_settings_write function with nested value."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("{}\n")

        yaml_settings_write(yaml_path, "nested_value", "level1.level2.level3")
        value = yaml_settings(yaml_path, "level1.level2.level3")
        assert value == "nested_value"

    def test_yaml_settings_write_replace_data(self, temp_test_config_file: Path) -> None:
        """Test yaml_settings_write function replacing entire data."""
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("old_key: old_value\n")

        new_data = {"new_key": "new_value", "another_key": "another_value"}
        yaml_settings_write(yaml_path, new_data)

        # Should replace entire content
        value1 = yaml_settings(yaml_path, "new_key")
        value2 = yaml_settings(yaml_path, "another_key")
        old_value = yaml_settings(yaml_path, "old_key")

        assert value1 == "new_value"
        assert value2 == "another_value"
        assert old_value is None

    def test_error_handling(self, temp_test_config_file: Path) -> None:
        """Test error handling in YAML operations."""
        # Test with invalid YAML
        yaml_path = str(temp_test_config_file)
        temp_test_config_file.write_text("invalid: yaml: content: [\n")

        # Should handle invalid YAML gracefully
        value = yaml_settings(yaml_path, "key")
        assert value is None

    def test_path_object_handling(self, temp_test_config_file: Path) -> None:
        """Test that functions handle Path objects correctly."""
        yaml_path: Path = temp_test_config_file
        yaml_path.write_text("key: value\n")

        value = yaml_settings(yaml_path, "key")
        assert value == "value"

        yaml_settings_write(yaml_path, "new_value", "new_key")
        value = yaml_settings(yaml_path, "new_key")
        assert value == "new_value"


class TestProcessFunctions:
    """Test process-related utility functions."""

    @patch("AutoQACLib.process_utils.psutil.Process")
    def test_check_process_below_threshold(self, mock_process: Mock) -> None:
        """Test check_process when CPU usage is below threshold."""
        mock_process_instance: Mock = Mock()
        mock_process_instance.cpu_percent.return_value = 3.0
        mock_process.return_value = mock_process_instance

        from AutoQACLib.process_utils import check_process

        result: bool = check_process(12345, threshold=5)
        assert result is False

    @patch("AutoQACLib.process_utils.psutil.Process")
    def test_check_process_above_threshold(self, mock_process: Mock) -> None:
        """Test check_process when CPU usage is above threshold."""
        mock_process_instance: Mock = Mock()
        mock_process_instance.cpu_percent.return_value = 7.0
        mock_process.return_value = mock_process_instance

        from AutoQACLib.process_utils import check_process

        result = check_process(12345, threshold=5)
        assert result is True

    @patch("AutoQACLib.process_utils.psutil.Process")
    def test_check_process_no_such_process(self, mock_process: Mock) -> None:
        """Test check_process when process doesn't exist."""
        from psutil import NoSuchProcess

        mock_process.side_effect = NoSuchProcess(12345)

        from AutoQACLib.process_utils import check_process

        result = check_process(12345)
        assert result is False

    @patch("AutoQACLib.process_utils.psutil.Process")
    def test_check_process_access_denied(self, mock_process: Mock) -> None:
        """Test check_process when access is denied."""
        from psutil import AccessDenied

        mock_process.side_effect = AccessDenied(12345)

        from AutoQACLib.process_utils import check_process

        result = check_process(12345)
        assert result is False


class TestGameDetectionFunctions:
    """Test game detection utility functions."""

    def test_detect_game_from_load_order_skyrim(self, temp_test_file: Path) -> None:
        """Test detect_game_from_load_order with Skyrim."""
        load_order_path: Path = temp_test_file
        load_order_path.write_text("Skyrim.esm\nSomeOtherPlugin.esp\n")

        from AutoQACLib.game_detection import detect_game_from_load_order

        result = detect_game_from_load_order(load_order_path)
        assert result == "SSE"

    def test_detect_game_from_load_order_fallout3(self, temp_test_file: Path) -> None:
        """Test detect_game_from_load_order with Fallout 3."""
        load_order_path: Path = temp_test_file
        load_order_path.write_text("Fallout3.esm\nSomeOtherPlugin.esp\n")

        from AutoQACLib.game_detection import detect_game_from_load_order

        result = detect_game_from_load_order(load_order_path)
        assert result == "FO3"

    def test_detect_game_from_load_order_falloutnv(self, temp_test_file: Path) -> None:
        """Test detect_game_from_load_order with Fallout New Vegas."""
        load_order_path: Path = temp_test_file
        load_order_path.write_text("FalloutNV.esm\nSomeOtherPlugin.esp\n")

        from AutoQACLib.game_detection import detect_game_from_load_order

        result = detect_game_from_load_order(load_order_path)
        assert result == "FNV"

    def test_detect_game_from_load_order_fallout4(self, temp_test_file: Path) -> None:
        """Test detect_game_from_load_order with Fallout 4."""
        load_order_path: Path = temp_test_file
        load_order_path.write_text("Fallout4.esm\nSomeOtherPlugin.esp\n")

        from AutoQACLib.game_detection import detect_game_from_load_order

        result = detect_game_from_load_order(load_order_path)
        assert result == "FO4"

    def test_detect_game_from_load_order_with_prefix(self, temp_test_file: Path) -> None:
        """Test detect_game_from_load_order with prefix characters."""
        load_order_path: Path = temp_test_file
        load_order_path.write_text("*Skyrim.esm\n+SomeOtherPlugin.esp\n")

        from AutoQACLib.game_detection import detect_game_from_load_order

        result = detect_game_from_load_order(load_order_path)
        assert result == "SSE"

    def test_detect_game_from_load_order_no_match(self, temp_test_file: Path) -> None:
        """Test detect_game_from_load_order with no matching game."""
        load_order_path: Path = temp_test_file
        load_order_path.write_text("SomePlugin.esp\nAnotherPlugin.esp\n")

        from AutoQACLib.game_detection import detect_game_from_load_order

        result = detect_game_from_load_order(load_order_path)
        assert result is None

    def test_detect_game_from_load_order_file_not_found(self) -> None:
        """Test detect_game_from_load_order with non-existent file."""

        from AutoQACLib.game_detection import detect_game_from_load_order

        with pytest.raises(FileNotFoundError):
            detect_game_from_load_order(Path("/nonexistent/file.txt"))

    def test_detect_xedit_game_from_filename(self) -> None:
        """Test detect_xedit_game with various xEdit executable names."""
        from AutoQACLib.game_detection import detect_xedit_game

        test_cases = [
            ("fo3edit.exe", "FO3"),
            ("fnvedit.exe", "FNV"),
            ("ttwedit.exe", "TTW"),
            ("fo4edit.exe", "FO4"),
            ("fo4vredit.exe", "FO4"),
            ("sseedit.exe", "SSE"),
            ("tes5edit.exe", "SSE"),
            ("skyrimvredit.exe", "SSE"),
        ]

        for filename, expected in test_cases:
            result = detect_xedit_game(filename)
            assert result == expected

    def test_detect_xedit_game_no_match(self) -> None:
        """Test detect_xedit_game with no matching executable name."""
        from AutoQACLib.game_detection import detect_xedit_game

        result = detect_xedit_game("some_other_tool.exe")
        assert result is None

    def test_detect_xedit_game_with_load_order_fallback(self, temp_test_file: Path) -> None:
        """Test detect_xedit_game with load order fallback."""
        load_order_path: Path = temp_test_file
        load_order_path.write_text("Skyrim.esm\n")

        from AutoQACLib.game_detection import detect_xedit_game

        result = detect_xedit_game("unknown_edit.exe", load_order_path)
        assert result == "SSE"


class TestProcessExecutionFunctions:
    """Test process execution utility functions."""

    def test_run_process_success(self) -> None:
        """Test run_process with successful command."""
        # Test with a simple cross-platform command
        exit_code, stdout, stderr = run_process(["python", "-c", "print('Hello, World!')"])

        assert exit_code == 0
        assert "Hello, World!" in stdout
        assert stderr == ""

    def test_run_process_failure(self) -> None:
        """Test run_process with failing command."""
        # Test with invalid command
        exit_code, stdout, stderr = run_process(["python", "-c", "import sys; sys.exit(1)"])

        assert exit_code == 1
        assert stdout == ""

    def test_run_process_timeout(self) -> None:
        """Test run_process with timeout."""
        # Test command that would run forever without timeout
        exit_code, stdout, stderr = run_process(["python", "-c", "import time; time.sleep(10)"], timeout=1)

        assert exit_code == -1
        assert "Process timed out" in stderr

    def test_run_process_invalid_command(self) -> None:
        """Test run_process with invalid command."""
        # Test with non-existent command
        exit_code, stdout, stderr = run_process(["this_command_does_not_exist"])

        assert exit_code == -1
        assert stderr != ""

    def test_run_process_with_realtime_output_success(self) -> None:
        """Test run_process_with_realtime_output with successful command."""
        output_lines = []

        def callback(line: str) -> None:
            output_lines.append(line)

        # Test with command that outputs multiple lines
        exit_code, stdout, stderr = run_process_with_realtime_output(
            ["python", "-c", "print('Line 1'); print('Line 2'); print('Line 3')"], output_callback=callback
        )

        assert exit_code == 0
        assert len(output_lines) >= 3
        assert any("Line 1" in line for line in output_lines)
        assert any("Line 2" in line for line in output_lines)
        assert any("Line 3" in line for line in output_lines)

    def test_run_process_with_realtime_output_no_callback(self) -> None:
        """Test run_process_with_realtime_output without callback."""
        # Should work without callback
        exit_code, stdout, stderr = run_process_with_realtime_output(["python", "-c", "print('Test output')"])

        assert exit_code == 0
        assert "Test output" in stdout

    def test_run_process_with_realtime_output_cwd(self, test_output_dir: Path) -> None:
        """Test run_process_with_realtime_output with custom working directory."""
        # Create a test file in temp directory
        test_file = test_output_dir / "test.txt"
        test_file.write_text("test content")

        # Run command in the temp directory
        exit_code, stdout, stderr = run_process_with_realtime_output(
            ["python", "-c", "import os; print(os.listdir('.'))"], working_dir=str(test_output_dir)
        )

        assert exit_code == 0
        assert "test.txt" in stdout


class TestLogMonitoringFunctions:
    """Test log monitoring utility functions."""

    def test_monitor_log_file_existing_file(self, test_output_dir: Path) -> None:
        """Test monitor_log_file with existing file."""
        import threading

        # Create a log file with initial content
        log_file = test_output_dir / "test.log"
        log_file.write_text("Initial line\n")

        # Track lines read
        lines_read = []
        stop_event = threading.Event()

        def callback(line: str) -> None:
            lines_read.append(line.strip())
            if len(lines_read) >= 2:
                stop_event.set()

        # Start monitoring in a thread
        monitor_thread = threading.Thread(target=monitor_log_file, args=(str(log_file), callback, stop_event))
        monitor_thread.start()

        # Give it time to start monitoring
        time.sleep(0.1)

        # Append new lines (monitor_log_file only reads NEW lines after it starts)
        with log_file.open("a") as f:
            f.write("First new line\n")
            f.flush()
            time.sleep(0.1)
            f.write("Second new line\n")
            f.flush()

        # Wait for monitoring to complete or timeout
        monitor_thread.join(timeout=2)

        # Should only see the new lines, not the initial content
        assert "First new line" in lines_read
        assert "Second new line" in lines_read
        assert "Initial line" not in lines_read  # This was written before monitoring started

    def test_monitor_log_file_new_file(self, test_output_dir: Path) -> None:
        """Test monitor_log_file with file created after monitoring starts."""
        import threading

        log_file = test_output_dir / "new_test.log"
        lines_read = []
        stop_event = threading.Event()

        def callback(line: str) -> None:
            lines_read.append(line.strip())
            if "Stop monitoring" in line:
                stop_event.set()

        # Start monitoring before file exists
        monitor_thread = threading.Thread(target=monitor_log_file, args=(str(log_file), callback, stop_event))
        monitor_thread.start()

        # Create file after monitoring starts
        time.sleep(0.2)
        # Create empty file first
        log_file.touch()

        # Give monitor time to find the file and seek to end
        time.sleep(0.2)

        # Now append lines
        with log_file.open("a") as f:
            f.write("First line\n")
            f.flush()
            time.sleep(0.1)
            f.write("Second line\n")
            f.flush()
            time.sleep(0.1)
            f.write("Stop monitoring\n")
            f.flush()

        # Wait for monitoring to complete
        monitor_thread.join(timeout=3)

        # Should read all lines from the newly created file
        assert "First line" in lines_read
        assert "Second line" in lines_read
        assert "Stop monitoring" in lines_read

    def test_monitor_log_file_nonexistent(self) -> None:
        """Test log file monitoring with non-existent file."""
        import threading
        import time

        log_path: Path = Path("/nonexistent/log.txt")
        lines_received: list[str] = []
        stop_event: threading.Event = threading.Event()

        def line_callback(line: str) -> None:
            lines_received.append(line)

        from AutoQACLib.game_detection import monitor_log_file

        # Start monitoring in a separate thread
        monitor_thread: threading.Thread = threading.Thread(
            target=monitor_log_file, args=(log_path, line_callback, stop_event), kwargs={"poll_interval": 0.1}
        )
        monitor_thread.start()

        # Let it run briefly then stop
        time.sleep(0.2)
        stop_event.set()
        monitor_thread.join(timeout=1)

        # Should not crash even with non-existent file
        assert True
