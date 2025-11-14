# -*- encoding: utf-8 -*-

import os
import importlib

os_dir = os.path.dirname(os.path.dirname(__file__))


def get_last_dir(path):
    """
    Return the last directory of the given path.
    """
    normalized_path = os.path.normpath(path)
    head, tail = os.path.split(normalized_path)
    return tail if tail else os.path.basename(head)


def inject_init():
    for root, dirs, files in os.walk(os_dir):
        for file in files:
            if file.endswith('.py') and file.startswith('_') and file != '__init__.py':
                _module_name = 'astraflux.{}.{}'.format(get_last_dir(root), file[:-3])
                importlib.import_module(_module_name).register()
