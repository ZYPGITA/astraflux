# -*- encoding: utf-8 -*-

import os
import sys
import inspect
import importlib
from typing import Union

from astraflux.settings import *
from astraflux.interface import *

__all__ = ['Build']


class Build:
    """
    Builds a worker by importing the specified class path and setting its attributes.
    """

    def __init__(self, config: dict, cls_path: str, build_type: str, constructor):
        self.config = config
        self.cls_path = cls_path
        self.build_type = build_type
        self.constructor = constructor

        initialization_mongo(config=config)
        initialization_redis(config=config)
        initialization_rabbitmq(config=config)
        initialization_rpc_proxy(config=config)
        initialization_logger(config=config)
        initialization_scheduler(config=config)

    def get_build_attr(self):
        """
        Imports the specified class path and returns its attributes.
        Returns:
            dict: A dictionary containing the attributes of the imported class.
        """
        if self.build_type == 'service':
            class_name = RPC.KEY_FUNCTION_RPC
        else:
            class_name = RPC.KEY_FUNCTION_WORKER

        script_path = os.path.dirname(self.cls_path)
        sys.path.insert(0, script_path)

        module_name, _file_extension = os.path.splitext(os.path.basename(self.cls_path))

        module = __import__(module_name, globals=globals(), locals=locals(), fromlist=[class_name])

        importlib.reload(module)
        cls = getattr(module, class_name)
        return cls.__dict__

    def build_functions(self, attrs):
        """
        Imports the specified class path and sets its attributes.
        """
        functions = {}
        for function_name in attrs:
            if function_name.startswith('__') is False:
                function = attrs[function_name]

                if type(function) in [type(lambda: None)]:
                    params = []
                    function = rpc_decorator(function)
                    signa = inspect.signature(function)
                    for name, param in signa.parameters.items():
                        if name != RPC.KEY_FUNCTION_SELF:
                            default_value = param.default
                            if param.default is inspect.Parameter.empty:
                                default_value = None

                            params.append({
                                RPC.KEY_FUNCTION_PARAM_NAME: name,
                                RPC.KEY_FUNCTION_PARAM_DEFAULT_VALUE: default_value
                            })

                    functions.setdefault(function_name, params)
                self.constructor.setattr(function_name, function)
        self.constructor.functions = functions

    def build(self, task_id: str = None) -> Union[ServiceConstructor, WorkerConstructor]:
        """
        Builds a worker by importing the specified class path and setting its attributes.
        Returns:
            ServiceConstructor: The constructed worker object.
        """
        attrs = self.get_build_attr()
        self.build_functions(attrs)

        self.constructor.subtask_create = subtask_create
        self.constructor.task_create = task_submit_databases
        self.constructor.task_create_and_run = task_submit_databases_and_send

        self.constructor.worker_ipaddr = get_ipaddr()
        self.constructor.service_ipaddr = get_ipaddr()
        self.constructor.worker_version = get_converted_time()
        self.constructor.service_version = get_converted_time()
        self.constructor.worker_name = attrs.get(BUILD.KEY_WORKER_NAME)
        self.constructor.service_name = attrs.get(BUILD.KEY_SERVICE_NAME)

        if self.build_type == 'service':
            self.constructor.name = '{}_{}'.format(KEY_PROJECT_NAME, self.constructor.service_name)

            self.constructor.loguru = loguru(filename=KEY_PROJECT_NAME, task_id=self.constructor.service_name)
        else:
            self.constructor.name = '{}_{}'.format(KEY_PROJECT_NAME, self.constructor.worker_name)

            if task_id is None:
                self.constructor.loguru = loguru(filename=KEY_PROJECT_NAME, task_id=self.constructor.worker_name)
            else:
                self.constructor.loguru = loguru(filename=self.constructor.worker_name, task_id=task_id)

        return self.constructor
