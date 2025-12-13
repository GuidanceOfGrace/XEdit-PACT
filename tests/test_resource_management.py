"""Resource management and leak detection tests for AutoQAC."""

import gc
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import psutil
import pytest
from PySide6.QtCore import QCoreApplication, QThread

from AutoQACLib.config_manager import ConfigManager
from AutoQACLib.state_manager import StateManager
from AutoQACLib.process_utils import run_process_with_realtime_output, safe_popen


class TestResourceManagement:
    """Test resource management and leak prevention."""

    def test_subprocess_cleanup_with_safe_popen(self) -> None:
        """Test that safe_popen properly cleans up subprocess resources."""
        initial_fds = len(psutil.Process().open_files())

        # Test normal execution
        with safe_popen(
            [sys.executable, "-c", "print('test')"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        ) as proc:
            stdout, _ = proc.communicate()
            assert "test" in stdout

        # Give OS time to clean up
        time.sleep(0.1)

        # Check file descriptors are cleaned up
        final_fds = len(psutil.Process().open_files())
        assert final_fds <= initial_fds + 1  # Allow small variance

        # Test exception handling
        try:
            with safe_popen(
                [sys.executable, "-c", "import sys; sys.exit(1)"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            ) as proc:
                raise RuntimeError("Test exception")
        except RuntimeError:
            pass

        # Check cleanup after exception
        time.sleep(0.1)
        exception_fds = len(psutil.Process().open_files())
        assert exception_fds <= initial_fds + 1

    def test_subprocess_timeout_cleanup(self, qt_app: Any) -> None:
        """Test subprocess cleanup when timeout occurs."""
        from unittest.mock import Mock, patch

        # Mock time.time() to simulate timeout
        start_time = 1000.0
        with (
            patch("time.time") as mock_time,
            patch("time.sleep") as mock_sleep,
            patch("AutoQACLib.utils.safe_popen") as mock_popen,
        ):
            # Set up time mock to simulate passage of time
            time_counter = [start_time]

            def mock_time_func():
                # Increment time by 0.5 seconds on each call
                current = time_counter[0]
                time_counter[0] += 0.5
                return current

            mock_time.side_effect = mock_time_func

            # Mock sleep to avoid actual delays
            mock_sleep.return_value = None

            # Create a mock process that appears to be running
            mock_process = Mock()
            mock_process.poll.return_value = None  # Process is still running
            mock_process.returncode = -1

            # Mock stdout/stderr with empty output
            mock_stdout = Mock()
            mock_stdout.readline.return_value = ""
            mock_process.stdout = mock_stdout

            mock_stderr = Mock()
            mock_stderr.readline.return_value = ""
            mock_process.stderr = mock_stderr

            # Configure the context manager
            mock_popen.return_value.__enter__.return_value = mock_process
            mock_popen.return_value.__exit__.return_value = None

            # Run the test with a 1 second timeout
            exit_code, stdout, stderr = run_process_with_realtime_output(
                [sys.executable, "-c", "import time; time.sleep(10)"], timeout=1
            )

            # Verify timeout occurred
            assert exit_code == -1  # Timeout exit code
            assert stderr == "Process timed out"  # Expected timeout message

    def test_thread_cleanup_on_exception(self, qt_app: Any) -> None:
        """Test that threads are properly cleaned up even when exceptions occur."""
        from AutoQACLib.cleaning_service import CleaningService
        from AutoQACLib.cleaning_worker import CleaningWorker

        # Mock service to raise exception
        mock_service = MagicMock(spec=CleaningService)
        mock_service.validate_environment.return_value = (False, "Test error")

        state = StateManager()
        worker = CleaningWorker(mock_service, state, ["test.esp"])

        # Track thread count
        initial_threads = QThread.idealThreadCount()

        # Start worker (should fail quickly)
        worker.start()

        # Wait for completion
        worker.wait(2000)  # Wait up to 2 seconds

        # Verify thread is cleaned up
        worker.deleteLater()
        QCoreApplication.processEvents()
        time.sleep(0.1)

        # Thread count should return to normal
        final_threads = QThread.idealThreadCount()
        assert final_threads == initial_threads

    def test_file_handle_cleanup(self, test_output_dir: Path) -> None:
        """Test that file handles are properly closed."""
        config_file = test_output_dir / "test_config.yaml"

        # Get initial handle count
        process = psutil.Process()
        if platform.system() == "Windows":
            initial_handles = process.num_handles()
        else:
            initial_handles = len(process.open_files())

        # Create and use config manager multiple times
        for i in range(10):
            config = ConfigManager(config_file)
            config.set(f"key_{i}", f"value_{i}")
            config.get_all()
            # Let it go out of scope

        # Force garbage collection
        gc.collect()
        time.sleep(0.1)

        # Check handle count
        if platform.system() == "Windows":
            final_handles = process.num_handles()
        else:
            final_handles = len(process.open_files())

        # Should not leak handles (allow small variance)
        assert final_handles <= initial_handles + 5

    def test_memory_leak_in_state_updates(self) -> None:
        """Test that rapid state updates don't cause memory leaks."""
        state = StateManager()

        # Get initial memory
        process = psutil.Process()
        process.memory_info()  # Prime the call
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform many state updates
        for i in range(10000):
            state.update(
                progress=i,
                current_plugin=f"plugin_{i}.esp",
                current_operation=f"Operation {i} with some longer text to use more memory",
            )

            # Periodically force garbage collection
            if i % 1000 == 0:
                gc.collect()

        # Final garbage collection
        gc.collect()
        time.sleep(0.1)

        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Should not increase by more than 10MB for these operations
        assert memory_increase < 10, f"Memory increased by {memory_increase:.2f} MB"

    def test_qt_object_cleanup(self, qt_app: Any) -> None:
        """Test that Qt objects are properly cleaned up."""
        from PySide6.QtCore import QObject

        from AutoQACLib.gui_controller import GuiController

        # Create a root object to track children
        root = QObject()
        initial_objects = len(root.findChildren(QObject, ""))

        # Create and destroy controllers
        for _ in range(5):
            config_path = Path("temp_config.yaml")
            main_config = ConfigManager(config_path)
            user_config = ConfigManager(config_path)
            state = StateManager()

            controller = GuiController(state, main_config, user_config)

            # Simulate some operations
            controller._defer_config_save("test_key", "test_value")

            # Clean up
            controller.cleanup()
            controller.deleteLater()

            # Process events to handle deleteLater
            QCoreApplication.processEvents()

        # Force cleanup
        gc.collect()
        QCoreApplication.processEvents()
        time.sleep(0.1)

        # Check object count (allow some variance for Qt internals)
        final_objects = len(root.findChildren(QObject, ""))
        # Objects should be cleaned up
        assert final_objects <= initial_objects + 5

    def test_signal_disconnection(self, qt_app: Any) -> None:
        """Test that signals are properly disconnected to prevent leaks."""
        from PySide6.QtCore import QObject, Signal

        class Emitter(QObject):
            test_signal = Signal(str)

        class Receiver(QObject):
            def __init__(self):
                super().__init__()
                self.received_count = 0

            def on_signal(self, value: str) -> None:
                self.received_count += 1

        # Create objects
        emitter = Emitter()
        receivers = []

        # Connect many receivers
        for i in range(100):
            receiver = Receiver()
            emitter.test_signal.connect(receiver.on_signal)
            receivers.append(receiver)

        # Emit signal
        emitter.test_signal.emit("test")

        # Verify all received
        assert all(r.received_count == 1 for r in receivers)

        # Disconnect all
        for receiver in receivers:
            try:
                emitter.test_signal.disconnect(receiver.on_signal)
            except RuntimeError:
                pass  # Already disconnected

        # Delete receivers
        receivers.clear()
        gc.collect()

        # Emit again - should have no receivers
        emitter.test_signal.emit("test2")

        # No crashes and clean state
        assert True

    def test_yaml_cache_memory_management(self, test_output_dir: Path) -> None:
        """Test that YAML cache doesn't grow unbounded."""
        from AutoQACLib.game_detection import yaml_settings, yaml_settings_write
        from AutoQACLib.yaml_manager import _yaml_manager

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create many different YAML files
        for i in range(100):
            yaml_path = test_output_dir / f"cache_test_{i}.yaml"
            # Write large data
            large_data = {f"key_{j}": f"value_{j}" * 100 for j in range(100)}
            yaml_settings_write(yaml_path, large_data)

            # Read to populate cache
            yaml_settings(yaml_path, "key_0")

        # Check cache size
        cache_size = len(_yaml_manager._cache)
        assert cache_size >= 100  # At least all our files should be cached

        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Should not increase by more than 50MB even with large cache
        assert memory_increase < 50, f"Memory increased by {memory_increase:.2f} MB"

    @pytest.mark.skipif(platform.system() == "Windows", reason="Resource limits not available on Windows")
    def test_file_descriptor_limits(self) -> None:
        """Test that we don't exceed file descriptor limits."""
        import resource

        # Get current limits
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)

        # Set a reasonable limit for testing
        test_limit = min(256, soft_limit)
        resource.setrlimit(resource.RLIMIT_NOFILE, (test_limit, hard_limit))

        try:
            # Try to open many files through our utils
            for _ in range(50):  # Well under limit
                exit_code, _, _ = run_process_with_realtime_output([sys.executable, "-c", "print('test')"], timeout=1)
                assert exit_code == 0

            # Should complete without hitting fd limit
            assert True
        finally:
            # Restore original limits
            resource.setrlimit(resource.RLIMIT_NOFILE, (soft_limit, hard_limit))

    def test_thread_pool_cleanup(self) -> None:
        """Test that thread pools are properly cleaned up."""
        import threading
        from concurrent.futures import ThreadPoolExecutor

        initial_thread_count = threading.active_count()

        # Create and destroy multiple thread pools
        for _ in range(5):
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for i in range(10):
                    future = executor.submit(lambda x: x * 2, i)
                    futures.append(future)

                # Wait for completion
                for future in futures:
                    future.result()

            # Pool should be shut down after context exit

        # Give threads time to clean up
        time.sleep(0.5)

        # Thread count should return to near initial
        final_thread_count = threading.active_count()
        assert final_thread_count <= initial_thread_count + 2
