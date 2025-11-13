# -*- encoding: utf-8 -*-
import time
from typing import Dict, List, Tuple, Optional, TypeVar, Any

from astraflux.definitions.constants import *
from astraflux.interface.snowflake import snowflake_id
from astraflux.interface.rabbitmq import rabbitmq_send_message
from astraflux.interface.utils import get_converted_time

from .mongodb import mongodb_get_task_collector, mongodb_get_service_collector
from .redisdb import redis_get_task_client

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
    task_id = task_data.get(DEFINITIONS.TASK.ID)
    if task_id is not None and task_id.strip() != "":
        return task_data

    task_data[DEFINITIONS.TASK.ID] = snowflake_id()
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

    _service_collector = mongodb_get_service_collector()
    count = 0

    while count < 10:
        service_count = _service_collector.count(query={DEFINITIONS.BUILD.SERVICE_NAME: queue_name})
        if service_count > 0:
            return True
        count += 1
        time.sleep(0.5)
    return False


def _build_task_full_data(queue_name: str, task_data: TaskData, weight: int = DefaultValues.TASK.WEIGHT) \
        -> Tuple[Dict[str, Any], TaskData]:
    """
    Build complete task data with system-level fields (for database storage).

    Private helper function: Supplements raw task data with system-generated fields (status, create time, etc.)
    to form a complete record ready for MongoDB insertion.

    Args:
        queue_name (str): Name of the queue the task belongs to.
        task_data (TaskData): Raw task data (already guaranteed to have a valid task ID).
        weight (int, optional): Task priority weight (higher = higher priority). Defaults to 
            `DefaultValues.TASK.WEIGHT` (typically 1).

    Returns:
        Tuple[Dict[str, Any], TaskData]:
            - First element: Complete task data (business fields + system fields).
            - Second element: Original task data (with valid task ID, unmodified).

    System Fields Added:
        - `DEFINITIONS.TASK.WEIGHT`: Task priority weight.
        - `DEFINITIONS.TASK.QUEUE_NAME`: Associated queue name.
        - `DEFINITIONS.TASK.IS_SUB_TASK`: Flag for subtask (always False for main tasks).
        - `DEFINITIONS.TASK.STATUS`: Initial status (`DEFINITIONS.STATUS.WAITING` = "waiting").
        - `DEFINITIONS.TASK.IS_SUB_TASK_ALL_FINISH`: Subtask completion flag (False initially).
        - `DEFINITIONS.TASK.CREATE_TIME`: Formatted creation timestamp (via `get_converted_time()`).
    """

    task_data = _ensure_task_id_exists(task_data)

    full_task_data = {
        DEFINITIONS.TASK.BODY: task_data,
        DEFINITIONS.TASK.WEIGHT: weight,
        DEFINITIONS.TASK.QUEUE_NAME: queue_name,
        DEFINITIONS.TASK.IS_SUB_TASK: False,
        DEFINITIONS.TASK.ID: task_data[DEFINITIONS.TASK.ID],
        DEFINITIONS.TASK.STATUS: DEFINITIONS.STATUS.WAITING,
        DEFINITIONS.TASK.IS_SUB_TASK_ALL_FINISH: False,
        DEFINITIONS.TASK.CREATE_TIME: get_converted_time()
    }
    return full_task_data, task_data


