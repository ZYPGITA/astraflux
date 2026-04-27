# -*- coding: utf-8 -*-
"""
Internet skill — unified entry point.

Exposes search, web fetch, file download, and URL check functions.
Concrete implementations are in sibling `_*.py` files.
"""

from agents import function_tool

from astraflux.astra_agents.skill.Internet._search import search_impl, SUPPORTED_ENGINES
from astraflux.astra_agents.skill.Internet._fetch import fetch_impl
from astraflux.astra_agents.skill.Internet._download import download_impl
from astraflux.astra_agents.skill.Internet._check_url import check_url_impl


@function_tool
async def search_web(
    query: str,
    engine: str = "duckduckgo",
    max_results: int = 10,
    region: str = "wt-wt",
) -> str:
    """
    Search the web using multiple search engines.

    Supports: duckduckgo (default, no API key), google, baidu, yandex, yahoo, bing.

    Args:
        query: Search keywords or phrase.
        engine: Search engine to use.
            Supported: "duckduckgo", "google", "baidu", "yandex", "yahoo", "bing".
            Default: "duckduckgo".
        max_results: Maximum number of results to return (1-20). Default 10.
        region: Region/language code (engine-dependent).
            DuckDuckGo: "wt-wt" (worldwide), "cn-zh" (China), "us-en" (USA), etc.
            Google: "hl=en" (English), "hl=zh-CN" (Chinese), etc.
            Baidu: region is ignored (always Chinese results).
            Yandex: "ru" (Russia), "com-tr" (Turkey), etc.
            Yahoo: "en-US", "zh-Hans-CN", etc.
            Bing: "en-US", "zh-CN", etc.

    Returns:
        A JSON string with search results. Each result contains:
        title, url, snippet/description.
        On error returns error message with status field.
    """
    return await search_impl(query, engine=engine, max_results=max_results, region=region)


@function_tool
async def fetch_webpage(
    url: str,
    max_chars: int = 10000,
    extract_mode: str = "markdown",
    timeout: int = 30,
) -> str:
    """
    Fetch a web page and extract its content as markdown or plain text.

    Args:
        url: Full HTTP(S) URL to fetch.
        max_chars: Maximum characters to return (100-50000). Default 10000.
        extract_mode: Content extraction mode.
            - "markdown": Convert HTML to markdown (requires lxml for best results,
              falls back to plain text stripping).
            - "text": Extract plain text only.
            Default: "markdown".
        timeout: Request timeout in seconds. Default 30.

    Returns:
        The page content as a string. On error returns an error message.
    """
    return await fetch_impl(url, max_chars=max_chars, extract_mode=extract_mode, timeout=timeout)


@function_tool
async def download_file(
    url: str,
    save_path: str = "",
    timeout: int = 120,
    headers: str = "",
) -> str:
    """
    Download a file from a URL and save it to disk (streaming).

    Args:
        url: Full HTTP(S) URL of the file to download.
        save_path: Local file path. If empty, auto-derived from the URL
            and saved in the current working directory.
        timeout: Maximum seconds for the download. Default 120.
        headers: Optional HTTP headers as a JSON string
            (e.g. '{"Authorization": "Bearer xxx", "Referer": "https://..."}').

    Returns:
        A message with file path and size, or an error description.
    """
    return await download_impl(url, save_path=save_path, timeout=timeout, headers=headers)


@function_tool
async def check_url(
    url: str,
    timeout: int = 15,
) -> str:
    """
    Check if a URL is accessible (HTTP HEAD) and return response info.

    Args:
        url: Full HTTP(S) URL to check.
        timeout: Request timeout in seconds. Default 15.

    Returns:
        A JSON string with: status, url, status_code, content_type,
        content_length, server. On error returns error message.
    """
    return await check_url_impl(url, timeout=timeout)
