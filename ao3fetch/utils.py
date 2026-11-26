"""Shared utilities, errors, HTML helpers, and plain-text conversion for AO3 scraping."""

from __future__ import annotations

import re
from typing import Literal

from bs4 import BeautifulSoup, Comment, Declaration, Doctype, NavigableString, ProcessingInstruction, Tag
from bs4.formatter import HTMLFormatter

from . import t
from .entities import ArchiveId

_HTML5_FORMATTER: t.Final[HTMLFormatter] = HTMLFormatter(void_element_close_prefix="")
_WHITESPACE_RE: t.Final[re.Pattern[str]] = re.compile(r"\s+")
_NEWLINE_RE: t.Final[re.Pattern[str]] = re.compile(r"[\r\n]+")
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
    return element.decode_contents(formatter=_HTML5_FORMATTER)


def _renderPlainNode(node: Tag | NavigableString, parts: list[str], *, inPre: bool = False) -> None:
    """Recursively serialize a BeautifulSoup DOM node into AO3.js-compatible plain text."""
    if isinstance(node, (Comment, Declaration, Doctype, ProcessingInstruction)):
        return
    if isinstance(node, NavigableString):
        text = str(node)
        parts.append(text if inPre else _NEWLINE_RE.sub(" ", text))
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
    if tagName in {"ul", "ol"}:
        parts.append("\n\n")
        index = 1
        itemLines: list[str] = []
        for child in node.children:
            if isinstance(child, Tag) and child.name and child.name.lower() == "li":
                itemParts: list[str] = []
                for grandchild in child.children:
                    if isinstance(grandchild, (Tag, NavigableString)):
                        _renderPlainNode(grandchild, itemParts, inPre=inPre)
                prefix = "- " if tagName == "ul" else f"{index}. "
                itemLines.append(prefix + "".join(itemParts).strip())
                index += 1
            elif isinstance(child, (Tag, NavigableString)):
                subParts: list[str] = []
                _renderPlainNode(child, subParts, inPre=inPre)
                subText = "".join(subParts).strip()
                if subText:
                    itemLines.append(subText)
        parts.append("\n".join(itemLines))
        parts.append("\n\n")
        return
    if tagName == "li":
        parts.append("\n")
        for child in node.children:
            if isinstance(child, (Tag, NavigableString)):
                _renderPlainNode(child, parts, inPre=inPre)
        return

    isBlock = tagName in _BLOCK_TAGS
    childInPre = inPre or tagName == "pre"
    if isBlock:
        parts.append("\n\n")
    for child in node.children:
        if isinstance(child, (Tag, NavigableString)):
            _renderPlainNode(child, parts, inPre=childInPre)
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