def task_submit_to_db(queue_name: str, task_data: TaskData, weight: int = DefaultValues.TASK.WEIGHT) -> str:
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
        weight (int, optional): Task priority weight. Defaults to `DefaultValues.TASK.WEIGHT` (1).

    Returns:
        str: Unique ID of the submitted task (stored in the database).

    Raises:
        ValueError: If the service associated with `queue_name` is not running.
    """

    if not _is_queue_service_running(queue_name):
        raise ValueError(f"Service for queue '{queue_name}' is not running")

    full_task_data, task_data = _build_task_full_data(queue_name, task_data, weight)

    _task_collector = mongodb_get_task_collector()
    _task_collector.update(
        query={DEFINITIONS.TASK.ID: full_task_data[DEFINITIONS.TASK.ID]},
        data=full_task_data,
        upsert=True
    )
    return task_data[DEFINITIONS.TASK.ID]


def task_submit_to_db_and_mq(queue_name: str, task_data: TaskData, weight: int = DefaultValues.TASK.WEIGHT) -> str:
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
        weight (int, optional): Task priority weight. Defaults to `DefaultValues.TASK.WEIGHT` (1).

    Returns:
        str: Unique ID of the submitted task (stored in DB and sent to MQ).

    Raises:
        ValueError: If the service associated with `queue_name` is not running.
    """
    if not _is_queue_service_running(queue_name):
        raise ValueError(f"Service for queue '{queue_name}' is not running")

    full_task_data, task_data = _build_task_full_data(queue_name, task_data, weight)

    rabbitmq_send_message(queue=queue_name, message=task_data)

    _task_collector = mongodb_get_task_collector()
    _task_collector.update(
        query={DEFINITIONS.TASK.ID: full_task_data[DEFINITIONS.TASK.ID]},
        data=full_task_data,
        upsert=True
    )
    return task_data[DEFINITIONS.TASK.ID]


