"""Tests for cleaning worker."""

from typing import Any
from unittest.mock import Mock, patch

from PySide6.QtCore import QThread

from AutoQACLib.cleaning_worker import CleaningWorker


class TestCleaningWorker:
    """Test the CleaningWorker class."""

    def test_initialization(self) -> None:
        """Test CleaningWorker initialization."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp", "plugin2.esp"]

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        assert worker.service == mock_service
        assert worker.state == mock_state
        assert worker.plugins == plugins
        assert worker._should_stop is False  # noqa: SLF001
        assert isinstance(worker, QThread)

    @patch.object(CleaningWorker, "progress")
    @patch.object(CleaningWorker, "plugin_started")
    @patch.object(CleaningWorker, "plugin_completed")
    @patch.object(CleaningWorker, "error")
    def test_run_successful_cleaning(
        self,
        mock_error: Mock,
        mock_plugin_completed: Mock,
        mock_plugin_started: Mock,
        mock_progress: Mock,
    ) -> None:
        """Test successful cleaning process."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp", "plugin2.esp"]

        # Mock state properties
        mock_state_snapshot: Mock = Mock()
        mock_state_snapshot.max_concurrent_subprocesses = 2
        mock_state.state = mock_state_snapshot

        # Mock validation success
        mock_service.validate_environment.return_value = (True, "Valid environment")

        # Mock clean result
        mock_result: Mock = Mock()
        mock_result.status = "cleaned"
        mock_result.success = True
        mock_result.message = "Successfully cleaned"
        mock_result.duration = 1.5
        mock_service.clean_plugin.return_value = mock_result

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        # Run the worker
        worker.run()

        # Verify service was called correctly
        mock_service.validate_environment.assert_called_once()
        mock_service.set_progress_callback.assert_called_once()
        mock_service.set_log_callback.assert_called_once()
        assert mock_service.clean_plugin.call_count == 2

        # Verify state updates
        mock_state.update.assert_called()
        mock_state.add_result.assert_called()

        # Verify signals were emitted (check emit method was called)
        assert mock_progress.emit.call_count == 2
        assert mock_plugin_started.emit.call_count == 2
        assert mock_plugin_completed.emit.call_count == 2

    @patch.object(CleaningWorker, "error")
    def test_run_validation_failure(self, mock_error: Mock) -> None:
        """Test cleaning process when validation fails."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp"]

        # Mock validation failure
        mock_service.validate_environment.return_value = (False, "Invalid environment")

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        # Run the worker
        worker.run()

        # Verify error signal was emitted
        mock_error.emit.assert_called_once_with("Invalid environment")

    @patch.object(CleaningWorker, "progress")
    @patch.object(CleaningWorker, "plugin_started")
    @patch.object(CleaningWorker, "plugin_completed")
    @patch.object(CleaningWorker, "error")
    def test_run_plugin_cleaning_failure(
        self,
        mock_error: Mock,
        mock_plugin_completed: Mock,
        mock_plugin_started: Mock,
        mock_progress: Mock,  # noqa: ARG002
    ) -> None:
        """Test cleaning process when a plugin fails to clean."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp"]

        # Mock state properties
        mock_state_snapshot: Mock = Mock()
        mock_state_snapshot.max_concurrent_subprocesses = 2
        mock_state.state = mock_state_snapshot

        # Mock validation success
        mock_service.validate_environment.return_value = (True, "Valid environment")

        # Mock clean failure
        mock_service.clean_plugin.side_effect = RuntimeError("Cleaning failed")

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        # Run the worker
        worker.run()

        # Verify error handling - check that emit was called
        assert mock_plugin_completed.emit.called
        # Get the call arguments
        call_args = mock_plugin_completed.emit.call_args[0]
        assert call_args[0] == "plugin1.esp"  # plugin name
        assert call_args[1] is False  # success = False
        assert "Error: Cleaning failed" in call_args[2]  # error message

    @patch.object(CleaningWorker, "progress")
    @patch.object(CleaningWorker, "plugin_started")
    @patch.object(CleaningWorker, "plugin_completed")
    @patch.object(CleaningWorker, "error")
    def test_run_with_stop_request(
        self, mock_error: Mock, mock_plugin_completed: Mock, mock_plugin_started: Mock, mock_progress: Mock
    ) -> None:
        """Test cleaning process when stop is requested."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp", "plugin2.esp"]

        # Mock validation success
        mock_service.validate_environment.return_value = (True, "Valid environment")

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        # Set stop flag before running
        worker._should_stop = True  # noqa: SLF001

        # Run the worker
        worker.run()

        # Verify no cleaning was performed
        mock_service.clean_plugin.assert_not_called()

    @patch.object(CleaningWorker, "progress")
    @patch.object(CleaningWorker, "plugin_started")
    @patch.object(CleaningWorker, "plugin_completed")
    @patch.object(CleaningWorker, "error")
    def test_run_with_interruption_request(
        self,
        mock_error: Mock,
        mock_plugin_completed: Mock,
        mock_plugin_started: Mock,
        mock_progress: Mock,  # noqa: ARG002
    ) -> None:
        """Test cleaning process when interruption is requested."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp", "plugin2.esp"]

        # Mock validation success
        mock_service.validate_environment.return_value = (True, "Valid environment")

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        # Mock interruption request
        with patch.object(worker, "isInterruptionRequested", return_value=True):
            worker.run()

        # Verify no cleaning was performed
        mock_service.clean_plugin.assert_not_called()

    @patch.object(CleaningWorker, "error")
    def test_run_with_exception(self, mock_error: Mock) -> None:
        """Test cleaning process when an exception occurs."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp"]

        # Mock state properties
        mock_state_snapshot: Mock = Mock()
        mock_state_snapshot.max_concurrent_subprocesses = 2
        mock_state.state = mock_state_snapshot

        # Mock validation success but service raises exception
        mock_service.validate_environment.return_value = (True, "Valid environment")
        # Only raise on first call, allow the finally block to succeed
        mock_state.update.side_effect = [RuntimeError("Service error"), None]

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        # Run the worker
        worker.run()

        # Verify error signal was emitted
        mock_error.emit.assert_called_once_with("Service error")

    @patch.object(CleaningWorker, "error")
    def test_run_with_keyboard_interrupt(self, mock_error: Mock) -> None:
        """Test cleaning process when interrupted by keyboard."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp"]

        # Mock state properties
        mock_state_snapshot: Mock = Mock()
        mock_state_snapshot.max_concurrent_subprocesses = 2
        mock_state.state = mock_state_snapshot

        # Mock validation success but raise KeyboardInterrupt
        mock_service.validate_environment.return_value = (True, "Valid environment")
        # Only raise on first call, allow the finally block to succeed
        mock_state.update.side_effect = [KeyboardInterrupt(), None]

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        # Run the worker
        worker.run()

        # Verify error signal was emitted
        mock_error.emit.assert_called_once_with("Cleaning process was interrupted by user")

    @patch.object(CleaningWorker, "error")
    def test_run_with_type_error(self, mock_error: Mock) -> None:
        """Test cleaning process when TypeError occurs."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp"]

        # Mock state properties
        mock_state_snapshot: Mock = Mock()
        mock_state_snapshot.max_concurrent_subprocesses = 2
        mock_state.state = mock_state_snapshot

        # Mock validation success but raise TypeError
        mock_service.validate_environment.return_value = (True, "Valid environment")
        # Only raise on first call, allow the finally block to succeed
        mock_state.update.side_effect = [TypeError("Type error"), None]

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        # Run the worker
        worker.run()

        # Verify error signal was emitted
        mock_error.emit.assert_called_once_with("Unexpected error: Type error")

    @patch.object(CleaningWorker, "progress")
    @patch.object(CleaningWorker, "plugin_started")
    @patch.object(CleaningWorker, "plugin_completed")
    @patch.object(CleaningWorker, "error")
    def test_run_final_state_reset(
        self, mock_error: Mock, mock_plugin_completed: Mock, mock_plugin_started: Mock, mock_progress: Mock
    ) -> None:
        """Test that cleaning state is reset in finally block."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp"]

        # Mock state properties
        mock_state_snapshot: Mock = Mock()
        mock_state_snapshot.max_concurrent_subprocesses = 2
        mock_state.state = mock_state_snapshot

        # Mock validation success
        mock_service.validate_environment.return_value = (True, "Valid environment")

        # Mock clean result
        mock_result: Mock = Mock()
        mock_result.status = "cleaned"
        mock_result.success = True
        mock_result.message = "Successfully cleaned"
        mock_result.duration = 1.5
        mock_service.clean_plugin.return_value = mock_result

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        # Run the worker
        worker.run()

        # Verify final state reset
        mock_state.update.assert_any_call(is_cleaning=False, current_plugin=None)

    def test_stop_method(self) -> None:
        """Test the stop method."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp"]

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        # Mock thread state
        with patch.object(worker, "isRunning", return_value=True) and patch.object(worker, "wait", return_value=True):
            worker.stop()

        # Verify stop flag was set
        assert worker._should_stop is True  # noqa: SLF001

    def test_stop_method_with_termination(self) -> None:
        """Test the stop method when graceful stop fails."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp"]

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        # Mock thread state - first wait returns False (graceful stop failed)
        with patch.object(worker, "isRunning", return_value=True), patch.object(worker, "wait") as mock_wait:
            mock_wait.side_effect = [False, True]  # First wait fails, second succeeds
            with patch.object(worker, "terminate"):
                worker.stop()

        # Verify stop flag was set
        assert worker._should_stop is True  # noqa: SLF001

    @patch.object(CleaningWorker, "plugin_progress")
    def test_on_cleaning_progress(self, mock_plugin_progress: Mock) -> None:
        """Test the _on_cleaning_progress callback."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp"]

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        progress_info: dict[str, Any] = {"current": 5, "total": 10, "message": "Processing..."}
        worker._on_cleaning_progress(progress_info)  # noqa: SLF001

        # Verify signal was emitted
        mock_plugin_progress.emit.assert_called_once_with(progress_info)

    @patch.object(CleaningWorker, "log_output")
    def test_on_log_output(self, mock_log_output: Mock) -> None:
        """Test the _on_log_output callback."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp"]

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        log_line: str = "Processing plugin..."
        worker._on_log_output(log_line)  # noqa: SLF001

        # Verify signal was emitted
        mock_log_output.emit.assert_called_once_with(log_line)

    def test_get_summary(self) -> None:
        """Test the get_summary method."""
        mock_service: Mock = Mock()
        mock_state: Mock = Mock()
        plugins: list[str] = ["plugin1.esp"]

        # Mock state with cleaning stats
        mock_state.state.cleaning_stats = {"cleaned": 5, "failed": 2, "skipped": 1, "total": 8}

        worker: CleaningWorker = CleaningWorker(mock_service, mock_state, plugins)

        summary: str = worker.get_summary()

        # Verify summary format
        assert "Cleaning complete:" in summary
        assert "Cleaned: 5" in summary
        assert "Failed: 2" in summary
        assert "Skipped: 1" in summary
        assert "Total: 8" in summary
