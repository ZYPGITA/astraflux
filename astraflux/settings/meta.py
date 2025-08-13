# -*- encoding: utf-8 -*-

import abc
import logging

__all__ = ['ServiceConstructor', 'WorkerConstructor']


class Meta(abc.ABC):

    @property
    @abc.abstractmethod
    def task_create(self): ...

    @property
    @abc.abstractmethod
    def task_create_and_run(self): ...

    @property
    @abc.abstractmethod
    def subtask_create(self): ...

    @property
    @abc.abstractmethod
    def loguru(self): ...

    @property
    @abc.abstractmethod
    def name(self): ...


class ServiceMeta(Meta):

    @property
    @abc.abstractmethod
    def service_name(self): ...

    @property
    @abc.abstractmethod
    def service_ipaddr(self): ...

    @property
    @abc.abstractmethod
    def service_version(self): ...


class WorkerMeta(Meta):

    @property
    @abc.abstractmethod
    def worker_name(self): ...

    @property
    @abc.abstractmethod
    def worker_version(self): ...

    @property
    @abc.abstractmethod
    def worker_ipaddr(self): ...

    @abc.abstractmethod
    def run(self, data): ...


class ServiceConstructor(ServiceMeta):
    """
    ServiceConstructor is a class that represents a constructor for a service
    """
    functions: list = []
    service_name: str = None
    service_ipaddr: str = None
    service_version: str = None

    name: str = None
    loguru: logging.Logger = None

    def task_create(self): ...

    def task_create_and_run(self): ...

    def subtask_create(self): ...

    @classmethod
    def setattr(cls, name, value):
        setattr(cls, name, value)

    def __call__(self):
        return self


class WorkerConstructor(WorkerMeta):
    """
    WorkerConstructor is a class that represents a constructor for a worker.
    It also contains a method called run, which takes in a body and runs the worker with the given body.
    """
    functions: list = []

    worker_name: str = None
    worker_ipaddr: str = None
    worker_version: str = None

    name: str = None
    loguru: logging.Logger = None

    def task_create(self): ...

    def task_create_and_run(self): ...

    def subtask_create(self): ...

    @classmethod
    def setattr(cls, name, value):
        setattr(cls, name, value)

    def run(self, body):
        """
        Runs the worker with the given body.
        Args:
            body (dict): The body of the worker.
        """

    def __call__(self):
        return self
