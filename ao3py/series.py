"""Series page scraper ported from FujoWebDev/AO3.js."""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from .entities import Author, PageInfo, Series, WorkBlurbSummary
from .pageLoaders import loadSeriesPage
from .tags import getPagesCount
from .urls import getAsShortUrl, getAuthorFromUrl, getSeriesUrl
from .utils import InvalidIDError, innerHtml, isValidArchiveId, parseArchiveId
from .works import ANONYMOUS_AUTHOR, parseWorkBlurb


def _selectInt(soup: BeautifulSoup, selector: str) -> int:
    el = soup.select_one(selector)
    raw = el.get_text().replace(",", "").strip() if el is not None else ""
    return int(raw) if raw else 0


def _selectText(soup: BeautifulSoup, selector: str) -> str:
    el = soup.select_one(selector)
    return el.get_text().strip() if el is not None else ""


def _getSeriesAuthors(soup: BeautifulSoup) -> tuple[Author, ...]:
    firstDd = soup.select_one("dl.meta > dd:nth-of-type(1)")
    if firstDd is not None and firstDd.get_text().strip() == "Anonymous":
        return (ANONYMOUS_AUTHOR,)
    authors: list[Author] = []
    for link in soup.select("dl.meta a[rel='author']"):
        href = link.get("href")
        if isinstance(href, str):
            authors.append(getAuthorFromUrl(href))
    return tuple(authors)


def _getSeriesNotes(soup: BeautifulSoup) -> str | None:
    notesEl = soup.select_one("dl.series dd:nth-of-type(5)")
    if notesEl is None:
        return None
    prevEl = notesEl.find_previous_sibling()
    if isinstance(prevEl, Tag) and prevEl.get_text().strip() == "Notes:":
        return innerHtml(notesEl).strip()
    return None


def getSeries(seriesId: str | int, *, page: int | None = None) -> Series:
    """Fetch metadata and one page of works for an archive series."""
    if not isValidArchiveId(seriesId):
        raise InvalidIDError(seriesId, "series")
    parsedId = parseArchiveId(seriesId)
    soup = loadSeriesPage(parsedId, page=page)

    works: tuple[WorkBlurbSummary, ...] = tuple(
        parseWorkBlurb(innerHtml(workEl)) for workEl in soup.select("ul.index > li.work")
    )
    url = getSeriesUrl(parsedId)
    descEl = soup.select_one("dl.series blockquote.userstuff")
    description = innerHtml(descEl).strip() if descEl is not None else None
    description = description or None

    return Series(
        id=parsedId,
        url=url,
        shortUrl=getAsShortUrl(url),
        name=_selectText(soup, "h2.heading"),
        startedAt=_selectText(soup, "dl.series > dd:nth-of-type(2)"),
        updatedAt=_selectText(soup, "dl.series > dd:nth-of-type(3)"),
        authors=_getSeriesAuthors(soup),
        description=description,
        notes=_getSeriesNotes(soup),
        words=_selectInt(soup, "dl.meta dl.stats dd:nth-of-type(1)"),
        bookmarks=_selectInt(soup, "dl.meta dl.stats dd:nth-of-type(4)"),
        complete=_selectText(soup, "dl.stats dd:nth-of-type(3)") == "Yes",
        workCount=_selectInt(soup, "dl.meta dl.stats dd:nth-of-type(2)"),
        pages=PageInfo(
            total=max(1, getPagesCount(soup)) if works else 0,
            current=page if page is not None else 1,
        ),
        works=works,
    )
