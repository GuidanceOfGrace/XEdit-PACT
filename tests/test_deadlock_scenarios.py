"""Deadlock detection and prevention tests for AutoQAC."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication, QMutex, QMutexLocker

from AutoQACLib.config_manager import ConfigManager
from AutoQACLib.gui_controller import GuiController
from AutoQACLib.state_manager import StateManager
from AutoQACLib.yaml_manager import _yaml_manager


class DeadlockDetector:
    """Helper class to detect potential deadlocks."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.detected_deadlock = False
        self.error_message = ""

    def run_with_timeout(self, func: Callable[[], Any]) -> bool:
        """Run function with timeout to detect deadlocks."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func)
            try:
                future.result(timeout=self.timeout)
                return True
            except TimeoutError:
                self.detected_deadlock = True
                self.error_message = f"Potential deadlock detected - operation didn't complete in {self.timeout}s"
                return False


class TestDeadlockScenarios:
    """Test various deadlock scenarios and verify they're prevented."""

    def test_state_config_circular_dependency(self, test_output_dir: Path) -> None:
        """Test that state updates and config saves don't create circular wait."""
        config_path = test_output_dir / "test_config.yaml"
        main_config = ConfigManager(config_path)
        user_config = ConfigManager(config_path)
        state = StateManager()
        controller = GuiController(state, main_config, user_config)

        detector = DeadlockDetector(timeout=3.0)

        def concurrent_operations() -> None:
            """Simulate operations that could deadlock."""

            # Thread 1: Update state then save config
            def thread1() -> None:
                for i in range(100):
                    state.update(progress=i)
                    controller._defer_config_save("key1", f"value_{i}")

            # Thread 2: Save config then update state
            def thread2() -> None:
                for i in range(100):
                    user_config.set("key2", f"value_{i}")
                    state.update(current_operation=f"op_{i}")

            # Thread 3: Rapid multi-updates
            def thread3() -> None:
                for i in range(100):
                    state.update_multiple_properties({
                        "progress": i,
                        "current_plugin": f"plugin_{i}",
                    })
                    controller._defer_config_save("key3", f"value_{i}")

            # Run all threads concurrently
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(thread1),
                    executor.submit(thread2),
                    executor.submit(thread3),
                ]
                for future in futures:
                    future.result()

        # Should complete without deadlock
        assert detector.run_with_timeout(concurrent_operations)
        assert not detector.detected_deadlock

        # Clean up
        controller.cleanup()

    def test_yaml_manager_nested_locks(self, test_output_dir: Path) -> None:
        """Test that nested YAML operations don't deadlock."""
        from AutoQACLib.game_detection import yaml_settings, yaml_settings_write

        yaml_path1 = test_output_dir / "file1.yaml"
        yaml_path2 = test_output_dir / "file2.yaml"

        # Initialize files
        yaml_settings_write(yaml_path1, {"initial": "value1"})
        yaml_settings_write(yaml_path2, {"initial": "value2"})

        detector = DeadlockDetector(timeout=3.0)

        def nested_operations() -> None:
            """Perform nested YAML operations that could deadlock."""

            def thread1() -> None:
                for i in range(50):
                    # Get file1, then file2
                    val1 = yaml_settings(yaml_path1, "initial")
                    yaml_settings_write(yaml_path2, f"from1_{i}", f"thread1_key_{i}")
                    time.sleep(0.001)

            def thread2() -> None:
                for i in range(50):
                    # Get file2, then file1 (opposite order)
                    val2 = yaml_settings(yaml_path2, "initial")
                    yaml_settings_write(yaml_path1, f"from2_{i}", f"thread2_key_{i}")
                    time.sleep(0.001)

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(thread1),
                    executor.submit(thread2),
                ]
                for future in futures:
                    future.result()

        # Should complete without deadlock
        assert detector.run_with_timeout(nested_operations)
        assert not detector.detected_deadlock

    def test_mutex_timeout_prevents_deadlock(self) -> None:
        """Test that mutex timeouts prevent permanent deadlocks."""
        # Test our YAML manager's tryLock timeout
        yaml_path = "test_timeout.yaml"

        # Simulate a stuck lock by holding it in another thread
        stuck_lock = _yaml_manager._get_file_mutex(yaml_path)

        def hold_lock() -> None:
            stuck_lock.lock()
            time.sleep(10)  # Hold for 10 seconds
            stuck_lock.unlock()

        # Start thread holding the lock
        holder = threading.Thread(target=hold_lock)
        holder.start()

        # Give it time to acquire the lock
        time.sleep(0.1)

        # Try to get value - should timeout and raise exception instead of deadlocking
        start_time = time.time()
        from AutoQACLib.yaml_manager import YAMLLockTimeoutError

        with pytest.raises(YAMLLockTimeoutError):
            _yaml_manager.get_value(yaml_path, "test_key")
        elapsed = time.time() - start_time

        # Should timeout in ~5 seconds (not deadlock forever)
        assert elapsed < 6.0

        # Clean up
        stuck_lock.unlock()  # Force unlock
        holder.join(timeout=1.0)

    def test_qt_signal_deadlock_prevention(self, qt_app: Any) -> None:
        """Test that Qt signal emission doesn't cause deadlocks."""
        from PySide6.QtCore import QObject, Signal

        class CircularEmitter(QObject):
            signal_a = Signal()
            signal_b = Signal()

            def __init__(self):
                super().__init__()
                self.mutex = QMutex()
                self.count_a = 0
                self.count_b = 0

                # Create potential circular dependency
                self.signal_a.connect(self.on_signal_a)
                self.signal_b.connect(self.on_signal_b)

            def on_signal_a(self) -> None:
                with QMutexLocker(self.mutex):
                    self.count_a += 1
                    if self.count_a < 10:
                        self.signal_b.emit()

            def on_signal_b(self) -> None:
                with QMutexLocker(self.mutex):
                    self.count_b += 1
                    if self.count_b < 10:
                        self.signal_a.emit()

        emitter = CircularEmitter()

        detector = DeadlockDetector(timeout=2.0)

        def emit_signals() -> None:
            # Start the circular emission
            emitter.signal_a.emit()

            # Process events
            for _ in range(100):
                QCoreApplication.processEvents()
                time.sleep(0.01)

        # Should complete without deadlock
        assert detector.run_with_timeout(emit_signals)
        assert not detector.detected_deadlock

    def test_cleaning_worker_state_deadlock(self, qt_app: Any) -> None:
        """Test that cleaning worker and state updates don't deadlock."""
        from AutoQACLib.cleaning_service import CleaningService
        from AutoQACLib.cleaning_worker import CleaningWorker

        state = StateManager()

        # Mock service
        mock_service = MagicMock(spec=CleaningService)
        mock_service.validate_environment.return_value = (True, "OK")
        mock_service.clean_plugin.side_effect = lambda p: MagicMock(
            success=True, message="OK", status="cleaned", duration=0.1
        )

        worker = CleaningWorker(mock_service, state, ["test1.esp", "test2.esp"])

        detector = DeadlockDetector(timeout=3.0)

        def concurrent_state_updates() -> None:
            """Update state while worker is running."""
            # Start worker
            worker.start()

            # Concurrent state updates
            def update_state() -> None:
                for i in range(100):
                    state.update(journal_expiration=i)
                    state.get("is_cleaning")
                    time.sleep(0.001)

            # Run updates in parallel with worker
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(update_state)

                # Wait for worker
                worker.wait(2000)

                future.result()

        # Should complete without deadlock
        assert detector.run_with_timeout(concurrent_state_updates)
        assert not detector.detected_deadlock

    def test_deferred_save_timer_deadlock(self, test_output_dir: Path) -> None:
        """Test that deferred save timer doesn't create deadlocks."""
        config_path = test_output_dir / "test_config.yaml"
        main_config = ConfigManager(config_path)
        user_config = ConfigManager(config_path)
        state = StateManager()
        controller = GuiController(state, main_config, user_config)

        detector = DeadlockDetector(timeout=3.0)

        def rapid_operations() -> None:
            """Rapidly trigger deferred saves from multiple threads."""

            def thread_ops(thread_id: int) -> None:
                for i in range(100):
                    # Trigger state update
                    state.update(progress=i * thread_id)

                    # Trigger deferred save
                    controller._defer_config_save(f"key_{thread_id}", f"value_{i}")

                    # Sometimes force process pending saves
                    if i % 10 == 0:
                        controller._process_pending_config_saves()

                    time.sleep(0.0001)

            # Run from multiple threads
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(thread_ops, i) for i in range(5)]
                for future in futures:
                    future.result()

            # Final cleanup
            controller._process_pending_config_saves()

        # Should complete without deadlock
        assert detector.run_with_timeout(rapid_operations)
        assert not detector.detected_deadlock

        # Clean up
        controller.cleanup()

    def test_lock_ordering_consistency(self) -> None:
        """Test that lock ordering is consistent to prevent deadlocks."""
        # Create multiple mutexes
        mutex_a = QMutex()
        mutex_b = QMutex()
        mutex_c = QMutex()

        shared_counter = {"value": 0}

        detector = DeadlockDetector(timeout=2.0)

        def consistent_ordering() -> None:
            """Always acquire locks in the same order."""

            def worker() -> None:
                for _ in range(100):
                    # Always acquire in order A, B, C
                    with QMutexLocker(mutex_a):
                        with QMutexLocker(mutex_b):
                            with QMutexLocker(mutex_c):
                                shared_counter["value"] += 1
                    time.sleep(0.0001)

            # Run multiple workers
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(worker) for _ in range(4)]
                for future in futures:
                    future.result()

        # Should complete without deadlock
        assert detector.run_with_timeout(consistent_ordering)
        assert not detector.detected_deadlock
        assert shared_counter["value"] == 400  # 4 workers * 100 iterations

    def test_gui_controller_cleanup_deadlock(self, test_output_dir: Path) -> None:
        """Test that cleanup operations don't deadlock."""
        config_path = test_output_dir / "test_config.yaml"
        main_config = ConfigManager(config_path)
        user_config = ConfigManager(config_path)
        state = StateManager()
        controller = GuiController(state, main_config, user_config)

        detector = DeadlockDetector(timeout=3.0)

        def cleanup_during_operations() -> None:
            """Test cleanup while operations are in progress."""
            # Start some operations
            for i in range(10):
                state.update(progress=i)
                controller._defer_config_save(f"key_{i}", f"value_{i}")

            # Cleanup from multiple threads
            def cleanup_thread() -> None:
                controller.cleanup()

            def operations_thread() -> None:
                for i in range(50):
                    try:
                        state.update(progress=i)
                        controller._defer_config_save(f"key2_{i}", f"value_{i}")
                    except Exception:
                        pass  # Might fail during cleanup
                    time.sleep(0.001)

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(cleanup_thread),
                    executor.submit(operations_thread),
                ]
                for future in futures:
                    try:
                        future.result()
                    except Exception:
                        pass  # Expected during cleanup

        # Should complete without deadlock
        assert detector.run_with_timeout(cleanup_during_operations)
        assert not detector.detected_deadlock
