# -*- coding: utf-8 -*-

from typing import TypeVar, Dict, Any

from astraflux.definitions.constants import *
from astraflux.interface.other import converted_time
from astraflux.interface.generate_id import snowflake_id
from astraflux.interface.redisdb import redis_scan_workers_by_service
from astraflux.interface.mongodb import mongodb_find_one_and_update_from_task

TaskData = TypeVar("TaskData", bound=Dict[str, Any])


def _ensure_task_id_exists(task_data: TaskData) -> TaskData:
    """
    Ensure a valid task ID exists in the task data (auto-generate if missing).

    Private helper function: Checks for a non-empty task ID in the input data. If missing or empty,
    generates a globally unique ID using the snowflake algorithm.

    Args:
        task_data (TaskData): Raw task data dictionary (business-related fields).

    Returns:
        TaskData: Task data dictionary with a valid task ID (existing or auto-generated).

    Notes:
        - Preserves all original business fields in `task_data`.
        - Uses `snowflake_id()` for ID generation (guarantees global uniqueness and time-ordering).
    """
    task_id = task_data.get(TASK.CONFIG.ID.value, None)
    if task_id is not None and task_id.strip() != "":
        return task_data

    task_data[TASK.CONFIG.ID.value] = snowflake_id()
    return task_data


def _is_queue_service_running(queue_name: str) -> bool:
    """
    Check if the service associated with the specified queue is running.

    Private helper function: Verifies service status by querying the MongoDB service collection.
    A service is considered "running" if it exists in the collection.

    Args:
        queue_name (str): Name of the target queue (maps to a specific service).

    Returns:
        bool: True if the service is running (exists in the collection), False otherwise.

    Notes:
        - Relies on the service collection being updated with active services.
        - Case-sensitive matching for `queue_name` (ensure consistency with service registration).
    """

    return True if redis_scan_workers_by_service(service_name=queue_name) else False


def _build_task_full_data(
        queue_name: str,
        task_data: TaskData,
        weight: int = TASK.DEFAULT.WEIGHT.value,
        source_id: str = TASK.DEFAULT.SOURCE_ID.value,
        resources: dict = TASK.DEFAULT.RESOURCES.value,
        depends_no: list[str] = TASK.DEFAULT.DEPENDS_ON.value,
) -> TaskData:
    """
    Constructs a complete task data dictionary by combining provided task data with system defaults.

    This internal function validates and enriches the provided task data with system-level metadata
    such as status, creation time, and organizational fields. It ensures the task has a valid ID
    and creates a standardized representation suitable for storage and processing.

    Args:
        queue_name: The name of the queue where the task will be submitted.
        task_data: The core task data containing business logic and configuration.
        weight: Task priority weight (higher values indicate higher priority).
               Defaults to system default weight.
        source_id: Identifier of the parent task if this is a subtask.
                  Empty string indicates no parent task. Defaults to system default.
        resources: Dictionary specifying resource requirements for task execution.
                  Includes keys: 'cpu_num', 'gpu_num', 'memory', 'gpu_memory', 'disk'.
                  All values are in megabytes except count fields. Defaults to system defaults.
        depends_no: List of task IDs that must complete before this task can execute.
                   Defaults to empty list.

    Returns:
        A complete TaskData dictionary containing both user-provided data and system metadata,
        ready for storage and processing.

    Note:
        This is an internal helper function and should not be called directly by application code.
    """

    task_data = _ensure_task_id_exists(task_data)

    full_task_data = {
        TASK.CONFIG.ID.value: task_data[TASK.CONFIG.ID.value],
        TASK.CONFIG.QUEUE_NAME.value: queue_name,
        TASK.CONFIG.BODY.value: task_data,
        TASK.CONFIG.STATUS.value: TASK.DEFAULT.STATUS.value,
        TASK.CONFIG.WEIGHT.value: weight,
        TASK.CONFIG.SOURCE_ID.value: source_id,
        TASK.CONFIG.RESOURCES.value: resources,
        TASK.CONFIG.DEPENDS_ON.value: depends_no,
        TASK.CONFIG.CREATE_TIME.value: converted_time()
    }
    return full_task_data


