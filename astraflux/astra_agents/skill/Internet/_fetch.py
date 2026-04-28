# -*- coding: utf-8 -*-
"""
Web page fetching — convert HTML to markdown or plain text.
"""

import re

import httpx

from astraflux.astra_agents.skill.Internet._common import make_client


async def fetch_impl(
        url: str,
        max_chars: int = 10000,
        extract_mode: str = "markdown",
        timeout: int = 30,
) -> str:
    """Fetch a web page and extract content."""
    max_chars = max(100, min(max_chars, 50000))

    if not url.startswith(("http://", "https://")):
        return f"Invalid URL: '{url}'. Must start with http:// or https://."

    try:
        async with make_client(timeout=timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").lower()
            raw = resp.text

        # Warn if binary
        if "text/" not in content_type and "html" not in content_type:
            if any(ct in content_type for ct in ("image/", "audio/", "video/", "application/octet")):
                return (
                    f"The URL appears to be binary content ({content_type}). "
                    f"Use download_file() instead."
                )

        if extract_mode == "markdown":
            try:
                from lxml import html as lxml_html
                doc = lxml_html.fromstring(raw)
                content = _html_to_markdown(doc)
            except ImportError:
                content = _strip_html_tags(raw)
        else:
            content = _strip_html_tags(raw)

        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[... truncated at {max_chars} characters]"

        return content

    except httpx.TimeoutException:
        return f"Request timed out after {timeout}s."
    except httpx.HTTPStatusError as e:
        return f"HTTP error {e.response.status_code}: {url}"
    except Exception as e:
        return f"Failed to fetch page: {str(e)}"


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags and decode common entities."""
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    html = html.replace("&nbsp;", " ").replace("&amp;", "&")
    html = html.replace("&lt;", "<").replace("&gt;", ">")
    html = html.replace("&quot;", '"').replace("&#39;", "'")
    html = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), html)
    return re.sub(r"\s+", " ", html).strip()


def _html_to_markdown(doc) -> str:
    """Convert an lxml HTML document to basic markdown."""
    lines = []

    def walk(node, depth=0):
        tag = node.tag if hasattr(node, "tag") else None
        if tag is None:
            return
        tag = tag.lower() if isinstance(tag, str) else ""

        text = (node.text or "").strip()
        tail = (node.tail or "").strip()

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            prefix = "#" * int(tag[1])
            if text:
                lines.append(f"\n{prefix} {text}\n")
        elif tag == "p" and text:
            lines.append(f"\n{text}\n")
        elif tag == "a":
            href = node.get("href", "")
            lines.append(f"[{text}]({href})" if text and href else text)
        elif tag in ("strong", "b") and text:
            lines.append(f"**{text}**")
        elif tag in ("em", "i") and text:
            lines.append(f"*{text}*")
        elif tag == "code" and text:
            lines.append(f"`{text}`")
        elif tag == "pre":
            code = node.text or ""
            if code.strip():
                lines.append(f"\n```\n{code}\n```\n")
        elif tag == "img":
            src = node.get("src", "")
            alt = node.get("alt", "")
            if src:
                lines.append(f"![{alt}]({src})")
        elif tag in ("li",) and text:
            bullet = "- " if depth == 0 else "  " * (depth - 1) + "  - "
            lines.append(f"{bullet}{text}")
        elif tag == "br":
            lines.append("\n")
        elif tag == "hr":
            lines.append("\n---\n")
        elif tag == "blockquote" and text:
            lines.append(f"\n> {text}\n")
        elif tail:
            lines.append(tail + " ")

        if hasattr(node, "getchildren"):
            for child in node.getchildren():
                walk(child, depth + 1 if tag in ("ul", "ol") else depth)

    walk(doc)
    return re.sub(r"\n{3,}", "\n\n", " ".join(lines).strip())
