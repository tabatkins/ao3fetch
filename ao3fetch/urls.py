"""URL builders, URL parsers, and base-URL configuration for AO3-compatible archives."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import quote, unquote, urlencode, urljoin, urlparse, urlunparse

from . import t
from .entities import ArchiveId, Author, SortDirection, TagSearchFilters, UserWorksSortColumn
from .utils import InvalidIDError, isValidArchiveId, parseArchiveId

DEFAULT_BASE_URL: t.Final[str] = os.environ.get("ARCHIVE_BASE_URL", "https://archiveofourown.org")

_USER_WORKS_SORT_COLUMNS: t.Final[dict[UserWorksSortColumn, str]] = {
    "authors": "authors_to_sort_on",
    "title": "title_to_sort_on",
    "created_at": "created_at",
    "updated_at": "revised_at",
    "word_count": "word_count",
    "hits": "hits",
    "kudos_count": "kudos_count",
    "comments_count": "comments_count",
    "bookmarks_count": "bookmarks_count",
}

_TOKEN_REPLACEMENTS: t.Final[dict[str, str]] = {
    "/": "*s*",
    "&": "*a*",
    ".": "*d*",
    "#": "*h*",
    "?": "*q*",
}
_REPLACE_TOKENS_RE: t.Final[re.Pattern[str]] = re.compile(r"(/|\.|&|#|\?)")
_USER_URL_RE: t.Final[re.Pattern[str]] = re.compile(r"/users/([^/?#]+)(?:/pseuds/([^/?#]+))?")
_WORK_ID_RE: t.Final[re.Pattern[str]] = re.compile(r"works/(\d+)")
_CHAPTER_ID_RE: t.Final[re.Pattern[str]] = re.compile(r"chapters/(\d+)")
_COLLECTION_RE: t.Final[re.Pattern[str]] = re.compile(r"collections/(\w+)")


class _BaseUrlState:
    """Mutable holder for the active archive base URL."""

    __slots__ = ("url",)

    def __init__(self, url: str) -> None:
        self.url = url


_BASE_URL_STATE = _BaseUrlState(DEFAULT_BASE_URL)


@dataclass(slots=True)
class ParsedUserUrl:
    """Username and optional pseud extracted from a user URL."""

    username: str
    pseud: str | None = None


@dataclass(slots=True)
class ParsedWorkUrl:
    """Work ID and optional chapter/collection/origin extracted from a work URL."""

    workId: ArchiveId
    chapterId: ArchiveId | None = None
    collectionName: str | None = None
    baseUrl: str | None = None


def setArchiveBaseUrl(url: str) -> None:
    """Configure the archive base URL (e.g. AO3 or a mirror/compatible archive)."""
    _BASE_URL_STATE.url = url


def getArchiveBaseUrl() -> str:
    """Return the currently active archive base URL."""
    return _BASE_URL_STATE.url


def resetArchiveBaseUrl() -> None:
    """Reset the archive base URL back to archiveofourown.org."""
    _BASE_URL_STATE.url = DEFAULT_BASE_URL


def _joinBase(path: str, query: str = "") -> str:
    """Join a path against the current archive base URL and attach an optional query string."""
    base = getArchiveBaseUrl().rstrip("/") + "/"
    joined = urljoin(base, path.lstrip("/"))
    if not query:
        return joined
    parsed = urlparse(joined)
    return urlunparse(parsed._replace(query=query))


def getWorkUrl(
    workId: str | int,
    *,
    chapterId: str | int | None = None,
    collectionName: str | None = None,
    fullWork: bool = False,
) -> str:
    """Construct the canonical URL for a work or specific chapter."""
    if not isValidArchiveId(workId):
        raise InvalidIDError(workId, "work")

    parts: list[str] = []
    if collectionName:
        parts.append(f"collections/{collectionName}")
    parts.append(f"works/{workId}")
    if chapterId is not None:
        if not isValidArchiveId(chapterId):
            raise InvalidIDError(chapterId, "chapter")
        parts.append(f"chapters/{chapterId}")

    query = "view_full_work=true" if fullWork else ""
    return _joinBase("/".join(parts), query=query)


def getWorkIndexUrl(workId: str | int) -> str:
    """Construct the URL for a work's /navigate chapter index page."""
    if not isValidArchiveId(workId):
        raise InvalidIDError(workId, "work")
    return _joinBase(f"works/{workId}/navigate")


def getSeriesUrl(seriesId: str | int, *, page: int | None = None) -> str:
    """Construct the URL for a series page."""
    if not isValidArchiveId(seriesId):
        raise InvalidIDError(seriesId, "series")
    query = urlencode({"page": str(page)}) if page is not None else ""
    return _joinBase(f"series/{seriesId}", query=query)


def getAsShortUrl(url: str) -> str | None:
    """Convert an archiveofourown.org URL to ao3.org, or return None for other hosts."""
    parsed = urlparse(url)
    if parsed.hostname != "archiveofourown.org":
        return None
    netloc = "ao3.org" if parsed.port is None else f"ao3.org:{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


