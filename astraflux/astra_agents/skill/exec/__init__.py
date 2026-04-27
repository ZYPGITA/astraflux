# -*- coding: utf-8 -*-

import platform

from agents import function_tool

from astraflux.astra_agents.skill.exec._win import Run as WinRun
from astraflux.astra_agents.skill.exec._unix import Run as UnixRun
from astraflux.astra_agents.skill.exec._win import is_wsl as _win_is_wsl_flag

_PLATFORM = platform.system().lower()  # "windows", "linux", "darwin"


def _detect_platform() -> str:
    """
    Return a platform category string used for routing.

    Returns one of: "windows", "linux", "macos", "wsl".

    "wsl" is returned only when the current process is *inside* WSL.
    To run WSL commands *from* Windows, use the 'wsl' shell option
    in the execute() function.
    """
    if _PLATFORM == "windows":
        return "windows"
    if _PLATFORM == "darwin":
        return "macos"
    if _PLATFORM == "linux" and _win_is_wsl_flag():
        return "wsl"
    if _PLATFORM == "linux":
        return "linux"
    return _PLATFORM  # fallback


def _is_wsl_from_windows() -> bool:
    """Check if WSL is accessible from the Windows host."""
    if _PLATFORM != "windows":
        return False
    from astraflux.astra_agents.skill.exec._win import has_wsl_support
    return has_wsl_support()


# ── Public API ─────────────────────────────────────────────────────────

@function_tool(strict_mode=False)
def execute(
        command: str,
        cwd: str = "",
        timeout: int = 60,
        env: str = "",
        shell: str = "auto") -> dict:
    """
    Execute a shell command on any platform (Windows / Linux / macOS / WSL).

    This is the **unified entry point** — it auto-detects the host OS
    and dispatches to the correct backend. You don't need to know which
    platform you're on; just pass your command and it works.

    Platform detection logic:
      - **Windows**: routes to cmd.exe / PowerShell / PowerShell Core
      - **macOS / Linux**: routes to sh / bash / zsh / fish
      - **WSL** (inside WSL): routes to Linux backend automatically
      - **WSL from Windows**: pass ``shell="wsl"`` to run Linux commands
        through the WSL interop layer

    Args:
        command (str): The command or script to execute. Supports:
            - Single-line commands: ``"ls -la"``, ``"dir /b"``
            - Multi-line scripts (with or without a shebang):
              ``"#!/bin/bash\nfor f in *; do echo $f; done"``
            - Shebangs trigger automatic shell detection:
              ``"#!/usr/bin/env python3\nprint('hello')"``  (runs with python3)

        cwd (str, optional): Working directory. If empty string, defaults
            to the current process's working directory.

        timeout (int, optional): Maximum seconds to wait for the command to
            complete. Use 0 for no timeout. Default: 60.

        env (str, optional): Extra environment variables as a JSON string
            (e.g. ``'{"MY_VAR": "value"}'``). Empty string means no extras.

        shell (str, optional): Which shell/interpreter to use.
            - ``"auto"`` (default): auto-detect from shebang or system default
            - **Windows**: ``"cmd"``, ``"powershell"``, ``"pwsh"``, ``"wsl"``
            - **Unix**: ``"sh"``, ``"bash"``, ``"zsh"``, ``"fish"``, or a
              custom path like ``"/opt/homebrew/bin/bash"``

    Returns:
        dict: A result dictionary with the following keys:
            - ``stdout`` (str): Standard output from the command.
            - ``stderr`` (str): Standard error from the command.
            - ``returncode`` (int): Exit code (0 = success).
            - ``shell_used`` (str): The shell that actually ran the command.
            - ``timed_out`` (bool): Whether the command was killed due to
              timeout.
    """
    import json

    # Normalise optional params from string defaults to Python None
    resolved_cwd = cwd if cwd else None
    resolved_timeout = timeout if timeout else None
    resolved_env = json.loads(env) if env else None

    platform_name = _detect_platform()

    # ── Windows ──
    if platform_name == "windows":
        # "wsl" shell on Windows means run via WSL interop
        if shell.lower() == "wsl":
            if not _is_wsl_from_windows():
                return {
                    "stdout": "",
                    "stderr": "WSL is not available on this Windows system. "
                              "Install WSL first: https://learn.microsoft.com/en-us/windows/wsl/install",
                    "returncode": -1,
                    "shell_used": "wsl",
                    "timed_out": False,
                }
            # Run the command through wsl.exe
            return WinRun.run(f"wsl {command}", cwd=resolved_cwd,
                              timeout=resolved_timeout, env=resolved_env,
                              shell="cmd")
        return WinRun.run(command, cwd=resolved_cwd, timeout=resolved_timeout,
                          env=resolved_env, shell=shell)

    # ── Linux / macOS / WSL (inside WSL) ──
    # All go to the Unix backend
    return UnixRun.run(command, cwd=resolved_cwd, timeout=resolved_timeout,
                       env=resolved_env, shell=shell)
