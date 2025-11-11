# -*- encoding: utf-8 -*-

from typing import Dict, List, Tuple, Optional, TypeVar, Any

from astraflux.definitions.constants import *

TaskData = TypeVar("TaskData", bound=Dict[str, Any])


def task_submit_to_db(queue_name: str, task_data: TaskData, weight: int = DefaultValues.TASK.TASK_WEIGHT) -> str:
    """
    Submit a task to the database (persist only, no message queue dispatch).

    Core Functionality:
        1. Validate that the queue's associated service is running.
        2. Build complete task data with system fields.
        3. Insert/update the task in MongoDB (upsert: create if missing, update if exists).
        4. Return the task ID for tracking.

    Use Case:
        Suitable for scenarios where task data needs to be persisted but execution does not need to be triggered immediately.

    Args:
        queue_name (str): Target queue name (maps to a running service).
        task_data (TaskData): Business-related task data (e.g., {"param1": "value1", "param2": 123}).
        weight (int, optional): Task priority weight. Defaults to `TASK.DEFAULT_VALUE_TASK_WEIGHT` (1).

    Returns:
        str: Unique ID of the submitted task (stored in the database).

    Raises:
        ValueError: If the service associated with `queue_name` is not running.
    """
    return task_submit_to_db(queue_name, task_data, weight)


def task_submit_to_db_and_mq(queue_name: str, task_data: TaskData, weight: int = DefaultValues.TASK.TASK_WEIGHT) -> str:
    """
    Submit a task to the database and dispatch to RabbitMQ (triggers execution).

    Core Functionality:
        Combines database persistence with message queue dispatch to immediately trigger task execution.
        Follows the same validation and data-building logic as `task_submit_to_db`, plus MQ publishing.

    Use Case:
        Primary method for submitting tasks that need to be executed immediately by workers listening to the queue.

    Args:
        queue_name (str): Target queue name (must have a running service/worker).
        task_data (TaskData): Business-related task data (e.g., {"action": "send_email", "recipient": "user@example.com"}).
        weight (int, optional): Task priority weight. Defaults to `TASK.DEFAULT_VALUE_TASK_WEIGHT` (1).

    Returns:
        str: Unique ID of the submitted task (stored in DB and sent to MQ).

    Raises:
        ValueError: If the service associated with `queue_name` is not running.
    """
    return task_submit_to_db_and_mq(queue_name, task_data, weight)


def subtask_batch_create(source_task_id: str, subtask_queue: str, subtask_list: List[TaskData]) -> List[str]:
    """
    Batch create subtasks and save to the database (linked to a parent task).

    Core Functionality:
        Generates multiple subtasks from a list of raw data, links them to a parent task via `source_task_id`,
        and persists all subtasks to MongoDB. Returns a list of subtask IDs for tracking.

    Key Features:
        - Auto-generates subtask IDs (if missing).
        - Links subtasks to the parent task via `DEFINITIONS.TASK.TASK_SOURCE_ID`.
        - Sets initial status to "waiting" and marks as subtasks (`DEFINITIONS.TASK.TASK_IS_SUB_TASK` = True).

    Args:
        source_task_id (str): ID of the parent task (subtasks are linked to this ID).
        subtask_queue (str): Queue name for subtask execution (must have a running service).
        subtask_list (List[TaskData]): List of raw subtask data (each element is a business data dict).

    Returns:
        List[str]: List of unique IDs for the created subtasks.

    Raises:
        ValueError: If the service associated with `subtask_queue` is not running.
        TypeError: If `subtask_list` is not a list (expected List[TaskData]).
    """
    return subtask_batch_create(source_task_id, subtask_queue, subtask_list)


def task_get_by_id(task_id: str) -> Dict[str, Any]:
    """
    Retrieve task details by task ID from the database.

    Core Functionality:
        Queries MongoDB for a task with the specified ID and returns the complete task data (excluding MongoDB's default `_id` field).
        Returns an empty dict if no matching task is found (avoids None-related errors).

    Args:
        task_id (str): Unique ID of the task to retrieve.

    Returns:
        Dict[str, Any]: Complete task data (business + system fields) if found; empty dict otherwise.
    """
    return task_get_by_id(task_id)


def worker_get_running_and_max_count(query: Dict[str, Any]) -> Tuple[int, int]:
    """
    Query the number of running worker processes and the maximum allowed processes.

    Core Functionality:
        Retrieves worker status from the MongoDB service collection using the provided query.
        Returns the count of currently running processes and the maximum allowed processes for the matching service.

    Args:
        query (Dict[str, Any]): Query criteria to filter services (e.g., {"service_name": "data_worker"}).

    Returns:
        Tuple[int, int]:
            - First element: Number of running worker processes (length of `BUILD.KEY_WORKER_RUN_PROCESS` list).
            - Second element: Maximum allowed worker processes (`BUILD.KEY_WORKER_MAX_PROCESS`).
            Returns (0, 0) if no matching service is found.

    """
    return worker_get_running_and_max_count(query)


def task_and_subtasks_stop(task_id: str, expire_seconds: int = 604800) -> None:
    """
    Stop a main task and all its associated subtasks (update status to "stopped").

    Core Functionality:
        1. Updates the main task's status to `DEFINITIONS.TASK.TASK_STOP_STATUS` in MongoDB.
        2. Updates all subtasks linked via `DEFINITIONS.TASK.TASK_SOURCE_ID` to "stopped" in MongoDB.
        3. Syncs the "stopped" status to Redis cache (with configurable expiration) for fast querying.

    Args:
        task_id (str): ID of the main task to stop (subtasks linked to this ID will also be stopped).
        expire_seconds (int, optional): Expiration time for Redis cache (in seconds). Defaults to 604800 (7 days).
            Use 0 to disable expiration (not recommended for temporary statuses).

    Notes:
        - This operation is idempotent: stopping an already stopped task/subtask has no effect.
        - Redis cache is updated to ensure consistency between DB and cache for status queries.
    """
    return task_and_subtasks_stop(task_id, expire_seconds)


def task_status_get_from_redis(task_id: str) -> Optional[str]:
    """
    Retrieve task status from Redis cache (cache-first query for performance).

    Core Functionality:
        Queries Redis cache for the task's status (faster than MongoDB for frequent status checks).
        Returns None if the task status is not found in cache (caller may fall back to `task_get_by_id`).

    Use Case:
        Optimized for high-frequency status queries (e.g., frontend task progress tracking).

    Args:
        task_id (str): ID of the task to query status for.

    Returns:
        Optional[str]: Task status (e.g., "waiting", "running", "stopped") if found in cache; None otherwise.

    Notes:
        - Cache is populated when the task is stopped (via `task_and_subtasks_stop`) or updated elsewhere.
        - For guaranteed accuracy (e.g., after task completion), use `task_get_by_id` to query MongoDB directly.

    """
    return task_status_get_from_redis(task_id)