def getDownloadUrls(
    workId: ArchiveId,
    title: str,
    *,
    publishedAt: str,
    updatedAt: str | None = None,
) -> dict[str, str]:
    """Build AO3 download URLs (azw3, epub, mobi, html, pdf) for a work."""
    dateStr = updatedAt or publishedAt
    dt = datetime.fromisoformat(dateStr.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    timestampMs = int(dt.timestamp() * 1000)
    base = _joinBase(f"downloads/{workId}/")
    safeTitle = re.sub(r"\s", "_", title)
    return {fmt: f"{base}{safeTitle}.{fmt}?updated_at={timestampMs}" for fmt in ("azw3", "epub", "mobi", "html", "pdf")}


def getUserProfileUrl(username: str) -> str:
    """Construct a user profile URL."""
    return _joinBase(f"users/{quote(username, safe='')}/profile")


def getUserWorksUrl(
    username: str,
    *,
    pseud: str | None = None,
    page: int | None = None,
    sortColumn: UserWorksSortColumn | None = None,
    sortDirection: SortDirection | None = None,
) -> str:
    """Construct a user's public works listing URL."""
    userPath = f"users/{quote(username, safe='')}"
    path = f"{userPath}/works" if pseud is None else f"{userPath}/pseuds/{quote(pseud, safe='')}/works"
    params: list[tuple[str, str]] = []
    if page is not None:
        params.append(("page", str(page)))
    if sortColumn is not None:
        params.append(("work_search[sort_column]", _USER_WORKS_SORT_COLUMNS[sortColumn]))
    if sortDirection is not None:
        params.append(("work_search[sort_direction]", sortDirection))
    return _joinBase(path, query=urlencode(params))


def getTagUrl(tagName: str) -> str:
    """Construct an AO3 tag URL with AO3's special character token replacements."""
    replaced = _REPLACE_TOKENS_RE.sub(lambda match: _TOKEN_REPLACEMENTS[match.group(1)], tagName)
    return _joinBase(f"tags/{quote(replaced, safe='')}/")


def getTagWorksFeedUrl(tagName: str) -> str:
    """Construct the works feed URL for a tag."""
    return urljoin(getTagUrl(tagName), "works")


def getTagWorksFeedAtomUrl(tagId: str | int) -> str:
    """Construct the Atom feed URL for a tag ID."""
    return _joinBase(f"tags/{tagId}/feed.atom")


def getUserDetailsFromUrl(url: str) -> ParsedUserUrl:
    """Extract username and optional pseud from a user or pseud URL."""
    match = _USER_URL_RE.search(url)
    if match is None:
        msg = f"Invalid user URL: {url}"
        raise ValueError(msg)
    username = match.group(1)
    pseud = match.group(2)
    return ParsedUserUrl(username=username, pseud=unquote(pseud) if pseud is not None else None)


def getAuthorFromUrl(url: str) -> Author:
    """Parse an AO3 author link into an Author record."""
    details = getUserDetailsFromUrl(url)
    if details.pseud is None:
        msg = f"Unexpected author URL: {url}"
        raise ValueError(msg)
    return Author(username=details.username, pseud=details.pseud, anonymous=False)


def getWorkDetailsFromUrl(url: str) -> ParsedWorkUrl:
    """Extract work ID, optional chapter ID, collection name, and origin from a work URL."""
    workMatch = _WORK_ID_RE.search(url)
    if workMatch is None:
        msg = f"Invalid work URL: {url}"
        raise ValueError(msg)

    matchedWorkId = workMatch.group(1)
    if not isValidArchiveId(matchedWorkId):
        raise InvalidIDError(matchedWorkId, "work")

    chapterMatch = _CHAPTER_ID_RE.search(url)
    chapterId: ArchiveId | None = None
    if chapterMatch is not None:
        matchedChapterId = chapterMatch.group(1)
        if not isValidArchiveId(matchedChapterId):
            raise InvalidIDError(matchedChapterId, "chapter")
        chapterId = parseArchiveId(matchedChapterId)

    collectionMatch = _COLLECTION_RE.search(url)
    collectionName = collectionMatch.group(1) if collectionMatch is not None else None

    parsed = urlparse(url)
    baseUrl: str | None = None
    if parsed.scheme and parsed.netloc:
        host = "archiveofourown.org" if parsed.hostname == "ao3.org" else parsed.netloc
        baseUrl = f"{parsed.scheme}://{host}"

    return ParsedWorkUrl(
        workId=parseArchiveId(matchedWorkId),
        chapterId=chapterId,
        collectionName=collectionName,
        baseUrl=baseUrl,
    )


def getSearchUrlFromTagFilters(filters: TagSearchFilters) -> str:
    """Construct an AO3 tag search URL from normalized TagSearchFilters."""
    tagTypeParam = "" if filters.type == "any" else filters.type.capitalize()
    wranglingParam = filters.wranglingStatus.replace("_or_", "_").replace("_and_", "_")
    sortColParam = "uses" if filters.sortColumn == "works_count" else filters.sortColumn

    params: list[tuple[str, str]] = []
    if filters.page:
        params.append(("page", str(filters.page)))
    params.append(("commit", "Search Tags"))
    params.extend(
        [
            ("tag_search[name]", filters.tagName or ""),
            ("tag_search[fandoms]", ",".join(filters.fandoms)),
            ("tag_search[type]", tagTypeParam),
            ("tag_search[wrangling_status]", wranglingParam),
            ("tag_search[sort_column]", sortColParam),
            ("tag_search[sort_direction]", filters.sortDirection),
        ],
    )
    return _joinBase("tags/search", query=urlencode(params))
