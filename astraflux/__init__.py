# -*- encoding: utf-8 -*-
"""
@author: yanPing
@email: zyphhxx18@foxmail.com
@date: 2025-11-8

AstraFlux Framework
    A lightweight, high-performance, and highly scalable intelligent architecture framework.
    It provides a complete set of tools and libraries to help developers build and deploy
    intelligent applications quickly and easily.
"""
import os

_ROOT_DIR = os.path.dirname(__file__)
_INITIALIZED = False

"""
Global Initializer
    Initialize the global environment of the framework.
    It will initialize the global environment of the framework, including the configuration,
    the service registry, and the function factory.
"""
if not _INITIALIZED:
    from astraflux.inject import inject_init

    inject_init(_ROOT_DIR)
    _INITIALIZED = True

from astraflux.interface import *


class AstraFlux(object):
    _instance = None

    def __init__(self, yaml_file: str, current_dir: str):
        """
        :param yaml_file: yaml file path
        :param current_dir: workspace path
        """
        if not hasattr(self, '_initialized'):
            init_global_vars(yaml_file=yaml_file, current_dir=current_dir, root_path=_ROOT_DIR)

            _initialized = True

    def __new__(cls, *args, **kwargs):
        """
        The underlying layer of the intelligent architecture framework implements dependency injection,
        interface generation, function factory initialization, and runtime environment
        """

        if not cls._instance:
            cls._instance = super().__new__(cls)
            inject_init(_ROOT_DIR)

            cls._instance.__init__(*args, **kwargs)

        return cls._instance
