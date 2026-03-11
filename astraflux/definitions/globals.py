# -*- coding: utf-8 -*-


_YAML_PATH = None
_CURRENT_DIR = None


def set_yaml_path(yaml_path: str):
    global _YAML_PATH
    _YAML_PATH = yaml_path


def set_current_dir(current_dir: str):
    global _CURRENT_DIR
    _CURRENT_DIR = current_dir


def get_yaml_path():
    global _YAML_PATH
    return _YAML_PATH


def get_current_dir():
    global _CURRENT_DIR
    return _CURRENT_DIR
