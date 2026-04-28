# -*- coding: utf-8 -*-
"""
URL health check — HTTP HEAD request to verify accessibility.
"""

import json

import httpx

from astraflux.astra_agents.skill.Internet._common import make_client


async def check_url_impl(url: str, timeout: int = 15) -> str:
    """Check if a URL is accessible via HTTP HEAD and return response info."""
    if not url.startswith(("http://", "https://")):
        return json.dumps({
            "status": "error",
            "message": f"Invalid URL: '{url}'. Must start with http:// or https://.",
        }, ensure_ascii=False)

    try:
        async with make_client(timeout=timeout) as client:
            resp = await client.head(url)

        result = {
            "status": "success",
            "url": str(resp.url),
            "status_code": resp.status_code,
            "content_type": resp.headers.get("content-type", ""),
            "content_length": resp.headers.get("content-length", "unknown"),
            "server": resp.headers.get("server", "unknown"),
        }
        return json.dumps(result, ensure_ascii=False)

    except httpx.TimeoutException:
        return json.dumps({
            "status": "error",
            "message": f"Request timed out after {timeout}s.",
        }, ensure_ascii=False)
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "status": "error",
            "url": url,
            "status_code": e.response.status_code,
            "message": f"HTTP {e.response.status_code}",
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e),
        }, ensure_ascii=False)
