"""Test the test output directory setup and fixtures."""

from pathlib import Path


def test_test_output_directory_exists(test_output_dir: Path) -> None:
    """Test that the test output directory exists and is accessible."""
    assert test_output_dir.exists()
    assert test_output_dir.is_dir()
    assert test_output_dir.name == "test_output"


def test_temp_test_file_fixture(temp_test_file: Path) -> None:
    """Test that the temp test file fixture works correctly."""
    # Initially the file doesn't exist
    assert not temp_test_file.exists()

    # Create the file
    temp_test_file.write_text("test content")
    assert temp_test_file.exists()
    assert temp_test_file.read_text() == "test content"

    # File should be in the test output directory
    assert temp_test_file.parent.name == "test_output"


def test_temp_test_config_file_fixture(temp_test_config_file: Path) -> None:
    """Test that the temp test config file fixture works correctly."""
    # Initially the file doesn't exist
    assert not temp_test_config_file.exists()

    # Create the file
    temp_test_config_file.write_text("test_key: test_value")
    assert temp_test_config_file.exists()
    assert temp_test_config_file.suffix == ".yaml"
    assert "test_key: test_value" in temp_test_config_file.read_text()

    # File should be in the test output directory
    assert temp_test_config_file.parent.name == "test_output"


def test_file_factory_fixture(test_file_factory: callable) -> None:
    """Test that the test file factory works correctly."""
    # Create a test file
    test_file = test_file_factory("test_factory.txt", "factory content")
    assert test_file.exists()
    assert test_file.read_text() == "factory content"
    assert test_file.parent.name == "test_output"

    # Create another file with suffix
    yaml_file = test_file_factory("test_config", "", ".yaml")
    assert yaml_file.exists()
    assert yaml_file.suffix == ".yaml"
    assert yaml_file.parent.name == "test_output"


def test_logging_goes_to_test_output(test_output_dir: Path) -> None:
    """Test that test logging goes to the test output directory."""
    log_file = test_output_dir / "test_autoqac.log"
    # Log file should exist (created by test setup)
    assert log_file.exists()

    # Should contain some log entries
    log_content = log_file.read_text()
    assert len(log_content) > 0
