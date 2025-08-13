# -*- encoding: utf-8 -*-

from astraflux.inject import inject_implementation

__all__ = [
    'initialization_redis',
    'redis_task',
    'redis_services'
]


class RedisClient:
    """
    Client to interact with a Redis database.
    """

    def set_hash_value(self, key, value, expire: int):
        """
        Set a hash value for a key.
        """

    def get_hash_value(self, key):
        """
        Get a hash value for a key.
        """

    def update_expire(self, key, expire: int):
        """
        Update the expiration time for a given key.
        """

    def delete(self, key):
        """
        Delete a key.
        """

    def get_db_all_value(self):
        """
        Get all values from a Redis database.
        """


@inject_implementation()
def initialization_redis(config: dict):
    """
    Initialize a Redis client for use with astraflux
    """


@inject_implementation()
def redis_task() -> RedisClient:
    """
    Generate a Redis task with a REDIS configuration.
    """


@inject_implementation()
def redis_services() -> RedisClient:
    """
    Generate a Redis service with a REDIS configuration
    """