def subtask_batch_create(source_task_id: str, subtask_queue: str, subtask_list: List[TaskData]) -> List[str]:
    """
    Batch create subtasks and save to the database (linked to a parent task).

    Core Functionality:
        Generates multiple subtasks from a list of raw data, links them to a parent task via `source_task_id`,
        and persists all subtasks to MongoDB. Returns a list of subtask IDs for tracking.

    Key Features:
        - Auto-generates subtask IDs (if missing).
        - Links subtasks to the parent task via `DEFINITIONS.TASK.SOURCE_ID`.
        - Sets initial status to "waiting" and marks as subtasks (`DEFINITIONS.TASK.IS_SUB_TASK` = True).

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

    if not isinstance(subtask_list, list):
        raise TypeError(f"Expected 'subtask_list' to be List[Dict], got {type(subtask_list).__name__}")

    if not _is_queue_service_running(subtask_queue):
        raise ValueError(f"Service for subtask queue '{subtask_queue}' is not running")

    subtask_ids = []
    for subtask_data in subtask_list:
        subtask_data = _ensure_task_id_exists(subtask_data)

        subtask_data[DEFINITIONS.TASK.SOURCE_ID] = source_task_id

        full_subtask_data = {
            DEFINITIONS.TASK.BODY: subtask_data,
            DEFINITIONS.TASK.WEIGHT: DefaultValues.TASK.WEIGHT,
            DEFINITIONS.TASK.QUEUE_NAME: subtask_queue,
            DEFINITIONS.TASK.SOURCE_ID: source_task_id,
            DEFINITIONS.TASK.IS_SUB_TASK: True,
            DEFINITIONS.TASK.ID: subtask_data[DEFINITIONS.TASK.ID],
            DEFINITIONS.TASK.STATUS: DEFINITIONS.STATUS.WAITING,
            DEFINITIONS.TASK.IS_SUB_TASK_ALL_FINISH: False,
            DEFINITIONS.TASK.CREATE_TIME: get_converted_time()
        }

        subtask_ids.append(subtask_data[DEFINITIONS.TASK.ID])

        _task_collector = mongodb_get_task_collector()
        _task_collector.update(
            query={DEFINITIONS.TASK.ID: full_subtask_data[DEFINITIONS.TASK.ID]},
            data=full_subtask_data,
            upsert=True
        )
    return subtask_ids


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

    _task_collector = mongodb_get_task_collector()
    task_data = _task_collector.find_one(
        query={DEFINITIONS.TASK.ID: task_id},
        fields={'_id': 0}
    )

    return task_data if task_data is not None else {}


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

    _service_collector = mongodb_get_service_collector()
    service_data = _service_collector.find_one(
        query=query,
        fields={
            '_id': 0,
            DEFINITIONS.BUILD.WORKER_RUN_PROCESS: 1,
            DEFINITIONS.BUILD.WORKER_MAX_PROCESS: 1
        }
    )
    if not service_data:
        return 0, 0

    running_processes = service_data.get(DEFINITIONS.BUILD.WORKER_RUN_PROCESS, [])
    max_processes = service_data.get(DEFINITIONS.BUILD.WORKER_MAX_PROCESS, 0)
    return len(running_processes), max_processes


def task_and_subtasks_stop(task_id: str, expire_seconds: int = 604800) -> None:
    """
    Stop a main task and all its associated subtasks (update status to "stopped").

    Core Functionality:
        1. Updates the main task's status to `DEFINITIONS.STATUS.STOPPED` in MongoDB.
        2. Updates all subtasks linked via `DEFINITIONS.TASK.SOURCE_ID` to "stopped" in MongoDB.
        3. Syncs the "stopped" status to Redis cache (with configurable expiration) for fast querying.

    Args:
        task_id (str): ID of the main task to stop (subtasks linked to this ID will also be stopped).
        expire_seconds (int, optional): Expiration time for Redis cache (in seconds). Defaults to 604800 (7 days).
            Use 0 to disable expiration (not recommended for temporary statuses).

    Notes:
        - This operation is idempotent: stopping an already stopped task/subtask has no effect.
        - Redis cache is updated to ensure consistency between DB and cache for status queries.
    """
    stop_status = {DEFINITIONS.TASK.STATUS: DEFINITIONS.STATUS.STOPPED}

    _task_collector = mongodb_get_task_collector()
    _task_collector.update(
        query={DEFINITIONS.TASK.ID: task_id},
        data=stop_status
    )

    _task_collector.update(
        query={DEFINITIONS.TASK.SOURCE_ID: task_id},
        data=stop_status
    )

    subtask_id_records = _task_collector.find(
        query={DEFINITIONS.TASK.SOURCE_ID: task_id},
        fields={DEFINITIONS.TASK.ID: 1, '_id': 0}
    )

    _redis_task_client = redis_get_task_client()
    for record in subtask_id_records:
        subtask_id = record.get(DEFINITIONS.TASK.ID)
        if subtask_id:
            _redis_task_client.hash_set(
                key=subtask_id,
                field_values=stop_status,
                expire_seconds=expire_seconds
            )

    _redis_task_client.hash_set(
        key=task_id,
        field_values=stop_status,
        expire_seconds=expire_seconds
    )


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

    _redis_task_client = redis_get_task_client()
    task_cache = _redis_task_client.hash_get(key=task_id)
    return task_cache.get(DEFINITIONS.TASK.STATUS)


def update_service(query: dict, update_data: dict, upsert: bool = True):
    """
      Update service information in the MongoDB service collection.

      This function provides an interface to update existing service records
      or create new ones if they don't exist. It's commonly used for:
      - Updating service status and health information
      - Modifying service configuration parameters
      - Tracking service instance lifecycle changes

      Args:
          query (dict): MongoDB query filter to select the service document(s) to update.

          update_data (dict): The data to update in the matched service document(s).
                             Can include both field updates and operations like $set, $push, etc.

          upsert (bool, optional): If True, creates a new document when no document matches the query.
                                  Defaults to True to prevent accidental document creation.

      Returns:
          None: This function doesn't return any value but may raise exceptions on database errors.

      Raises:
          pymongo.errors.PyMongoError: If there's an issue with the MongoDB operation.
          ValueError: If query or update_data parameters are invalid.
      """
    _service_collector = mongodb_get_service_collector()
    _service_collector.update(query=query, data=update_data, upsert=upsert)


def update_task(query: dict, update_data: dict, upsert: bool = True):
    """
      Update task information in the MongoDB task collection.

      This function provides an interface to update existing task records
      or create new ones if they don't exist. It's commonly used for:
      - Updating task status and health information
      - Modifying task configuration parameters
      - Tracking task instance lifecycle changes

      Args:
          query (dict): MongoDB query filter to select the task document(s) to update.

          update_data (dict): The data to update in the matched task document(s).
                             Can include both field updates and operations like $set, $push, etc.

          upsert (bool, optional): If True, creates a new document when no document matches the query.
                                  Defaults to True to prevent accidental document creation.

      Returns:
          None: This function doesn't return any value but may raise exceptions on database errors.

      Raises:
          pymongo.errors.PyMongoError: If there's an issue with the MongoDB operation.
          ValueError: If query or update_data parameters are invalid.
      """
    _task_collector = mongodb_get_task_collector()
    _task_collector.update(query=query, data=update_data, upsert=upsert)


def update_running_worker(name: str, ipaddr: str, pid: int, action: str = 'push'):
    """
    Update running worker information in the MongoDB worker collection.
    Args:
        name: worker name
        ipaddr: worker ip address
        pid: worker pid
        action: push / pull
    """
    _service_collector = mongodb_get_service_collector()
    query = {
        DEFINITIONS.BUILD.WORKER_NAME: name,
        DEFINITIONS.BUILD.WORKER_IPADDR: ipaddr,
    }
    data = {DEFINITIONS.BUILD.WORKER_RUN_PROCESS: pid}

    if action == 'push':
        _service_collector.array_push(query=query, data=data)
    else:
        _service_collector.array_pull(query=query, data=data)


def task_find_paginated(
        query: Dict[str, Any],
        fields: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        skip: int = 0,
        sort_field: str = 'create_time',
        sort_order: int = -1
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Performs a paginated query on the task collection to retrieve filtered task records with pagination support.

    This function provides a convenient wrapper for paginated data retrieval from the task database collection.
    It supports filtering via a query dictionary, field projection to select specific fields, result limiting,
    offset-based pagination (skip), and customizable sorting. The return value includes both the total count
    of matching records (for pagination metadata) and the list of tasks for the current page.

    Args:
        query: A MongoDB query filter dictionary to specify which tasks to retrieve.
            Example: {"status": "completed", "priority": {"$gte": 2}}
            (Follows MongoDB query syntax: https://www.mongodb.com/docs/manual/tutorial/query-documents/)
        fields: Optional projection dictionary to specify which fields to include/exclude in the result.
            - Include fields: {"_id": 1, "name": 1, "status": 1}
            - Exclude fields: {"_id": 0, "description": 0}
            Defaults to None, which returns all fields.
        limit: Maximum number of task records to return per page. Must be a non-negative integer.
            Defaults to 10. Use 0 with caution (may return all matching records if allowed by the collection).
        skip: Number of task records to skip before returning results (for offset-based pagination).
            Defaults to 0 (starts from the first matching record). Use cautiously with large values (can impact performance).
        sort_field: Name of the field to sort the results by. Must be a valid field in the task collection.
            Defaults to 'create_time' (common use case for chronological sorting).
        sort_order: Sort direction. Use 1 for ascending order (A→Z, oldest→newest) and -1 for descending order (Z→A, newest→oldest).
            Defaults to -1 (descending order, e.g., newest tasks first when sorting by 'create_time').

    Returns:
        A tuple containing two elements:
            1. Total count (int): Number of task records that match the query (across all pages).
            2. Task list (List[Dict[str, Any]]): List of task records for the current page, formatted as dictionaries
               (each dictionary represents a task with selected fields).

    Dependencies:
        - Relies on the `mongodb_get_task_collector()` function to retrieve the MongoDB task collection instance.
        - The task collection must implement a `find_paginated()` method that accepts the same parameters
          and returns the (total_count, results_list) tuple.

    Example Usage:
        # Get 20 completed tasks (page 2, 10 per page), sorted by priority (high to low), include specific fields
        query = {"status": "completed"}
        fields = {"_id": 1, "name": 1, "priority": 1, "completed_at": 1}
        total_tasks, current_page_tasks = task_find_paginated(
            query=query,
            fields=fields,
            limit=20,
            skip=20,  # Skip first 20 tasks (page 1), get page 2
            sort_field="priority",
            sort_order=-1
        )
        print(f"Total completed tasks: {total_tasks}")
        print(f"Page 2 tasks: {current_page_tasks}")

    Notes:
        - For large collections, consider using cursor-based pagination instead of offset-based (skip) for better performance.
        - Ensure the `sort_field` is indexed in the MongoDB collection to optimize sorting performance.
        - The `fields` parameter follows MongoDB projection rules (cannot mix include/exclude except for _id).
    """
    _task_collector = mongodb_get_task_collector()

    return _task_collector.find_paginated(
        query=query,
        fields=fields,
        limit=limit,
        skip=skip,
        sort_field=sort_field,
        sort_order=sort_order
    )


