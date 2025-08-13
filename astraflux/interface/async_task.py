# -*- encoding: utf-8 -*-
from typing import Callable, Optional, Dict, Any, List

from astraflux.inject import inject_implementation

__all__ = [
    "async_task_add",
    "async_task_run",
    "async_task_get_status",
    "async_task_wait",
    "async_task_stop_all",
    "async_task_list",
    "async_task_run_all",
    "async_task_wait_all"
]


@inject_implementation()
def async_task_add(
        task_type: str,
        target: Callable,
        task_id: Optional[str],
        args: tuple = (),
        kwargs: dict = None) -> str:
    """
    add task
    :param task_type: 'thread' / 'process'
    :param target:
    :param args:
    :param kwargs:
    :param task_id:
    :return: task_id
    """


@inject_implementation()
def async_task_run(task_id: str) -> bool:
    """run task"""


@inject_implementation()
def async_task_get_status(task_id: str) -> Optional[Dict[str, Any]]:
    """get task status"""


@inject_implementation()
def async_task_wait(task_id: str, timeout: Optional[float] = None) -> bool:
    """wait task"""


@inject_implementation()
def async_task_stop_all():
    """stop all tasks"""


@inject_implementation()
def async_task_list() -> Dict[str, Dict[str, Any]]:
    """get all tasks"""


@inject_implementation()
def async_task_run_all() -> List[str]:
    """
    run all tasks
    :return:
    """


@inject_implementation()
def async_task_wait_all(timeout: Optional[float] = None) -> bool:
    """
    wait all tasks
    :param timeout:
    :return:
    """
