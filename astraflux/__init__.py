# -*- encoding: utf-8 -*-

_INITIALIZED = False

if not _INITIALIZED:
    from astraflux.inject import inject_init

    inject_init()
    _INITIALIZED = True

from .meta import *
from .interface import *

_version_ = '1.0.0'


class AstraFlux(object):
    """
    AstraFlux Framework
    """
    _instance = None

    def __init__(self, yaml_file: str, workspace: str):
        """
        :param yaml_file: yaml file path
        :param workspace: workspace path
        """
        if not hasattr(self, '_initialized'):
            load_settings(yaml_file=yaml_file, workspace=workspace)
            initialization_nexusflow(config=global_config())

            _initialized = True

    def __new__(cls, *args):
        """
        The underlying layer of the intelligent architecture framework implements dependency injection,
        interface generation, function factory initialization, and runtime environment
        """

        if not cls._instance:
            cls._instance = super().__new__(cls)

            from .inject import inject_init
            inject_init()

            cls._instance.__init__(*args)

        return cls._instance

    @staticmethod
    def registry(services: list):
        services_registry(services=services)

    @staticmethod
    def start():
        services_start()
