# -*- encoding: utf-8 -*-

import os
import sys
import inspect
import importlib
from typing import Union

from astraflux.definitions.constants import *
from astraflux.interface.core import ServiceConstructor, WorkerConstructor

from astraflux.interface.rpc import rpc_decorator
from astraflux.interface.logger import get_logger
from astraflux.interface.utils import get_ipaddr, get_converted_time

__all__ = ['Build']


class Build:
    """
     Service and Worker Builder for Dynamic Component Construction.

     Dynamically imports service/worker classes, discovers RPC functions,
     and configures component attributes with proper dependency injection.

     This class handles the dynamic loading of service and worker classes
     from specified file paths, automatically discovers callable methods,
     wraps them with RPC decorators, and configures the component with
     necessary attributes like IP address, version, and logging.

     Args:
         class_path (str): File path to the service/worker class definition
         component_type (str): Type of component - 'service' or 'worker'
         constructor: Constructor class (ServiceConstructor or WorkerConstructor)
     """

    def __init__(self, class_path: str, component_type: str, constructor):
        """
        Initialize the ServiceBuilder with configuration and component details.

        Args:
            class_path: Path to the Python file containing the component class
            component_type: Type of component ('service' or 'worker')
            constructor: Constructor class for building the component instance
        """
        self.class_path = class_path
        self.component_type = component_type
        self.constructor = constructor

    def import_component_class(self):
        """
        Imports the specified class path and returns its attributes.
        Returns:
            dict: A dictionary containing the attributes of the imported class.
        """
        if self.component_type == 'service':
            class_name = DEFINITIONS.RPC.FUNCTION_RPC
        else:
            class_name = DEFINITIONS.RPC.FUNCTION_WORKER

        script_path = os.path.dirname(self.class_path)
        sys.path.insert(0, script_path)

        module_name, _file_extension = os.path.splitext(os.path.basename(self.class_path))

        module = __import__(module_name, globals=globals(), locals=locals(), fromlist=[class_name])

        importlib.reload(module)
        cls = getattr(module, class_name)
        return cls.__dict__

    def register_functions(self, attributes):
        """
        Discover and register callable functions with RPC decorators.

        Iterates through class attributes to find callable methods,
        wraps them with RPC decorators, extracts parameter information,
        and injects them into the constructor.

        Args:
            attributes: Dictionary of class attributes to process
        """
        functions = {}
        for function_name in attributes:
            if function_name.startswith('__') is False:
                function = attributes[function_name]

                if type(function) in [type(lambda: None)]:
                    params = []
                    function = rpc_decorator(function)
                    signa = inspect.signature(function)
                    for name, param in signa.parameters.items():
                        if name != DEFINITIONS.RPC.FUNCTION_SELF:
                            default_value = param.default
                            if param.default is inspect.Parameter.empty:
                                default_value = None

                            params.append({
                                DEFINITIONS.RPC.FUNCTION_PARAM_NAME: name,
                                DEFINITIONS.RPC.FUNCTION_PARAM_DEFAULT_VALUE: default_value
                            })

                    functions.setdefault(function_name, params)
                self.constructor.setattr(function_name, function)
        self.constructor.functions = functions

    def build_component(self, task_id: str = None) -> Union[ServiceConstructor, WorkerConstructor]:
        """
        Build and configure the service or worker component.

        This is the main entry point that orchestrates the complete
        component building process including class import, function
        registration, and attribute configuration.

        Args:
            task_id: Optional task identifier for worker instances

        Returns:
            Fully configured ServiceConstructor or WorkerConstructor instance

        Raises:
            RuntimeError: If component building fails at any stage
        """
        attrs = self.import_component_class()
        self.register_functions(attrs)

        self.constructor.ipaddr = get_ipaddr()
        self.constructor.version = get_converted_time()
        self.constructor.service_name = attrs.get(DEFINITIONS.BUILD.SERVICE_NAME)
        self.constructor.worker_name = attrs.get(DEFINITIONS.BUILD.WORKER_NAME)

        if self.component_type == 'service':
            self.constructor.name = '{}_{}'.format(PROJECT_NAME, self.constructor.service_name)

            self.constructor.logger = get_logger(filename=PROJECT_NAME, task_id=self.constructor.service_name)
        else:
            self.constructor.name = '{}_{}'.format(PROJECT_NAME, self.constructor.worker_name)

            if task_id is None:
                self.constructor.logger = get_logger(filename=PROJECT_NAME, task_id=self.constructor.worker_name)
            else:
                self.constructor.logger = get_logger(filename=self.constructor.worker_name, task_id=task_id)

        return self.constructor
