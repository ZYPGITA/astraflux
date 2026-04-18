# -*- encoding: utf-8 -*-


import time
import json
import logging
import threading
from typing import Dict, List, Optional, Any

import redis
from redis import Redis

from astraflux.core import global_manager
from astraflux.definitions.constants import *


class RedisWorkerClient:
    """
    A thread-safe Redis client specifically designed for managing worker-related data operations.
    This client handles storage, retrieval, and update of worker metadata (such as max process count,
    running process list), maintains Redis key naming conventions, and uses connection pooling for
    efficient connection management. All operations are wrapped with exception handling and logging
    for robust error tracking.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize the RedisWorkerClient with configuration parameters and logger.
        Establishes a Redis connection pool with specified timeout and retry settings,
        and initializes a reentrant lock for thread-safe operations.

        Args:
            config: A dictionary containing Redis connection configuration (host, port, password, etc.)
            logger: A logging.Logger instance for recording error and operational logs
        """
        self.logger = logger

        self._host = config.get(REDIS.CONFIG.HOST.value, REDIS.DEFAULT.HOST.value)
        self._port = config.get(REDIS.CONFIG.PORT.value, REDIS.DEFAULT.PORT.value)
        self._password = config.get(REDIS.CONFIG.PASSWORD.value, REDIS.DEFAULT.PASSWORD.value)
        self._db = config.get(REDIS.CONFIG.DB_INDEX.value, REDIS.DEFAULT.DB_INDEX.value)
        self._max_connections = config.get(REDIS.CONFIG.MAX_CONNECTIONS.value, REDIS.DEFAULT.MAX_CONNECTIONS.value)

        self._connection_pool = redis.ConnectionPool(
            host=self._host,
            port=self._port,
            password=self._password,
            db=self._db,
            max_connections=self._max_connections,
            decode_responses=False,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )

        self._lock = threading.RLock()

    def get_connection(self) -> Redis:
        """
        Retrieve a Redis connection instance from the pre-configured connection pool.
        The connection is automatically managed by the pool and does not require manual closing.

        Returns:
            A Redis client instance bound to the connection pool
        """
        return redis.Redis(connection_pool=self._connection_pool)

    @staticmethod
    def _get_worker_key(unique_id: str) -> str:
        """
        Generate the Redis key for storing the main metadata of a specific worker.
        Follows the naming convention: "worker:{unique_id}".

        Args:
            unique_id: The unique identifier of the worker

        Returns:
            The fully qualified Redis key for the worker's main data
        """
        return f"worker:{unique_id}"

    @staticmethod
    def _get_run_process_key(unique_id: str) -> str:
        """
        Generate the Redis key for storing the running process list of a specific worker.
        The running processes are stored as a sorted set (ZSET).
        Follows the naming convention: "worker:{unique_id}:run_process".

        Args:
            unique_id: The unique identifier of the worker

        Returns:
            The fully qualified Redis key for the worker's running process list
        """
        return f"worker:{unique_id}:run_process"

    @staticmethod
    def _get_max_process_key(unique_id: str) -> str:
        """
        Generate the Redis key for storing the maximum allowed process count of a specific worker.
        Follows the naming convention: "worker:{unique_id}:max_process".

        Args:
            unique_id: The unique identifier of the worker

        Returns:
            The fully qualified Redis key for the worker's max process count
        """
        return f"worker:{unique_id}:max_process"

    def store_worker_data(self, data: Dict[str, Any]) -> bool:
        """
        Store the complete metadata of a worker into Redis with transactional consistency.
        Separates worker main data, max process count, and running process list into dedicated keys,
        serializes JSON-compatible fields (service_functions, worker_functions), sets an expiration
        time of 24 hours for all keys, and maintains a service name index for worker discovery.

        Args:
            data: A dictionary containing the worker's metadata (must include 'unique_id' field)

        Returns:
            Boolean indicating whether the storage operation succeeded (True) or failed (False)
        """
        if 'unique_id' not in data:
            raise ValueError("Data must contain 'unique_id' field")

        try:
            conn = self.get_connection()
            unique_id = data['unique_id']

            with conn.pipeline(transaction=True) as pipe:

                main_data = data.copy()

                worker_run_process = main_data.pop('worker_run_process', [])
                worker_max_process = main_data.pop('worker_max_process', 0)

                for key in ['service_functions', 'worker_functions']:
                    if key in main_data:
                        main_data[key] = json.dumps(main_data[key])

                main_key = self._get_worker_key(unique_id)
                if main_data:
                    # 兼容旧版 Redis 服务器和 redis-py 客户端
                    hmset_args = [main_key]
                    for field, value in main_data.items():
                        hmset_args.append(field)
                        hmset_args.append(value)
                    pipe.execute_command('HMSET', *hmset_args)

                max_process_key = self._get_max_process_key(unique_id)
                pipe.set(max_process_key, str(worker_max_process))

                run_process_key = self._get_run_process_key(unique_id)
                pipe.delete(run_process_key)

                if worker_run_process:
                    current_time = time.time()
                    zadd_args = []
                    for i, process_id in enumerate(worker_run_process):
                        score = current_time + (i * 0.000001)
                        zadd_args.append(score)
                        zadd_args.append(str(process_id))
                    pipe.execute_command('ZADD', run_process_key, *zadd_args)

                expire_time = 86400
                pipe.expire(main_key, expire_time)
                pipe.expire(max_process_key, expire_time)
                pipe.expire(run_process_key, expire_time)

                if 'service_name' in data:
                    service_name = data['service_name']
                    pipe.sadd(f"index:service_name:{service_name}", unique_id)
                    pipe.expire(f"index:service_name:{service_name}", expire_time)

                pipe.execute()
            return True
        except Exception as e:
            self.logger.error(f"Error storing worker data: {e}")
            return False

    def get_max_process(self, unique_id: str) -> Optional[int]:
        """
        Retrieve the maximum allowed process count for a specific worker.
        Prioritizes fetching from the dedicated max process key for performance. If the key does not exist,
        falls back to the worker's main data key and synchronizes the value to the dedicated key for
        future queries. Handles byte decoding and type conversion from string to integer.

        Args:
            unique_id: The unique identifier of the worker

        Returns:
            The maximum process count as an integer if available, None if the key does not exist or an error occurs
        """
        try:
            conn = self.get_connection()
            key = self._get_max_process_key(unique_id)
            result = conn.get(key)

            if result is None:
                main_key = self._get_worker_key(unique_id)
                result = conn.hget(main_key, 'worker_max_process')
                if result:
                    conn.set(key, result)

            return int(result.decode()) if result else None

        except Exception as e:
            self.logger.error(f"Error getting max_process: {e}")
            return None

    def update_max_process(self, unique_id: str, new_value: int) -> bool:
        """
        Update the maximum allowed process count for a specific worker with transactional consistency.
        Synchronizes the new value to both the dedicated max process key and the worker's main data key
        using a Redis pipeline to ensure atomicity of the two write operations.

        Args:
            unique_id: The unique identifier of the worker
            new_value: The new maximum process count to set

        Returns:
            Boolean indicating whether the update operation succeeded (True) or failed (False)
        """
        try:
            conn = self.get_connection()

            with conn.pipeline(transaction=True) as pipe:
                max_key = self._get_max_process_key(unique_id)
                pipe.set(max_key, str(new_value))

                main_key = self._get_worker_key(unique_id)
                pipe.hset(main_key, 'worker_max_process', str(new_value))

                pipe.execute()

            return True

        except Exception as e:
            self.logger.error(f"Error updating max_process: {e}")
            return False

    def increment_max_process(self, unique_id: str, delta: int = 1) -> Optional[int]:
        """
        Increment the maximum allowed process count for a specific worker by a specified delta.
        Uses Redis's atomic INCRBY operation to avoid race conditions during concurrent updates.
        Synchronizes the updated value to the worker's main data key after the increment.

        Args:
            unique_id: The unique identifier of the worker
            delta: The integer value to increment the max process count by (default: 1)

        Returns:
            The updated maximum process count as an integer if the operation succeeds, None if an error occurs
        """
        try:
            conn = self.get_connection()
            key = self._get_max_process_key(unique_id)

            result = conn.incrby(key, delta)

            main_key = self._get_worker_key(unique_id)
            conn.hset(main_key, 'worker_max_process', str(result))

            return result

        except Exception as e:
            self.logger.error(f"Error incrementing max_process: {e}")
            return None

    def get_run_process_count(self, unique_id: str) -> int:
        """
        Retrieve the number of currently running processes for a specific worker.
        Counts the number of members in the running process sorted set using Redis ZCARD operation.
        Returns 0 if the key does not exist or an error occurs during the operation.

        Args:
            unique_id: The unique identifier of the worker

        Returns:
            The count of running processes as a non-negative integer
        """
        try:
            conn = self.get_connection()
            key = self._get_run_process_key(unique_id)
            return conn.zcard(key)
        except Exception as e:
            self.logger.error(f"Error getting run_process count: {e}")
            return 0

    def get_all_run_process(self, unique_id: str) -> List[int]:
        """
        Retrieve the complete list of currently running process IDs for a specific worker.
        Fetches all members from the running process sorted set using Redis ZRANGE, decodes byte strings
        to UTF-8, and converts each process ID to an integer (falls back to string if conversion fails).
        Returns an empty list if the key does not exist or an error occurs.

        Args:
            unique_id: The unique identifier of the worker

        Returns:
            A list of integers representing the running process IDs
        """
        try:
            conn = self.get_connection()
            key = self._get_run_process_key(unique_id)
            members = conn.zrange(key, 0, -1)

            process_list = []
            for member in members:
                try:
                    process_list.append(int(member.decode()))
                except (ValueError, AttributeError):
                    process_list.append(member.decode())

            return process_list

        except Exception as e:
            self.logger.error(f"Error getting all run_process: {e}")
            return []

    def add_to_run_process(self, unique_id: str, process_id: int) -> bool:
        """
        Add a single process ID to the running process list of a specific worker.
        Uses the current Unix timestamp as the score for the sorted set to maintain insertion order.
        Synchronizes the updated running process list to the worker's main data key after addition.
        Returns True if the process ID was successfully added (new member), False otherwise.

        Args:
            unique_id: The unique identifier of the worker
            process_id: The integer ID of the process to add

        Returns:
            Boolean indicating whether the process ID was successfully added
        """
        try:
            conn = self.get_connection()
            key = self._get_run_process_key(unique_id)
            score = time.time()
            result = conn.zadd(key, {str(process_id): score})
            self._sync_run_process_to_main(unique_id)

            return result > 0

        except Exception as e:
            self.logger.error(f"Error adding to run_process: {e}")
            return False

    def batch_add_to_run_process(self, unique_id: str, process_ids: List[int]) -> int:
        """
        Batch add multiple process IDs to the running process list of a specific worker.
        Generates unique scores for each process ID by appending a small index-based offset to the
        current Unix timestamp (to avoid score collisions in the sorted set). Uses Redis ZADD to
        batch insert the process IDs and synchronizes the list to the worker's main data key.
        Returns the number of successfully added new process IDs.

        Args:
            unique_id: The unique identifier of the worker
            process_ids: A list of integer process IDs to add

        Returns:
            The count of successfully added process IDs (non-negative integer)
        """
        try:
            conn = self.get_connection()
            key = self._get_run_process_key(unique_id)

            import time
            current_time = time.time()

            zset_data = {}
            for i, pid in enumerate(process_ids):
                score = current_time + (i * 0.000001)
                zset_data[str(pid)] = score

            if zset_data:
                result = conn.zadd(key, zset_data)
                self._sync_run_process_to_main(unique_id)
                return result

            return 0

        except Exception as e:
            self.logger.error(f"Error batch adding to run_process: {e}")
            return 0

    def remove_from_run_process(self, unique_id: str, process_id: int) -> bool:
        """
        Remove a single process ID from the running process list of a specific worker.
        Uses Redis ZREM operation to delete the process ID from the sorted set.
        Synchronizes the updated running process list to the worker's main data key if the removal
        was successful. Returns True if the process ID was found and removed, False otherwise.

        Args:
            unique_id: The unique identifier of the worker
            process_id: The integer ID of the process to remove

        Returns:
            Boolean indicating whether the process ID was successfully removed
        """
        try:
            conn = self.get_connection()
            key = self._get_run_process_key(unique_id)

            result = conn.zrem(key, str(process_id))

            if result > 0:
                self._sync_run_process_to_main(unique_id)

            return result > 0

        except Exception as e:
            self.logger.error(f"Error removing from run_process: {e}")
            return False

    def clear_run_process(self, unique_id: str) -> bool:
        """
        Clear all running process IDs from the running process list of a specific worker.
        Deletes the entire running process sorted set using Redis DELETE and resets the
        'worker_run_process' field in the worker's main data key to an empty JSON array.
        Returns True if any data was deleted (i.e., the key existed), False otherwise.

        Args:
            unique_id: The unique identifier of the worker

        Returns:
            Boolean indicating whether the running process list was successfully cleared
        """
        try:
            conn = self.get_connection()
            key = self._get_run_process_key(unique_id)

            result = conn.delete(key)

            main_key = self._get_worker_key(unique_id)
            conn.hset(main_key, 'worker_run_process', '[]')

            return result > 0

        except Exception as e:
            self.logger.error(f"Error clearing run_process: {e}")
            return False

    def _sync_run_process_to_main(self, unique_id: str) -> None:
        """
        Internal helper method to synchronize the running process list to the worker's main data key.
        Fetches the current running process list, serializes it to a JSON string, and updates the
        'worker_run_process' field in the worker's main hash key. Logs any errors that occur during
        the synchronization process without propagating exceptions.

        Args:
            unique_id: The unique identifier of the worker
        """
        try:
            conn = self.get_connection()

            process_ids = self.get_all_run_process(unique_id)

            main_key = self._get_worker_key(unique_id)
            conn.hset(main_key, 'worker_run_process', json.dumps(process_ids))

        except Exception as e:
            self.logger.error(f"Error syncing run_process to main: {e}")

    def get_available_slots(self, unique_id: str) -> int:
        """
        Calculate the number of available process slots for a specific worker.
        Available slots are defined as the difference between maximum allowed processes and
        currently running processes (clamped to a non-negative value). Uses a Redis pipeline to
        fetch both values atomically, ensuring consistency between the two queries. Returns 0
        if the max process key does not exist or an error occurs.

        Args:
            unique_id: The unique identifier of the worker

        Returns:
            The number of available process slots as a non-negative integer
        """
        try:
            conn = self.get_connection()

            with conn.pipeline() as pipe:
                pipe.get(self._get_max_process_key(unique_id))
                pipe.zcard(self._get_run_process_key(unique_id))
                results = pipe.execute()

            max_process = results[0]
            run_count = results[1] or 0

            if max_process is None:
                return 0

            max_process_int = int(max_process.decode())
            return max(max_process_int - run_count, 0)

        except Exception as e:
            self.logger.error(f"Error calculating available slots: {e}")
            return 0

    def get_total_available_slots_by_server_name(self, server_name: str):
        workers = self.scan_workers_by_service(service_name=server_name)

        total_available_slots = 0
        for unique_id in workers:
            total_available_slots += self.get_available_slots(unique_id=unique_id)

        return total_available_slots

    def get_worker_status(self, unique_id: str) -> Dict[str, Any]:
        """
        Retrieve the core status metadata for a specific worker.
        Fetches key metrics (max processes, running processes) and identifiers (worker name, service IP)
        using a Redis pipeline for atomicity. Calculates available slots and packages all data into
        a structured dictionary. Returns an empty dictionary if an error occurs.

        Args:
            unique_id: The unique identifier of the worker

        Returns:
            A dictionary containing the worker's core status information
        """
        try:
            conn = self.get_connection()

            with conn.pipeline() as pipe:
                pipe.get(self._get_max_process_key(unique_id))
                pipe.zcard(self._get_run_process_key(unique_id))
                pipe.hget(self._get_worker_key(unique_id), 'worker_name')
                pipe.hget(self._get_worker_key(unique_id), 'service_ipaddr')

                results = pipe.execute()

            status = {
                'unique_id': unique_id,
                'max_process': int(results[0].decode()) if results[0] else 0,
                'run_process_count': results[1] or 0,
                'available_slots': 0,
                'worker_name': results[2].decode() if results[2] else None,
                'service_ipaddr': results[3].decode() if results[3] else None
            }

            status['available_slots'] = max(status['max_process'] - status['run_process_count'], 0)

            return status

        except Exception as e:
            self.logger.error(f"Error getting worker status: {e}")
            return {}

    def get_full_worker_data(self, unique_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the complete metadata for a specific worker, including main data, max processes,
        and running processes. Deserializes JSON-encoded fields (service_functions, worker_functions)
        from the main hash key, combines data from dedicated keys, and returns a fully structured
        dictionary. Returns None if the worker's main data key does not exist or an error occurs.

        Args:
            unique_id: The unique identifier of the worker

        Returns:
            A dictionary containing the complete worker metadata if available, None otherwise
        """
        try:
            conn = self.get_connection()

            with conn.pipeline() as pipe:
                main_key = self._get_worker_key(unique_id)
                pipe.hgetall(main_key)
                pipe.get(self._get_max_process_key(unique_id))
                pipe.zrange(self._get_run_process_key(unique_id), 0, -1)
                results = pipe.execute()

            if not results[0]:
                return None

            worker_data = {}
            for key, value in results[0].items():
                key_str = key.decode('utf-8')
                value_str = value.decode('utf-8')

                if key_str in ['service_functions', 'worker_functions']:
                    try:
                        worker_data[key_str] = json.loads(value_str)
                    except (ValueError, AttributeError):
                        worker_data[key_str] = value_str
                else:
                    worker_data[key_str] = value_str

            worker_data['unique_id'] = unique_id

            if results[1]:
                worker_data['worker_max_process'] = int(results[1].decode())

            run_process_list = []
            for member in results[2]:
                try:
                    run_process_list.append(int(member.decode()))
                except (ValueError, AttributeError):
                    run_process_list.append(member.decode())

            worker_data['worker_run_process'] = run_process_list

            return worker_data

        except Exception as e:
            self.logger.error(f"Error getting full worker data: {e}")
            return None

    def delete_worker_data(self, unique_id: str) -> bool:
        """
        Delete all metadata associated with a specific worker from Redis.
        Removes the worker's main data key, max process key, and running process key using a pipeline.
        Also removes the worker's unique ID from all service name index sets. Returns True if any
        keys were deleted or modified, False otherwise.

        Args:
            unique_id: The unique identifier of the worker

        Returns:
            Boolean indicating whether any worker data was successfully deleted
        """
        try:
            conn = self.get_connection()

            with conn.pipeline() as pipe:
                pipe.delete(
                    self._get_worker_key(unique_id),
                    self._get_max_process_key(unique_id),
                    self._get_run_process_key(unique_id)
                )
                pipe.srem(f"index:service_name:*", unique_id)
                results = pipe.execute()

            return sum(results) > 0

        except Exception as e:
            self.logger.error(f"Error deleting worker data: {e}")
            return False

    def scan_workers_by_service(self, service_name: str) -> List[str]:
        """
        Retrieve the list of worker unique IDs associated with a specific service name.
        Fetches all members from the service name index set and decodes byte strings to UTF-8.
        Returns an empty list if the index set does not exist or an error occurs.

        Args:
            service_name: The name of the service to filter workers by

        Returns:
            A list of worker unique IDs as strings
        """
        try:
            conn = self.get_connection()
            key = f"index:service_name:{service_name}"

            return [uid.decode() for uid in conn.smembers(key)]

        except Exception as e:
            self.logger.error(f"Error scanning workers by service: {e}")
            return []

    def get_all_service_names(self) -> List[str]:
        """
        Retrieve the names of all registered services.

        Uses Redis SCAN command to iteratively find all keys matching the pattern
        "index:service_name:*", extracts the service name from each key, and returns
        a list of unique service names. This method is efficient for large key spaces
        as it uses cursor-based iteration without blocking the server.

        Returns:
            A list of service name strings. If an error occurs or no services are
            found, an empty list is returned.
        """
        try:
            conn = self.get_connection()
            cursor = 0
            service_names = []
            pattern = "index:service_name:*"
            while True:
                cursor, keys = conn.scan(cursor=cursor, match=pattern, count=100)
                for key in keys:
                    key_str = key.decode()
                    # Key format: index:service_name:<service_name>
                    service_name = key_str.split(':', 2)[-1]
                    service_names.append(service_name)
                if cursor == 0:
                    break
            return service_names
        except Exception as e:
            self.logger.error(f"Get all Server Error: {e}")
            return []

    def refresh_service_expiry(self, server_name: str, expire_seconds: int = 86400) -> bool:
        """
        Refresh the expiration time for all Redis keys associated with a specific service.

        For the given service, this method renews the TTL (time-to-live) on:
            - Each worker's main data key
            - Each worker's max process key
            - Each worker's running process key
            - The service index key (used for service discovery)

        The operation is performed atomically using a Redis pipeline to ensure
        all keys are updated together efficiently.

        Args:
            server_name: The name of the service whose keys should be refreshed.
            expire_seconds: New expiration time in seconds (default is 86400 seconds = 24 hours).

        Returns:
            True if all keys were successfully refreshed; False if no workers were
            found for the service or if an error occurred during the operation.
        """
        try:
            conn = self.get_connection()
            worker_ids = self.scan_workers_by_service(server_name)
            if not worker_ids:
                self.logger.warning(f"Server '{server_name}' Not Fund worker")
                return False

            with conn.pipeline(transaction=False) as pipe:
                # Refresh each worker's keys
                for unique_id in worker_ids:
                    main_key = self._get_worker_key(unique_id)
                    max_key = self._get_max_process_key(unique_id)
                    run_key = self._get_run_process_key(unique_id)
                    pipe.expire(main_key, expire_seconds)
                    pipe.expire(max_key, expire_seconds)
                    pipe.expire(run_key, expire_seconds)

                # Refresh the service index key
                service_index_key = f"index:service_name:{server_name}"
                pipe.expire(service_index_key, expire_seconds)

                pipe.execute()
            return True
        except Exception as e:
            self.logger.error(f"Refresh '{server_name}' Expiry Error: {e}")
            return False


@global_manager.register_fixture(name="fixture_redis_client", scope=Scope.GLOBAL)
def _redis_client(fixture_config, fixture_logger):
    """
    A global fixture function for creating and managing a RedisWorkerClient instance.
    Retrieves Redis configuration from the global fixture config, initializes a logger for Redis operations,
    and yields the RedisWorkerClient instance. The fixture follows the global scope lifecycle, meaning
    a single instance is reused across the entire application context.

    Args:
        fixture_config: The global application configuration fixture containing Redis settings
        fixture_logger: The global logging fixture for creating Redis-specific loggers

    Yields:
        An initialized instance of RedisWorkerClient
    """
    _redis_config = fixture_config[REDIS.CONFIG.KEY.value]
    _logger = fixture_logger.get_logger(PROJECT.NAME.value, REDIS.CONFIG.KEY.value)

    _redis_producer = RedisWorkerClient(
        config=_redis_config,
        logger=_logger,
    )

    yield _redis_producer
