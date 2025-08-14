# -*- encoding: utf-8 -*-

import sys

__all__ = [
    'initialization_nexusflow',
    'services_registry',
    'services_start'
]


def initialization_nexusflow(config: dict):
    """
    initialization astraflux
    """
    return sys.modules[__name__].initialization_nexusflow(config)


def services_registry(services: list):
    """
    Registers a list of services to be managed.

    Args:
        services (list): A list of services to be registered.
    """
    return sys.modules[__name__].services_registry(services)


def services_start():
    """
    Starts the service management process. Currently, this method is a placeholder
    and does not perform any actions.
    """
    return sys.modules[__name__].services_start()
