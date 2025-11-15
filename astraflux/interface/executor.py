# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Callable, List, Any, Dict, Tuple

from astraflux.definitions.constants import *


@dataclass
class Task:
    """
    Data class representing a task to be executed by the thread/process pool.

    Attributes:
        id: Unique identifier for the task
        func: Callable function to be executed
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        max_retries: Maximum number of retry attempts upon failure
        retry_delay: Base delay time (in seconds) between retries
        status: Current execution status of the task
        retry_count: Number of retry attempts already made
        result: Result returned by the function upon successful execution
        error: Exception information if the task failed
    """
    id: int
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    max_retries: int = 3
    retry_delay: float = 1.0
    status: DEFINITIONS.STATUS = DEFINITIONS.STATUS.PENDING
    retry_count: int = 0
    result: Any = None
    error: str = None


class ThreadPoolExecutorWithRetry:
    """
    A thread pool executor with built-in retry mechanism for failed tasks.

    Features:
    - Automatic retry of failed tasks with exponential backoff
    - Progress tracking and monitoring
    - Batch task submission
    - Thread-safe operations

    Args:
        logger: Logger instance for logging operations
        max_workers: Maximum number of worker threads (default: 5)
        retry_delay: Base delay time between retries in seconds (default: 1.0)
    """

    def __init__(self, logger, max_workers: int = 5, retry_delay: float = 1.0):
        pass

    def submit(self, func: Callable, *args, max_retries: int = 3, **kwargs) -> int:
        """
        Submit a single task for execution.

        Args:
            func: Callable function to execute
            *args: Positional arguments for the function
            max_retries: Maximum number of retry attempts (default: 3)
            **kwargs: Keyword arguments for the function

        Returns:
            int: Unique task ID that can be used to track the task
        """

    def submit_batch(self, tasks: List[Tuple[Callable, tuple, dict]]) -> List[int]:
        """
        Submit multiple tasks for batch execution.

        Args:
            tasks: List of task tuples in format (func, args, kwargs) or (func, args) or (func)

        Returns:
            List[int]: List of task IDs for the submitted tasks
        """

    def start(self):
        """Start the thread pool executor and launch worker threads."""

    def wait_completion(self, timeout: float = None):
        """
        Wait for all tasks to complete execution.

        Args:
            timeout: Maximum time to wait in seconds (default: None for unlimited)
        """

    def shutdown(self):
        """Gracefully shutdown the executor and stop all worker threads."""

    def get_progress(self) -> Dict[str, Any]:
        """
        Get current execution progress statistics.

        Returns:
            Dict containing progress information including:
            - total: Total number of tasks
            - completed: Number of completed tasks (success + failed)
            - pending: Number of pending tasks
            - running: Number of currently running tasks
            - retrying: Number of tasks waiting for retry
            - success: Number of successfully completed tasks
            - failed: Number of failed tasks
            - progress: Completion percentage (0-100)
        """

    def get_results(self) -> Dict[int, Any]:
        """
        Get results from successfully completed tasks.

        Returns:
            Dict mapping task IDs to their results
        """

    def get_failed_tasks(self) -> List[Task]:
        """
        Get list of tasks that failed after all retry attempts.

        Returns:
            List of failed Task objects
        """


class ProcessPoolExecutorWithRetry:
    """
    A process pool executor with built-in retry mechanism for failed tasks.

    Features:
    - Multiprocessing-based execution for CPU-bound tasks
    - Automatic retry with configurable delay
    - Progress tracking across processes
    - Batch task submission
    - Process-safe operations using shared memory

    Args:
        logger: Logger instance for logging operations
        max_workers: Maximum number of worker processes (default: CPU count)
        retry_delay: Base delay time between retries in seconds (default: 1.0)
    """

    def __init__(self, logger=None, max_workers: int = None, retry_delay: float = 1.0):
        pass

    def submit(self, func: Callable, *args, max_retries: int = 3, **kwargs) -> int:
        """
        Submit a single task for execution in the process pool.

        Args:
            func: Callable function to execute
            *args: Positional arguments for the function
            max_retries: Maximum number of retry attempts (default: 3)
            **kwargs: Keyword arguments for the function

        Returns:
            int: Unique task ID for tracking
        """

    def submit_batch(self, tasks: List[Tuple[Callable, tuple, dict]]) -> List[int]:
        """
        Submit multiple tasks for batch execution.

        Args:
            tasks: List of task tuples in format (func, args, kwargs) or variations

        Returns:
            List[int]: List of task IDs for submitted tasks
        """

    def start(self):
        """Start the process pool executor and launch worker processes."""

    def wait_completion(self, timeout: float = None):
        """
        Wait for all tasks to complete execution.

        Args:
            timeout: Maximum time to wait in seconds (default: None for unlimited)
        """

    def shutdown(self, timeout: float = 5):
        """
        Gracefully shutdown the executor and terminate worker processes.

        Args:
            timeout: Time to wait for processes to terminate gracefully before force termination
        """

    def get_progress(self) -> Dict[str, Any]:
        """
        Get current execution progress statistics across all processes.

        Returns:
            Dict containing comprehensive progress information
        """

    def get_results(self) -> Dict[int, Any]:
        """
        Get results from successfully completed tasks.

        Returns:
            Dict mapping task IDs to their execution results
        """

    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about failed tasks.

        Returns:
            List of dictionaries containing failure information
        """


def gen_thread_executor(logger, max_workers: int = 5, retry_delay: float = 1.0) -> ThreadPoolExecutorWithRetry:
    """
    Factory function to create a ThreadPoolExecutorWithRetry instance.

    This function provides a convenient way to instantiate a thread-based executor
    with retry capabilities for executing tasks with automatic failure recovery.

    Args:
        logger: Logger instance for tracking execution progress and errors
        max_workers: Maximum number of worker threads to create (default: 5)
        retry_delay: Base delay time in seconds between retry attempts (default: 1.0)

    Returns:
        ThreadPoolExecutorWithRetry: Configured thread pool executor instance
    """
    return gen_thread_executor(logger, max_workers, retry_delay)


def gen_process_executor(logger, max_workers: int = 5, retry_delay: float = 1.0) -> ProcessPoolExecutorWithRetry:
    """
    Factory function to create a ProcessPoolExecutorWithRetry instance.

    This function provides a convenient way to instantiate a process-based executor
    with retry capabilities, suitable for CPU-intensive tasks that benefit from
    true parallel execution across multiple CPU cores.

    Args:
        logger: Logger instance for tracking execution progress and errors
        max_workers: Maximum number of worker processes to create (default: 5)
                    If not specified, defaults to the number of CPU cores
        retry_delay: Base delay time in seconds between retry attempts (default: 1.0)

    Returns:
        ProcessPoolExecutorWithRetry: Configured process pool executor instance
    """
    return gen_process_executor(logger, max_workers, retry_delay)
