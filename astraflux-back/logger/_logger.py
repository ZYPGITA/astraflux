# -*- encoding: utf-8 -*-


import os
import logging
from logging.handlers import TimedRotatingFileHandler

from astraflux.definitions.constants import *
from astraflux.interface.definitions import get_logs_path, get_log_level

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR
}

_LOGS_POOL = {}


def _get_log_file_path(filename: str, task_id: str = None):
    if task_id is None:
        return os.path.join(get_logs_path(), f'{filename}.log')
    else:
        os.makedirs(os.path.join(get_logs_path(), f'{filename}'), exist_ok=True)
        return os.path.join(get_logs_path(), filename, f'{task_id}.log')


def _get_logger(filename: str, task_id: str = None) -> logging.Logger:
    """
    Get a logger instance for logging messages.
    Args:
        filename (str): The name of the log file.
        task_id (str, optional): The ID of the task. Defaults to None.
    Returns:
        logging.Logger: A logger instance.
    """
    level = get_log_level()
    log_formatter = logging.Formatter(DefaultValues.LOG.FMT)

    handler = _get_log_file_path(filename, task_id)

    if handler not in _LOGS_POOL:
        _logger = logging.getLogger(handler)
        _logger.setLevel(level)
        _logger.propagate = False

        th = TimedRotatingFileHandler(filename=handler, when='MIDNIGHT', backupCount=7, encoding='utf-8')
        th.suffix = DefaultValues.LOG.SUFFIX
        th.setFormatter(log_formatter)

        if not any(isinstance(h, logging.StreamHandler) for h in _logger.handlers):
            ch = logging.StreamHandler()
            ch.setFormatter(log_formatter)
            _logger.addHandler(ch)

        _logger.addHandler(th)

        _LOGS_POOL[handler] = _logger
    return _LOGS_POOL[handler]


def get_logger(filename: str = None, task_id: str = None) -> logging.Logger:
    """
    Get a logger instance for logging messages.
    Args:
        filename (str): The name of the log file.
        task_id (str, optional): The ID of the task. Defaults to None.
    Returns:
        logging.Logger: A logger instance.
    """
    if task_id and filename:
        return _get_logger(filename, task_id)
    return _get_logger(filename=PROJECT_NAME, task_id=PROJECT_NAME)


def register():
    from astraflux.interface import logger
    logger.get_logger = get_logger

    if REPLACE_SYS_MODULE:
        import sys
        sys.modules['astraflux.interface.logger'] = logger
