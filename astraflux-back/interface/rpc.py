# -*- encoding: utf-8 -*-


def generate_unique():
    """
    Generates a unique identifier.
    Returns:
        str: The generated identifier.
    """
    return generate_unique()


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
    return remote_call(service_name, method_name, **params)


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
    return proxy_call(service_name, method_name, **params)


def rpc_decorator(func):
    """
    Decorator for RPC functions.
    Args:
        func (function): The function to be decorated.
    Returns:
        function: The decorated function.
    """
    return rpc_decorator(func)


def service_running(service_cls):
    """
    Start a RabbitMQ consumer.
    Args:
        service_cls (class): The function to be called when a message is received.
    """
    return service_running(service_cls)
