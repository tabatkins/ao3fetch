"""Page loaders that fetch AO3 HTML/Atom pages and parse them into BeautifulSoup trees."""

from __future__ import annotations

import warnings
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from .entities import ArchiveId, SortDirection, TagSearchFilters, UserWorksSortColumn
from .fetcher import getFetcher
from .urls import (
    getSearchUrlFromTagFilters,
    getSeriesUrl,
    getTagUrl,
    getTagWorksFeedAtomUrl,
    getTagWorksFeedUrl,
    getUserProfileUrl,
    getUserWorksUrl,
    getWorkIndexUrl,
    getWorkUrl,
)
from .utils import ArchivePageRequestError


def fetchPage(url: str, *, skipAdultBanner: bool = True) -> BeautifulSoup:
    """Fetch an archive page and parse it into a BeautifulSoup document."""
    headers = {"Cookie": "view_adult=true;"} if skipAdultBanner else {}
    response = getFetcher()(url, headers)
    if not response.ok:
        raise ArchivePageRequestError(url=url, status=response.status)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
        return BeautifulSoup(response.text, "html.parser")


def loadTagWorksFeed(tagName: str) -> BeautifulSoup:
    """Load the recent works feed page for a tag."""
    return fetchPage(getTagWorksFeedUrl(tagName))


def loadTagPage(tagName: str) -> BeautifulSoup:
    """Load the tag profile page for a tag."""
    return fetchPage(getTagUrl(tagName))


def loadTagSearchPage(filters: TagSearchFilters) -> BeautifulSoup:
    """Load a tag search results page."""
    return fetchPage(getSearchUrlFromTagFilters(filters))


def loadTagFeedAtomPage(tagId: str | int) -> BeautifulSoup:
    """Load the Atom feed page for a tag ID."""
    return fetchPage(getTagWorksFeedAtomUrl(tagId))


def loadFullWorkChapter(chapterHtml: str) -> BeautifulSoup:
    """Wrap one chapter from a full-work page in #chapters for chapter getters."""
    return BeautifulSoup(f'<div id="chapters">{chapterHtml}</div>', "html.parser")


def loadWorkPage(
    workId: ArchiveId,
    *,
    chapterId: ArchiveId | None = None,
    fullWork: bool = False,
) -> BeautifulSoup:
    """Load a work or chapter page with view_adult=true confirmation."""
    rawUrl = getWorkUrl(workId, chapterId=chapterId, fullWork=fullWork)
    parsed = urlparse(rawUrl)
    params = dict(parse_qsl(parsed.query))
    params["view_adult"] = "true"
    adultUrl = urlunparse(parsed._replace(query=urlencode(params)))
    return fetchPage(adultUrl)


def loadUserProfilePage(username: str) -> BeautifulSoup:
    """Load a user profile page."""
    return fetchPage(getUserProfileUrl(username))


def loadUserWorksPage(
    username: str,
    *,
    pseud: str | None = None,
    page: int | None = None,
    sortColumn: UserWorksSortColumn | None = None,
    sortDirection: SortDirection | None = None,
) -> BeautifulSoup:
    """Load one page of a user's public works listing."""
    return fetchPage(
        getUserWorksUrl(
            username,
            pseud=pseud,
            page=page,
            sortColumn=sortColumn,
            sortDirection=sortDirection,
        ),
    )


def loadChaptersIndexPage(workId: ArchiveId) -> BeautifulSoup:
    """Load a work's /navigate chapter index page."""
    return fetchPage(getWorkIndexUrl(workId))


def loadSeriesPage(seriesId: ArchiveId, *, page: int | None = None) -> BeautifulSoup:
    """Load one page of a series."""
    return fetchPage(getSeriesUrl(seriesId, page=page))
