"""Shared test helpers, HTML snapshot matchers, and file-backed mock archive server."""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urljoin, urlparse

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

import ao3fetch

TESTS_DIR = Path(__file__).resolve().parent
MOCK_DATA_DIR = TESTS_DIR / "mocks" / "data"
SNAPSHOTS_DIR = TESTS_DIR / "snapshots"

_FILENAMIFY_RESERVED_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_WS_RE = re.compile(r"\s+")
_HTMLFY_PUNCT_SPLIT_RE = re.compile(
    r"(</[^>]+>[.!?,;:])\n[ \t]+(?=[!?,;:'\"\u2019\u201d)\]]|&#x2019;|&#x201d;|&apos;|&quot;)",
)
_VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    },
)
_ARCHIVE_DIRS = {
    "archiveofourown.org": "ao3",
    "superlove.sayitditto.net": "superlove",
}

type RouteMatcher = Callable[[str], bool]
type RouteHandler = Callable[[str, Mapping[str, str] | None], ao3fetch.FetchResponse]


def _filenamify(name: str, *, replacement: str = "!", maxLength: int = 100) -> str:
    """Port of npm `filenamify` used by AO3.js mock file paths."""
    result = _FILENAMIFY_RESERVED_RE.sub(replacement, name)
    if replacement:
        escaped = re.escape(replacement)
        result = re.sub(f"{escaped}+", replacement, result)
    result = result.strip(".")
    if len(result) > maxLength:
        result = result[:maxLength]
    return result


def safeFilenamify(name: str) -> str:
    """Port of AO3.js's safeFilenamify helper (encodes | as !p! before filenamify)."""
    return _filenamify(name.replace("|", "!p!"))


def _getNormalizedQueryFolder(params: list[tuple[str, str]]) -> str:
    byKey: dict[str, list[str]] = {}
    for key, value in params:
        if key == "page":
            continue
        byKey.setdefault(key, []).append(value)

    entries: list[str] = []
    for key in sorted(byKey):
        values = byKey[key]
        sortedValues = sorted(values) if len(values) > 1 else values
        for value in sortedValues:
            segment = f"{key}={'' if value == 'any' else value}"
            entries.append(_filenamify(segment.lower(), replacement="_", maxLength=100))

    return "__".join(entries) if entries else "default"


def _getPageFileName(params: list[tuple[str, str]]) -> str:
    pageStr = next((value for key, value in params if key == "page"), "1")
    page = int(pageStr)
    return f"{page:02d}.html"


def _getFilePathForSearchUrl(params: list[tuple[str, str]]) -> Path:
    folderName = _getNormalizedQueryFolder(params)
    fileName = _getPageFileName(params)
    return Path("tag-search") / folderName / fileName


def _getUserWorksQueryPath(params: list[tuple[str, str]]) -> Path | None:
    filtered = [
        (key, value) for key, value in params if not (key == "work_search[sort_column]" and value == "revised_at")
    ]
    folderName = _getNormalizedQueryFolder(filtered)
    fileName = _getPageFileName(filtered)
    if folderName == "default" and fileName == "01.html":
        return None
    return Path(folderName) / fileName


