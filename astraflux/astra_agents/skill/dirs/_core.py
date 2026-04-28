# -*- coding: utf-8 -*-

import os
import stat
import shutil
from pathlib import Path
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# Pure functions (callable from tests without FunctionTool)
# ═══════════════════════════════════════════════════════════

def create_directory(path: str, exist_ok: bool = True) -> str:
    """Create a directory and all necessary parent directories."""
    try:
        os.makedirs(path, exist_ok=exist_ok)
        status = "already exists" if os.path.isdir(path) and exist_ok else "created"
        return f"Directory '{path}' {status}."
    except FileExistsError:
        return f"Directory '{path}' already exists (use exist_ok=True to suppress this)."
    except PermissionError:
        return f"Permission denied: Cannot create directory '{path}'."
    except OSError as e:
        return f"Failed to create directory: {str(e)}"


def remove_directory(path: str, recursive: bool = False) -> str:
    """Remove a directory."""
    try:
        if recursive:
            shutil.rmtree(path)
        else:
            os.rmdir(path)
        return f"Directory '{path}' removed."
    except FileNotFoundError:
        return f"Directory not found: '{path}'."
    except NotADirectoryError:
        return f"Not a directory: '{path}'."
    except OSError as e:
        if "not empty" in str(e):
            return f"Directory '{path}' is not empty. Use recursive=True to remove it and all contents."
        return f"Failed to remove directory: {str(e)}"


