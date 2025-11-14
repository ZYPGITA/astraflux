# -*- encoding: utf-8 -*-


from astraflux.definitions.constants import *
from typing import Dict, List, Tuple, Optional, TypeVar, Any

TaskData = TypeVar("TaskData", bound=Dict[str, Any])


class MongoDBCollector:
    """
    MongoDB Collection Operation Wrapper Class.

    This class encapsulates core CRUD (Create, Read, Update, Delete) operations for MongoDB collections,
    supports array manipulation (push/pull), and implements instance caching by collection name to avoid
    redundant connections and improve performance.

    Subclasses must specify the `_collection_name` class attribute to bind to a specific MongoDB collection.
    """

    def update(self, query: Dict, data: Dict, upsert: bool = False) -> None:
        """
        Update Multiple Documents Matching the Query.

        Uses MongoDB's $set operator to update specified fields without overwriting the entire document.
        Supports upsert (insert new document if no match is found).

        Args:
            query (Dict): Query filter to match target documents (e.g., {"task_id": "123456"}).
            data (Dict): Fields to update (e.g., {"status": "completed", "update_time": "2024-01-01"}).
            upsert (bool, optional): Whether to insert a new document if no match exists. Defaults to False.

        Returns:
            None
        """

    def array_push(self, query: Dict, data: Dict, single: bool = False, upsert: bool = False) -> None:
        """
        Push Data to Array Fields in Documents.

        Uses MongoDB's $push operator to add elements to array-type fields. Supports single or multiple documents.

        Args:
            query (Dict): Query filter to match target documents (e.g., {"user_id": "789"}).
            data (Dict): Array fields and values to push (e.g., {"tags": "urgent", "subtasks": {"id": "sub_1"}}).
            single (bool, optional): Whether to update only the first matching document. Defaults to False (update all).
            upsert (bool, optional): Whether to insert a new document if no match exists. Defaults to False.

        Returns:
            None
        """

    def array_pull(self, query: Dict, data: Dict, single: bool = True) -> None:
        """
        Remove Data from Array Fields in Documents.

        Uses MongoDB's $pull operator to remove elements from array-type fields. Supports single or multiple documents.

        Args:
            query (Dict): Query filter to match target documents (e.g., {"user_id": "789"}).
            data (Dict): Array fields and values to remove (e.g., {"tags": "urgent", "subtasks": {"id": "sub_1"}}).
            single (bool, optional): Whether to update only the first matching document.
                Defaults to True (update first).

        Returns:
            None
        """

    def insert(self, data: Dict) -> None:
        """
        Insert a Single Document into the Collection.

        Adds a new document to the target collection. The document must be a valid MongoDB BSON-serializable dict.

        Args:
            data (Dict): Document to insert (e.g., {"task_id": "123", "name": "Task A", "status": "pending"}).

        Returns:
            None
        """

    def delete(self, query: Dict) -> None:
        """
        Delete Multiple Documents Matching the Query.

        Removes all documents that match the query filter. Use with caution to avoid accidental data loss.

        Args:
            query (Dict): Query filter to match documents to delete (e.g., {"expired": True}).

        Returns:
            None
        """

    def find(self, query: Dict, fields: Dict = None) -> List[Dict]:
        """
        Query All Documents Matching the Filter.

        Retrieves all documents that satisfy the query, with optional field projection to include/exclude fields.

        Args:
            query (Dict): Query filter (e.g., {"status": "running"}). Use {} to retrieve all documents.
            fields (Dict, optional): Field projection (e.g., {"_id": 0, "task_id": 1, "status": 1}).
                - 1: Include the field
                - 0: Exclude the field (cannot mix 1 and 0 except for _id)
                Defaults to None (return all fields).

        Returns:
            List[Dict]: List of matching documents (empty list if no matches).
        """

    def find_one(self, query: Dict, fields: Dict = None) -> Optional[Dict]:
        """
        Query a Single Document Matching the Filter.

        Retrieves the first document that matches the query filter (ordered by insertion time by default).

        Args:
            query (Dict): Query filter (e.g., {"task_id": "123456"}).
            fields (Dict, optional): Field projection (same as `find` method). Defaults to None.

        Returns:
            Optional[Dict]: Matching document (None if no match is found).
        """

    def count(self, query: Dict) -> int:
        """
        Count Documents Matching the Query.

        Returns the total number of documents that satisfy the query filter (supports large collections efficiently).

        Args:
            query (Dict): Query filter (e.g., {"queue": "task_queue_1"}). Use {} to count all documents.

        Returns:
            int: Number of matching documents.
        """

    def find_paginated(self, query: Dict, fields: Dict = None, limit: int = 10, skip: int = 0,
                       sort_field: str = 'create_time', sort_order: int = -1) -> Tuple[int, List[Dict]]:
        """
        Paginated Query with Sorting.

        Retrieves a paginated subset of documents with specified sorting, returns total count and current page data.
        Ideal for large datasets to avoid loading all documents at once.

        Args:
            query (Dict): Query filter (e.g., {"status": "completed"}).
            fields (Dict, optional): Field projection. Defaults to None.
            limit (int, optional): Maximum number of documents per page. Defaults to 10.
            skip (int, optional): Number of documents to skip (for pagination). Defaults to 0 (first page).
            sort_field (str, optional): Field to sort by (e.g., "create_time", "priority"). Defaults to 'create_time'.
            sort_order (int, optional): Sort direction:
                - 1: Ascending (from oldest to newest)
                - -1: Descending (from newest to oldest)
                Defaults to -1.

        Returns:
            Tuple[int, List[Dict]]:
                - First element: Total number of matching documents (for pagination controls)
                - Second element: List of documents for the current page
        """


