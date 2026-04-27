# -*- coding: utf-8 -*-
"""
Shared HTTP client factory and utilities for Internet skill.
"""

import os
import re
import json
from urllib.parse import urlparse

import httpx

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT = 30
DOWNLOAD_CHUNK_SIZE = 8192


def make_client(timeout: int = DEFAULT_TIMEOUT, **kwargs) -> httpx.AsyncClient:
    """Create a reusable async HTTP client with sensible defaults."""
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", USER_AGENT)
    return httpx.AsyncClient(
        headers=headers,
        timeout=httpx.Timeout(timeout, connect=10, read=timeout, write=timeout),
        follow_redirects=True,
        **kwargs,
    )


def safe_filename(url: str, default: str = "download") -> str:
    """Derive a safe local filename from a URL."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if path and "/" in path:
        name = path.rsplit("/", 1)[-1]
        if name:
            name = name.split("?")[0]
            name = re.sub(r'[<>:"/\\|?*]', "_", name)
            return name or default
    return default


def format_size(size_bytes: int) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