def find_services(
        query: Dict[str, Any],
        fields: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves a list of service records from the MongoDB service collection based on the specified query and field projection.

    This function acts as a wrapper for MongoDB's find operation on the service collection, providing a clean,
    reusable interface to fetch service data. It supports filtering results with a query dictionary and selecting
    specific fields to include or exclude, adhering to MongoDB's query and projection syntax.

    Args:
        query: A MongoDB-compatible filter dictionary to specify which service records to retrieve.
            Defines conditions that services must satisfy to be included in the result.
            Example 1: Fetch active services → {"status": "active"}
            Example 2: Fetch services with specific tags → {"tags": {"$in": ["api", "microservice"]}}
            Example 3: Fetch services created after a date → {"created_at": {"$gt": datetime(2024, 1, 1)}}
            For full syntax: https://www.mongodb.com/docs/manual/tutorial/query-documents/

        fields: Optional projection dictionary to control which fields are included in the returned service records.
            - Include specific fields (explicitly set to 1, _id is included by default):
              {"_id": 1, "name": 1, "host": 1, "port": 1}
            - Exclude specific fields (explicitly set to 0, cannot mix with include except for _id):
              {"_id": 0, "internal_metadata": 0, "credentials": 0}
            Defaults to None, which returns all fields of matching service records.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a service record that matches
        the query. Each dictionary contains key-value pairs corresponding to the service's fields (filtered by the
        `fields` parameter if provided). Returns an empty list if no services match the query.

    Dependencies:
        - Requires the `mongodb_get_service_collector()` helper function, which must return a valid MongoDB collection
          instance for the service data store (handles connection pooling, authentication, and collection selection).
        - The underlying MongoDB collection must support the `find()` method with standard query and projection parameters.

    Example Usage:
        # 1. Fetch all active services, including only name, host, and port
        active_services = find_services(
            query={"status": "active"},
            fields={"name": 1, "host": 1, "port": 1}
        )
        print("Active services:", active_services)

        # 2. Fetch services with type "database" and exclude internal metadata
        db_services = find_services(
            query={"type": "database"},
            fields={"_id": 1, "name": 1, "type": 1, "internal_metadata": 0}
        )
        print("Database services:", db_services)

        # 3. Fetch all services (no filter), return all fields
        all_services = find_services(query={})
        print("All services count:", len(all_services))

    Notes:
        - Field projection rules: MongoDB does not allow mixing inclusion (1) and exclusion (0) except for the _id field.
          For example: {"name": 1, "host": 0} is invalid, but {"_id": 0, "name": 1} is valid.
        - For large result sets, consider adding pagination (limit/skip) or cursor-based iteration to avoid memory issues.
        - Ensure frequently queried fields (e.g., "status", "type") are indexed in MongoDB for improved performance.
        - The function does not handle exceptions (e.g., database connection errors, invalid query syntax) —
          error handling should be implemented at the call site if needed.
    """

    service_collection = mongodb_get_service_collector()
    return list(service_collection.find(query=query, fields=fields))


def register():
    import sys
    from astraflux.interface import data_access
    data_access.task_submit_to_db = task_submit_to_db
    data_access.task_submit_to_db_and_mq = task_submit_to_db_and_mq
    data_access.subtask_batch_create = subtask_batch_create
    data_access.task_get_by_id = task_get_by_id
    data_access.worker_get_running_and_max_count = worker_get_running_and_max_count
    data_access.task_and_subtasks_stop = task_and_subtasks_stop
    data_access.task_status_get_from_redis = task_status_get_from_redis
    data_access.update_service = update_service
    data_access.update_task = update_task
    data_access.update_running_worker = update_running_worker
    data_access.task_find_paginated = task_find_paginated
    data_access.find_services = find_services

    if REPLACE_SYS_MODULE:
        sys.modules['astraflux.interface.data_access'] = data_access
