# -*- encoding: utf-8 -*-
import redis
from astraflux.settings.keys import *

_REDIS_CONFIG = REDIS.DEFAULT_VALUE_REDIS_URI


class RedisClient:
    """
    Client to interact with a Redis database.
    """
    _instance = None

    def __init__(self, db):
        url = '{}/{}'.format(_REDIS_CONFIG, db)
        _connection_pool = redis.ConnectionPool.from_url(url=url)
        self._client = redis.Redis(connection_pool=_connection_pool)

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    def set_hash_value(self, key, value, expire: int):
        """
        Set a hash value for a key.
        """
        self._client.hmset(key, value)
        if expire > 0:
            self._client.expire(key, expire)

    def get_hash_value(self, key):
        """
        Get a hash value for a key.
        """
        data = self._client.hgetall(key)
        return {k.decode(): v.decode() for k, v in data.items()}

    def update_expire(self, key, expire: int):
        """
        Update the expiration time for a given key.
        """
        self._client.expire(key, expire)

    def delete(self, key):
        """
        Delete a key.
        """
        self._client.delete(key)

    def get_db_all_value(self):
        """
        Get all values from a Redis database.
        """
        all_keys = self._client.keys('*')
        result = {}
        for key in all_keys:
            result[key] = self.get_hash_value(key)
        return result


def initialization_redis(config: dict):
    """
    Initialize a Redis client for use with astraflux
    """
    global _REDIS_CONFIG
    _REDIS_CONFIG = config.get(REDIS.KEY_REDIS_URI, REDIS.DEFAULT_VALUE_REDIS_URI)


def redis_task() -> RedisClient:
    """
    Generate a Redis task with a REDIS configuration.
    """
    return RedisClient(0)


def redis_services() -> RedisClient:
    """
    Generate a Redis service with a REDIS configuration
    """
    return RedisClient(1)


def register():
    from astraflux.interface import redisdb
    redisdb.redis_task = redis_task
    redisdb.redis_services = redis_services
    redisdb.initialization_redis = initialization_redis

    import sys
    sys.modules['astraflux.interface.redisdb'] = redisdb
