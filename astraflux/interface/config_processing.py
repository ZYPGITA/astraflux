# -*- encoding: utf-8 -*-

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
    return current_dir()


def global_config() -> dict:
    """
    Return the global configuration settings.
    """
    return global_config()


def load_settings(yaml_file: str, workspace: str) -> None:
    """
    Load settings from yaml file.
    :param yaml_file: yaml file path
    :param workspace: workspace path
    :return:
    """
    return load_settings(yaml_file, workspace)


def load_config(encoded_config: str) -> dict:
    """
    Decode and load the encoded configuration string.

    Args:
        encoded_config (str): The encoded configuration string.

    Returns:
        dict: The decoded configuration dictionary.
    """
    return load_config(encoded_config)


def dump_config(config: dict) -> str:
    """
    Dump the encoded configuration string.
    """
    return dump_config(config)
