# -*- encoding: utf-8 -*-
import logging


def get_logger(filename: str = None, task_id: str = None) -> logging.Logger:
    """
    Get a logger instance for logging messages.
    Args:
        filename (str): The name of the log file.
        task_id (str, optional): The ID of the task. Defaults to None.
    Returns:
        logging.Logger: A logger instance.
    """
    return get_logger(filename, task_id)
