# -*- encoding: utf-8 -*-
from astraflux.inject import inject_implementation

__all__ = [
    'initialization_rpc_proxy',
    'generate_unique',
    'remote_call',
    'proxy_call',
    'rpc_decorator',
    'service_running'
]


@inject_implementation()
def initialization_rpc_proxy(config: dict):
    """
    Initialize the logger with the given configuration.
    Args:
        config (dict): A dictionary containing the configuration.
    """


@inject_implementation()
def generate_unique():
    """
    Generates a unique identifier.
    Returns:
        str: The generated identifier.
    """


@inject_implementation()
def remote_call(service_name: str, method_name: str, **params):
    """
    Makes a remote procedure call to the specified service and method with the given parameters.

    Args:
        service_name (str): The name of the service to call.
        method_name (str): The name of the method to call.
        **params: Arbitrary keyword arguments to pass to the method.

    Returns:
        Any: The result of the remote procedure call.
    """


@inject_implementation()
def proxy_call(service_name: str, method_name: str, **params):
    """
    Makes a remote procedure call to the specified service and method with the given parameters.

    Args:
        service_name (str): The name of the service to call.
        method_name (str): The name of the method to call.
        **params: Arbitrary keyword arguments to pass to the method.

    Returns:
        Any: The result of the remote procedure call.
    """


@inject_implementation()
def rpc_decorator(func):
    """
    Decorator for RPC functions.
    Args:
        func (function): The function to be decorated.
    Returns:
        function: The decorated function.
    """


@inject_implementation()
def service_running(service_cls, config):
    """
    Start a RabbitMQ consumer.
    Args:
        config (dict): The AMQP URL for the RabbitMQ server.
        service_cls (class): The function to be called when a message is received.
    """
