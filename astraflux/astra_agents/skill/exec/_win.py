# -*- coding: utf-8 -*-
"""
Windows command execution module.

Supports:
  - cmd.exe (batch commands, .bat/.cmd scripts)
  - PowerShell / pwsh (.ps1 scripts)
  - PowerShell Core (pwsh) when available
  - Windows Subsystem for Linux (wsl), detected automatically
"""

import os
import sys
import subprocess
import shlex
import tempfile
from pathlib import Path


def _which(program: str) -> str | None:
    """Locate a program in PATH, cross-platform."""
    which_cmd = "where" if sys.platform == "win32" else "which"
    try:
        result = subprocess.run(
            [which_cmd, program],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


# ── detection helpers ──────────────────────────────────────────────────

def is_wsl() -> bool:
    """Detect if we're running *inside* WSL."""
    if sys.platform != "linux":
        return False
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except (FileNotFoundError, OSError):
        return False


def is_windows() -> bool:
    """Detect if the current system is Windows."""
    return sys.platform == "win32"


def has_wsl_support() -> bool:
    """Check if Windows host has WSL available."""
    if not is_windows():
        return False
    return _which("wsl") is not None


def has_powershell() -> bool:
    """Check if PowerShell (not cmd) is available."""
    return _which("powershell") is not None


def has_pwsh() -> bool:
    """Check if PowerShell Core (pwsh) is available."""
    return _which("pwsh") is not None


# ── execution API ──────────────────────────────────────────────────────

class Run:
    """Run Windows commands (cmd, bat, powershell)."""

    @staticmethod
    def run(command: str, cwd: str | None = None,
            timeout: int | None = 60, env: dict | None = None,
            shell: str = "auto") -> dict:
        """
        Execute a command on Windows.

        Args:
            command: Command string or list of arguments.
            cwd: Working directory (default: CWD of the parent process).
            timeout: Max seconds to wait. None = no limit.
            env: Additional environment variables (merged with current).
            shell: One of "auto", "cmd", "powershell", "pwsh".
                   "auto" picks the best available shell.

        Returns:
            dict with keys: stdout, stderr, returncode, shell_used, timed_out.
        """
        shell = shell.lower()
        resolved_cmd = command
        resolved_shell = shell

        # Auto-detect shell
        if shell == "auto":
            if command.strip().startswith(("#!", "#!/")):
                resolved_shell = "cmd"
                resolved_cmd = command[command.index("\n") + 1:].strip() if "\n" in command else command
            else:
                resolved_shell = "cmd"

        # ── cmd.exe ──
        if resolved_shell == "cmd":
            return _run_cmd(resolved_cmd, cwd, timeout, env)

        # ── PowerShell ──
        if resolved_shell == "powershell":
            return _run_powershell(resolved_cmd, cwd, timeout, env)

        if resolved_shell == "pwsh":
            if not has_pwsh():
                return {
                    "stdout": "",
                    "stderr": "pwsh (PowerShell Core) not found on this system.",
                    "returncode": -1,
                    "shell_used": "pwsh",
                    "timed_out": False,
                }
            return _run_powershell(resolved_cmd, cwd, timeout, env, use_pwsh=True)

        return {
            "stdout": "",
            "stderr": f"Unsupported shell '{shell}'.",
            "returncode": -1,
            "shell_used": shell,
            "timed_out": False,
        }


def _build_env(extra_env: dict | None) -> dict | None:
    if extra_env is None:
        return None
    env = os.environ.copy()
    env.update(extra_env)
    return env


def _run_cmd(command: str, cwd: str | None,
             timeout: int | None, env: dict | None) -> dict:
    """Execute via cmd.exe /c."""
    try:
        proc = subprocess.run(
            ["cmd.exe", "/c", command],
            capture_output=True, text=True,
            cwd=cwd, env=_build_env(env),
            timeout=timeout,
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
            "shell_used": "cmd",
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s.",
            "returncode": -1,
            "shell_used": "cmd",
            "timed_out": True,
        }
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": "cmd.exe not found. Are you on Windows?",
            "returncode": -1,
            "shell_used": "cmd",
            "timed_out": False,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "shell_used": "cmd",
            "timed_out": False,
        }


def _run_powershell(command: str, cwd: str | None,
                    timeout: int | None, env: dict | None,
                    use_pwsh: bool = False) -> dict:
    """Execute via PowerShell -Command."""
    exe = "pwsh" if use_pwsh else "powershell"
    shell_name = "pwsh" if use_pwsh else "powershell"
    try:
        proc = subprocess.run(
            [exe, "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True,
            cwd=cwd, env=_build_env(env),
            timeout=timeout,
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
            "shell_used": shell_name,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s.",
            "returncode": -1,
            "shell_used": shell_name,
            "timed_out": True,
        }
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": f"{exe} not found.",
            "returncode": -1,
            "shell_used": shell_name,
            "timed_out": False,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "shell_used": shell_name,
            "timed_out": False,
        }
