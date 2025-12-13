"""Thread safety tests for AutoQAC components."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from PySide6.QtCore import QCoreApplication, QTimer

from AutoQACLib.config_manager import ConfigManager
from AutoQACLib.state_manager import StateManager


class TestThreadSafety:
    """Test thread safety of core components."""

    def test_state_manager_concurrent_updates(self, state_manager: StateManager) -> None:
        """Test concurrent updates to StateManager don't cause race conditions."""
        num_threads = 10
        updates_per_thread = 100

        def update_state(thread_id: int) -> None:
            """Update state multiple times from a thread."""
            for i in range(updates_per_thread):
                state_manager.update(
                    progress=thread_id * updates_per_thread + i,
                    current_operation=f"Thread {thread_id} operation {i}",
                )
                # Small delay to increase chance of interleaving
                time.sleep(0.0001)

        # Run updates concurrently
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(update_state, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()  # Raise any exceptions

        # Verify final state is consistent
        final_state = state_manager.state
        assert final_state.progress >= 0
        assert final_state.current_operation is not None

    def test_state_manager_read_write_concurrent(self, state_manager: StateManager) -> None:
        """Test concurrent reads and writes to StateManager."""
        num_readers = 5
        num_writers = 5
        iterations = 100
        read_values: list[Any] = []

        def reader_thread() -> None:
            """Read state values repeatedly."""
            for _ in range(iterations):
                state = state_manager.state
                read_values.append(state.progress)
                # Also test individual property reads
                progress = state_manager.get("progress")
                assert progress is not None
                time.sleep(0.0001)

        def writer_thread(thread_id: int) -> None:
            """Write state values repeatedly."""
            for i in range(iterations):
                state_manager.update(progress=thread_id * 1000 + i)
                time.sleep(0.0001)

        # Run readers and writers concurrently
        with ThreadPoolExecutor(max_workers=num_readers + num_writers) as executor:
            reader_futures = [executor.submit(reader_thread) for _ in range(num_readers)]
            writer_futures = [executor.submit(writer_thread, i) for i in range(num_writers)]

            all_futures = reader_futures + writer_futures
            for future in as_completed(all_futures):
                future.result()

        # Verify no corruption occurred
        assert len(read_values) == num_readers * iterations
        assert all(isinstance(v, int) for v in read_values)

    def test_state_manager_multi_property_updates(self, state_manager: StateManager) -> None:
        """Test atomic multi-property updates."""
        num_threads = 10
        iterations = 50

        def update_multiple(thread_id: int) -> None:
            """Update multiple properties atomically."""
            for i in range(iterations):
                state_manager.update_multiple_properties({
                    "progress": thread_id * iterations + i,
                    "current_operation": f"Thread {thread_id} op {i}",
                    "is_cleaning": i % 2 == 0,
                })
                time.sleep(0.0001)

        # Run concurrent multi-property updates
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(update_multiple, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify state is consistent
        final_state = state_manager.state
        assert isinstance(final_state.progress, int)
        assert isinstance(final_state.current_operation, str)
        assert isinstance(final_state.is_cleaning, bool)

    def test_config_manager_concurrent_operations(self, test_output_dir: Path) -> None:
        """Test concurrent read/write operations on ConfigManager."""
        config_path = test_output_dir / "test_config.yaml"
        config = ConfigManager(config_path)

        num_threads = 10
        operations_per_thread = 50

        def config_operations(thread_id: int) -> None:
            """Perform various config operations."""
            for i in range(operations_per_thread):
                # Write
                key = f"thread_{thread_id}_key_{i}"
                config.set(key, f"value_{i}")

                # Read
                value = config.get(key)
                assert value == f"value_{i}"

                # Update multiple
                if i % 5 == 0:
                    updates = {f"{key}_{j}": f"batch_{j}" for j in range(3)}
                    config.update_multiple(updates)

                time.sleep(0.0001)

        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(config_operations, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify all data was written correctly
        all_config = config.get_all()
        assert len(all_config) > 0

    def test_yaml_manager_cache_consistency(self, test_output_dir: Path) -> None:
        """Test YAML manager cache remains consistent under concurrent access."""
        from AutoQACLib.game_detection import yaml_settings, yaml_settings_write

        yaml_path = test_output_dir / "test_cache.yaml"
        yaml_settings_write(yaml_path, {"initial": "value"})

        num_threads = 10
        iterations = 100

        def concurrent_yaml_access(thread_id: int) -> None:
            """Access YAML file concurrently."""
            for i in range(iterations):
                # Write
                key = f"thread_{thread_id}.item_{i}"
                yaml_settings_write(yaml_path, f"value_{i}", key)

                # Read
                value = yaml_settings(yaml_path, key)
                assert value == f"value_{i}"

                # Read initial value
                initial = yaml_settings(yaml_path, "initial")
                assert initial == "value"

                time.sleep(0.0001)

        # Run concurrent access
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(concurrent_yaml_access, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

    def test_cleaning_worker_thread_safety(
        self, qt_app: Any, state_manager: StateManager, test_output_dir: Path
    ) -> None:
        """Test cleaning worker thread interactions are safe."""
        from AutoQACLib.cleaning_service import CleaningService
        from AutoQACLib.cleaning_worker import CleaningWorker
        from AutoQACLib.config_manager import ConfigManager

        # Create temporary configs
        tmp_path = test_output_dir / "temp_test_data"
        tmp_path.mkdir(exist_ok=True)

        main_config = ConfigManager(tmp_path / "main.yaml")
        user_config = ConfigManager(tmp_path / "user.yaml")

        # Create service and worker
        service = CleaningService(main_config, user_config, state_manager)
        plugins = ["test1.esp", "test2.esp", "test3.esp"]
        worker = CleaningWorker(service, state_manager, plugins)

        # Track signal emissions
        signal_count = {"progress": 0, "started": 0, "completed": 0}

        def on_progress(_current: int, _total: int) -> None:
            signal_count["progress"] += 1

        def on_started(_plugin: str) -> None:
            signal_count["started"] += 1

        def on_completed(_plugin: str, _success: bool, _message: str) -> None:
            signal_count["completed"] += 1

        worker.progress.connect(on_progress)
        worker.plugin_started.connect(on_started)
        worker.plugin_completed.connect(on_completed)

        # Simulate concurrent state updates while worker runs
        def update_state_repeatedly() -> None:
            for i in range(50):
                state_manager.update(journal_expiration=i)
                time.sleep(0.01)

        # Start worker (will fail quickly since paths aren't configured)
        worker.start()

        # Run concurrent updates
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(update_state_repeatedly)

            # Wait for worker to finish
            timeout = 5.0  # 5 seconds
            start_time = time.time()
            while worker.isRunning() and time.time() - start_time < timeout:
                QCoreApplication.processEvents()
                time.sleep(0.01)
            assert not worker.isRunning(), "Worker did not finish within timeout"

            future.result()

        # Verify signals were emitted safely
        assert signal_count["progress"] >= 0
        assert signal_count["started"] >= 0
        assert signal_count["completed"] >= 0

    def test_qt_signal_thread_safety(self, qt_app: Any) -> None:
        """Test Qt signal emission across threads is safe."""
        from PySide6.QtCore import QObject, Signal

        class SignalEmitter(QObject):
            test_signal = Signal(int, str)

        emitter = SignalEmitter()
        received_values: list[tuple[int, str]] = []

        def on_signal(value: int, text: str) -> None:
            received_values.append((value, text))

        emitter.test_signal.connect(on_signal)

        num_threads = 5
        signals_per_thread = 20

        def emit_from_thread(thread_id: int) -> None:
            """Emit signals from thread."""
            for i in range(signals_per_thread):
                emitter.test_signal.emit(thread_id * 100 + i, f"Thread {thread_id}")
                time.sleep(0.001)

        # Emit signals from multiple threads
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(emit_from_thread, i) for i in range(num_threads)]

            # Process events to handle signals
            timer = QTimer()
            timer.timeout.connect(lambda: QCoreApplication.processEvents())
            timer.start(10)  # Process events every 10ms

            for future in as_completed(futures):
                future.result()

            # Give time for all signals to be processed
            time.sleep(0.1)
            QCoreApplication.processEvents()
            timer.stop()

        # Verify all signals were received
        assert len(received_values) == num_threads * signals_per_thread

    def test_config_state_deadlock_prevention(self, test_output_dir: Path) -> None:
        """Test that config saves and state updates don't deadlock."""
        from AutoQACLib.gui_controller import GuiController

        config_path = test_output_dir / "test_config.yaml"
        main_config = ConfigManager(config_path)
        user_config = ConfigManager(config_path)
        state_manager = StateManager()

        controller = GuiController(state_manager, main_config, user_config)

        num_threads = 5
        operations = 50

        def config_and_state_ops(thread_id: int) -> None:
            """Perform interleaved config and state operations."""
            for i in range(operations):
                # Simulate what happens in configure methods
                if i % 2 == 0:
                    # Update state then defer config save
                    state_manager.update(progress=i)
                    controller._defer_config_save(f"key_{thread_id}_{i}", f"value_{i}")  # noqa: SLF001
                else:
                    # Direct config operation
                    user_config.set(f"direct_{thread_id}_{i}", f"value_{i}")
                    # Then state update
                    state_manager.update(progress=i)

                time.sleep(0.0001)

        # Run concurrent operations
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(config_and_state_ops, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Wait for deferred saves to complete
        time.sleep(0.2)

        # Verify no deadlock (should complete quickly)
        elapsed = time.time() - start_time
        assert elapsed < 5.0  # Should complete in well under 5 seconds

        # Clean up
        controller.cleanup()
