# -*- encoding: utf-8 -*-

def set_root_path(root_path: str):
    """
    Sets the root directory for the global variables.
    :param root_path: The root directory for the global variables.
    """
    return set_root_path(root_path)


def get_root_path():
    """
    Gets the root directory for the global variables.
    """
    return get_current_dir()


def set_current_dir(current_dir: str):
    """
    Sets the current directory for the global variables.
    :param current_dir: The current directory for the global variables.
    """
    return set_current_dir(current_dir)


def get_current_dir() -> str | None:
    """
    Gets the current directory for the global variables.
    """
    return get_current_dir()


def set_rabbitmq_uri(uri: str):
    """
    Sets the RabbitMQ URI for the global variables.
    :param uri: The RabbitMQ URI for the global variables.
    """
    return set_rabbitmq_uri(uri)


def get_rabbitmq_uri() -> str | None:
    """
    Gets the RabbitMQ URI for the global variables.
    """
    return get_rabbitmq_uri()


def set_redis_uri(redis_uri: str):
    """
    Sets the Redis URI for the global variables.
    :param redis_uri: The Redis URI for the global variables.
    """
    return set_redis_uri(redis_uri)


def get_redis_uri() -> str | None:
    """
    Gets the Redis URI for the global variables.
    """
    return get_redis_uri()


def set_mongo_uri(mongo_uri: str):
    """
    Sets the Mongo URI for the global variables.
    :param mongo_uri: The Mongo URI for the global variables.
    """
    return set_mongo_uri(mongo_uri)


def get_mongo_uri() -> str | None:
    """
    Gets the Mongo URI for the global variables.
    """
    return get_mongo_uri()


def set_logs_path(logs_path: str):
    """
    Sets the logs path for the global variables.
    :param logs_path: The logs path for the global variables.
    """
    return set_logs_path(logs_path)


def get_logs_path() -> str | None:
    """
    Gets the logs path for the global variables.
    """
    return get_logs_path()


def set_log_level(log_level: str) -> None:
    """
    Sets the log level for the global variables.
    :param log_level: The log level for the global variables.
    """
    return set_log_level(log_level)


def get_log_level() -> str | None:
    """
    Gets the log level for the global variables.
    """
    return get_log_level()
