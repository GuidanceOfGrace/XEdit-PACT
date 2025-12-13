"""Process execution and subprocess management utilities."""

from __future__ import annotations

import contextlib
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any

import psutil
from PySide6.QtCore import QMutex, QMutexLocker, QThread, QWaitCondition

from AutoQACLib.logging_config import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from logging import Logger
    from pathlib import Path
    from subprocess import CompletedProcess

logger: Logger = get_logger(__name__)

# Subprocess resource management
_subprocess_semaphore = QMutex()
_subprocess_condition = QWaitCondition()
_active_subprocesses = 0
_max_concurrent_subprocesses = 3  # Default limit


def set_max_concurrent_subprocesses(limit: int) -> None:
    """
    Set the maximum number of concurrent subprocesses.

    Args:
        limit: Maximum number of subprocesses allowed to run concurrently.
               Must be greater than 0.
    """
    global _max_concurrent_subprocesses  # noqa: PLW0603
    if limit <= 0:
        raise ValueError("Subprocess limit must be greater than 0")
    with QMutexLocker(_subprocess_semaphore):
        _max_concurrent_subprocesses = limit
        logger.info(f"Set maximum concurrent subprocesses to {limit}")


def get_active_subprocess_count() -> int:
    """Get the current number of active subprocesses."""
    with QMutexLocker(_subprocess_semaphore):
        return _active_subprocesses


@contextlib.contextmanager
def _subprocess_resource_manager() -> Generator[None, None, None]:
    """
    Context manager to track and limit subprocess resources.

    Uses QWaitCondition for proper thread synchronization when waiting
    for available subprocess slots.

    Raises:
        RuntimeError: If subprocess limit is exceeded after timeout.
    """
    global _active_subprocesses  # noqa: PLW0603

    # Wait for available slot using proper condition variable
    wait_timeout_ms = 100  # 100ms per wait cycle
    max_wait_cycles = 600  # 60 seconds total timeout

    _subprocess_semaphore.lock()
    try:
        wait_count = 0
        while _active_subprocesses >= _max_concurrent_subprocesses:
            # Wait on condition with timeout
            if not _subprocess_condition.wait(_subprocess_semaphore, wait_timeout_ms):
                wait_count += 1
                if wait_count >= max_wait_cycles:
                    _subprocess_semaphore.unlock()
                    raise RuntimeError(
                        f"Subprocess limit exceeded: maximum {_max_concurrent_subprocesses} concurrent processes"
                    )

        # Slot is available, acquire it
        _active_subprocesses += 1
        logger.debug(f"Acquired subprocess slot ({_active_subprocesses}/{_max_concurrent_subprocesses})")
    finally:
        _subprocess_semaphore.unlock()

    try:
        yield
    finally:
        with QMutexLocker(_subprocess_semaphore):
            _active_subprocesses -= 1
            logger.debug(f"Released subprocess slot ({_active_subprocesses}/{_max_concurrent_subprocesses})")
            # Wake up any waiting threads
            _subprocess_condition.wakeOne()


@contextlib.contextmanager
def safe_popen(*args: Any, **kwargs: Any) -> Any:
    """
    Context manager for safe subprocess handling with guaranteed cleanup.

    Ensures that:
    - Process is terminated/killed on exit
    - All pipes are properly closed
    - Resources are freed even on exceptions
    """
    with _subprocess_resource_manager():
        process = None
        try:
            process = subprocess.Popen(*args, **kwargs)
            yield process
        finally:
            if process is not None:
                # Close pipes first to prevent deadlock
                for pipe in [process.stdin, process.stdout, process.stderr]:
                    if pipe is not None:
                        with contextlib.suppress(OSError, ValueError):
                            pipe.close()

                # Terminate process if still running
                if process.poll() is None:
                    try:
                        process.terminate()
                        # Give it time to terminate gracefully
                        try:
                            process.wait(timeout=2.0)
                        except subprocess.TimeoutExpired:
                            # Force kill if still running
                            process.kill()
                            process.wait(timeout=1.0)
                    except (OSError, subprocess.SubprocessError):
                        pass


def check_process(pid: int, threshold: int = 5) -> bool:
    """
    Checks if a process's CPU usage exceeds a specified threshold.

    This function monitors the CPU usage of the process identified by its process
    ID (PID) and compares it against a defined threshold. If the usage surpasses
    the threshold, it returns True. If the process doesn't exist or access is
    denied, it safely handles these scenarios and returns False.

    Args:
        pid (int): The process ID of the target process.
        threshold (int): The CPU usage threshold percentage to compare against.
            Defaults to 5.

    Returns:
        bool: True if the process's CPU usage exceeds the threshold, False
        otherwise.
    """
    try:
        process: psutil.Process = psutil.Process(pid)
        cpu_percent: float = process.cpu_percent(interval=1)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
    else:
        return cpu_percent > threshold


def run_process(command: list[str] | str, timeout: int | None = None) -> tuple[int, str, str]:
    """
    Executes a subprocess command and captures its output, handling potential errors
    gracefully. The function allows setting a timeout for the subprocess execution
    and returns the exit code, standard output, and standard error.

    Args:
        command: The command to execute as a list of strings or a string. Each element should
            represent a part of the command, such as the executable and its
            arguments.
        timeout: The timeout in seconds for the command to complete execution. If
            the command takes longer than this, it will be forcibly terminated.
            Defaults to None.

    Returns:
        A tuple containing the exit code of the subprocess, its standard output, and
        its standard error. If an error occurs, the exit code will be -1, and either
        or both standard output and error may contain error details.

    Raises:
        subprocess.TimeoutExpired: If the timeout is exceeded before the command
            completes. This is handled internally but may be raised in certain
            scenarios.
        OSError: If there is an OS-related error while attempting to execute the
            subprocess.
        subprocess.SubprocessError: If a generic subprocess-related error occurs.
    """
    try:
        result: CompletedProcess[str] = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return -1, "", "Process timed out"
    except (OSError, subprocess.SubprocessError) as e:
        return -1, "", str(e)
    else:
        return result.returncode, result.stdout, result.stderr


