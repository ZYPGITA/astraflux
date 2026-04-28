# -*- coding: utf-8 -*-

from astraflux.interface.astra_agents import function_tool

from astraflux.astra_agents.skill.dirs._core import (
    create_directory as _create_directory,
    remove_directory as _remove_directory,
    list_directory as _list_directory,
    rename_directory as _rename_directory,
    get_directory_info as _get_directory_info,
    set_permissions as _set_permissions,
    get_permissions as _get_permissions,
)


@function_tool
def create_directory(path: str, exist_ok: bool = True) -> str:
    """
    Create a directory and all necessary parent directories.

    Args:
        path (str): Directory path to create.
        exist_ok (bool): If True (default), no error if directory already exists.
                         If False, fails when directory exists.

    Returns:
        str: Status message.
    """
    return _create_directory(path, exist_ok)


@function_tool
def remove_directory(path: str, recursive: bool = False) -> str:
    """
    Remove a directory.

    Args:
        path (str): Directory path to remove.
        recursive (bool): If True, remove directory and all contents.
                          If False, only remove empty directories.

    Returns:
        str: Status message.
    """
    return _remove_directory(path, recursive)


@function_tool
def list_directory(path: str, pattern: str = None, recursive: bool = False, details: bool = True) -> str:
    """
    List contents of a directory with optional filtering.

    Args:
        path (str): Directory path to list.
        pattern (str, optional): Glob pattern (e.g. "*.py", "data*").
        recursive (bool): If True, list contents of all subdirectories.
        details (bool): If True, include size, modified time, and type.

    Returns:
        str: Formatted listing.
    """
    return _list_directory(path, pattern, recursive, details)


@function_tool
def rename_directory(src: str, dst: str, overwrite: bool = False) -> str:
    """
    Rename or move a directory.

    Args:
        src (str): Source directory path.
        dst (str): Destination directory path.
        overwrite (bool): If True, replace existing destination.

    Returns:
        str: Status message.
    """
    return _rename_directory(src, dst, overwrite)


@function_tool
def get_directory_info(path: str) -> str:
    """
    Show metadata and statistics for a directory.

    Args:
        path (str): Directory path to inspect.

    Returns:
        str: Detailed directory information (files, subdirs, size, permissions).
    """
    return _get_directory_info(path)


@function_tool
def set_permissions(path: str, mode: str = None, readonly: bool = None) -> str:
    """
    Change permissions of a file or directory.

    On Windows, the main operation is toggling the read-only attribute.
    On Linux/macOS, numeric modes (e.g. "755", "644") are supported.

    Args:
        path (str): Path to the file or directory.
        mode (str, optional): POSIX permission mode (3-digit octal, e.g. "755").
        readonly (bool, optional): Set or remove read-only attribute (Windows).

    Returns:
        str: Status message.
    """
    return _set_permissions(path, mode, readonly)


@function_tool
def get_permissions(path: str) -> str:
    """
    Show current permission information for a file or directory.

    Args:
        path (str): Path to inspect.

    Returns:
        str: Permission details (mode, bits, access flags).
    """
    return _get_permissions(path)
