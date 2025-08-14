# -*- encoding: utf-8 -*-

import sys

__all__ = [
    'load_settings',
    'current_dir',
    'global_config',
    'load_config',
    'dump_config'
]


def current_dir() -> str:
    """
    Return the current directory of the current working directory.
    """
    return sys.modules[__name__].current_dir()


def global_config() -> dict:
    """
    Return the global configuration settings.
    """
    return sys.modules[__name__].global_config()


def load_settings(yaml_file: str, workspace: str) -> None:
    """
    Load settings from yaml file.
    :param yaml_file: yaml file path
    :param workspace: workspace path
    :return:
    """
    return sys.modules[__name__].load_settings(yaml_file, workspace)


def load_config(encoded_config: str) -> dict:
    """
    Decode and load the encoded configuration string.

    Args:
        encoded_config (str): The encoded configuration string.

    Returns:
        dict: The decoded configuration dictionary.
    """
    return sys.modules[__name__].load_config(encoded_config)


def dump_config(config: dict) -> str:
    """
    Dump the encoded configuration string.
    """
    return sys.modules[__name__].dump_config(config)