class OutputReaderThread(QThread):
    """Thread for reading process output asynchronously."""

    def __init__(self, pipe: Any, line_list: list[str], callback: Callable[[str], None] | None) -> None:
        super().__init__()
        self.pipe = pipe
        self.line_list = line_list
        self.callback = callback
        self._stop_flag = False

    def run(self) -> None:
        """Read output from pipe and call callback for each line, checking stop flag."""
        try:
            if self.pipe is None:
                return
            for line in iter(self.pipe.readline, ""):
                # Check stop flag before processing each line
                if self._stop_flag:
                    logger.debug("Output reader thread stop flag detected, exiting")
                    break
                line = line.rstrip("\n\r")
                if line:
                    self.line_list.append(line)
                    if self.callback:
                        self.callback(line)
        except (OSError, ValueError) as e:
            if not self._stop_flag:  # Only log error if not intentionally stopped
                logger.error(f"Error in output reader thread: {e}")

    def stop(self) -> None:
        """Stop the thread gracefully."""
        self._stop_flag = True
        self.quit()
        if not self.wait(3000):  # Wait up to 3 seconds
            logger.warning("Output reader thread did not stop gracefully within 3 seconds")
            # Don't use terminate() - the stop flag should cause it to exit soon
            # The pipe will close when the process ends, which will also cause the thread to exit


def run_process_with_realtime_output(
    command: list[str] | str,
    output_callback: Callable[[str], None] | None = None,
    timeout: int | None = None,
    working_dir: str | Path | None = None,
    startup_info: Any = None,
) -> tuple[int, str, str]:
    """
    Runs a subprocess command with real-time output streaming and optional timeout handling.

    This function starts an external process and streams its output, both standard output and
    standard error, in real-time using threads for reading the output. Callbacks can be used
    to handle each line of the output dynamically. It also provides support for timeout to
    terminate processes that exceed the specified duration.

    Args:
        command (list[str] | str): The command to be executed as a list of strings or a string. For example,
            ["ls", "-la"] or "ls -la".
        output_callback (Callable[[str], None] | None): A callback function to handle each line
            of the standard output in real time. If None, the lines will only be collected and
            returned at the end.
        timeout (int | None): The maximum time in seconds to allow the command to execute.
            If the timeout expires, the process is forcefully killed. If None, no timeout is
            applied.
        working_dir (str | Path | None): The directory in which to execute the command.
            If None, the current working directory is used.
        startup_info (Any): Windows-specific STARTUPINFO structure for optimized process creation.
            If None on Windows, a default optimized configuration is used.

    Returns:
        tuple[int, str, str]: A tuple containing three elements:
            - The exit code of the executed process. Returns -1 if an error occurs or a timeout
              is reached.
            - A string with all the concatenated lines from the standard output.
            - A string with all the concatenated lines from the standard error.
    """
    start_time: float = time.time()
    stdout_lines: list[Any] = []
    stderr_lines: list[Any] = []
    process: subprocess.Popen | None = None
    stdout_thread: OutputReaderThread | None = None
    stderr_thread: OutputReaderThread | None = None

    # Optimize subprocess creation for Windows
    if startup_info is None and sys.platform == "win32":
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup_info.wShowWindow = subprocess.SW_HIDE

    try:
        with safe_popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            bufsize=1,  # Line buffered
            universal_newlines=True,
            cwd=str(working_dir) if working_dir else None,
            startupinfo=startup_info if sys.platform == "win32" else None,
            close_fds=sys.platform != "win32",  # Faster on Windows
        ) as process:
            # Start threads to read stdout and stderr
            stdout_thread = OutputReaderThread(process.stdout, stdout_lines, output_callback)
            stderr_thread = OutputReaderThread(process.stderr, stderr_lines, None)

            stdout_thread.start()
            stderr_thread.start()

            # Monitor for timeout
            while process.poll() is None:
                if timeout and (time.time() - start_time) > timeout:
                    # Timeout reached - terminate process and threads
                    logger.info("Process timeout reached, terminating...")
                    # Process termination is handled by safe_popen

                    # Stop threads
                    if stdout_thread and stdout_thread.isRunning():
                        stdout_thread.stop()
                    if stderr_thread and stderr_thread.isRunning():
                        stderr_thread.stop()

                    return -1, "\n".join(stdout_lines), "Process timed out"

                time.sleep(0.1)

            # Wait for threads to finish reading all output
            if stdout_thread and stdout_thread.isRunning():
                stdout_thread.wait(5000)  # 5 second timeout
            if stderr_thread and stderr_thread.isRunning():
                stderr_thread.wait(5000)  # 5 second timeout

            return process.returncode, "\n".join(stdout_lines), "\n".join(stderr_lines)

    except (OSError, subprocess.SubprocessError, ValueError) as e:
        logger.error(f"Error in run_process_with_realtime_output: {e}")
        return -1, "", str(e)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        # Process cleanup is handled by safe_popen

        # Stop threads
        if stdout_thread and stdout_thread.isRunning():
            stdout_thread.stop()
        if stderr_thread and stderr_thread.isRunning():
            stderr_thread.stop()

        return -1, "\n".join(stdout_lines), "Process interrupted by user"
    finally:
        # Ensure threads are cleaned up
        if stdout_thread and stdout_thread.isRunning():
            stdout_thread.stop()
        if stderr_thread and stderr_thread.isRunning():
            stderr_thread.stop()
