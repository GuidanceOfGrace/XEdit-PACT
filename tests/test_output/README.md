# Test Output Directory

This directory is used to store temporary files and output generated during test execution.

## Purpose

- Contains test artifacts such as temporary configuration files, log files, and other test outputs
- Keeps test-related files organized and separate from the main project structure
- Provides a clean, dedicated space for test file operations

## Git Configuration

- The contents of this directory are ignored by git (see `.gitignore`)
- Only the `.gitkeep` file is tracked to ensure the directory structure is preserved
- Test output files are automatically cleaned up after test completion

## Usage

Tests can use the following fixtures to work with this directory:

- `test_output_dir`: Returns the Path to this directory
- `temp_test_file`: Creates a temporary file with automatic cleanup
- `temp_test_config_file`: Creates a temporary YAML config file
- `test_file_factory`: Factory function for creating multiple test files with cleanup

## Cleanup

Test files are automatically cleaned up after each test run through pytest fixtures.
If manual cleanup is needed, you can safely delete all files in this directory except `.gitkeep`.
