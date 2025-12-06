# -*- encoding: utf-8 -*-
from astraflux.definitions.constants import REPLACE_SYS_MODULE

CURRENT_DIR = None
RABBITMQ_URI = None
MONGO_URI = None
REDIS_URI = None
LOGS_PATH = None
LOG_LEVEL = None
INITIALIZED = False
ROOT_PATH = None

GLOBAL_CONFIG = {}


def set_global_config(config: dict):
    """
    Sets the global global variables.
    """
    global GLOBAL_CONFIG
    GLOBAL_CONFIG = config


def get_global_config():
    """
    Gets the global global variables.
    """
    return GLOBAL_CONFIG


def set_root_path(root_path: str):
    """
    Sets the root directory for the global variables.
    :param root_path: The root directory for the global variables.
    """
    global ROOT_PATH
    ROOT_PATH = root_path


def get_root_path():
    """
    Gets the root directory for the global variables.
    """
    return ROOT_PATH


def set_current_dir(current_dir: str):
    """
    Sets the current directory for the global variables.
    :param current_dir: The current directory for the global variables.
    """
    global CURRENT_DIR
    CURRENT_DIR = current_dir


def get_current_dir() -> str | None:
    """
    Gets the current directory for the global variables.
    """
    if CURRENT_DIR is None:
        raise ValueError("Current directory is not set")
    return CURRENT_DIR


def set_rabbitmq_uri(uri: str):
    """
    Sets the RabbitMQ URI for the global variables.
    :param uri: The RabbitMQ URI for the global variables.
    """
    global RABBITMQ_URI
    RABBITMQ_URI = uri


def get_rabbitmq_uri() -> str | None:
    """
    Gets the RabbitMQ URI for the global variables.
    """
    if RABBITMQ_URI is None:
        raise ValueError("RabbitMQ URI is not set")
    return RABBITMQ_URI


def set_redis_uri(redis_uri: str):
    """
    Sets the Redis URI for the global variables.
    :param redis_uri: The Redis URI for the global variables.
    """
    global REDIS_URI
    REDIS_URI = redis_uri


def get_redis_uri() -> str | None:
    """
    Gets the Redis URI for the global variables.
    """
    if REDIS_URI is None:
        raise ValueError("Redis URI is not set")
    return REDIS_URI


def set_mongo_uri(mongo_uri: str):
    """
    Sets the Mongo URI for the global variables.
    :param mongo_uri: The Mongo URI for the global variables.
    """
    global MONGO_URI
    MONGO_URI = mongo_uri


def get_mongo_uri() -> str | None:
    """
    Gets the Mongo URI for the global variables.
    """
    if MONGO_URI is None:
        raise ValueError("Mongo URI is not set")
    return MONGO_URI


def set_logs_path(logs_path: str):
    """
    Sets the logs path for the global variables.
    :param logs_path: The logs path for the global variables.
    """
    global LOGS_PATH
    LOGS_PATH = logs_path


def get_logs_path() -> str | None:
    """
    Gets the logs path for the global variables.
    """
    if LOGS_PATH is None:
        raise ValueError("Logs path is not set")
    return LOGS_PATH


def set_log_level(log_level: str):
    """
    Sets the log level for the global variables.
    :param log_level: The log level for the global variables.
    """
    global LOG_LEVEL
    LOG_LEVEL = log_level


def get_log_level() -> str | None:
    """
    Gets the log level for the global variables.
    """
    if LOG_LEVEL is None:
        raise ValueError("Log level is not set")
    return LOG_LEVEL


def register():
    import sys
    from astraflux.interface import definitions

    definitions.set_global_config = set_global_config
    definitions.set_root_path = set_root_path
    definitions.set_current_dir = set_current_dir
    definitions.set_rabbitmq_uri = set_rabbitmq_uri
    definitions.set_redis_uri = set_redis_uri
    definitions.set_mongo_uri = set_mongo_uri
    definitions.set_logs_path = set_logs_path
    definitions.set_log_level = set_log_level

    definitions.get_global_config = get_global_config
    definitions.get_root_path = get_root_path
    definitions.get_current_dir = get_current_dir
    definitions.get_rabbitmq_uri = get_rabbitmq_uri
    definitions.get_redis_uri = get_redis_uri
    definitions.get_mongo_uri = get_mongo_uri
    definitions.get_logs_path = get_logs_path
    definitions.get_log_level = get_log_level

    if REPLACE_SYS_MODULE:
        sys.modules['astraflux.interface.definitions'] = definitions
