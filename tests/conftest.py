"""Pytest configuration and common fixtures for AutoQAC tests."""

from collections.abc import Generator
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from AutoQACLib.config_manager import ConfigManager
from AutoQACLib.logging_config import setup_test_logging
from AutoQACLib.state_manager import StateManager

# Test output directory path
TEST_OUTPUT_DIR = Path(__file__).parent / "test_output"


@pytest.fixture(scope="session")
def test_output_dir() -> Path:
    """Get the test output directory path."""
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)
    return TEST_OUTPUT_DIR


@pytest.fixture
def temp_test_file(test_output_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary file in the test output directory."""
    import uuid

    temp_file = test_output_dir / f"temp_{uuid.uuid4().hex}.tmp"
    yield temp_file
    # Cleanup
    temp_file.unlink(missing_ok=True)


@pytest.fixture
def temp_test_config_file(test_output_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary YAML config file in the test output directory."""
    import uuid

    temp_file = test_output_dir / f"temp_config_{uuid.uuid4().hex}.yaml"
    yield temp_file
    # Cleanup
    temp_file.unlink(missing_ok=True)


@pytest.fixture
def temp_test_config_files(test_output_dir: Path) -> Generator[tuple[Path, Path], None, None]:
    """Create two temporary YAML config files in the test output directory."""
    import uuid

    temp_file1 = test_output_dir / f"temp_config_{uuid.uuid4().hex}.yaml"
    temp_file2 = test_output_dir / f"temp_config_{uuid.uuid4().hex}.yaml"
    yield (temp_file1, temp_file2)
    # Cleanup
    temp_file1.unlink(missing_ok=True)
    temp_file2.unlink(missing_ok=True)


@pytest.fixture(scope="session")
def qt_app() -> Generator[QCoreApplication, None, None]:
    """Create a Qt application for testing."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app
    app.quit()


@pytest.fixture
def temp_config_file(temp_test_config_file: Path) -> Path:
    """Create a temporary configuration file for testing."""
    return temp_test_config_file


@pytest.fixture
def config_manager(temp_config_file: Path) -> ConfigManager:
    """Create a ConfigManager instance with a temporary config file."""
    return ConfigManager(temp_config_file)


@pytest.fixture
def state_manager() -> StateManager:
    """Create a StateManager instance for testing."""
    return StateManager()


@pytest.fixture
def sample_config_data() -> dict:
    """Provide sample configuration data for testing."""
    return {
        "AutoQAC_Data": {
            "Skip_Lists": {
                "Skyrim": ["Skyrim.esm", "Update.esm", "Dawnguard.esm"],
                "Fallout4": ["Fallout4.esm", "DLCRobot.esm"],
            },
            "XEdit_Lists": {
                "Skyrim": ["Skyrim.esm", "Update.esm"],
                "Fallout4": ["Fallout4.esm"],
            },
        },
        "Settings": {
            "Partial_Forms": False,
            "MO2_Mode": False,
        },
    }


@pytest.fixture
def sample_plugin_list() -> list[str]:
    """Sample list of plugins for testing."""
    return [
        "Skyrim.esm",
        "Update.esm",
        "Dawnguard.esm",
        "HearthFires.esm",
        "Dragonborn.esm",
        "Unofficial Skyrim Patch.esp",
        "TestPlugin1.esp",
        "TestPlugin2.esp",
    ]


@pytest.fixture
def test_file_factory(test_output_dir: Path) -> Generator[callable, None, None]:
    """Factory fixture for creating test files with automatic cleanup."""
    created_files = []

    def create_test_file(filename: str, content: str = "", suffix: str = "") -> Path:
        """Create a test file in the test output directory."""
        if suffix and not filename.endswith(suffix):
            filename = f"{filename}{suffix}"
        file_path = test_output_dir / filename
        if content:
            file_path.write_text(content, encoding="utf-8")
        else:
            file_path.touch()
        created_files.append(file_path)
        return file_path

    yield create_test_file

    # Cleanup all created files
    for file_path in created_files:
        file_path.unlink(missing_ok=True)


# Configure logging for tests
@pytest.fixture(autouse=True)
def setup_logging() -> None:
    """Setup logging for tests with file output."""
    setup_test_logging()
