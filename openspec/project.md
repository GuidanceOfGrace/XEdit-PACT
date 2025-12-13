# Project Context

## Purpose

**AutoQAC (Auto Quick Auto Clean)** is a PySide6 (Qt) application for batch cleaning Bethesda game plugins using xEdit's Quick Auto Clean (-QAC) functionality. It automates the removal of:

- **ITMs (Identical To Master Records)**: Records identical to the master file that overwrite valid changes
- **UDRs (Undisabled References)**: Deleted references that can cause crashes and broken quests
- **Deleted Navmeshes**: Navigation meshes that can cause crashes

**Supported Games**: Fallout 3, Fallout New Vegas, Fallout 4, Fallout 4 VR, Skyrim Special Edition, Skyrim VR

## Tech Stack

### Core Technologies
- **Python**: 3.12+ (required)
- **UI Framework**: PySide6 (Qt 6.8+)
- **Configuration**: ruamel-yaml for YAML file I/O
- **Process Management**: psutil for subprocess monitoring

### Development Tools
- **Package Manager**: uv (for dependency management)
- **Linting/Formatting**: ruff
- **Type Checking**: mypy
- **Testing**: pytest with pytest-qt, pytest-cov, pytest-mock
- **Build/Distribution**: PyInstaller, hatchling

### Alternative Implementation
- A Rust/Slint implementation exists in `autoqac-rust/` with Microsoft Fluent Design

## Project Conventions

### Code Style

- **Line Length**: 120 characters maximum
- **Indentation**: 4 spaces
- **Quote Style**: Double quotes
- **File Encoding**: UTF-8 always
- **Type Annotations**: Required for all new code

**Linting Rules** (ruff):
- Import sorting enabled (I)
- Pylint rules (PL)
- Type annotations (ANN)
- Modern Python syntax (UP)
- Performance anti-patterns (PERF)
- See `pyproject.toml` for full configuration

**Commands**:
```bash
uv run ruff check .        # Check for issues
uv run ruff check . --fix  # Auto-fix issues
uv run ruff format .       # Format code
uv run mypy AutoQAC_Interface.py AutoQACLib/*.py  # Type check
```

### Architecture Patterns

#### Component Structure
1. **StateManager** (`state_manager.py`): Centralized thread-safe state management with `AppState` dataclass
2. **ConfigManager** (`config_manager.py`): YAML configuration file I/O
3. **YamlManager** (`yaml_manager.py`): Low-level YAML operations with file-level mutex locking
4. **CleaningService** (`cleaning_service.py`): Pure business logic for plugin cleaning (no Qt dependencies)
5. **GuiController** (`gui_controller.py`): Mediator between GUI and business logic
6. **CleaningWorker** (`cleaning_worker.py`): QThread for background cleaning operations
7. **MainWindow** (`ui/main_window.py`): Composed of multiple mixins for separation of concerns

#### GUI Development Guidelines
- **New GUI functionality**: Create as MixIn classes in `AutoQACLib/ui/mixins/`
- **Dialog components**: Define in `AutoQACLib/ui/dialogs/`
- **MixIn pattern**: Compose MainWindow functionality through multiple focused mixins
- **Separation of concerns**: Each mixin should handle a single responsibility

#### Dependency Injection Pattern
```python
def __init__(self, state: StateManager, config: ConfigManager):
    self.state = state
    self.config = config
```
No global variables or direct imports between layers.

### Testing Strategy

**Test Organization**:
- Tests located in `tests/` directory
- Test files follow `test_*.py` naming pattern
- Test classes follow `Test*` naming pattern

**Markers**:
- `@pytest.mark.unit`: Unit tests (isolated, fast)
- `@pytest.mark.integration`: Integration tests (cross-component)
- `@pytest.mark.gui`: GUI tests (require Qt)
- `@pytest.mark.slow`: Slow tests (deselect with `-m "not slow"`)

**Commands**:
```bash
uv run pytest                    # All tests
uv run pytest -m unit            # Unit tests only
uv run pytest -m integration     # Integration tests only
uv run pytest --cov --cov-report=html  # With coverage
```

**Coverage**: Targets `AutoQACLib/` and `AutoQAC_Interface.py`

### Git Workflow

- Feature branches for new work
- Main branch protected
- Commits should be atomic and well-described
- Test before committing

## Domain Context

### xEdit Integration
- Commands built with `-QAC` flag for Quick Auto Clean
- Supports MO2 integration via `ModOrganizer.exe run` command wrapper
- Optional `-iknowwhatimdoing -allowmakepartial` flags for experimental Partial Forms feature
- Timeout handling (default 300s per plugin)
- Output parsing for ITMs, UDRs, and deleted navmeshes

### Game Identification
| Game                   | Short Code | xEdit Executables          |
| ---------------------- | ---------- | -------------------------- |
| Fallout 3              | FO3        | FO3Edit.exe, FO3Edit64.exe |
| Fallout New Vegas      | FNV        | FNVEdit.exe, FNVEdit64.exe |
| Fallout 4              | FO4        | FO4Edit.exe, FO4Edit64.exe |
| Fallout 4 VR           | FO4VR      | FO4VREdit.exe              |
| Skyrim Special Edition | SSE        | SSEEdit.exe, SSEEdit64.exe |
| Skyrim VR              | SkyrimVR   | TES5VREdit.exe             |

Also supports universal xEdit executables (`xEdit.exe`, `xEdit64.exe`) with automatic game detection.

### Plugin Files
- **ESP**: Elder Scrolls Plugin (mod content)
- **ESM**: Elder Scrolls Master (master file)
- **ESL**: Elder Scrolls Light (lightweight plugin)

## Important Constraints

### Threading Rules (CRITICAL)
**MUST use PySide6 threading exclusively**:
- Use: `QThread`, `QThreadPool`, `QMutex`, `QReadWriteLock`, `QWaitCondition`
- **NEVER use**: Python's `threading`, `asyncio`, or `concurrent.futures`
- All inter-thread communication through Qt signals/slots only
- All shared data access must be synchronized via StateManager
- Resource limit for concurrent subprocesses controlled by `max_concurrent_subprocesses` in AppState

### State Management
- State updates ONLY through StateManager, never direct manipulation
- All mutations use QMutex/QReadWriteLock protection
- Qt signals for state change notifications

### Critical Operational Constraint
**⚠ AutoQAC SHOULD ONLY CLEAN ONE (1) PLUGIN AT A TIME**

If multiple xEdit windows start opening simultaneously, this is a critical bug.

### Python Version
- Requires Python 3.12+, <3.14
- Uses new generic syntax features (`enable_incomplete_feature = ["NewGenericSyntax"]`)

## External Dependencies

### xEdit (External Tool)
- Not bundled with application
- Must be downloaded separately from Nexus Mods
- Must be run at least once before using AutoQAC
- Executables vary by game (SSEEdit, FO4Edit, etc.)

### Mod Organizer 2 (Optional)
- Optional integration for MO2 users
- MO2 must be completely closed during cleaning
- Wraps xEdit commands through MO2's virtual filesystem

### Configuration Files
- `AutoQAC Data/AutoQAC Main.yaml`: Game configurations, plugin skip lists
- `AutoQAC Data/AutoQAC Config.yaml`: User settings, file paths
- `AutoQAC Data/AutoQAC Ignore.yaml`: User-defined plugin ignore lists

### Logging
- Rotating file logs in `logs/` directory
- Not console output (file-based only)
- Configurable retention
