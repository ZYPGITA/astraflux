# -*- coding: utf-8 -*-
"""
File download — streaming HTTP download to local disk.
"""

import os
import re
import json

import httpx

from astraflux.astra_agents.skill.Internet._common import (
    make_client,
    safe_filename,
    format_size,
    DOWNLOAD_CHUNK_SIZE,
)


async def download_impl(
        url: str,
        save_path: str = "",
        timeout: int = 120,
        headers: str = "",
) -> str:
    """Download a file from a URL to disk (streaming)."""
    if not url.startswith(("http://", "https://")):
        return f"Invalid URL: '{url}'. Must start with http:// or https://."

    extra_headers = {}
    if headers:
        try:
            extra_headers = json.loads(headers)
            if not isinstance(extra_headers, dict):
                return "headers must be a JSON object string."
        except json.JSONDecodeError as e:
            return f"Invalid headers JSON: {e}"

    # Determine save path
    if not save_path:
        save_path = safe_filename(url, "downloaded_file")
    save_path = os.path.abspath(save_path)

    parent = os.path.dirname(save_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    try:
        async with make_client(timeout=timeout, headers=extra_headers) as client:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()

                # Auto-name from Content-Disposition if no explicit path given
                content_disp = resp.headers.get("content-disposition", "")
                if content_disp:
                    fname_match = re.search(
                        r'filename[^;=\n]*=((["\']).*?\2|[^;\n]*)',
                        content_disp,
                    )
                    if fname_match:
                        candidate = fname_match.group(1).strip("\"'").strip()
                        if candidate and save_path == os.path.abspath(
                                safe_filename(url, "downloaded_file")
                        ):
                            save_path = os.path.join(os.path.dirname(save_path), candidate)

                downloaded = 0
                with open(save_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(DOWNLOAD_CHUNK_SIZE):
                        f.write(chunk)
                        downloaded += len(chunk)

        size_str = format_size(downloaded)
        return (
            f"Download complete.\n"
            f"  File: {save_path}\n"
            f"  Size: {size_str}\n"
            f"  URL : {url}"
        )

    except httpx.TimeoutException:
        return f"Download timed out after {timeout}s."
    except httpx.HTTPStatusError as e:
        return f"HTTP error {e.response.status_code} when downloading {url}"
    except PermissionError:
        return f"Permission denied: Cannot write to '{save_path}'."
    except Exception as e:
        return f"Download failed: {str(e)}"
