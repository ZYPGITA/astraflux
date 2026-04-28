# -*- coding: utf-8 -*-
"""
Multi-engine web search — DuckDuckGo, Google, Baidu, Yandex, Yahoo, Bing.

Each engine is implemented as a stateless async function that takes
(query, max_results, region) and returns a list of dicts or raises
an exception. The public entry point is search_impl().
"""

import re
import json

import httpx

from astraflux.astra_agents.skill.Internet._common import make_client

# ── Registry ───────────────────────────────────────────────────────────

SUPPORTED_ENGINES = {
    "duckduckgo",
    "google",
    "baidu",
    "yandex",
    "yahoo",
    "bing",
}

_ENGINES = {
    "duckduckgo": "_search_ddg",
    "google": "_search_google",
    "baidu": "_search_baidu",
    "yandex": "_search_yandex",
    "yahoo": "_search_yahoo",
    "bing": "_search_bing",
}

_ENGINE_LABELS = {
    "duckduckgo": "DuckDuckGo",
    "google": "Google",
    "baidu": "Baidu",
    "yandex": "Yandex",
    "yahoo": "Yahoo",
    "bing": "Bing",
}


# ── Public entry point ─────────────────────────────────────────────────

async def search_impl(query: str, engine: str = "duckduckgo",
                      max_results: int = 10, region: str = "wt-wt") -> str:
    """Run a search on the specified engine and return JSON string."""

    engine = engine.lower()
    max_results = max(1, min(max_results, 20))

    if engine not in _ENGINES:
        supported = ", ".join(sorted(SUPPORTED_ENGINES))
        return json.dumps({
            "status": "error",
            "message": f"Unsupported engine '{engine}'. Supported: {supported}.",
        }, ensure_ascii=False)

    func_name = _ENGINES[engine]
    func = globals().get(func_name)
    if func is None:
        return json.dumps({
            "status": "error",
            "message": f"Engine '{engine}' implementation not found.",
        }, ensure_ascii=False)

    try:
        results = await func(query, max_results, region)
        if not results:
            return json.dumps({
                "status": "success",
                "engine": _ENGINE_LABELS.get(engine, engine),
                "results": [],
                "message": "No results found.",
            }, ensure_ascii=False)

        return json.dumps({
            "status": "success",
            "engine": _ENGINE_LABELS.get(engine, engine),
            "results": results,
        }, ensure_ascii=False)

    except httpx.TimeoutException:
        return json.dumps({
            "status": "error",
            "engine": _ENGINE_LABELS.get(engine, engine),
            "message": "Search request timed out.",
        }, ensure_ascii=False)
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "status": "error",
            "engine": _ENGINE_LABELS.get(engine, engine),
            "message": f"HTTP {e.response.status_code} from search engine.",
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "engine": _ENGINE_LABELS.get(engine, engine),
            "message": f"Search failed: {str(e)}",
        }, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════════
#  Engine implementations
# ═══════════════════════════════════════════════════════════════════════

# ── DuckDuckGo (no API key needed) ─────────────────────────────────────

async def _search_ddg(query: str, max_results: int, region: str) -> list[dict]:
    """Search via DuckDuckGo HTML interface."""
    async with make_client(timeout=15) as client:
        # Use a more realistic browser User-Agent to avoid captcha page
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        resp = await client.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "kl": region},
            headers=headers,
        )
        # DDG returns 202 when it needs to render JS/bot challenge
        if resp.status_code == 202:
            raise Exception(
                "DuckDuckGo returned a challenge page (202). Try a different engine or reduce request frequency.")
        resp.raise_for_status()
        return _parse_ddg(resp.text, max_results)


def _parse_ddg(html: str, limit: int) -> list[dict]:
    """Parse DuckDuckGo HTML results."""
    results = []
    blocks = re.split(r'<div class="result[^"]*web-result[^"]*"', html, flags=re.IGNORECASE)
    for block in blocks[1:]:
        if len(results) >= limit:
            break
        m = re.search(
            r'<h2[^>]*class="result__title"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            block, re.DOTALL,
        )
        if not m:
            continue
        url = m.group(1)
        title = _strip(m.group(2))
        if not title:
            continue
        snip = ""
        sm = re.search(r'class="result__snippet"[^>]*>(.*?)</(?:a|div|span)>', block, re.DOTALL)
        if sm:
            snip = _strip(sm.group(1))
        results.append({"title": title, "url": url, "snippet": snip})
    return results


# ── Google (scrape) ────────────────────────────────────────────────────

