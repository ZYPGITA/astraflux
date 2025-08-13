# -*- encoding: utf-8 -*-

from astraflux.settings import *
from astraflux.interface.snowflake import snowflake_id
from astraflux.interface.format_time import get_converted_time
from astraflux.interface.rabbitmq import rabbitmq_send_message

from ._mongodb import mongodb_task, mongodb_services
from ._redisdb import redis_task


def _task_required_field_check(message: dict):
    """
    Check if the required fields are present in the task message.
    Args:
        message (dict): The task message.
    Raises:
        Exception: If any of the required fields are missing.
    Returns:
        message (dict): The task message.
    """
    if TASK.KEY_TASK_ID in message and message[TASK.KEY_TASK_ID] is not None and message[TASK.KEY_TASK_ID] != "":
        return message

    message[TASK.KEY_TASK_ID] = snowflake_id()
    return message


def _is_server_run(queue: str) -> bool:
    """
    Check if the given queue is running.
    """
    count = mongodb_services().query_count(query={BUILD.KEY_SERVICE_NAME: queue})
    return count > 0


def _gen_task_message(queue: str, message: dict, weight: int = TASK.DEFAULT_VALUE_TASK_WEIGHT) -> tuple[dict, dict]:
    """
    Generate a task message.
    """

    message = _task_required_field_check(message=message)
    body = {
        TASK.KEY_TASK_BODY: message,
        TASK.KEY_TASK_WEIGHT: weight,
        TASK.KEY_TASK_QUEUE_NAME: queue,
        TASK.KEY_TASK_IS_SUB_TASK: False,
        TASK.KEY_TASK_ID: message[TASK.KEY_TASK_ID],
        TASK.KEY_TASK_STATUS: TASK.KEY_TASK_WAIT_STATUS,
        TASK.KEY_TASK_IS_SUB_TASK_ALL_FINISH: False,
        TASK.KEY_TASK_CREATE_TIME: get_converted_time()
    }
    return body, message


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
    if _is_server_run(queue) is False:
        raise f"Server run is not supported {queue}"

    body, message = _gen_task_message(queue=queue, message=message, weight=weight)
    mongodb_task().update_many(query={TASK.KEY_TASK_ID: body[TASK.KEY_TASK_ID]}, update_data=body, upsert=True)
    return message[TASK.KEY_TASK_ID]


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
    if _is_server_run(queue) is False:
        raise f"Server run is not supported {queue}"

    body, message = _gen_task_message(queue=queue, message=message, weight=weight)

    rabbitmq_send_message(queue=queue, message=message)
    mongodb_task().update_many(query={TASK.KEY_TASK_ID: body[TASK.KEY_TASK_ID]}, update_data=body, upsert=True)
    return message[TASK.KEY_TASK_ID]


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
    if _is_server_run(subtask_queue) is False:
        raise f"Server run is not supported {subtask_queue}"

    subtask_ids = []
    for subtask in subtasks:
        message = _task_required_field_check(message=subtask)
        message[TASK.KEY_TASK_SOURCE_ID] = source_task_id
        body = {
            TASK.KEY_TASK_BODY: message,
            TASK.KEY_TASK_WEIGHT: TASK.DEFAULT_VALUE_TASK_WEIGHT,
            TASK.KEY_TASK_QUEUE_NAME: subtask_queue,
            TASK.KEY_TASK_SOURCE_ID: source_task_id,
            TASK.KEY_TASK_IS_SUB_TASK: True,
            TASK.KEY_TASK_ID: message[TASK.KEY_TASK_ID],
            TASK.KEY_TASK_STATUS: TASK.KEY_TASK_WAIT_STATUS,
            TASK.KEY_TASK_IS_SUB_TASK_ALL_FINISH: False,
            TASK.KEY_TASK_CREATE_TIME: get_converted_time()
        }
        subtask_ids.append(message[TASK.KEY_TASK_ID])
        mongodb_task().update_many(query={TASK.KEY_TASK_ID: body[TASK.KEY_TASK_ID]}, update_data=body, upsert=True)
    return subtask_ids


def query_task_by_task_id(task_id: str) -> dict:
    """
    Query the task data of the given task ID.
    Args:
        task_id (str): The ID of the task to query.
    Returns:
        dict: task data
    """
    data = mongodb_task().query_all(
        query={TASK.KEY_TASK_ID: task_id},
        field={'_id': 0}
    )
    data = [i for i in data]
    return data[0] if len(data) > 0 else {}


def query_worker_running_number(query: dict):
    """
    Query the number of running workers based on the given query.
    Args:
        query (dict): A dictionary containing the query criteria.
    Returns:
        tuple: A tuple containing the number of running workers and the maximum number of workers.
    """

    data = mongodb_services().query_all(
        query=query,
        field={
            '_id': 0,
            BUILD.KEY_WORKER_RUN_PROCESS: 1,
            BUILD.KEY_WORKER_MAX_PROCESS: 1
        }
    )
    if len(data) > 0:
        return len(data[0].get(BUILD.KEY_WORKER_RUN_PROCESS)), data[0].get(BUILD.KEY_WORKER_MAX_PROCESS)
    return 0, 0


def task_stop(task_id: str) -> None:
    """
    Stop the given task ID.
    """
    mongodb_task().update_many(
        query={TASK.KEY_TASK_ID: task_id},
        update_data={TASK.KEY_TASK_STATUS: TASK.KEY_TASK_STOP_STATUS}
    )
    mongodb_task().update_many(
        query={TASK.KEY_TASK_SOURCE_ID: task_id},
        update_data={TASK.KEY_TASK_STATUS: TASK.KEY_TASK_STOP_STATUS}
    )

    subtask_ids = mongodb_task().query_all(
        query={TASK.KEY_TASK_SOURCE_ID: task_id},
        field={TASK.KEY_TASK_ID: 1, '_id': 0}
    )

    for subtask_id in subtask_ids:
        redis_task().set_hash_value(
            subtask_id.get(TASK.KEY_TASK_ID),
            {TASK.KEY_TASK_STATUS: TASK.KEY_TASK_STOP_STATUS}, expire=604800)

    redis_task().set_hash_value(task_id, {TASK.KEY_TASK_STATUS: TASK.KEY_TASK_STOP_STATUS}, expire=604800)


def redis_get_task_status_by_task_id(task_id: str) -> str:
    """
    Get the status of the given task ID.
    Args:
        task_id (str): The ID of the task to get the status of.

    Returns:
        str: The status of the given task ID.
    """
    data = redis_task().get_hash_value(key=task_id)
    return data.get(TASK.KEY_TASK_STATUS)


def register():
    from astraflux.interface import databases_api
    databases_api.task_submit_databases = task_submit_databases
    databases_api.task_submit_databases_and_send = task_submit_databases_and_send
    databases_api.subtask_create = subtask_create
    databases_api.query_task_by_task_id = query_task_by_task_id
    databases_api.query_worker_running_number = query_worker_running_number
    databases_api.task_stop = task_stop
    databases_api.redis_get_task_status_by_task_id = redis_get_task_status_by_task_id

    import sys
    sys.modules['astraflux.interface.databases_api'] = databases_api