def resolveMockFilePath(url: str) -> Path | None:
    """Resolve an archive request URL to its AO3.js mock data file path."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    archiveName = _ARCHIVE_DIRS.get(host)
    if archiveName is None:
        return None

    archiveDir = MOCK_DATA_DIR / archiveName
    rawSegments = [seg for seg in parsed.path.split("/") if seg]
    if not rawSegments:
        return None
    segments = [unquote(seg) for seg in rawSegments]
    params = parse_qsl(parsed.query, keep_blank_values=True)
    lastSegment = segments[-1]

    if archiveName == "superlove" and len(segments) == 2 and segments[0] == "works":
        return archiveDir / "works" / safeFilenamify(segments[1]) / "index.html"

    if segments[0] == "series" and len(segments) == 2:
        hasPage = any(key == "page" for key, _ in params)
        if hasPage:
            pageFile = _getPageFileName(params)
            fileName = "index.html" if pageFile == "01.html" else pageFile
        else:
            fileName = "index.html"
        return archiveDir / "series" / safeFilenamify(segments[1]) / fileName

    if segments[0] == "tags":
        if lastSegment == "search":
            return archiveDir / _getFilePathForSearchUrl(params)
        if len(segments) == 3 and lastSegment == "feed.atom":
            return archiveDir / "tags" / safeFilenamify(segments[1]) / "feed.atom"
        if len(segments) == 3 and lastSegment == "works":
            return archiveDir / "tags" / safeFilenamify(segments[1]) / "works.html"
        if len(segments) == 2:
            return archiveDir / "tags" / safeFilenamify(segments[1]) / "index.html"

    if segments[0] == "users":
        if len(segments) == 3 and lastSegment == "profile":
            return archiveDir / "users" / safeFilenamify(segments[1]) / "profile" / "index.html"
        if lastSegment == "works":
            queryPath = _getUserWorksQueryPath(params)
            if queryPath is not None:
                path = archiveDir
                for segment in segments:
                    path = path / safeFilenamify(segment)
                return path / queryPath
            path = archiveDir
            for segment in segments[:-1]:
                path = path / safeFilenamify(segment)
            return path / "works.html"

    if segments[0] == "works":
        if len(segments) == 3 and lastSegment == "navigate":
            return archiveDir / "works" / safeFilenamify(segments[1]) / "navigate.html"
        if len(segments) == 4 and segments[2] == "chapters":
            return (
                archiveDir / "works" / safeFilenamify(segments[1]) / "chapters" / f"{safeFilenamify(segments[3])}.html"
            )
        if len(segments) == 2:
            isFullWork = any(key == "view_full_work" and value == "true" for key, value in params)
            fileName = "full.html" if isFullWork else "index.html"
            return archiveDir / "works" / safeFilenamify(segments[1]) / fileName

    return None


@dataclass(slots=True)
class MockArchiveServer:
    """In-process file-backed mock server matching AO3.js's MSW test harness."""

    requestedUrls: list[str] = field(default_factory=list)
    _overrides: list[tuple[RouteMatcher, RouteHandler]] = field(default_factory=list)

    def reset(self) -> None:
        """Clear recorded request URLs and per-test route overrides."""
        self.requestedUrls.clear()
        self._overrides.clear()

    def override(self, matcher: RouteMatcher, handler: RouteHandler) -> None:
        """Install a temporary route override checked before default file handlers."""
        self._overrides.insert(0, (matcher, handler))

    def overrideStatus(self, matcher: RouteMatcher, status: int, *, body: bytes = b"") -> None:
        """Override matching URLs to return a fixed HTTP status."""

        def _handler(url: str, _headers: Mapping[str, str] | None) -> ao3fetch.FetchResponse:
            return ao3fetch.FetchResponse(status=status, headers={}, body=body, url=url)

        self.override(matcher, _handler)

    def overrideRedirect(self, matcher: RouteMatcher, targetUrl: str, *, status: int = 302) -> None:
        """Override matching URLs to redirect to targetUrl (followed like fetch)."""

        def _handler(url: str, _headers: Mapping[str, str] | None) -> ao3fetch.FetchResponse:
            return ao3fetch.FetchResponse(
                status=status,
                headers={"location": targetUrl},
                body=b"",
                url=url,
            )

        self.override(matcher, _handler)

    def _dispatchOnce(self, url: str, headers: Mapping[str, str] | None) -> ao3fetch.FetchResponse:
        self.requestedUrls.append(url)
        for matcher, handler in self._overrides:
            if matcher(url):
                return handler(url, headers)

        mockPath = resolveMockFilePath(url)
        if mockPath is not None and mockPath.is_file():
            contentType = "application/atom+xml" if mockPath.suffix == ".atom" else "text/html"
            return ao3fetch.FetchResponse(
                status=200,
                headers={"content-type": contentType},
                body=mockPath.read_bytes(),
                url=url,
            )

        msg = f"Unknown archive mock route: {url} (resolved path: {mockPath})"
        return ao3fetch.FetchResponse(status=500, headers={}, body=msg.encode("utf-8"), url=url)

    def fetch(self, url: str, headers: Mapping[str, str] | None = None) -> ao3fetch.FetchResponse:
        """Fetch a mocked URL, following HTTP 3xx redirects up to 10 hops."""
        currentUrl = url
        for _ in range(10):
            response = self._dispatchOnce(currentUrl, headers)
            location = response.header("location")
            if response.status in {301, 302, 303, 307, 308} and location:
                currentUrl = urljoin(currentUrl, location)
                continue
            return response
        return ao3fetch.FetchResponse(status=500, headers={}, body=b"Too many redirects", url=currentUrl)