async def _search_google(query: str, max_results: int, region: str) -> list[dict]:
    """Search via Google HTML (no API key, scrapes serp)."""
    # region acts as hl parameter: "en", "zh-CN", "ja", etc.
    params = {"q": query, "num": max_results}
    if region and region != "wt-wt":
        # Extract language code from region (e.g. "en-US" -> "en")
        lang = region.split("-")[0] if "-" in region else region
        if lang and len(lang) <= 5:
            params["hl"] = lang

    async with make_client(timeout=15) as client:
        resp = await client.get("https://www.google.com/search", params=params)
        resp.raise_for_status()
        return _parse_google(resp.text, limit=max_results)


def _parse_google(html: str, limit: int) -> list[dict]:
    """Parse Google HTML search results."""
    results = []
    # Google uses <a href="/url?q=..."> or direct <h3>... links
    # Approach: find <div class="g"> ... </div> blocks

    blocks = re.split(r'<div class="g[^"]*"[^>]*>', html, flags=re.IGNORECASE)

    for block in blocks[1:]:
        if len(results) >= limit:
            break

        # Title is in <h3> -> <a href="...">
        m = re.search(
            r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            block, re.DOTALL,
        )
        if not m:
            continue

        url = m.group(1)
        # Google wraps URLs in /url?q=...&... redirect
        url_match = re.search(r'/url\?q=([^&]+)', url)
        if url_match:
            from urllib.parse import unquote
            url = unquote(url_match.group(1))
        elif url.startswith("//"):
            url = "https:" + url

        title = _strip(m.group(2))
        if not title:
            continue

        # Snippet: <span class="aCOpRe"> or <div class="VwiC3b">
        snip = ""
        sm = re.search(r'class="(?:aCOpRe|VwiC3b)[^"]*"[^>]*>(.*?)</(?:span|div)>', block, re.DOTALL)
        if sm:
            snip = _strip(sm.group(1))

        results.append({"title": title, "url": url, "snippet": snip})

    return results


# ── Baidu ──────────────────────────────────────────────────────────────