def list_directory(path: str, pattern: str = None, recursive: bool = False, details: bool = True) -> str:
    """List contents of a directory with optional filtering."""
    try:
        if not os.path.isdir(path):
            return f"Not a directory or not found: '{path}'."

        entries = []
        p = Path(path)

        if recursive:
            iterator = p.rglob(pattern) if pattern else p.rglob("*")
        else:
            iterator = p.glob(pattern) if pattern else p.iterdir()

        for entry in sorted(iterator, key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                stat_info = entry.stat()
                is_dir = entry.is_dir()
                type_indicator = "[DIR]" if is_dir else "[FILE]"

                if details:
                    size = stat_info.st_size
                    size_str = f"{size / 1024 / 1024:.1f} MB" if size >= 1024 * 1024 else (f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B")
                    time_str = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
                    entries.append(f"  {type_indicator}  {entry.name:<30s}  {size_str:>10s}  {time_str}")
                else:
                    entries.append(f"  {type_indicator}  {entry.name}")

            except PermissionError:
                entries.append(f"  [?]  {entry.name}  (permission denied)")
            except OSError:
                entries.append(f"  [?]  {entry.name}  (access error)")

        if not entries:
            return f"Directory '{path}' is empty."

        return f"Contents of '{path}' ({len(entries)} items):\n" + "\n".join(entries)

    except PermissionError:
        return f"Permission denied: Cannot list directory '{path}'."
    except FileNotFoundError:
        return f"Directory not found: '{path}'."
    except Exception as e:
        return f"Failed to list directory: {str(e)}"


def rename_directory(src: str, dst: str, overwrite: bool = False) -> str:
    """Rename or move a directory."""
    try:
        if not os.path.exists(src):
            return f"Source not found: '{src}'."
        if not os.path.isdir(src):
            return f"Source is not a directory: '{src}'."

        if os.path.exists(dst):
            if not overwrite:
                return f"Destination already exists: '{dst}'. Use overwrite=True to replace."
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)

        os.rename(src, dst)
        return f"Directory renamed: '{src}' -> '{dst}'."

    except PermissionError:
        return f"Permission denied: Cannot rename directory '{src}'."
    except OSError as e:
        return f"Failed to rename directory: {str(e)}"


def get_directory_info(path: str) -> str:
    """Show metadata and statistics for a directory."""
    try:
        if not os.path.isdir(path):
            return f"Not a directory or not found: '{path}'."

        p = Path(path)
        stat_info = p.stat()

        file_count = 0
        dir_count = 0
        total_size = 0
        for entry in p.rglob("*"):
            try:
                if entry.is_dir():
                    dir_count += 1
                else:
                    file_count += 1
                    total_size += entry.stat().st_size
            except (OSError, PermissionError):
                pass

        size_str = (f"{total_size / 1024 / 1024 / 1024:.2f} GB" if total_size >= 1073741824 else
                    f"{total_size / 1024 / 1024:.2f} MB" if total_size >= 1048576 else
                    f"{total_size / 1024:.2f} KB" if total_size >= 1024 else
                    f"{total_size} B")

        lines = [
            f"Directory: {path}",
            f"Absolute:  {os.path.abspath(path)}",
            f"Created:   {datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}",
            f"Modified:  {datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
            f"Files:     {file_count}",
            f"Subdirs:   {dir_count}",
            f"Total:     {size_str}",
            f"Readable:  {os.access(path, os.R_OK)}",
            f"Writable:  {os.access(path, os.W_OK)}",
        ]
        return "\n".join(lines)

    except PermissionError:
        return f"Permission denied: Cannot access '{path}'."
    except FileNotFoundError:
        return f"Path not found: '{path}'."
    except Exception as e:
        return f"Failed to get directory info: {str(e)}"


def set_permissions(path: str, mode: str = None, readonly: bool = None) -> str:
    """Change permissions of a file or directory."""
    try:
        if not os.path.exists(path):
            return f"Path not found: '{path}'."

        if mode is not None:
            try:
                mode_int = int(str(mode), 8)
                os.chmod(path, mode_int)
            except ValueError:
                return f"Invalid mode '{mode}'. Must be a 3-digit octal string (e.g. '755', '644')."

        if readonly is not None:
            import platform
            if platform.system() == "Windows":
                if readonly:
                    os.chmod(path, os.stat(path).st_mode & ~stat.S_IWRITE)
                else:
                    os.chmod(path, os.stat(path).st_mode | stat.S_IWRITE)
            else:
                if mode is None:
                    return f"On this platform, use the 'mode' parameter to set permissions."

        changes = []
        if mode:
            changes.append(f"mode={mode}")
        if readonly is not None:
            changes.append(f"readonly={readonly}")

        return f"Permissions updated for '{path}': {', '.join(changes)}."

    except PermissionError:
        return f"Permission denied: Cannot change permissions for '{path}'."
    except Exception as e:
        return f"Failed to set permissions: {str(e)}"


def get_permissions(path: str) -> str:
    """Show current permission information for a file or directory."""
    try:
        if not os.path.exists(path):
            return f"Path not found: '{path}'."

        stat_info = os.stat(path)
        import platform

        lines = [f"Path: {path}", f"Type: {'Directory' if os.path.isdir(path) else 'File'}"]

        mode = stat_info.st_mode
        lines.append(f"Mode: {oct(stat.S_IMODE(mode))}")

        perms = ""
        perms += "r" if mode & stat.S_IRUSR else "-"
        perms += "w" if mode & stat.S_IWUSR else "-"
        perms += "x" if mode & stat.S_IXUSR else "-"
        perms += "r" if mode & stat.S_IRGRP else "-"
        perms += "w" if mode & stat.S_IWGRP else "-"
        perms += "x" if mode & stat.S_IXGRP else "-"
        perms += "r" if mode & stat.S_IROTH else "-"
        perms += "w" if mode & stat.S_IWOTH else "-"
        perms += "x" if mode & stat.S_IXOTH else "-"
        lines.append(f"Bits:  {perms}")

        if platform.system() == "Windows":
            readonly = bool(stat_info.st_file_attributes & stat.FILE_ATTRIBUTE_READONLY)
            lines.append(f"Windows Read-Only: {readonly}")

        lines.append(f"Owner Readable: {os.access(path, os.R_OK)}")
        lines.append(f"Owner Writable: {os.access(path, os.W_OK)}")
        lines.append(f"Owner Executable: {os.access(path, os.X_OK)}")

        return "\n".join(lines)

    except PermissionError:
        return f"Permission denied: Cannot access '{path}'."
    except FileNotFoundError:
        return f"Path not found: '{path}'."
    except Exception as e:
        return f"Failed to get permissions: {str(e)}"
