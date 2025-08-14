# -*- encoding: utf-8 -*-
import sys
import logging

__all__ = ['initialization_logger', 'loguru']


def initialization_logger(config: dict):
    """
    Initialize the logger with the given configuration.
    Args:
        config (dict): A dictionary containing the configuration.
    """
    return sys.modules[__name__].initialization_logger(config)


def loguru(filename: str = None, task_id: str = None) -> logging.Logger:
    """
    Get a logger instance for logging messages.
    Args:
        filename (str): The name of the log file.
        task_id (str, optional): The ID of the task. Defaults to None.
    Returns:
        logging.Logger: A logger instance.
    """
    return sys.modules[__name__].loguru(filename, task_id)