async def _search_baidu(query: str, max_results: int, region: str = "") -> list[dict]:
    """Search via Baidu (Chinese search engine, always Chinese results)."""
    params = {"wd": query, "rn": min(max_results, 20)}

    async with make_client(timeout=15) as client:
        # Use a standard browser Accept-Language for Chinese content
        headers = {"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
        resp = await client.get("https://www.baidu.com/s", params=params, headers=headers)
        resp.raise_for_status()
        return _parse_baidu(resp.text, limit=max_results)


def _parse_baidu(html: str, limit: int) -> list[dict]:
    """Parse Baidu HTML results."""
    results = []
    # Baidu result blocks: <div class="result c-container ...">
    blocks = re.split(r'<div[^>]*class="result[^"]*c-container[^"]*"', html, flags=re.IGNORECASE)

    for block in blocks[1:]:
        if len(results) >= limit:
            break
        m = re.search(
            r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            block, re.DOTALL,
        )
        if not m:
            # Try alternate: <a class="... " href="..." target="_blank">
            m = re.search(
                r'<a[^>]*href="(https?://[^"]*)"[^>]*target="_blank"[^>]*>(.*?)</a>',
                block, re.DOTALL,
            )
        if not m:
            continue

        url = m.group(1)
        title = _strip(m.group(2))
        if not title:
            continue

        # Snippet: <span class="content-right_..."> or <div class="c-abstract">
        snip = ""
        for cls in ("c-abstract", "content-right"):
            sm = re.search(rf'class="{cls}[^"]*"[^>]*>(.*?)</(?:div|span)>', block, re.DOTALL)
            if sm:
                snip = _strip(sm.group(1))
                break

        results.append({"title": title, "url": url, "snippet": snip})

    return results


# ── Yandex ─────────────────────────────────────────────────────────────

async def _search_yandex(query: str, max_results: int, region: str = "") -> list[dict]:
    """Search via Yandex HTML."""
    params = {"text": query}
    if region and region != "wt-wt":
        params["lr"] = _yandex_lr(region)

    async with make_client(timeout=15) as client:
        resp = await client.get("https://yandex.com/search/", params=params)
        resp.raise_for_status()
        return _parse_yandex(resp.text, limit=max_results)


def _yandex_lr(region: str) -> str:
    """Map region to Yandex lr (region) code."""
    mapping = {
        "ru": "225", "com-tr": "983", "by": "149",
        "kz": "159", "ua": "187", "us-en": "84",
    }
    return mapping.get(region, "225")  # default Russia


def _parse_yandex(html: str, limit: int) -> list[dict]:
    """Parse Yandex HTML results."""
    results = []
    # Yandex <li class="serp-item"> ... </li>
    blocks = re.split(r'<li[^>]*class="serp-item[^"]*"[^>]*>', html, flags=re.IGNORECASE)

    for block in blocks[1:]:
        if len(results) >= limit:
            break
        # Title link
        m = re.search(r'<a[^>]*href="(https?://[^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
        if not m:
            continue

        url = m.group(1)
        title = _strip(m.group(2))
        if not title or len(title) < 2:
            continue

        # Snippet: <div class="text-container"> or similar
        snip = ""
        sm = re.search(r'class="(?:text-container|organic__greenurl)[^"]*"[^>]*>(.*?)</(?:div|span)>',
                       block, re.DOTALL)
        if sm:
            snip = _strip(sm.group(1))
        if not snip:
            # Try <span class="extended-text__full">
            sm = re.search(r'class="extended-text__full"[^>]*>(.*?)</span>', block, re.DOTALL)
            if sm:
                snip = _strip(sm.group(1))

        results.append({"title": title, "url": url, "snippet": snip})

    return results


# ── Yahoo ──────────────────────────────────────────────────────────────

async def _search_yahoo(query: str, max_results: int, region: str = "") -> list[dict]:
    """Search via Yahoo HTML."""
    params = {"p": query, "n": min(max_results, 20)}
    if region and region != "wt-wt":
        params["vl"] = region

    async with make_client(timeout=15) as client:
        # Yahoo requires a full browser User-Agent
        ua_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        resp = await client.get("https://search.yahoo.com/search", params=params, headers=ua_headers)
        resp.raise_for_status()
        return _parse_yahoo(resp.text, limit=max_results)


def _parse_yahoo(html: str, limit: int) -> list[dict]:
    """Parse Yahoo HTML results."""
    results = []
    # Yahoo results: <div class="algo-sr" ...> or <div class="dd ...">
    blocks = re.split(r'<div[^>]*class="[^"]*algo(?:-sr)?[^"]*"[^>]*>', html, flags=re.IGNORECASE)

    for block in blocks[1:]:
        if len(results) >= limit:
            break
        # Title: <h3><a href="..."> title </a></h3>
        m = re.search(
            r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            block, re.DOTALL,
        )
        if not m:
            continue

        url = m.group(1)
        # Skip Yahoo internal links
        if "search.yahoo.com" in url and "p=" in url:
            continue

        title = _strip(m.group(2))
        if not title:
            continue

        # Snippet: <div class="compText ...">
        snip = ""
        sm = re.search(r'class="[^"]*compText[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
        if sm:
            snip = _strip(sm.group(1))

        results.append({"title": title, "url": url, "snippet": snip})

    return results


# ── Bing ───────────────────────────────────────────────────────────────

async def _search_bing(query: str, max_results: int, region: str = "") -> list[dict]:
    """Search via Bing HTML."""
    params = {"q": query, "count": min(max_results, 20)}
    if region and region != "wt-wt":
        # Bing uses setlang or cc parameter
        params["setlang"] = region.split("-")[0] if "-" in region else region
        if "-" in region:
            params["cc"] = region.split("-")[1]

    async with make_client(timeout=15) as client:
        resp = await client.get("https://www.bing.com/search", params=params)
        resp.raise_for_status()
        return _parse_bing(resp.text, limit=max_results)


def _parse_bing(html: str, limit: int) -> list[dict]:
    """Parse Bing HTML results."""
    results = []
    # Bing: <li class="b_algo"> ... </li>
    blocks = re.split(r'<li[^>]*class="b_algo[^"]*"[^>]*>', html, flags=re.IGNORECASE)

    for block in blocks[1:]:
        if len(results) >= limit:
            break
        m = re.search(
            r'<h2[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            block, re.DOTALL,
        )
        if not m:
            continue

        url = m.group(1)
        title = _strip(m.group(2))
        if not title:
            continue

        # Snippet: <p class="b_lineclamp...">
        snip = ""
        sm = re.search(r'<p[^>]*class="b_lineclamp[^"]*"[^>]*>(.*?)</p>', block, re.DOTALL)
        if sm:
            snip = _strip(sm.group(1))

        results.append({"title": title, "url": url, "snippet": snip})

    return results


# ── Shared utilities ───────────────────────────────────────────────────

def _strip(html_fragment: str) -> str:
    """Strip HTML tags and decode common entities."""
    text = re.sub(r"<[^>]+>", " ", html_fragment)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    return re.sub(r"\s+", " ", text).strip()
