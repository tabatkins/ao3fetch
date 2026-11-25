"""Convert AO3 work HTML (prose, summaries, notes) into clean Markdown."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag

from . import t

_MULTI_SPACE_RE: t.Final[re.Pattern[str]] = re.compile(r"[ \t]+")
_HTML_WS_RE: t.Final[re.Pattern[str]] = re.compile(r"[ \t\r\n]+")
_MULTI_BLANK_RE: t.Final[re.Pattern[str]] = re.compile(r"\n{3,}")
_SETEXT_UNDERLINE_RE: t.Final[re.Pattern[str]] = re.compile(r"^(?:-{3,}|={3,})$")
_BR_MARKER: t.Final[str] = "\ufdd0"
_BR_SUFFIX: t.Final[str] = f"{_BR_MARKER}\n"
_STRIP_BLOCK_CHARS: t.Final[str] = " \t\r\n" + _BR_MARKER
_HTML_INLINE_KEEP: t.Final[frozenset[str]] = frozenset({"u", "s", "del", "sup", "sub"})


def _wrapInlineMarker(text: str, marker: str) -> str:
    """Wrap inline text in Markdown emphasis markers while keeping outer whitespace/breaks outside."""
    if not text.strip(_STRIP_BLOCK_CHARS):
        return text
    leadingLen = len(text) - len(text.lstrip(_STRIP_BLOCK_CHARS))
    trailingLen = len(text) - len(text.rstrip(_STRIP_BLOCK_CHARS))
    leading = text[:leadingLen]
    trailing = text[len(text) - trailingLen :] if trailingLen else ""
    core = text.strip(_STRIP_BLOCK_CHARS)
    return f"{leading}{marker}{core}{marker}{trailing}"


def _renderChildren(node: Tag | BeautifulSoup) -> str:
    parts: list[str] = []
    afterBreak = False
    for child in node.children:
        if not isinstance(child, (Tag, NavigableString)):
            continue
        rendered = _renderNode(child)
        if not rendered:
            continue
        if afterBreak:
            rendered = rendered.lstrip(" \t")
            if not rendered:
                continue
            afterBreak = False
        if rendered.startswith(_BR_SUFFIX) and parts:
            parts[-1] = parts[-1].rstrip(" \t")
        if rendered.endswith(_BR_SUFFIX):
            afterBreak = True
        parts.append(rendered)
    return "".join(parts)


def _renderBlockquote(inner: str) -> str:
    stripped = inner.strip(_STRIP_BLOCK_CHARS)
    if not stripped:
        return ""
    rawLines = [line if line.strip(_STRIP_BLOCK_CHARS) else "" for line in stripped.split("\n")]
    normalized = _MULTI_BLANK_RE.sub("\n\n", "\n".join(rawLines)).strip("\n")
    quotedLines = [f"> {line}" if line else ">" for line in normalized.split("\n")]
    return "\n\n" + "\n".join(quotedLines) + "\n\n"


def _renderList(node: Tag, *, ordered: bool) -> str:
    items: list[str] = []
    index = 1
    for child in node.find_all("li", recursive=False):
        if not isinstance(child, Tag):
            continue
        itemText = _renderChildren(child).strip(_STRIP_BLOCK_CHARS)
        if not itemText:
            continue
        prefix = f"{index}. " if ordered else "- "
        indented = itemText.replace("\n", "\n  ")
        items.append(prefix + indented)
        index += 1
    if not items:
        return ""
    return "\n\n" + "\n".join(items) + "\n\n"


def _renderNode(node: Tag | NavigableString) -> str:
    """Convert a BeautifulSoup DOM subtree into clean fiction Markdown."""
    if isinstance(node, NavigableString):
        text = str(node).replace("\xa0", " ").replace(_BR_MARKER, "")
        return _HTML_WS_RE.sub(" ", text)

    tag = node.name.lower() if node.name else ""
    if tag in {"script", "style"}:
        return ""
    if tag == "br":
        return _BR_SUFFIX
    if tag == "hr":
        return "\n\n---\n\n"
    if tag in {"em", "i"}:
        return _wrapInlineMarker(_renderChildren(node), "_")
    if tag in {"strong", "b"}:
        return _wrapInlineMarker(_renderChildren(node), "**")
    if tag == "code":
        parentName = node.parent.name.lower() if node.parent and node.parent.name else ""
        if parentName == "pre":
            return node.get_text()
        codeText = node.get_text()
        return f"`{codeText}`" if "`" not in codeText else f"`` {codeText} ``"
    if tag == "pre":
        codeText = node.get_text().strip("\n")
        return f"\n\n```\n{codeText}\n```\n\n"
    if tag == "a":
        inner = _renderChildren(node).strip(_STRIP_BLOCK_CHARS)
        href = node.get("href")
        if not isinstance(href, str) or not href.strip():
            return inner
        hrefClean = href.strip()
        if not inner or inner == hrefClean:
            return hrefClean
        return f"[{inner}]({hrefClean})"
    if tag == "img":
        src = node.get("src")
        if not isinstance(src, str) or not src.strip():
            return ""
        alt = node.get("alt")
        altStr = alt.strip() if isinstance(alt, str) else ""
        return f"![{altStr}]({src.strip()})"
    if tag in _HTML_INLINE_KEEP:
        inner = _renderChildren(node)
        return f"<{tag}>{inner}</{tag}>" if inner.strip(_STRIP_BLOCK_CHARS) else ""
    if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(tag[1])
        headingText = _renderChildren(node).strip(_STRIP_BLOCK_CHARS)
        return f"\n\n{'#' * level} {headingText}\n\n" if headingText else ""
    if tag == "blockquote":
        return _renderBlockquote(_renderChildren(node))
    if tag == "ul":
        return _renderList(node, ordered=False)
    if tag == "ol":
        return _renderList(node, ordered=True)
    if tag in {"p", "div", "center", "section", "article"}:
        inner = _renderChildren(node).strip(_STRIP_BLOCK_CHARS)
        return f"\n\n{inner}\n\n" if inner else ""

    return _renderChildren(node)


def _collapseLineSpaces(line: str) -> str:
    """Collapse internal horizontal whitespace runs while preserving leading indent and break markers."""
    hasBreak = line.endswith(_BR_MARKER)
    core = line[:-1] if hasBreak else line
    stripped = core.rstrip(" \t")
    if not stripped:
        return ""
    leadLen = len(stripped) - len(stripped.lstrip(" "))
    body = _MULTI_SPACE_RE.sub(" ", stripped[leadLen:])
    return stripped[:leadLen] + body + (_BR_MARKER if hasBreak else "")


def _isSetextUnderline(line: str) -> bool:
    """Return True if a Markdown line is a setext heading underline (`---` or `===`)."""
    candidate = line.lstrip("> ") if line.startswith(">") else line
    return _SETEXT_UNDERLINE_RE.match(candidate.strip()) is not None


def _finalizeLines(raw: str) -> list[str]:
    """Normalize horizontal spacing and resolve internal hard-break markers outside fenced code blocks."""
    cleaned: list[str] = []
    inCodeFence = False
    for line in raw.split("\n"):
        if line.strip().startswith("```"):
            inCodeFence = not inCodeFence
            cleaned.append(line)
            continue
        cleaned.append(line if inCodeFence else _collapseLineSpaces(line))

    finalLines: list[str] = []
    inCodeFence = False
    for idx, line in enumerate(cleaned):
        if line.strip().startswith("```"):
            inCodeFence = not inCodeFence
            finalLines.append(line)
            continue
        if inCodeFence or not line.endswith(_BR_MARKER):
            finalLines.append(line)
            continue
        nextLine = cleaned[idx + 1] if idx + 1 < len(cleaned) else ""
        nextIsBlank = not nextLine or nextLine.strip() == ">"
        if nextIsBlank or _isSetextUnderline(nextLine):
            finalLines.append(line[:-1])
        else:
            finalLines.append(line[:-1] + "  ")
    return finalLines


def toMarkdown(html: str) -> str:
    """Convert AO3 HTML content (prose, summary, or notes) into clean Markdown."""
    if not html or not html.strip():
        return ""
    soup = BeautifulSoup(html, "html.parser")
    raw = _renderChildren(soup)
    joined = "\n".join(_finalizeLines(raw))
    return _MULTI_BLANK_RE.sub("\n\n", joined).strip()
