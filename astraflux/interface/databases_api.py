# -*- encoding: utf-8 -*-
from astraflux.settings import *
from astraflux.inject import inject_implementation

__all__ = [
    "task_submit_databases",
    "task_submit_databases_and_send",
    "subtask_create",
    "query_task_by_task_id",
    "query_worker_running_number",
    "task_stop",
    "redis_get_task_status_by_task_id"
]


@inject_implementation()
def task_submit_databases(queue: str, message: dict, weight: int = TASK.DEFAULT_VALUE_TASK_WEIGHT) -> str:
    """
        Submit a task to the specified queue.
        Args:
            queue (str): The name of the queue to submit the task to.
            message (dict): The message to be submitted as a task.
            weight (int): The weight of the task. Default is 1.
        Returns:
            str: The task ID associated with the submitted task.
        This method submits the provided task to the specified queue using the RabbitMQ instance.
    """


@inject_implementation()
def task_submit_databases_and_send(queue: str, message: dict, weight: int = TASK.DEFAULT_VALUE_TASK_WEIGHT) -> str:
    """
        Send a message to the queue.
        Args:
            queue (str): The name of the queue to send the message to.
            message (dict): The message to be sent.
            weight (int): The weight of the message. Default is 1.
        Returns:
            str: The task ID associated with the message.
        This method sends the provided message to the specified queue using the RabbitMQ instance.
    """


@inject_implementation()
def subtask_create(source_task_id: str, subtask_queue: str, subtasks: list) -> list:
    """
        Create a subtask for the given task ID.
        Args:
            source_task_id (str): The ID of the task to create a subtask for.
            subtask_queue (str): The name of the queue to create the subtask in.
            subtasks (dict): The subtask to be created.
        Returns:
            str: The subtask ID associated with the created subtask.
        This method creates a subtask for the given task ID using the RabbitMQ instance.
    """


@inject_implementation()
def query_task_by_task_id(task_id: str) -> dict:
    """
    Query the task data of the given task ID.
    Args:
        task_id (str): The ID of the task to query.
    Returns:
        dict: task data
    """


@inject_implementation()
def query_worker_running_number(query: dict):
    """
    Query the number of running workers based on the given query.
    Args:
        query (dict): A dictionary containing the query criteria.
    Returns:
        tuple: A tuple containing the number of running workers and the maximum number of workers.
    """


@inject_implementation()
def task_stop(task_id: str) -> None:
    """
    Stop the given task ID.
    """


@inject_implementation()
def redis_get_task_status_by_task_id(task_id: str) -> str:
    """
    Get the status of the given task ID.
    Args:
        task_id (str): The ID of the task to get the status of.

    Returns:
        str: The status of the given task ID.
    """
