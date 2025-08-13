# -*- encoding: utf-8 -*-

import importlib

__all__ = ['inject_implementation']


def inject_implementation():
    """
    Inject NexusFlow implementation
    """

    def wrapper(func):
        def wrapped(*args, **kwargs):
            _module = importlib.import_module(func.__module__)
            _class = getattr(_module, func.__name__)
            return _class(*args, **kwargs)

        return wrapped

    return wrapper
