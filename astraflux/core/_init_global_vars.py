# -*- encoding: utf-8 -*-

import os
from astraflux.definitions.constants import *

from astraflux.interface.definitions import *

__all__ = ['init_global_vars']


def _init_rabbitmq_config(data: dict):
    """
    Generate rabbitmq uri
    """
    rabbitmq_uri = 'amqp://{}:{}@{}:{}'.format(
        data[ConfigKeys.RABBITMQ.KEY][ConfigKeys.USERNAME],
        data[ConfigKeys.RABBITMQ.KEY][ConfigKeys.PASSWORD],
        data[ConfigKeys.RABBITMQ.KEY][ConfigKeys.HOST],
        data[ConfigKeys.RABBITMQ.KEY][ConfigKeys.PORT]
    )
    data[ConfigKeys.RABBITMQ.RABBITMQ_URI] = rabbitmq_uri
    set_rabbitmq_uri(rabbitmq_uri)


def _init_mongodb_config(data: dict):
    """
    Generate mongodb uri
    """
    mongodb_uri = 'mongodb://{}:{}@{}:{}'.format(
        data[ConfigKeys.MONGODB.KEY][ConfigKeys.USERNAME],
        data[ConfigKeys.MONGODB.KEY][ConfigKeys.PASSWORD],
        data[ConfigKeys.MONGODB.KEY][ConfigKeys.HOST],
        data[ConfigKeys.MONGODB.KEY][ConfigKeys.PORT]
    )
    data[ConfigKeys.MONGODB.MONGODB_URI] = mongodb_uri
    set_mongo_uri(mongodb_uri)


def _init_redis_config(data: dict):
    """
    Generate Redis uri
    """
    redis_uri = 'redis://:{}@{}:{}'.format(
        data[ConfigKeys.REDIS.KEY][ConfigKeys.PASSWORD],
        data[ConfigKeys.REDIS.KEY][ConfigKeys.HOST],
        data[ConfigKeys.REDIS.KEY][ConfigKeys.PORT]
    )
    data[ConfigKeys.REDIS.REDIS_URI] = redis_uri
    set_redis_uri(redis_uri)


def _init_logs_config(data: dict, current_dir: str):
    """
    Generate logs path
    """
    path = data[ConfigKeys.LOG.KEY][ConfigKeys.LOG.LOG_PATH]
    logs_path = os.path.join(current_dir, path)
    data[ConfigKeys.LOG.LOG_PATH] = logs_path
    set_logs_path(logs_path)

    level = data[ConfigKeys.LOG.KEY][ConfigKeys.LOG.LOG_LEVEL]
    set_log_level(level)


def init_global_vars(yaml_file: str, current_dir: str, root_path: str) -> dict:
    """
    Initialize global variables from a YAML file.
    Args:
        yaml_file (str): Path to the YAML file containing global variable definitions.
        current_dir (str): Current directory path.
        root_path (str): Root directory path.
    """
    import sys
    import yaml

    set_current_dir(current_dir)

    sys.path.insert(0, root_path)

    with open(yaml_file, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

        _init_rabbitmq_config(data)
        _init_mongodb_config(data)
        _init_redis_config(data)
        _init_logs_config(data, current_dir)

    data[ConfigKeys.CURRENT_DIR] = current_dir
    set_global_config(data)
    return data


def register():
    import sys
    from astraflux.interface import core
    core.init_global_vars = init_global_vars

    if REPLACE_SYS_MODULE:
        sys.modules['astraflux.interface.core'] = core
