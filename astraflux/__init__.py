# -*- coding: utf-8 -*-

import os
import importlib

from astraflux.interface import *


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
