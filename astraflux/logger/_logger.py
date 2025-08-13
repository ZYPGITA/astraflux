# -*- encoding: utf-8 -*-

import os
import logging
from logging.handlers import TimedRotatingFileHandler

from astraflux.settings import *

_FMT = logging.Formatter(LOG.DEFAULT_VALUE_LOGS_FMT)
_SUFFIX = LOG.DEFAULT_VALUE_LOGS_SUFFIX

_LOGS_POOL = {}
_LOGS_LEVEL = logging.INFO
_LOGS_FILE_PATH = os.path.expanduser("~")


def _get_log_file_path(filename: str, task_id: str = None):
    if task_id is None:
        return os.path.join(_LOGS_FILE_PATH, f'{filename}.log')
    else:
        os.makedirs(os.path.join(_LOGS_FILE_PATH, f'{filename}'), exist_ok=True)
        return os.path.join(_LOGS_FILE_PATH, filename, f'{task_id}.log')


def _get_logger(filename: str, task_id: str = None) -> logging.Logger:
    """
    Get a logger instance for logging messages.
    Args:
        filename (str): The name of the log file.
        task_id (str, optional): The ID of the task. Defaults to None.
    Returns:
        logging.Logger: A logger instance.
    """
    handler = _get_log_file_path(filename, task_id)
    if handler not in _LOGS_POOL:
        _logger = logging.getLogger(handler)
        _logger.setLevel(_LOGS_LEVEL)
        _logger.propagate = False

        th = TimedRotatingFileHandler(filename=handler, when='MIDNIGHT', backupCount=7, encoding='utf-8')
        th.suffix = _SUFFIX
        th.setFormatter(_FMT)

        if not any(isinstance(h, logging.StreamHandler) for h in _logger.handlers):
            ch = logging.StreamHandler()
            ch.setFormatter(_FMT)
            _logger.addHandler(ch)

        _logger.addHandler(th)

        _LOGS_POOL[handler] = _logger
    return _LOGS_POOL[handler]


def initialization_logger(config: dict):
    """
    Initialize the logger with the given configuration.
    Args:
        config (dict): A dictionary containing the configuration.
    """
    global _LOGS_FILE_PATH, _LOGS_LEVEL
    _LOGS_FILE_PATH = os.path.join(config.get(KEY_ROOT_PATH), LOG.KEY_LOGS_PATH)
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    level = config.get(LOG.KEY_LOGS_CONFIG_NAME).get(LOG.KEY_LOGS_CONFIG_LEVEL)
    _LOGS_LEVEL = log_levels.get(level, logging.INFO)


def loguru(filename: str = None, task_id: str = None) -> logging.Logger:
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
    return _get_logger(filename=KEY_PROJECT_NAME, task_id=KEY_PROJECT_NAME)


def register():
    from astraflux.interface import logger
    logger.initialization_logger = initialization_logger
    logger.loguru = loguru

    import sys
    sys.modules['astraflux.interface.logger'] = logger