def task_submit(
        queue_name: str,
        task_data: TaskData,
        weight: int = TASK.DEFAULT.WEIGHT.value,
        resources: dict = TASK.DEFAULT.RESOURCES.value,
        depends_no: list[str] = TASK.DEFAULT.DEPENDS_ON.value,
) -> str:
    """
    Submits a single task to the specified queue for execution.

    Validates queue availability, constructs complete task data with metadata,
    and persists it to the database. Returns the unique identifier of the submitted task.

    Args:
        queue_name: The name of the target queue for task submission.
        task_data: Core task data containing execution logic and parameters.
        weight: Priority weight for task scheduling (higher = higher priority).
               Defaults to system default.
                  Empty string indicates standalone task. Defaults to system default.
        resources: Resource requirements dictionary with keys:
                  'cpu_num' (CPU core count),
                  'gpu_num' (GPU device count),
                  'memory' (system memory in MB),
                  'gpu_memory' (GPU memory in MB),
                  'disk' (storage space in MB).
                  Defaults to system defaults.
        depends_no: List of prerequisite task IDs that must complete successfully
                   before this task can start execution. Defaults to empty list.

    Returns:
        The unique string identifier of the submitted task.

    Raises:
        ValueError: If the specified queue service is not currently running.
    """

    if not _is_queue_service_running(queue_name):
        raise ValueError(f"Service for queue '{queue_name}' is not running")

    full_task_data = _build_task_full_data(
        queue_name=queue_name,
        task_data=task_data,
        weight=weight, resources=resources, depends_no=depends_no)

    mongodb_find_one_and_update_from_task(
        query={TASK.CONFIG.ID.value: task_data[TASK.CONFIG.ID.value]},
        data=full_task_data,
        upsert=True
    )

    return task_data[TASK.CONFIG.ID.value]


def subtask_batch_create(
        subtask_queue: str,
        subtask_list: list[TaskData],
        weight: int = TASK.DEFAULT.WEIGHT.value,
        source_id: str = TASK.DEFAULT.SOURCE_ID.value,
        resources: dict = TASK.DEFAULT.RESOURCES.value
) -> list[str]:
    """
    Creates and submits multiple subtasks in batch to the specified queue.

    Processes a list of subtask data, assigns them common properties (weight, parent, resources),
    and submits each to the database. All subtasks inherit the same source_id indicating
    they belong to the same parent task.

    Args:
        subtask_queue: The queue name where all subtasks will be submitted.
        subtask_list: List of dictionaries containing individual subtask data.
        weight: Priority weight applied to all subtasks in the batch.
               Defaults to system default.
        source_id: Identifier of the common parent task for all subtasks.
                  Defaults to system default (typically empty string).
        resources: Resource requirements applied uniformly to all subtasks.
                  Dictionary with keys: 'cpu_num', 'gpu_num', 'memory',
                  'gpu_memory', 'disk'. Defaults to system defaults.

    Returns:
        A list of unique string identifiers for all created subtasks, maintaining
        the same order as the input subtask_list.

    Raises:
        TypeError: If subtask_list is not a list.
        ValueError: If the specified subtask queue service is not running.
    """

    if not isinstance(subtask_list, list):
        raise TypeError(f"Expected 'subtask_list' to be List[Dict], got {type(subtask_list).__name__}")

    if not _is_queue_service_running(subtask_queue):
        raise ValueError(f"Service for subtask queue '{subtask_queue}' is not running")

    subtask_ids = []
    for subtask_data in subtask_list:
        subtask_data = _ensure_task_id_exists(subtask_data)

        full_task_data = _build_task_full_data(
            queue_name=subtask_queue,
            task_data=subtask_data,
            weight=weight, source_id=source_id, resources=resources)

        subtask_ids.append(subtask_data[TASK.CONFIG.ID.value])
        mongodb_find_one_and_update_from_task(
            query={TASK.CONFIG.ID.value: subtask_data[TASK.CONFIG.ID.value]},
            data=full_task_data,
            upsert=True
        )

    return subtask_ids
