# -*- encoding: utf-8 -*-

import time
import threading
import multiprocessing
from typing import Callable, Optional, Dict, Any, List
import uuid


class BaseTask:
    """Base class for all tasks"""

    def __init__(self, task_id: str, target: Callable, args: tuple = (), kwargs: dict = None):
        self.task_id = task_id
        self.target = target
        self.args = args or ()
        self.kwargs = kwargs or {}
        self._is_running = False
        self._stop_event = None
        self.result = None
        self.exception = None

    def start(self):
        """start the task"""
        raise NotImplementedError

    def stop(self):
        """stop the task"""
        if self._stop_event:
            self._stop_event.set()

    def is_running(self) -> bool:
        """check if task is running"""
        return self._is_running

    def get_result(self, task_id=None):
        """get result from task"""
        return self.result

    def get_exception(self):
        """get exception from task"""
        return self.exception

    def wait(self, timeout: Optional[float] = None) -> bool:
        """wait for task to finish"""
        raise NotImplementedError


class ThreadTask(BaseTask):
    """asynchronous task"""

    def __init__(self, task_id: str, target: Callable, args: tuple = (), kwargs: dict = None):
        super().__init__(task_id, target, args, kwargs)
        self._thread = None
        self._stop_event = threading.Event()

    def _run(self):
        """task is running"""
        try:
            self._is_running = True
            self.result = self.target(*self.args, **self.kwargs)
        except Exception as e:
            self.exception = e
        finally:
            self._is_running = False

    def start(self):
        if self._is_running:
            return False

        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()
        return True

    def stop(self):
        super().stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        self._is_running = False

    def wait(self, timeout: Optional[float] = None) -> bool:
        if not self._thread:
            return True
        self._thread.join(timeout=timeout)
        return not self._thread.is_alive()


class ProcessTask(BaseTask):
    """asynchronous task"""

    def __init__(self, task_id: str, target: Callable, args: tuple = (), kwargs: dict = None):
        super().__init__(task_id, target, args, kwargs)
        self._process = None
        self._stop_event = multiprocessing.Event()
        self._queue = multiprocessing.Queue()

    def _run(self, _queue):
        """task is running"""
        try:
            self._is_running = True
            result = self.target(*self.args, **self.kwargs)
            _queue.put(result)
        except Exception as e:
            _queue.put(e)
        finally:
            self._is_running = False

    def start(self):
        if self._is_running:
            return False

        self._process = multiprocessing.Process(target=self._run, args=(self._queue,))
        self._process.daemon = True
        self._process.start()

        item = self._queue.get()
        self.result = item

        return True

    def stop(self):
        super().stop()
        if self._process and self._process.is_alive():
            self._process.terminate()
        self._is_running = False

    def wait(self, timeout: Optional[float] = None) -> bool:
        if not self._process:
            return True

        self._process.join(timeout=timeout)

        return not self._process.is_alive()


