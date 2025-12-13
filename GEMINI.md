# AutoQAC (Auto Quick Auto Clean)

**Project Context:**
AutoQAC is a tool for automating the cleaning of Bethesda game plugins (ESP/ESM/ESL) using xEdit's Quick Auto Clean functionality. It is currently in a transitional phase, maintaining a stable Python/Qt implementation while actively migrating to a modern Rust/Slint architecture.

## 1. Project Structure & Implementations

The project contains two distinct implementations of the same tool:

### A. Python/Qt (Stable/Legacy)
*   **Root Directory:** `./`
*   **Entry Point:** `AutoQAC_Interface.py`
*   **Core Library:** `AutoQACLib/`
*   **UI Framework:** PySide6 (Qt 6)
*   **Status:** Feature-complete, stable.

### B. Rust/Slint (Modern/Migration)
*   **Root Directory:** `./autoqac-rust/`
*   **Entry Point:** `src/main.rs`
*   **UI Framework:** Slint (Fluent Design)
*   **Status:** Active development, nearing feature parity.
*   **Key features:** Async (Tokio), Thread-safe state management, Native performance.

## 2. Build & Run Instructions

### Python Version
Dependency management uses `uv` (or standard pip).
```bash
# Install dependencies
uv sync --extra dev

# Run Application
uv run python AutoQAC_Interface.py
```

### Rust Version
Standard Cargo workflow.
```bash
cd autoqac-rust

# Run in Release mode (recommended for UI performance)
cargo run --release

# Run in Debug mode
cargo run
```

## 3. Testing Standards (CRITICAL)

**Strict adherence to testing protocols is MANDATORY.**
Refer to `.cursor/rules/testing-comprehensive.mdc` for detailed rules.

### General Rules
*   **Coverage:** Minimum **90%** for Unit Tests, **80%** for Integration.
*   **Critical Paths:** 100% coverage required for thread safety, I/O, and error handling.
*   **Pattern:** Always use **Arrange-Act-Assert**.
*   **Never** ignore failing tests. Fix the underlying issue.

### Python Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=AutoQACLib --cov=AutoQAC_Interface
```

### Rust Testing
```bash
cd autoqac-rust

# Run all tests
cargo test

# Run specific test
cargo test test_state_manager
```

## 4. Key Configuration Files

Configuration is stored in YAML files within the `AutoQAC Data/` directory (shared structure).

*   `AutoQAC Main.yaml`: Game definitions, xEdit executable names, and skip lists.
*   `AutoQAC Config.yaml`: User-specific settings (paths, timeouts).
*   `AutoQAC Ignore.yaml`: User-defined plugin ignore lists.

## 5. Development Guidelines

*   **Migration Focus:** When working on `autoqac-rust`, ensure feature parity with the Python version. Refer to `docs/rust-migration-plan.md`.
*   **Thread Safety:**
    *   **Python:** Uses `QThread` and Signals. Ensure GUI updates only happen on the main thread.
    *   **Rust:** Uses `Tokio` runtime. GUI updates **MUST** be marshaled via `EventLoopBridge` to the Slint event loop.
*   **Style:**
    *   Python: Follow `ruff` configuration in `pyproject.toml`.
    *   Rust: Standard `rustfmt` and `clippy`.

## 6. Directory Map

*   `AutoQACLib/`: Python backend logic.
*   `AutoQAC_Interface.py`: Python GUI entry point.
*   `AutoQAC Data/`: Runtime configuration and assets.
*   `tests/`: Python test suite.
