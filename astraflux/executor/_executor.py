# -*- coding: utf-8 -*-

import time
import dill
import queue
import platform
import threading
import traceback
import multiprocessing as mp
from dataclasses import dataclass, asdict
from multiprocessing import Queue, Manager, Lock
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

    def __post_init__(self):
        """Initialize default values after instance creation."""
        if self.kwargs is None:
            self.kwargs = {}


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
        self.logger = logger
        self.max_workers = max_workers
        self.retry_delay = retry_delay

        # Task management
        self.task_queue = queue.Queue()
        self.results = {}
        self.failed_tasks = []

        # Progress tracking
        self.completed_tasks = 0
        self.total_tasks = 0

        # Thread synchronization
        self.lock = threading.Lock()
        self.workers = []
        self.is_running = False

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
        with self.lock:
            task_id = self.total_tasks
            task = Task(
                id=task_id,
                func=func,
                args=args,
                kwargs=kwargs,
                max_retries=max_retries,
                retry_delay=self.retry_delay
            )
            self.task_queue.put(task)
            self.total_tasks += 1
            self.results[task_id] = task
            return task_id

    def submit_batch(self, tasks: List[Tuple[Callable, tuple, dict]]) -> List[int]:
        """
        Submit multiple tasks for batch execution.

        Args:
            tasks: List of task tuples in format (func, args, kwargs) or (func, args) or (func)

        Returns:
            List[int]: List of task IDs for the submitted tasks
        """
        task_ids = []
        for task_info in tasks:
            if len(task_info) == 1:
                func, args, kwargs = task_info[0], (), {}
            elif len(task_info) == 2:
                func, args, kwargs = task_info[0], task_info[1], {}
            else:
                func, args, kwargs = task_info[0], task_info[1], task_info[2]

            task_id = self.submit(func, *args, **kwargs)
            task_ids.append(task_id)
        return task_ids

    def _worker(self):
        """
        Worker thread function that continuously processes tasks from the queue.

        This function runs in each worker thread and:
        - Retrieves tasks from the queue
        - Executes the task function
        - Handles retries on failure
        - Updates task status and results
        """
        while self.is_running:
            try:
                # Get task from queue with timeout to allow graceful shutdown
                task = self.task_queue.get(timeout=1)
            except queue.Empty:
                continue

            try:
                # Update task status to running
                with self.lock:
                    task.status = DEFINITIONS.STATUS.RUNNING

                self.logger.info(f"Executing task {task.id}: {task.func.__name__}")

                # Execute the task function
                result = task.func(*task.args, **task.kwargs)

                # Mark task as successfully completed
                with self.lock:
                    task.status = DEFINITIONS.STATUS.SUCCESS
                    task.result = result
                    self.completed_tasks += 1

                self.logger.info(f"Task {task.id} completed successfully")

            except Exception as e:
                # Handle task execution failure
                with self.lock:
                    task.retry_count += 1
                    task.error = e

                if task.retry_count <= task.max_retries:
                    # Schedule task for retry with exponential backoff
                    with self.lock:
                        task.status = DEFINITIONS.STATUS.RETRYING

                    self.logger.warning(
                        f"Task {task.id} failed, retry {task.retry_count}/{task.max_retries}. Error: {e}"
                    )

                    # Wait before retrying (exponential backoff)
                    time.sleep(task.retry_delay * task.retry_count)

                    # Re-queue the task for retry
                    self.task_queue.put(task)
                else:
                    # Mark task as failed after exhausting all retries
                    with self.lock:
                        task.status = DEFINITIONS.STATUS.FAILED
                        self.failed_tasks.append(task)
                        self.completed_tasks += 1

                    self.logger.error(f"Task {task.id} failed after {task.max_retries} retry attempts")

            finally:
                # Mark task as processed in the queue
                self.task_queue.task_done()

    def start(self):
        """Start the thread pool executor and launch worker threads."""
        if self.is_running:
            self.logger.warning("Executor is already running")
            return

        self.is_running = True
        self.workers = []

        # Create and start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker,
                name=f"Worker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        self.logger.info(f"Started {self.max_workers} worker threads")

    def wait_completion(self, timeout: float = None):
        """
        Wait for all tasks to complete execution.

        Args:
            timeout: Maximum time to wait in seconds (default: None for unlimited)
        """
        # Wait for all tasks to be processed
        self.task_queue.join()

        # Signal workers to stop
        self.is_running = False

        # Wait for worker threads to finish
        start_time = time.time()
        for worker in self.workers:
            if timeout:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    break
                worker.join(remaining)
            else:
                worker.join()

    def shutdown(self):
        """Gracefully shutdown the executor and stop all worker threads."""
        self.is_running = False
        self.logger.info("Executor has been shutdown")

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
        with self.lock:
            pending = sum(1 for task in self.results.values() if task.status == DEFINITIONS.STATUS.PENDING)
            running = sum(1 for task in self.results.values() if task.status == DEFINITIONS.STATUS.RUNNING)
            retrying = sum(1 for task in self.results.values() if task.status == DEFINITIONS.STATUS.RETRYING)
            success = sum(1 for task in self.results.values() if task.status == DEFINITIONS.STATUS.SUCCESS)
            failed = sum(1 for task in self.results.values() if task.status == DEFINITIONS.STATUS.FAILED)

            progress_percentage = (
                (self.completed_tasks / self.total_tasks * 100)
                if self.total_tasks > 0 else 0
            )

            return {
                "total": self.total_tasks,
                "completed": self.completed_tasks,
                "pending": pending,
                "running": running,
                "retrying": retrying,
                "success": success,
                "failed": failed,
                "progress": progress_percentage
            }

    def get_results(self) -> Dict[int, Any]:
        """
        Get results from successfully completed tasks.

        Returns:
            Dict mapping task IDs to their results
        """
        return {
            task_id: task.result
            for task_id, task in self.results.items()
            if task.status == DEFINITIONS.STATUS.SUCCESS
        }

    def get_failed_tasks(self) -> List[Task]:
        """
        Get list of tasks that failed after all retry attempts.

        Returns:
            List of failed Task objects
        """
        return self.failed_tasks.copy()


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
        self.logger = logger
        self.max_workers = max_workers or mp.cpu_count()
        self.retry_delay = retry_delay

        if platform.system() == 'Windows':
            mp.set_start_method('spawn', force=True)

        # Multiprocessing manager for shared objects
        self.manager = Manager()

        # Inter-process communication queues and shared data
        self.task_queue = Queue()
        self.results = self.manager.dict()  # Shared dictionary for task results
        self.failed_tasks = self.manager.list()  # Shared list for failed tasks

        # Progress tracking with shared values
        self.completed_tasks = self.manager.Value('i', 0)  # Integer value
        self.total_tasks = self.manager.Value('i', 0)  # Integer value

        # Process management
        self.workers = []
        self.is_running = False
        self._task_counter = 0
        self._lock = Lock()  # Process-safe lock

    @staticmethod
    def _serialize_task(task: Task) -> Dict[str, Any]:
        """
        Serialize task for inter-process communication using dill.

        Args:
            task: Task object to serialize

        Returns:
            Dict containing serialized task data
        """
        task_dict = asdict(task)
        # Serialize function and arguments for process-safe transfer
        task_dict['func'] = dill.dumps(task.func)
        task_dict['args'] = dill.dumps(task.args)
        task_dict['kwargs'] = dill.dumps(task.kwargs)
        task_dict['status'] = task.status.value  # Convert enum to string
        return task_dict

    @staticmethod
    def _deserialize_task(task_dict: Dict[str, Any]) -> Task:
        """
        Deserialize task received from inter-process communication.

        Args:
            task_dict: Serialized task dictionary

        Returns:
            Deserialized Task object
        """
        task_dict = task_dict.copy()
        # Deserialize function and arguments
        task_dict['func'] = dill.loads(task_dict['func'])
        task_dict['args'] = dill.loads(task_dict['args'])
        task_dict['kwargs'] = dill.loads(task_dict['kwargs'])
        task_dict['status'] = DEFINITIONS.STATUS(task_dict['status'])  # Convert back to enum
        return Task(**task_dict)

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
        with self._lock:
            task_id = self._task_counter
            task = Task(
                id=task_id,
                func=func,
                args=args,
                kwargs=kwargs,
                max_retries=max_retries,
                retry_delay=self.retry_delay
            )

            # Serialize and store task in shared memory
            task_dict = self._serialize_task(task)
            self.results[task_id] = task_dict
            self.task_queue.put(task_dict)

            # Update counters
            self._task_counter += 1
            self.total_tasks.value += 1

            return task_id

    def submit_batch(self, tasks: List[Tuple[Callable, tuple, dict]]) -> List[int]:
        """
        Submit multiple tasks for batch execution.

        Args:
            tasks: List of task tuples in format (func, args, kwargs) or variations

        Returns:
            List[int]: List of task IDs for submitted tasks
        """
        task_ids = []
        for task_info in tasks:
            # Handle different tuple formats
            if len(task_info) == 1:
                func, args, kwargs = task_info[0], (), {}
            elif len(task_info) == 2:
                func, args, kwargs = task_info[0], task_info[1], {}
            else:
                func, args, kwargs = task_info[0], task_info[1], task_info[2]

            task_id = self.submit(func, *args, **kwargs)
            task_ids.append(task_id)
        return task_ids

    def _worker_process(self, worker_id: int):
        """
        Worker process function that executes tasks from the queue.

        Args:
            worker_id: Unique identifier for the worker process
        """
        if self.logger:
            self.logger.info(f"Worker process {worker_id} started")

        while self.is_running:
            try:
                # Get task from queue with timeout for graceful shutdown
                task_dict = self.task_queue.get(timeout=1)
                task = self._deserialize_task(task_dict)

                # Update task status to running
                task.status = DEFINITIONS.STATUS.RUNNING
                self.results[task.id] = self._serialize_task(task)

                if self.logger:
                    self.logger.info(f"Process {worker_id} executing task {task.id}: {task.func.__name__}")

                try:
                    # Execute the task function
                    result = task.func(*task.args, **task.kwargs)

                    # Mark task as successfully completed
                    task.status = DEFINITIONS.STATUS.SUCCESS
                    task.result = result
                    self.completed_tasks.value += 1

                    if self.logger:
                        self.logger.info(f"Process {worker_id} completed task {task.id}")

                except Exception as e:
                    # Handle task execution failure
                    task.retry_count += 1
                    # Store detailed error information
                    task.error = f"{type(e).__name__}: {str(e)}\n {traceback.format_exc()}"

                    if task.retry_count <= task.max_retries:
                        # Schedule task for retry
                        task.status = DEFINITIONS.STATUS.RETRYING
                        if self.logger:
                            self.logger.warning(
                                f"Process {worker_id} task {task.id} failed, "
                                f"retry {task.retry_count}/{task.max_retries}. Error: {e}"
                            )

                        # Wait before retrying (exponential backoff)
                        time.sleep(task.retry_delay * task.retry_count)

                        # Re-queue task for retry
                        self.task_queue.put(self._serialize_task(task))
                    else:
                        # Mark task as failed after exhausting retries
                        task.status = DEFINITIONS.STATUS.FAILED
                        self.failed_tasks.append(self._serialize_task(task))
                        self.completed_tasks.value += 1
                        if self.logger:
                            self.logger.error(
                                f"Process {worker_id} task {task.id} failed after maximum retries"
                            )

                # Update task results in shared memory
                self.results[task.id] = self._serialize_task(task)

            except queue.Empty:
                # No tasks available, continue waiting
                continue
            except Exception as e:
                # Handle unexpected errors in worker process
                if self.is_running:
                    if self.logger:
                        self.logger.error(f"Worker process {worker_id} encountered error: {e}")
                    continue
                else:
                    break

        if self.logger:
            self.logger.info(f"Worker process {worker_id} exited")

    def start(self):
        """Start the process pool executor and launch worker processes."""
        if self.is_running:
            if self.logger:
                self.logger.warning("Executor is already running")
            return

        self.is_running = True
        self.workers = []

        # Create and start worker processes
        for i in range(self.max_workers):
            worker = mp.Process(
                target=self._worker_process,
                args=(i,),
                name=f"WorkerProcess-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        if self.logger:
            self.logger.info(f"Started {self.max_workers} worker processes")

    def wait_completion(self, timeout: float = None):
        """
        Wait for all tasks to complete execution.

        Args:
            timeout: Maximum time to wait in seconds (default: None for unlimited)
        """
        start_time = time.time()

        # Monitor completion progress
        while self.completed_tasks.value < self.total_tasks.value:
            # Check for timeout
            if timeout and (time.time() - start_time) > timeout:
                if self.logger:
                    self.logger.warning("Timeout waiting for task completion")
                break

            # Check if all workers are still alive
            active_workers = sum(1 for w in self.workers if w.is_alive())
            if active_workers == 0 and not self.task_queue.empty():
                if self.logger:
                    self.logger.error("All worker processes terminated with tasks remaining")
                break

            time.sleep(0.1)  # Prevent busy waiting

        # Shutdown the executor
        self.shutdown()

    def shutdown(self, timeout: float = 5):
        """
        Gracefully shutdown the executor and terminate worker processes.

        Args:
            timeout: Time to wait for processes to terminate gracefully before force termination
        """
        self.is_running = False

        # Wait for worker processes to finish
        start_time = time.time()
        for worker in self.workers:
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time > 0:
                worker.join(timeout=remaining_time)
            if worker.is_alive():
                worker.terminate()  # Force termination if still alive

        # Clean up shared resources
        self.manager.shutdown()

        if self.logger:
            self.logger.info("Executor has been shutdown")

    def get_progress(self) -> Dict[str, Any]:
        """
        Get current execution progress statistics across all processes.

        Returns:
            Dict containing comprehensive progress information
        """
        total = self.total_tasks.value
        completed = self.completed_tasks.value

        # Count tasks by status from shared results
        status_count = {
            DEFINITIONS.STATUS.PENDING: 0,
            DEFINITIONS.STATUS.RUNNING: 0,
            DEFINITIONS.STATUS.RETRYING: 0,
            DEFINITIONS.STATUS.SUCCESS: 0,
            DEFINITIONS.STATUS.FAILED: 0
        }

        for task_id in list(self.results.keys()):
            try:
                task_dict = self.results[task_id]
                task = self._deserialize_task(task_dict)
                status_count[task.status] += 1
            except (KeyError, dill.UnpicklingError):
                # Skip corrupted or missing task entries
                continue

        progress_percentage = (
            (completed / total * 100)
            if total > 0 else 0
        )

        return {
            "total": total,
            "completed": completed,
            "pending": status_count[DEFINITIONS.STATUS.PENDING],
            "running": status_count[DEFINITIONS.STATUS.RUNNING],
            "retrying": status_count[DEFINITIONS.STATUS.RETRYING],
            "success": status_count[DEFINITIONS.STATUS.SUCCESS],
            "failed": status_count[DEFINITIONS.STATUS.FAILED],
            "progress": progress_percentage
        }

    def get_results(self) -> Dict[int, Any]:
        """
        Get results from successfully completed tasks.

        Returns:
            Dict mapping task IDs to their execution results
        """
        results = {}
        for task_id in list(self.results.keys()):
            try:
                task_dict = self.results[task_id]
                task = self._deserialize_task(task_dict)
                if task.status == DEFINITIONS.STATUS.SUCCESS:
                    results[task_id] = task.result
            except (KeyError, dill.UnpicklingError):
                # Skip corrupted task entries
                continue
        return results

    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about failed tasks.

        Returns:
            List of dictionaries containing failure information
        """
        failed = []
        for task_dict in self.failed_tasks:
            try:
                task = self._deserialize_task(task_dict)
                failed.append({
                    'id': task.id,
                    'func': task.func.__name__,
                    'error': task.error,
                    'retry_count': task.retry_count
                })
            except (KeyError, dill.UnpicklingError):
                # Skip corrupted task entries
                continue
        return failed

    def __enter__(self):
        """Context manager entry point."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.shutdown()


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
    return ThreadPoolExecutorWithRetry(logger, max_workers, retry_delay)


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
    return ProcessPoolExecutorWithRetry(logger, max_workers, retry_delay)


def register():
    from astraflux.interface import executor
    executor.gen_thread_executor = gen_thread_executor
    executor.gen_process_executor = gen_process_executor

    if REPLACE_SYS_MODULE:
        import sys
        sys.modules['astraflux.interface.executor'] = executor
