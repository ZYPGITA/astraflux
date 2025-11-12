# -*- encoding: utf-8 -*-
import abc
from typing import overload

from astraflux.interface.logger import get_logger


class Constructor(object):
    @property
    def name(self): return

    @property
    def ipaddr(self): return

    @property
    def version(self): return

    @property
    def logger(self) -> get_logger: return

    functions = []


class ServiceConstructor(abc.ABC, Constructor):

    @classmethod
    def setattr(cls, name, value):
        setattr(cls, name, value)

    def __call__(self):
        return self


class WorkerConstructor(abc.ABC, Constructor):

    @abc.abstractmethod
    def run(self, data): ...

    @classmethod
    def setattr(cls, name, value):
        setattr(cls, name, value)

    def __call__(self):
        return self


def init_global_vars(yaml_file: str, current_dir: str, root_path: str) -> dict:
    """
    Initialize global variables from a YAML file.
    Args:
        yaml_file (str): Path to the YAML file containing global variable definitions.
        current_dir (str): Current directory path.
        root_path: Root directory path.
    """
    return init_global_vars(yaml_file, current_dir, root_path)


def services_registry(services: list):
    """Legacy function for service registration."""
    return services_registry(services)


def services_start(yaml_config: str):
    """Legacy function for starting all services."""
    return services_start(yaml_config)
