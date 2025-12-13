<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AutoQAC is a PySide6 (Qt) application for batch cleaning Bethesda game plugins using xEdit's quickautoclean. It removes Identical To Master Records (ITMs) and Undisabled References (UDRs) from game plugins for Fallout 3/NV/4, Skyrim SE, and VR variants.

## Essential Commands

```bash
# Install dependencies
uv sync --extra dev

# Run linting and formatting
uv run ruff check .                  # Check for issues
uv run ruff check . --fix           # Auto-fix issues
uv run ruff format .                # Format code

# Run type checking
uv run mypy AutoQAC_Interface.py AutoQACLib/*.py

# Run tests
uv run pytest                                   # All tests
uv run pytest -m unit                          # Unit tests only
uv run pytest -m integration                   # Integration tests only
uv run pytest tests/test_state_manager.py     # Single test file
uv run pytest -v                               # Verbose output
uv run pytest --cov=AutoQACLib --cov=AutoQAC_Interface --cov-report=html  # With coverage

# Run the application
uv run python AutoQAC_Interface.py
```

## Code Organization Rules

### GUI Development Guidelines
- **New GUI functionality**: Create as MixIn classes in `AutoQACLib/ui/mixins/`
- **Dialog components**: Define in `AutoQACLib/ui/dialogs/`
- **MixIn pattern**: Compose MainWindow functionality through multiple focused mixins
- **Separation of concerns**: Each mixin should handle a single responsibility

## Architecture

### Core Components

1. **StateManager** (`state_manager.py`): Centralized thread-safe state management with `AppState` dataclass. All state mutations go through here with QMutex/QReadWriteLock protection and Qt signals for changes.

2. **ConfigManager** (`config_manager.py`): YAML configuration file I/O. Two instances used:
   - Main config (`AutoQAC Data/AutoQAC Main.yaml`): Game configs, skip lists
   - User config (`AutoQAC Data/AutoQAC Config.yaml`): User settings, paths

3. **YamlManager** (`yaml_manager.py`): Low-level YAML operations with file-level mutex locking for thread-safe concurrent access.

4. **CleaningService** (`cleaning_service.py`): Pure business logic for plugin cleaning. No Qt dependencies. Handles subprocess execution and output parsing.

5. **GuiController** (`gui_controller.py`): Mediator between GUI and business logic. Manages worker threads and coordinates state updates.

6. **CleaningWorker** (`cleaning_worker.py`): QThread for background cleaning operations. Communicates via Qt signals only.

7. **MainWindow** (`ui/main_window.py`): Main application window composed of multiple mixins for separation of concerns.

8. **AutoQAC_Interface.py**: Slim entry point that creates the application and window instances.

### Critical Threading Rules

**MUST use PySide6 threading exclusively**:
- Use: `QThread`, `QThreadPool`, `QMutex`, `QReadWriteLock`, `QWaitCondition`
- NEVER use: Python's `threading`, `asyncio`, or `concurrent.futures`
- All inter-thread communication through Qt signals/slots only
- All shared data access must be synchronized via StateManager
- Resource limit for concurrent subprocesses controlled by `max_concurrent_subprocesses` in AppState

### Key Technical Constraints

- **Python Version**: 3.12+ required
- **File Encoding**: UTF-8 always
- **Logging**: Rotating file logs in `logs/` directory (not console)
- **Type Annotations**: Required for all new code
- **Line Length**: 120 characters maximum
- **State Updates**: Only through StateManager, never direct manipulation

### Workflow

1. User configures paths via GUI → saved to YAML configs
2. GuiController validates environment (xEdit.exe, load order files)
3. CleaningWorker (QThread) processes plugins sequentially
4. For each plugin:
   - Check skip list in main config
   - Build xEdit command with QAC flags
   - Execute subprocess with timeout (default 300s)
   - Parse output for ITMs/UDRs/deleted navmeshes
   - Update state and emit progress signals
5. GUI updates based on Qt signals
6. Final summary displayed on completion

### Configuration Files

- `pyproject.toml`: Project dependencies and tool configs (ruff, mypy, pytest, coverage)
- `AutoQAC Data/AutoQAC Main.yaml`: Game configurations, plugin skip lists
- `AutoQAC Data/AutoQAC Config.yaml`: User settings, file paths
- `AutoQAC Data/AutoQAC Ignore.yaml`: User-defined plugin ignore lists

### Dependency Injection Pattern

Components receive dependencies through constructors:
```python
def __init__(self, state: StateManager, config: ConfigManager):
    self.state = state
    self.config = config
```

No global variables or direct imports between layers.

### xEdit Integration

The application interfaces with xEdit (SSEEdit/FO4Edit) via subprocess:
- Commands built with `-QAC` flag for Quick Auto Clean
- Supports MO2 integration via `ModOrganizer.exe run` command wrapper
- Optional `-iknowwhatimdoing -allowmakepartial` flags for experimental Partial Forms feature
- Timeout handling (default 300s per plugin)
- Output parsing for ITMs, UDRs, and deleted navmeshes

### Supported Games

| Game                   | Short Code | xEdit Executables          |
| ---------------------- | ---------- | -------------------------- |
| Fallout 3              | FO3        | FO3Edit.exe, FO3Edit64.exe |
| Fallout New Vegas      | FNV        | FNVEdit.exe, FNVEdit64.exe |
| Fallout 4              | FO4        | FO4Edit.exe, FO4Edit64.exe |
| Fallout 4 VR           | FO4VR      | FO4VREdit.exe              |
| Skyrim Special Edition | SSE        | SSEEdit.exe, SSEEdit64.exe |
| Skyrim VR              | SkyrimVR   | TES5VREdit.exe             |

Also supports universal xEdit executables (`xEdit.exe`, `xEdit64.exe`) with automatic game detection.

Each game has specific configuration in `AutoQAC Data/AutoQAC Main.yaml`.
