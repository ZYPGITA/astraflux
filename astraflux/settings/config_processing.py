# -*- encoding: utf-8 -*-

from astraflux.inject import inject_implementation

__all__ = ['load_settings', 'current_dir', 'global_config', 'load_config', 'dump_config']


@inject_implementation()
def current_dir() -> str:
    """
    Return the current directory of the current working directory.
    """


@inject_implementation()
def global_config() -> dict:
    """
    Return the global configuration settings.
    """


@inject_implementation()
def load_settings(yaml_file: str, workspace: str) -> None:
    """
    Load settings from yaml file.
    :param yaml_file: yaml file path
    :param workspace: workspace path
    :return:
    """


@inject_implementation()
def load_config(encoded_config: str) -> dict:
    """
    Decode and load the encoded configuration string.

    Args:
        encoded_config (str): The encoded configuration string.

    Returns:
        dict: The decoded configuration dictionary.
    """


@inject_implementation()
def dump_config(config: dict) -> str:
    """
    Dump the encoded configuration string.
    """
