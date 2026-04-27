# -*- coding: utf-8 -*-
"""
Unix command execution module (Linux, macOS, WSL).

Supports:
  - sh (POSIX shell)
  - bash
  - zsh (macOS default)
  - fish
  - Any shell found at /bin/$SHELL
  - WSL (Windows Subsystem for Linux) — commands run via `wsl` prefix
  - Shebang detection for .sh / .bash / .zsh scripts

Notes on macOS:
  - The default shell changed to zsh as of macOS Catalina (2019).
  - bash on macOS is usually an older version at /bin/bash.
  - For modern bash, users may install via Homebrew at /opt/homebrew/bin/bash.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path


def _which(program: str) -> str | None:
    """Locate a program in PATH."""
    try:
        result = subprocess.run(
            ["which", program],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    # Fallback: check common locations
    for prefix in ["/bin", "/usr/bin", "/usr/local/bin",
                   "/opt/homebrew/bin", "/opt/local/bin"]:
        candidate = Path(prefix) / program
        if candidate.exists():
            return str(candidate)
    return None


def _is_macos() -> bool:
    return sys.platform == "darwin"


def _is_linux() -> bool:
    return sys.platform == "linux"


def _is_wsl() -> bool:
    """Detect if running inside WSL."""
    if not _is_linux():
        return False
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except (FileNotFoundError, OSError):
        return False


def detect_default_shell() -> str:
    """Return the default user shell path (e.g. /bin/zsh, /bin/bash)."""
    shell = os.environ.get("SHELL", "")
    if shell and Path(shell).exists():
        return shell
    # Fallback order
    for candidate in ["/bin/bash", "/bin/zsh", "/bin/sh"]:
        if Path(candidate).exists():
            return candidate
    return "/bin/sh"


def available_shells() -> list[str]:
    """List available Unix shells on this system."""
    found = []
    for shell in ["sh", "bash", "zsh", "fish", "dash", "ksh", "tcsh"]:
        if _which(shell):
            found.append(shell)
    return found


# ── execution API ──────────────────────────────────────────────────────

class Run:
    """Run Unix commands (sh, bash, zsh, etc.)."""

    @staticmethod
    def run(command: str, cwd: str | None = None,
            timeout: int | None = 60, env: dict | None = None,
            shell: str = "auto") -> dict:
        """
        Execute a command on Linux / macOS / WSL.

        Args:
            command: Command string or script content.
            cwd: Working directory (default: CWD of parent process).
            timeout: Max seconds to wait. None = no limit.
            env: Additional environment variables (merged with current).
            shell: One of "auto", "sh", "bash", "zsh", "fish", or a
                   custom path like "/bin/bash". "auto" detects the
                   user's default shell (from $SHELL or fallback chain).

        Returns:
            dict with keys: stdout, stderr, returncode, shell_used, timed_out.
        """
        resolved_shell = shell
        resolved_cmd = command

        # Auto-detect shell
        if shell == "auto":
            shell_name = _which_shell_from_shebang(command)
            if shell_name:
                resolved_shell = shell_name
            else:
                resolved_shell = Path(detect_default_shell()).name
        else:
            resolved_shell = shell

        # If shell is a path, extract the name for reporting
        shell_bin = _resolve_shell_bin(resolved_shell)
        if shell_bin is None:
            return {
                "stdout": "",
                "stderr": f"Shell '{resolved_shell}' not found on this system. Available: {', '.join(available_shells())}",
                "returncode": -1,
                "shell_used": resolved_shell,
                "timed_out": False,
            }

        return _run_with_shell(shell_bin, shell_bin.name, resolved_cmd,
                               cwd, timeout, env)


def _which_shell_from_shebang(command: str) -> str | None:
    """Extract shell name from shebang like #!/bin/bash -> bash."""
    if not command.startswith("#!"):
        return None
    first_line = command.split("\n")[0].strip()  # e.g. "#!/usr/bin/env bash"
    parts = first_line[2:].split()
    if not parts:
        return None
    path = parts[0]
    # Handle /usr/bin/env bash
    if "env" in path and len(parts) > 1:
        return parts[1]
    return Path(path).name


def _resolve_shell_bin(shell: str) -> Path | None:
    """Convert a shell name or path to an existing binary Path."""
    if Path(shell).is_absolute() and Path(shell).exists():
        return Path(shell)
    found = _which(shell)
    if found:
        return Path(found)
    return None


def _build_env(extra_env: dict | None) -> dict | None:
    if extra_env is None:
        return None
    env = os.environ.copy()
    env.update(extra_env)
    return env


def _run_with_shell(shell_bin: Path, shell_name: str, command: str,
                    cwd: str | None, timeout: int | None,
                    env: dict | None) -> dict:
    """Execute command using the given shell binary."""
    try:
        proc = subprocess.run(
            [str(shell_bin), "-c", command],
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
            "stderr": f"Shell '{shell_name}' not found.",
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
