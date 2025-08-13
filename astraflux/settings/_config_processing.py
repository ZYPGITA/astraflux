# -*- encoding: utf-8 -*-

import sys
import json
import yaml
import base64

from .keys import *

current_dir_ = 'None'
global_config_ = {}


def _gen_rabbitmq_uri(_config):
    """
    Generate rabbitmq uri
    """
    rabbitmq_uri = 'amqp://{}:{}@{}:{}'.format(
        _config['RabbitMQ']['username'],
        _config['RabbitMQ']['password'],
        _config['RabbitMQ']['host'],
        _config['RabbitMQ']['port']
    )
    _config[RABBITMQ.KEY_RABBITMQ_URI] = rabbitmq_uri


def _gen_mongodb_uri(_config):
    """
    Generate mongodb uri
    """
    mongodb_uri = 'mongodb://{}:{}@{}:{}'.format(
        _config['Mongodb']['username'],
        _config['Mongodb']['password'],
        _config['Mongodb']['host'],
        _config['Mongodb']['port']
    )
    _config[MONGODB.KEY_MONGODB_URI] = mongodb_uri


def _gen_redis_uri(_config):
    """
    Generate Redis uri
    """
    redis_uri = 'redis://:{}@{}:{}'.format(
        _config['Redis']['password'],
        _config['Redis']['host'],
        _config['Redis']['port']
    )
    _config[REDIS.KEY_REDIS_URI] = redis_uri


def _config_default_value_processing(config: dict):
    """
    Process the default values in the configuration dictionary.
    Args:
        config (dict): The configuration dictionary.
    Returns:
        dict: The configuration dictionary with processed default values.
    """

    if SCHEDULE.KEY_DEFAULT_SCHEDULE_TIME not in config:
        config[SCHEDULE.KEY_DEFAULT_SCHEDULE_TIME] = SCHEDULE.DEFAULT_VALUE_SCHEDULE_TIME

    return config


def current_dir() -> str:
    """
    Return the current directory of the current working directory.
    """
    return current_dir_


def global_config() -> dict:
    """
    Return the global configuration settings.
    """
    return global_config_


def load_settings(yaml_file: str, workspace: str) -> None:
    """
    Load settings from yaml file.
    :param yaml_file: yaml file path
    :param workspace: workspace path
    :return:
    """
    with open(yaml_file, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f)

    _gen_rabbitmq_uri(_config)
    _gen_mongodb_uri(_config)
    _gen_redis_uri(_config)

    _config[KEY_ROOT_PATH] = workspace

    global global_config_, current_dir_
    current_dir_ = workspace
    global_config_ = _config


def load_config(encoded_config: str) -> dict:
    """
    Decode and load the encoded configuration string.

    Args:
        encoded_config (str): The encoded configuration string.

    Returns:
        dict: The decoded configuration dictionary.
    """
    try:
        decoded_bytes = base64.b64decode(encoded_config)
        decoded_string = decoded_bytes.decode('utf-8')
        return _config_default_value_processing(json.loads(decoded_string))
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)


def dump_config(config: dict) -> str:
    """
    Dump the encoded configuration string.
    """
    json_str = json.dumps(config, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    return base64.b64encode(json_bytes).decode('utf-8')


def register():
    from astraflux.settings import config_processing
    config_processing.current_dir = current_dir
    config_processing.global_config = global_config
    config_processing.load_settings = load_settings
    config_processing.load_config = load_config
    config_processing.dump_config = dump_config

    import sys
    sys.modules['astraflux.settings.config_processing'] = config_processing