class TaskManager:
    """asynchronous task manager"""

    _instance = None
    tasks: Dict[str, BaseTask] = {}
    task_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
        return cls._instance

    def add_task(
            self,
            task_type: str,
            target: Callable,
            task_id: Optional[str] = None,
            args: tuple = (),
            kwargs: dict = None) -> str:
        """
        add task
        :param task_type: ('thread' 或 'process')
        :param target: task function
        :param task_id: optional task ID
        :param args: task arguments
        :param kwargs: task keyword arguments
        :return: task_id
        """
        if task_id is None:
            task_id = str(uuid.uuid4())

        with self.task_lock:
            if task_id in self.tasks:
                raise ValueError(f"Task '{task_id}' already exists. Skipping insertion.")

            if task_type == 'thread':
                task = ThreadTask(task_id, target, args, kwargs)
            elif task_type == 'process':
                task = ProcessTask(task_id, target, args, kwargs)
            else:
                raise ValueError(f"Invalid task type: '{task_type}'")

            self.tasks[task_id] = task
            return task_id

    def run_task(self, task_id: str) -> bool:
        """run task"""
        with self.task_lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            return task.start()

    def stop_task(self, task_id: str) -> bool:
        """stop task"""
        with self.task_lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            task.stop()
            return True

    def remove_task(self, task_id: str) -> bool:
        """remove task"""
        with self.task_lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            if task.is_running():
                task.stop()

            del self.tasks[task_id]
            return True

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """get task status"""
        with self.task_lock:
            task = self.tasks.get(task_id)
            if not task:
                return None

            return {
                'id': task.task_id,
                'running': task.is_running(),
                'result': task.get_result(task_id),
                'exception': task.get_exception()
            }

    def wait_task(self, task_id: str, timeout: Optional[float] = None) -> bool:
        """wait task"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        return task.wait(timeout)

    def stop_all_tasks(self):
        """stop all tasks"""
        with self.task_lock:
            for task in self.tasks.values():
                if task.is_running():
                    task.stop()

    def list_tasks(self) -> Dict[str, Dict[str, Any]]:
        """get all tasks"""
        with self.task_lock:
            return {
                task_id: self.get_task_status(task_id)
                for task_id in self.tasks
            }

    def run_all_tasks(self) -> List[str]:
        """
        run all tasks
        :return: list of started task IDs
        """
        started_tasks = []
        with self.task_lock:
            for task_id, task in self.tasks.items():
                if not task.is_running() and task.start():
                    started_tasks.append(task_id)
        return started_tasks

    def wait_all_tasks(self, timeout: Optional[float] = None) -> bool:
        """
        wait all tasks
        :param timeout: maximum time to wait (seconds)
        :return: True if all tasks completed, False if timeout
        """
        start_time = time.time()
        all_completed = False

        while not all_completed:
            all_completed = True
            with self.task_lock:
                for task in self.tasks.values():
                    if task.is_running():
                        all_completed = False
                        break

            if not all_completed:
                if timeout is not None and (time.time() - start_time) > timeout:
                    return False
                time.sleep(0.1)

        return True


def async_task_add(
        task_type: str,
        target: Callable,
        args: tuple = (),
        kwargs: dict = None,
        task_id: Optional[str] = None) -> str:
    """
    add task
    :param task_type: ('thread' 或 'process')
    :param target: task function
    :param args: task arguments
    :param kwargs: task keyword arguments
    :param task_id: optional task ID
    :return: task_id
    """
    return TaskManager().add_task(
        task_type=task_type,
        target=target,
        args=args,
        kwargs=kwargs,
        task_id=task_id
    )


def async_task_run(task_id: str) -> bool:
    """run task"""
    return TaskManager().run_task(task_id=task_id)


def async_task_get_status(task_id: str) -> Optional[Dict[str, Any]]:
    """get task status"""
    return TaskManager().get_task_status(task_id=task_id)


def async_task_wait(task_id: str, timeout: Optional[float] = None) -> bool:
    """wait task"""
    return TaskManager().wait_task(task_id=task_id, timeout=timeout)


def async_task_stop(task_id: str) -> bool:
    """stop a specific task"""
    return TaskManager().stop_task(task_id=task_id)


def async_task_remove(task_id: str) -> bool:
    """remove a specific task"""
    return TaskManager().remove_task(task_id=task_id)


def async_task_stop_all():
    """stop all tasks"""
    TaskManager().stop_all_tasks()


def async_task_list() -> Dict[str, Dict[str, Any]]:
    """get all tasks"""
    return TaskManager().list_tasks()


def async_task_run_all() -> List[str]:
    """
    run all tasks
    :return: list of started task IDs
    """
    return TaskManager().run_all_tasks()


def async_task_wait_all(timeout: Optional[float] = None) -> bool:
    """
    wait all tasks
    :param timeout: maximum time to wait (seconds)
    :return: True if all tasks completed, False if timeout
    """
    return TaskManager().wait_all_tasks(timeout=timeout)


def register():
    from astraflux.interface import async_task
    async_task.async_task_add = async_task_add
    async_task.async_task_run = async_task_run
    async_task.async_task_get_status = async_task_get_status
    async_task.async_task_wait = async_task_wait
    async_task.async_task_stop_all = async_task_stop_all
    async_task.async_task_list = async_task_list
    async_task.async_task_run_all = async_task_run_all
    async_task.async_task_wait_all = async_task_wait_all

    import sys
    sys.modules['astraflux.interface.async_task'] = async_task
