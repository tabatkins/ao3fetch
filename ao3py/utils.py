"""Shared utilities, errors, HTML helpers, and plain-text conversion for AO3 scraping."""

from __future__ import annotations

import re
from typing import Literal

from bs4 import BeautifulSoup, NavigableString, Tag

from . import t
from .entities import ArchiveId

_WHITESPACE_RE: t.Final[re.Pattern[str]] = re.compile(r"\s+")
_MULTI_NEWLINE_RE: t.Final[re.Pattern[str]] = re.compile(r"\n{3,}")
_INT_STR_RE: t.Final[re.Pattern[str]] = re.compile(r"^\d+$")
_MONTHS: t.Final[dict[str, str]] = {
    "Jan": "01",
    "Feb": "02",
    "Mar": "03",
    "Apr": "04",
    "May": "05",
    "Jun": "06",
    "Jul": "07",
    "Aug": "08",
    "Sep": "09",
    "Oct": "10",
    "Nov": "11",
    "Dec": "12",
}
_BLOCK_TAGS: t.Final[frozenset[str]] = frozenset(
    "p div blockquote center table tr td th h1 h2 h3 h4 h5 h6 ul ol pre".split(),
)


class InvalidIDError(ValueError):
    """Raised when an invalid archive work, chapter, or series ID is supplied."""

    def __init__(self, rawId: str | int, kind: Literal["work", "chapter", "series"]) -> None:
        self.rawId = rawId
        self.kind = kind
        msg = f"{rawId} is not a valid {kind} id"
        super().__init__(msg)


class ArchivePageRequestError(RuntimeError):
    """Raised when an HTTP request to an AO3-compatible archive fails."""

    def __init__(self, url: str, status: int) -> None:
        self.url = url
        self.status = status
        msg = f"Archive request failed with status {status}: {url}"
        super().__init__(msg)


def cleanText(text: str) -> str:
    """Collapse internal whitespace runs to single spaces and trim ends."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def innerHtml(element: Tag | BeautifulSoup | None) -> str:
    """Return the inner HTML string of a BeautifulSoup element, matching Cheerio's .html()."""
    if element is None:
        return ""
    return "".join(str(child) for child in element.contents)


def _renderPlainNode(node: Tag | NavigableString, parts: list[str]) -> None:
    """Recursively serialize a BeautifulSoup DOM node into AO3.js-compatible plain text."""
    if isinstance(node, NavigableString):
        parts.append(str(node))
        return

    tagName = node.name.lower() if node.name else ""
    if tagName in {"img", "script", "style"}:
        return
    if tagName == "br":
        parts.append("\n")
        return
    if tagName == "hr":
        parts.append("\n\n---\n\n")
        return
    if tagName == "li":
        parentName = node.parent.name.lower() if node.parent and node.parent.name else ""
        prefix = "- " if parentName == "ul" else ""
        parts.append("\n" + prefix)
        for child in node.children:
            if isinstance(child, (Tag, NavigableString)):
                _renderPlainNode(child, parts)
        parts.append("\n")
        return

    isBlock = tagName in _BLOCK_TAGS
    if isBlock:
        parts.append("\n\n")
    for child in node.children:
        if isinstance(child, (Tag, NavigableString)):
            _renderPlainNode(child, parts)
    if isBlock:
        parts.append("\n\n")


def toPlainText(html: str) -> str:
    """Convert AO3 work HTML to plain text (paragraphs separated by blank lines, --- for <hr>)."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    parts: list[str] = []
    for child in soup.contents:
        if isinstance(child, (Tag, NavigableString)):
            _renderPlainNode(child, parts)
    raw = "".join(parts)
    cleanedLines = [cleanText(line) for line in raw.split("\n")]
    return _MULTI_NEWLINE_RE.sub("\n\n", "\n".join(cleanedLines)).strip()


def isValidArchiveId(rawId: str | int | None) -> bool:
    """Return True if rawId is a positive integer or base-10 digit string."""
    if rawId is None or isinstance(rawId, bool):
        return False
    if isinstance(rawId, int):
        return rawId >= 0
    return _INT_STR_RE.match(rawId) is not None


def parseArchiveId(rawId: str | int) -> ArchiveId:
    """Parse a validated archive ID into an int."""
    if isinstance(rawId, int) and not isinstance(rawId, bool):
        return rawId
    return int(rawId)


def parseBlurbDate(text: str) -> str:
    """Convert an AO3 blurb date like '01 Jan 2026' into ISO '2026-01-01'."""
    parts = text.strip().split()
    if len(parts) != 3 or parts[1] not in _MONTHS:
        msg = f"Unexpected work blurb date: {text}"
        raise ValueError(msg)
    day, month, year = parts
    return f"{year}-{_MONTHS[month]}-{day.zfill(2)}"
