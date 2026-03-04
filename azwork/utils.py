"""HTML to Markdown conversion and helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString, Tag


@dataclass
class ImageCollector:
    """Collects images found during HTML→MD conversion.

    Each image gets a sequential local filename, and the Markdown src
    is rewritten to point at ``{assets_prefix}/{local_filename}``.
    """

    assets_prefix: str = ""
    images: list[tuple[str, str]] = field(default_factory=list)
    _counter: int = field(default=0, repr=False)

    def rewrite(self, src: str, alt: str) -> str:
        """Register an image and return the rewritten local path."""
        if not src:
            return src
        # Only rewrite HTTP(S) URLs — leave local/relative paths alone
        parsed = urlparse(src)
        if parsed.scheme not in ("http", "https"):
            return src

        self._counter += 1
        ext = PurePosixPath(parsed.path).suffix or ".png"
        # Sanitise extension
        ext = ext.split("?")[0][:5]
        if not ext.startswith("."):
            ext = ".png"
        local_name = f"image-{self._counter}{ext}"
        self.images.append((src, local_name))

        if self.assets_prefix:
            return f"{self.assets_prefix}/{local_name}"
        return local_name


def html_to_markdown(
    html: str,
    image_collector: ImageCollector | None = None,
) -> str:
    """Convert Azure DevOps HTML content to clean Markdown.

    If *image_collector* is provided, remote ``<img>`` URLs are rewritten
    to local relative paths and the original URLs are recorded for later
    downloading.
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    result = _convert_element(soup, image_collector)
    # Clean up excessive blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _convert_element(
    element: Tag | NavigableString,
    collector: ImageCollector | None = None,
) -> str:
    if isinstance(element, NavigableString):
        text = str(element)
        # Collapse whitespace within text nodes (but keep single newlines)
        text = re.sub(r"[ \t]+", " ", text)
        return text

    tag = element.name
    if tag is None:
        # Document node — process children
        return "".join(_convert_element(child, collector) for child in element.children)

    children_text = "".join(_convert_element(child, collector) for child in element.children)

    if tag in ("br",):
        return "\n"

    if tag in ("b", "strong"):
        stripped = children_text.strip()
        if not stripped:
            return ""
        return f"**{stripped}**"

    if tag in ("i", "em"):
        stripped = children_text.strip()
        if not stripped:
            return ""
        return f"*{stripped}*"

    if tag == "code":
        return f"`{children_text.strip()}`"

    if tag == "pre":
        code_content = children_text.strip()
        return f"\n```\n{code_content}\n```\n"

    if tag == "a":
        href = element.get("href", "")
        text = children_text.strip()
        if href:
            return f"[{text}]({href})"
        return text

    if tag == "img":
        alt = element.get("alt", "image")
        src = element.get("src", "")
        if collector:
            src = collector.rewrite(src, alt)
        return f"![{alt}]({src})"

    if tag == "ul":
        return "\n" + _convert_list(element, collector, ordered=False) + "\n"

    if tag == "ol":
        return "\n" + _convert_list(element, collector, ordered=True) + "\n"

    if tag == "li":
        return children_text.strip()

    if tag == "table":
        return "\n" + _convert_table(element, collector) + "\n"

    if tag in ("p", "div"):
        stripped = children_text.strip()
        if not stripped:
            return "\n"
        return f"\n\n{stripped}\n\n"

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        prefix = "#" * level
        return f"\n\n{prefix} {children_text.strip()}\n\n"

    if tag in ("span", "font", "u", "s", "strike", "del", "ins",
               "sup", "sub", "mark", "small", "big",
               "thead", "tbody", "tfoot"):
        return children_text

    if tag in ("tr", "td", "th"):
        return children_text

    if tag in ("style", "script"):
        return ""

    # Default: preserve text content
    return children_text


def _convert_list(
    element: Tag,
    collector: ImageCollector | None,
    ordered: bool,
) -> str:
    items = []
    for i, child in enumerate(element.children):
        if isinstance(child, Tag) and child.name == "li":
            text = _convert_element(child, collector).strip()
            prefix = f"{i + 1}. " if ordered else "- "
            items.append(f"{prefix}{text}")
    return "\n".join(items)


def _convert_table(table: Tag, collector: ImageCollector | None) -> str:
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = []
        for cell in tr.find_all(["td", "th"]):
            cells.append(_convert_element(cell, collector).strip())
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    # Determine column count
    max_cols = max(len(row) for row in rows)
    # Pad rows
    for row in rows:
        while len(row) < max_cols:
            row.append("")

    lines = []
    # Header
    lines.append("| " + " | ".join(rows[0]) + " |")
    lines.append("| " + " | ".join("---" for _ in rows[0]) + " |")
    # Body
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def slugify(text: str, max_length: int = 50) -> str:
    """Create a URL-friendly slug from text."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text[:max_length]