def task_submit_to_db(queue_name: str, task_data: TaskData, weight: int = DefaultValues.TASK.WEIGHT) -> str:
    """
    Submit a task to the database (persist only, no message queue dispatch).

    Core Functionality:
        1. Validate that the queue's associated service is running.
        2. Build complete task data with system fields.
        3. Insert/update the task in MongoDB (upsert: create if missing, update if exists).
        4. Return the task ID for tracking.

    Use Case:
        Suitable for scenarios where task data needs to be persisted but execution does
            not need to be triggered immediately.

    Args:
        queue_name (str): Target queue name (maps to a running service).
        task_data (TaskData): Business-related task data (e.g., {"param1": "value1", "param2": 123}).
        weight (int, optional): Task priority weight. Defaults to `DefaultValues.TASK.WEIGHT` (1).

    Returns:
        str: Unique ID of the submitted task (stored in the database).

    Raises:
        ValueError: If the service associated with `queue_name` is not running.
    """

    return task_submit_to_db(queue_name=queue_name, task_data=task_data, weight=weight)


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
        task_data (TaskData): Business-related task data
            (e.g., {"action": "send_email", "recipient": "user@example.com"}).
        weight (int, optional): Task priority weight. Defaults to `DefaultValues.TASK.WEIGHT` (1).

    Returns:
        str: Unique ID of the submitted task (stored in DB and sent to MQ).

    Raises:
        ValueError: If the service associated with `queue_name` is not running.
    """
    return task_submit_to_db_and_mq(queue_name=queue_name, task_data=task_data, weight=weight)


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

    return subtask_batch_create(source_task_id=source_task_id, subtask_queue=subtask_queue, subtask_list=subtask_list)


def task_get_by_id(task_id: str) -> Dict[str, Any]:
    """
    Retrieve task details by task ID from the database.

    Core Functionality:
        Queries MongoDB for a task with the specified ID and returns the complete task data
            (excluding MongoDB's default `_id` field).
        Returns an empty dict if no matching task is found (avoids None-related errors).

    Args:
        task_id (str): Unique ID of the task to retrieve.

    Returns:
        Dict[str, Any]: Complete task data (business + system fields) if found; empty dict otherwise.
    """

    return task_get_by_id(task_id=task_id)


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

    return worker_get_running_and_max_count(query=query)


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
    return task_and_subtasks_stop(task_id=task_id, expire_seconds=expire_seconds)


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

    return task_status_get_from_redis(task_id=task_id)


def update_running_worker(name: str, ipaddr: str, pid: int, action: str = 'push'):
    """
    Update running worker information in the MongoDB worker collection.
    Args:
        name: worker name
        ipaddr: worker ip address
        pid: worker pid
        action: push / pull
    """
    return update_running_worker(name=name, ipaddr=ipaddr, pid=pid, action=action)


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
            Defaults to 0 (starts from the first matching record). Use cautiously with large values
                (can impact performance).
        sort_field: Name of the field to sort the results by. Must be a valid field in the task collection.
            Defaults to 'create_time' (common use case for chronological sorting).
        sort_order: Sort direction. Use 1 for ascending order (A→Z, oldest→newest) and -1 for descending order
            (Z→A, newest→oldest).
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
        - For large collections, consider using cursor-based pagination instead of offset-based
            (skip) for better performance.
        - Ensure the `sort_field` is indexed in the MongoDB collection to optimize sorting performance.
        - The `fields` parameter follows MongoDB projection rules (cannot mix include/exclude except for _id).
    """
    return task_find_paginated(
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
    Retrieves a list of service records from the MongoDB service collection based on the specified query
        and field projection.

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
        - The underlying MongoDB collection must support the `find()` method with standard query
            and projection parameters.

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
        - Field projection rules: MongoDB does not allow mixing inclusion (1) and exclusion (0)
            except for the _id field.
          For example: {"name": 1, "host": 0} is invalid, but {"_id": 0, "name": 1} is valid.
        - For large result sets, consider adding pagination (limit/skip) or cursor-based iteration
            to avoid memory issues.
        - Ensure frequently queried fields (e.g., "status", "type") are indexed in MongoDB for improved performance.
        - The function does not handle exceptions (e.g., database connection errors, invalid query syntax) —
          error handling should be implemented at the call site if needed.
    """

    return find_services(query=query, fields=fields)


def task_collector() -> MongoDBCollector:
    """
    Get Instance of TaskMongoDBCollector.

    Provides global access to the task collection operation wrapper.

    Returns:
        MongoDBCollector: Instance of TaskMongoDBCollector for task collection operations.
    """
    return task_collector()


def service_collector() -> MongoDBCollector:
    """
    Get Instance of ServiceMongoDBCollector.

    Provides global access to the service collection operation wrapper.

    Returns:
        MongoDBCollector: Instance of ServiceMongoDBCollector for service collection operations.
    """
    return service_collector()


def node_collector() -> MongoDBCollector:
    """
    Get Instance of NodeMongoDBCollector.

    Provides global access to the node collection operation wrapper.

    Returns:
        MongoDBCollector: Instance of NodeMongoDBCollector for node collection operations.
    """
    return node_collector()
