# AutoQAC Test Suite

This directory contains a comprehensive test suite for the AutoQAC application, covering all major components and their interactions.

## Test Structure

### Unit Tests

- **`test_state_manager.py`** - Tests for the `StateManager` class and `AppState` dataclass
  - State initialization and updates
  - Signal emission and handling
  - Thread safety
  - Configuration state management
  - Progress tracking
  - Plugin result management

- **`test_config_manager.py`** - Tests for the `ConfigManager` class
  - Configuration file creation and management
  - YAML read/write operations
  - Path validation
  - Game-specific configuration
  - Settings management
  - Error handling

- **`test_utils.py`** - Tests for utility functions
  - YAML manager operations
  - Thread-safe file operations
  - Cache functionality
  - Error handling

- **`test_gui_controller.py`** - Tests for the `GuiController` class
  - File dialog operations
  - Configuration management
  - Cleaning service integration
  - Signal handling
  - Error handling

### Integration Tests

- **`test_integration.py`** - Tests for component interactions
  - State manager and config manager integration
  - GUI controller and state manager integration
  - Full configuration workflow
  - Cleaning workflow integration
  - Signal propagation
  - Error handling across components
  - Configuration persistence

### Main Interface Tests

- **`test_main_interface.py`** - Tests for the main application interface
  - `CleaningProgressDialog` functionality
  - `MainWindow` UI setup and interactions
  - Application creation and initialization
  - Event handling
  - Progress tracking UI

## Running Tests

### Prerequisites

Install the test dependencies:

```bash
poetry install --with dev
```

### Basic Test Execution

Run all tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=AutoQACLib --cov=AutoQAC_Interface --cov-report=html
```

### Specific Test Categories

Run only unit tests:

```bash
pytest -m unit
```

Run only integration tests:

```bash
pytest -m integration
```

Run only GUI tests:

```bash
pytest -m gui
```

Run tests excluding slow tests:

```bash
pytest -m "not slow"
```

### Test Output

- **Verbose output**: `pytest -v`
- **Detailed failure information**: `pytest -vv`
- **Stop on first failure**: `pytest -x`
- **Show local variables on failure**: `pytest -l`

### Coverage Reports

After running tests with coverage, you can view the HTML report:

```bash
# Open the coverage report in your browser
open htmlcov/index.html
```

## Test Configuration

### Pytest Configuration

The test configuration is defined in `pyproject.toml` under `[tool.pytest.ini_options]`:

- **Test discovery**: Tests are discovered in the `tests/` directory
- **Coverage**: Automatically generates coverage reports for `AutoQACLib` and `AutoQAC_Interface`
- **Markers**: Defines test categories (unit, integration, gui, slow)
- **Warnings**: Filters out deprecation warnings

### Fixtures

Common test fixtures are defined in `conftest.py`:

- **`qt_app`