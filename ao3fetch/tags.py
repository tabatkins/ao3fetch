"""Tag profile, tag search, and tag feed scrapers ported from FujoWebDev/AO3.js."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag as BsTag

from . import t
from .entities import (
    ChildTag,
    PageInfo,
    SortDirection,
    SubTag,
    Tag,
    TagCategory,
    TagSearchFilters,
    TagSearchResult,
    TagSearchResultSummary,
    TagSearchResultType,
    TagSearchSortColumn,
    TagSearchType,
    TagWranglingStatus,
)
from .pageLoaders import loadTagFeedAtomPage, loadTagPage, loadTagSearchPage, loadTagWorksFeed
from .utils import isValidArchiveId, parseArchiveId

_TAG_CATEGORY_RE: t.Final[re.Pattern[str]] = re.compile(r"This tag belongs to the (.+) Category")
_INT_PREFIX_RE: t.Final[re.Pattern[str]] = re.compile(r"^(\d+)")
_FOUND_RE: t.Final[re.Pattern[str]] = re.compile(r"(\d+)\s+Found")
_WORKS_COUNT_RE: t.Final[re.Pattern[str]] = re.compile(r"\((\d+)\)\s*$")
_TAG_TYPE_RE: t.Final[re.Pattern[str]] = re.compile(r"^([^:]+):")
_FEED_TITLE_RE: t.Final[re.Pattern[str]] = re.compile(r"AO3 works tagged '(.+)'")

_VALID_TAG_CATEGORIES: t.Final[frozenset[str]] = frozenset(
    {"fandom", "character", "relationship", "archive warning", "additional tags"},
)
_VALID_SEARCH_RESULT_TYPES: t.Final[frozenset[str]] = frozenset(
    {"fandom", "character", "relationship", "freeform", "unsorted"},
)


def _parseIntOrThrow(text: str) -> int:
    match = _INT_PREFIX_RE.match(text.strip())
    if match is None:
        msg = f"Invalid integer: {text}"
        raise ValueError(msg)
    return int(match.group(1))


def getPagesCount(soup: BeautifulSoup) -> int:
    """Extract the highest page number from an AO3 pagination bar, or 0 if unpaginated."""
    items = soup.select(".pagination.actions li:not(.next, .previous)")
    if not items:
        return 0
    lastText = items[-1].get_text().strip()
    return _parseIntOrThrow(lastText) if lastText else 0


def _firstChildText(element: BsTag) -> str:
    for child in element.children:
        if isinstance(child, BsTag):
            return child.get_text()
    return ""


def _getTagCategory(soup: BeautifulSoup) -> TagCategory:
    para = soup.select_one(".tag.profile > p")
    sentence = para.get_text() if para is not None else ""
    match = _TAG_CATEGORY_RE.search(sentence)
    if match is None:
        msg = "Category type not found for tag."
        raise ValueError(msg)
    lowered = match.group(1).lower()
    if lowered not in _VALID_TAG_CATEGORIES:
        msg = f"Unknown tag category: {lowered}"
        raise ValueError(msg)
    return t.cast("TagCategory", lowered)


def _getChildTags(soup: BeautifulSoup) -> tuple[ChildTag, ...]:
    children: list[ChildTag] = []
    for div in soup.select(".child > div"):
        classes = div.get("class")
        firstClass = classes[0] if isinstance(classes, list) and classes else ""
        catRaw = "additional tags" if firstClass == "freeforms" else firstClass
        category = t.cast("TagCategory", catRaw)
        for link in div.select("ul > li a"):
            name = link.get_text()
            if name:
                children.append(ChildTag(tagName=name, category=category))
    return tuple(children)


def _getSubTags(soup: BeautifulSoup) -> tuple[SubTag, ...]:
    subTags: list[SubTag] = []
    for li in soup.select(".sub > ul.tags > li"):
        subTags.append(SubTag(tagName=_firstChildText(li), parentSubTag=None))
        for nestedUl in li.select("ul.tags"):
            for childLi in nestedUl.find_all("li", recursive=False):
                if not isinstance(childLi, BsTag):
                    continue
                parentLi = childLi.find_parent("li")
                parentName = _firstChildText(parentLi) if isinstance(parentLi, BsTag) else None
                subTags.append(SubTag(tagName=_firstChildText(childLi), parentSubTag=parentName))
    return tuple(subTags)


def _getTagId(worksFeedSoup: BeautifulSoup) -> str | None:
    rss = worksFeedSoup.select_one(".rss")
    if rss is None:
        return None
    href = rss.get("href")
    if not isinstance(href, str):
        return None
    parts = href.split("/")
    return parts[2] if len(parts) > 2 and parts[2] else None


def getTag(tagName: str) -> Tag:
    """Fetch full wrangling and hierarchy details for an AO3 tag."""
    tagSoup = loadTagPage(tagName)
    worksFeedSoup = loadTagWorksFeed(tagName)

    rawTagId = _getTagId(worksFeedSoup)
    if rawTagId is not None and not isValidArchiveId(rawTagId):
        msg = f"Found invalid tag id: {rawTagId}"
        raise ValueError(msg)

    para = tagSoup.select_one(".tag.profile > p")
    sentence = para.get_text() if para is not None else ""
    hasMergers = tagSoup.select_one(".merger") is not None
    canonical = "It's a canonical tag." in sentence
    common = "It's a common tag." in sentence or hasMergers

    heading = tagSoup.select_one(".tag.profile h2")
    displayedName = heading.get_text() if heading is not None else tagName
    if canonical:
        canonicalName: str | None = displayedName
    elif hasMergers:
        mergerTag = tagSoup.select_one(".merger a.tag")
        canonicalName = mergerTag.get_text() if mergerTag is not None else None
    else:
        canonicalName = None

    return Tag(
        name=tagName,
        id=parseArchiveId(rawTagId) if rawTagId is not None else None,
        category=_getTagCategory(tagSoup),
        canonical=canonical,
        common=common,
        canonicalName=canonicalName,
        parentTags=tuple(el.get_text() for el in tagSoup.select(".parent ul.tags li")),
        childTags=_getChildTags(tagSoup),
        subTags=_getSubTags(tagSoup),
        tagsWithSameMeaning=tuple(el.get_text() for el in tagSoup.select(".synonym ul.tags li")),
    )


def getTagNameById(tagId: str | int) -> str | None:
    """Resolve a canonical tag name from its numeric tag ID via its Atom feed."""
    feedSoup = loadTagFeedAtomPage(tagId)
    titleEl = feedSoup.find("title")
    if titleEl is None:
        return None
    match = _FEED_TITLE_RE.search(titleEl.get_text())
    return match.group(1) if match is not None else None


def searchTags(
    *,
    tagName: str | None = None,
    fandoms: t.Sequence[str] = (),
    tagType: TagSearchType = "any",
    wranglingStatus: TagWranglingStatus = "any",
    sortColumn: TagSearchSortColumn = "name",
    sortDirection: SortDirection = "asc",
    page: int = 1,
) -> TagSearchResultSummary:
    """Search AO3 tags with filters and pagination."""
    filters = TagSearchFilters(
        tagName=tagName,
        fandoms=tuple(fandoms),
        type=tagType,
        wranglingStatus=wranglingStatus,
        sortColumn=sortColumn,
        sortDirection=sortDirection,
        page=page,
    )
    soup = loadTagSearchPage(filters)

    heading = soup.select_one("h3.heading")
    foundMatch = _FOUND_RE.search(heading.get_text()) if heading is not None else None
    totalResults = _parseIntOrThrow(foundMatch.group(1)) if foundMatch is not None else 0

    results: list[TagSearchResult] = []
    for li in soup.select("ol.tag.index.group > li"):
        link = li.select_one("a.tag")
        if link is None:
            continue
        name = link.get_text().strip()
        liText = li.get_text()
        worksMatch = _WORKS_COUNT_RE.search(liText)
        worksCount = _parseIntOrThrow(worksMatch.group(1)) if worksMatch is not None else 0
        typeMatch = _TAG_TYPE_RE.match(liText)
        if typeMatch is None:
            msg = f"Invalid tag type: {liText}"
            raise ValueError(msg)
        rawType = typeMatch.group(1).strip().lower()
        normalizedType = "unsorted" if rawType == "unsortedtag" else rawType
        if normalizedType not in _VALID_SEARCH_RESULT_TYPES:
            msg = f"Unexpected tag search result type: {normalizedType}"
            raise ValueError(msg)

        span = li.select_one("span")
        spanClasses = set(span.get("class") or []) if span is not None else set()
        results.append(
            TagSearchResult(
                name=name,
                type=t.cast(TagSearchResultType, normalizedType),
                canonical="canonical" in spanClasses,
                worksCount=worksCount,
            ),
        )

    return TagSearchResultSummary(
        filters=filters,
        totalResults=totalResults,
        pages=PageInfo(total=getPagesCount(soup), current=filters.page),
        tags=tuple(results),
    )
