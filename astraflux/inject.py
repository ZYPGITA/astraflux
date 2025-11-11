# -*- encoding: utf-8 -*-

import os
import importlib


def get_last_dir(path):
    """
    Return the last directory of the given path.
    """
    normalized_path = os.path.normpath(path)
    head, tail = os.path.split(normalized_path)
    return tail if tail else os.path.basename(head)


def inject_init(root_path):
    """
    Inject the register method of the modules in the given root path.
    """
    _globals = importlib.import_module('astraflux.definitions._globals')
    _globals.register()

    for root, dirs, files in os.walk(root_path):
        if '_globals' in root:
            continue

        for file in files:
            if file.endswith('.py') and file.startswith('_') and file != '__init__.py':
                _module_name = 'astraflux.{}.{}'.format(get_last_dir(root), file[:-3])
                importlib.import_module(_module_name).register()

    _globals.INITIALIZED = True
