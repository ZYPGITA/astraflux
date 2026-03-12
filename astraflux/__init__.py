# -*- coding: utf-8 -*-

import os
import importlib

from astraflux.interface import *
from astraflux.definitions.globals import get_current_dir
from astraflux.definitions.constructor import ServiceConstructor, WorkerConstructor

__all__ = [
    'AstraFlux',
    'get_current_dir',
    'ServiceConstructor',
    'WorkerConstructor',
    'snowflake_id',
    'logger',
    'rabbitmq_send_message',
    'rabbitmq_receive_message',
    'ipaddr',
    'devices_id',
    'date_time_obj',
    'format_converted_time',
    'converted_time',
    'rpc_decorator',
    'proxy_call',
    'start_consumer',
    'mongodb_find_one_and_update_from_task',
    'mongodb_delete_from_task',
    'mongodb_find_from_task',
    'mongodb_find_paginated_from_task',
    'redis_store_worker_data',
    'redis_get_max_process',
    'redis_update_max_process',
    'redis_increment_max_process',
    'redis_get_run_process_count',
    'redis_get_all_run_process',
    'redis_get_available_slots',
    'redis_get_worker_status',
    'redis_get_full_worker_data',
    'redis_scan_workers_by_service',
    'start_scheduler',
    'stop_scheduler',
    'add_scheduled_job',
    'remove_scheduled_job'
]


class AstraFlux:
    _instance = None

    def __init__(self, yaml_path: str, current_dir: str):
        """
        :param yaml_path: yaml file path
        :param current_dir: workspace path
        """
        if not hasattr(self, '_initialized'):
            self.yaml_path = yaml_path
            self.current_dir = current_dir

            from .definitions.globals import set_current_dir, set_yaml_path

            set_current_dir(current_dir)
            set_yaml_path(yaml_path)

            from . import fixtures

            for _ in os.listdir(fixtures.__path__[0]):

                if _.startswith('__'):
                    continue

                if _.startswith('_') and _.endswith('.py'):
                    importlib.import_module('astraflux.fixtures.' + _.strip('.py'))

            _initialized = True

    def __new__(cls, *args, **kwargs):
        """
        The underlying layer of the intelligent architecture framework implements dependency injection,
        interface generation, function factory initialization, and runtime environment
        """

        if not cls._instance:
            cls._instance = super().__new__(cls)

            cls._instance.__init__(*args, **kwargs)

        return cls._instance
