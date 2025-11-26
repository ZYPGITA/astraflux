# -*- encoding: utf-8 -*-
import json
import redis
from typing import Dict, Any

from astraflux.definitions.constants import *
from astraflux.interface.definitions import get_redis_uri, get_global_config


class RedisHashClient:
    """
    Redis Hash Data Structure Operation Client.

    Core Purpose:
        Encapsulates core operations for Redis hash data structures, focusing on storage and querying
        of key-field-value sets. Supports expiration time management and binds to different Redis
        databases (via DB index) for business module isolation (task/service).

    Design Principles:
        - Each business module maps to an independent Redis database (isolated by DB index) to avoid data conflicts.
        - Instance caching by DB index ensures connection pool reuse for the same database, improving performance.
        - Only retains hash-related core operations;
            removes redundant functionality to align with actual business needs.
    """
    _instance_map: Dict[int, 'RedisHashClient'] = {}

    def __new__(cls, db_index: int):
        """
        Singleton Pattern Implementation by Redis DB Index.

        Logic Explanation:
            1. Different DB indexes correspond to different instances (ensures data isolation).
            2. Reuses instances for the same DB index to avoid redundant connection pool creation.

        Args:
            db_index (int): Redis database index (e.g., 0 for task cache, 1 for service cache).

        Returns:
            RedisHashClient: Cached or newly created instance for the target DB index.
        """
        if db_index not in cls._instance_map:
            instance = super().__new__(cls)
            cls._instance_map[db_index] = instance
        return cls._instance_map[db_index]

    def __init__(self, db_index: int):
        """
        Initialize Redis Connection (Bind to Specified Database).

        Args:
            db_index (int): Redis database index to bind (e.g., 0 for tasks, 1 for services).

        Notes:
            Uses connection pool for efficient connection reuse. Initialization is skipped for cached instances.
        """
        if not hasattr(self, '_client_initialized'):
            redis_uri = get_redis_uri()
            full_uri = f"{redis_uri}/{db_index}"
            self._pool = redis.ConnectionPool.from_url(url=full_uri)
            self._client = redis.Redis(connection_pool=self._pool)
            self._client_initialized = True

    def hash_set(self, key: str, field_values: Dict[str, Any], expire_seconds: int = 0) -> None:
        """
        Set Fields and Values for a Redis Hash Key (Supports Expiration).

        Functionality:
            Batch sets multiple field-value pairs for a Redis hash key (replaces deprecated `hmset`).
            Optional expiration time (takes effect only if expire_seconds > 0).

        Args:
            key (str): Redis hash key (e.g., "task:123456", "service:789").
            field_values (Dict[str, Any]): Dictionary of field-value pairs to set
                (e.g., {"status": "stopped", "update_time": "2024-01-01"}).
            expire_seconds (int, optional): Expiration time in seconds. Defaults to 0 (no expiration).

        Notes:
            - Values are automatically serialized to Redis-compatible format (supports str, int, float, etc.).
            - Overwrites existing fields with the same name; preserves unmentioned fields.
        """

        self._client.hset(key, mapping=field_values)
        if expire_seconds > 0:
            self._client.expire(key, expire_seconds)

    def hash_get(self, key: str) -> Dict[str, str]:
        """
        Retrieve All Fields and Values of a Redis Hash Key.

        Functionality:
            Reads all field-value pairs for the specified hash key. Automatically decodes Redis's byte string
            responses to UTF-8 strings for direct use in Python. Returns an empty dict if the key does not exist.

        Args:
            key (str): Redis hash key to query (e.g., "task:123456").

        Returns:
            Dict[str, str]: Dictionary of field-value pairs (all values decoded to UTF-8 strings).
                Empty dict if key not found.

        Notes:
            - Handles empty results gracefully (no exceptions thrown for non-existent keys).
            - Nested objects must be serialized (e.g., to JSON string) before storage to be retrieved correctly.
        """
        data = self._client.hgetall(key)
        return {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()} if data else {}

    def hash_expire_update(self, key: str, expire_seconds: int) -> None:
        """
        Update Expiration Time of a Redis Hash Key.

        Args:
            key (str): Redis hash key to update (e.g., "task:123456").
            expire_seconds (int): New expiration time in seconds.
                Use 0 to remove expiration (key persists indefinitely).

        Notes:
            - If the key does not exist, this operation has no effect.
            - Expiration time is reset to the new value (replaces any existing expiration).
        """
        self._client.expire(key, expire_seconds)

    def hash_delete(self, key: str) -> None:
        """
        Delete a Redis Hash Key (and All Its Fields/Values).

        Args:
            key (str): Redis hash key to delete (e.g., "task:123456").

        Notes:
            - This is a permanent deletion; deleted keys cannot be recovered.
            - Has no effect if the key does not exist (no exceptions thrown).
        """
        self._client.delete(key)

    def hash_list_push(self, key: str, field: str, value: Any, expire_seconds: int = 0) -> None:
        """
        Push an element to a list stored in a Redis Hash field (JSON serialized).

        Functionality:
            1. Read existing list from Hash field (JSON string -> Python list)
            2. Add new element (avoid duplicates)
            3. Serialize back to JSON string and update Hash field
            4. Optional expiration for the Hash key

        Args:
            key (str): Redis hash key (e.g., "worker:demo_worker:192.168.1.100")
            field (str): Hash field name (e.g., "worker_run_process")
            value (Any): Element to add (e.g., 12345 for PID)
            expire_seconds (int, optional): Expiration time for the Hash key. Defaults to 0 (no expiration).

        Notes:
            - Creates empty list if field does not exist
            - Ignores duplicate elements to keep list unique
        """
        # Read existing list (handle empty/non-JSON data gracefully)
        raw_data = self._client.hget(key, field)
        current_list = []
        if raw_data:
            try:
                current_list = json.loads(raw_data.decode('utf-8'))
                if not isinstance(current_list, list):
                    current_list = []
            except (json.JSONDecodeError, ValueError):
                current_list = []

        # Add element (avoid duplicates)
        if value not in current_list:
            current_list.append(value)

        # Update Hash field with serialized list
        self._client.hset(key, field, json.dumps(current_list))
        if expire_seconds > 0:
            self._client.expire(key, expire_seconds)

    def hash_list_pull(self, key: str, field: str, value: Any) -> None:
        """
        Remove an element from a list stored in a Redis Hash field (JSON serialized).

        Functionality:
            1. Read existing list from Hash field (JSON string -> Python list)
            2. Remove target element (if exists)
            3. Serialize back to JSON string and update Hash field

        Args:
            key (str): Redis hash key (e.g., "worker:demo_worker:192.168.1.100")
            field (str): Hash field name (e.g., "worker_run_process")
            value (Any): Element to remove (e.g., 12345 for PID)

        Notes:
            - No effect if field does not exist or element not in list
        """
        # Read existing list (handle empty/non-JSON data gracefully)
        raw_data = self._client.hget(key, field)
        if not raw_data:
            return

        try:
            current_list = json.loads(raw_data.decode('utf-8'))
            if not isinstance(current_list, list):
                return
        except (json.JSONDecodeError, ValueError):
            return

        # Remove element (if exists)
        if value in current_list:
            current_list.remove(value)
            # Update Hash field with serialized list
            self._client.hset(key, field, json.dumps(current_list))

    def hash_list_get(self, key: str, field: str) -> list:
        """
        Get the list stored in a Redis Hash field (JSON deserialized).

        Args:
            key (str): Redis hash key
            field (str): Hash field name

        Returns:
            list: Deserialized list (empty list if field does not exist or data is invalid)
        """
        raw_data = self._client.hget(key, field)
        if not raw_data:
            return []

        try:
            current_list = json.loads(raw_data.decode('utf-8'))
            return current_list if isinstance(current_list, list) else []
        except (json.JSONDecodeError, ValueError):
            return []

    def update_json_field(self, key: str, field_path: str, value: Any, expire_seconds: int = 0) -> None:
        """
        Update a Redis Hash Key (JSON serialized).

        Args:
            key (str): Redis hash key
            field_path (str): JSON path (e.g., "." or ".x1.x2")
            value (Any): Value to set at the specified path
            expire_seconds (int, optional): Expiration time for the Hash key. Defaults to 0 (no expiration).
        """

        print(f"update_json_field: {key}, {field_path}, {value}")


def redis_get_task_client() -> RedisHashClient:
    """
    Get Redis Hash Client for Task Module.

    Functionality:
        Returns a RedisHashClient instance bound to Redis DB index 0, dedicated to task-related hash operations
        (e.g., caching task status, temporary task metadata).

    Returns:
        RedisHashClient: Initialized client instance for task module operations.
    """
    db_index = get_global_config().get(ConfigKeys.REDIS.KEY).get(
        ConfigKeys.REDIS.TASK_DB_INDEX, DefaultValues.REDIS.TASK_DB_INDEX)

    return RedisHashClient(db_index=db_index)


def redis_get_service_client() -> RedisHashClient:
    """
    Get Redis Hash Client for Service Module.

    Functionality:
        Returns a RedisHashClient instance bound to Redis DB index 1, dedicated to service-related hash operations
        (e.g., caching service status, service runtime metadata).

    Returns:
        RedisHashClient: Initialized client instance for service module operations.
    """
    db_index = get_global_config().get(ConfigKeys.REDIS.KEY).get(
        ConfigKeys.REDIS.SERVICE_DB_INDEX, DefaultValues.REDIS.SERVICE_DB_INDEX)

    return RedisHashClient(db_index=db_index)