def expectUnlocked(
    content: ao3fetch.WorkWithText | ao3fetch.LockedWorkSummary,
) -> ao3fetch.WorkWithText:
    """Assert that a work returned by getWorkContent is unlocked and narrow its type."""
    if not isinstance(content, ao3fetch.LockedWorkSummary):
        return content
    msg = f"Work {content.id} is somehow locked"
    raise AssertionError(msg)


def expectUnlockedSummary(
    work: ao3fetch.WorkSummary | ao3fetch.LockedWorkSummary,
) -> ao3fetch.WorkSummary:
    """Assert that a work returned by getWork is unlocked and narrow its type."""
    if not isinstance(work, ao3fetch.LockedWorkSummary):
        return work
    msg = f"Work {work.id} is somehow locked"
    raise AssertionError(msg)


def assertDriftingCount(received: int, *, atLeast: int, atMost: int) -> None:
    """Assert a fluctuating archive stat falls within expected inclusive bounds."""
    assert isinstance(received, int) and not isinstance(received, bool)
    assert math.isfinite(received)
    assert atLeast <= received <= atMost, f"expected {received} to be within [{atLeast}, {atMost}]"


def _canonicalizeDom(node: BeautifulSoup | Tag | NavigableString, parts: list[str]) -> None:
    if isinstance(node, Comment):
        return
    if isinstance(node, NavigableString):
        text = _WS_RE.sub(" ", str(node))
        if text:
            parts.append(text)
        return

    if isinstance(node, BeautifulSoup):
        for child in node.contents:
            if isinstance(child, (Tag, NavigableString)):
                _canonicalizeDom(child, parts)
        return

    tagName = node.name.lower()
    attrStrs: list[str] = []
    for key in sorted(node.attrs):
        rawVal = node.attrs[key]
        valStr = " ".join(str(v) for v in rawVal) if isinstance(rawVal, list) else str(rawVal)
        escapedVal = valStr.replace("&", "&amp;").replace('"', "&quot;")
        attrStrs.append(f'{key.lower()}="{escapedVal}"')
    attrPart = (" " + " ".join(attrStrs)) if attrStrs else ""

    if tagName in _VOID_ELEMENTS:
        parts.append(f"<{tagName}{attrPart}>")
        return

    parts.append(f"<{tagName}{attrPart}>")
    for child in node.contents:
        if isinstance(child, (Tag, NavigableString)):
            _canonicalizeDom(child, parts)
    parts.append(f"</{tagName}>")


def normalizeHtml(html: str) -> str:
    """Normalize an HTML fragment into a canonical entity-decoded, whitespace-normalized DOM string."""
    soup = BeautifulSoup(html, "html.parser")
    parts: list[str] = []
    _canonicalizeDom(soup, parts)
    joined = "".join(parts)
    # Match htmlfy's prettification behavior where whitespace around tag boundaries is non-significant.
    joined = re.sub(r"\s*(<[^>]+>)\s*", r"\1", joined)
    return _WS_RE.sub(" ", joined).strip()


def assertHtmlEqual(actual: str | None, expected: str | None) -> None:
    """Assert two HTML fragments (or None) are DOM-equivalent, matching AO3.js's toEqualHtml."""
    if actual is None or expected is None:
        assert actual == expected
        return
    assert normalizeHtml(actual) == normalizeHtml(expected)


def assertMatchesHtmlSnapshot(actual: str | None, relativeSnapshotPath: str) -> None:
    """Assert an HTML fragment matches an AO3.js HTML snapshot file under tests/snapshots/."""
    assert actual is not None
    expected = (SNAPSHOTS_DIR / relativeSnapshotPath).read_text(encoding="utf-8")
    expected = _HTMLFY_PUNCT_SPLIT_RE.sub(r"\1", expected)
    assertHtmlEqual(actual, expected)


def assertMatchesTextSnapshot(actual: str, relativeSnapshotPath: str) -> None:
    """Assert plain text matches an AO3.js text snapshot file verbatim."""
    expected = (SNAPSHOTS_DIR / relativeSnapshotPath).read_text(encoding="utf-8")
    assert actual == expected
