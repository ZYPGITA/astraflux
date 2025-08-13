# -*- encoding: utf-8 -*-
import logging
from astraflux.inject import inject_implementation

__all__ = ['initialization_logger', 'loguru']


@inject_implementation()
def initialization_logger(config: dict):
    """
    Initialize the logger with the given configuration.
    Args:
        config (dict): A dictionary containing the configuration.
    """


@inject_implementation()
def loguru(filename: str, task_id: str = None) -> logging.Logger:
    """
    Get a logger instance for logging messages.
    Args:
        filename (str): The name of the log file.
        task_id (str, optional): The ID of the task. Defaults to None.
    Returns:
        logging.Logger: A logger instance.
    """
