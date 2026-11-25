"""User profile and public works scrapers ported from FujoWebDev/AO3.js."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from . import t
from .entities import (
    PageInfo,
    SortDirection,
    User,
    UserWorks,
    UserWorksFilters,
    UserWorksSortColumn,
)
from .pageLoaders import loadUserProfilePage, loadUserWorksPage
from .tags import getPagesCount
from .urls import getAsShortUrl, getAuthorFromUrl, getUserProfileUrl
from .utils import innerHtml, parseArchiveId
from .works import parseWorkBlurb

_DATE_LEN: t.Final[int] = len("0000-00-00")
_WORKS_TOTAL_RE: t.Final[re.Pattern[str]] = re.compile(r"([\d,]+)\s+Works?\b", re.IGNORECASE)


def _selectText(soup: BeautifulSoup, selector: str) -> str:
    el = soup.select_one(selector)
    return el.get_text().strip() if el is not None else ""


def _parseDashboardCount(soup: BeautifulSoup, suffix: str, prefix: str) -> int:
    text = _selectText(soup, f"#dashboard a[href$='{suffix}']")
    if not text or not text.startswith(prefix) or not text.endswith(")"):
        return 0
    raw = text[len(prefix) : -1].replace(",", "").strip()
    return int(raw) if raw else 0


def getUser(username: str) -> User:
    """Fetch public profile details for an archive username."""
    soup = loadUserProfilePage(username)
    url = getUserProfileUrl(username)
    shortUrl = getAsShortUrl(url)

    pseudsList: list[str] = []
    for link in soup.select("dd.pseuds a"):
        href = link.get("href")
        if isinstance(href, str):
            pseudsList.append(getAuthorFromUrl(href).pseud)

    joinedAndId = "".join(
        el.get_text() for el in soup.select(".meta dd:not(.email):not(dt.location + dd):not(.birthday):not(.pseuds)")
    ).strip()
    joined = joinedAndId[:_DATE_LEN]
    userId = parseArchiveId(joinedAndId[_DATE_LEN:].strip())

    iconEl = soup.select_one("img.icon")
    iconSrc = iconEl.get("src") if iconEl is not None else None
    if not isinstance(iconSrc, str) or not iconSrc:
        msg = "Users must have profile pic. Something is wrong."
        raise ValueError(msg)

    bioEl = soup.select_one(".bio .userstuff")
    bioHtml = innerHtml(bioEl) if bioEl is not None else None

    return User(
        username=_selectText(soup, ".user.profile .header h2"),
        pseuds=", ".join(pseudsList),
        id=userId,
        joined=joined,
        icon=iconSrc,
        header=_selectText(soup, "div.user.home.profile > h3.heading") or None,
        location=_selectText(soup, "dt.location + dd") or None,
        birthday=_selectText(soup, "dd.birthday") or None,
        url=url,
        shortUrl=shortUrl,
        works=_parseDashboardCount(soup, "works", "Works ("),
        series=_parseDashboardCount(soup, "series", "Series ("),
        bookmarks=_parseDashboardCount(soup, "bookmarks", "Bookmarks ("),
        collections=_parseDashboardCount(soup, "collections", "Collections ("),
        gifts=_parseDashboardCount(soup, "gifts", "Gifts ("),
        bioHtml=bioHtml,
    )


def getUserWorks(
    username: str,
    *,
    pseud: str | None = None,
    page: int | None = None,
    sortColumn: UserWorksSortColumn | None = None,
    sortDirection: SortDirection | None = None,
) -> UserWorks:
    """Fetch one page of a user's public works (optionally filtered to a pseud)."""
    resolvedColumn: UserWorksSortColumn = sortColumn if sortColumn is not None else "updated_at"
    defaultDir: SortDirection = "asc" if resolvedColumn in {"authors", "title"} else "desc"
    resolvedDir: SortDirection = sortDirection if sortDirection is not None else defaultDir
    resolvedPage = page if page is not None else 1

    filters = UserWorksFilters(
        sortColumn=resolvedColumn,
        sortDirection=resolvedDir,
        page=resolvedPage,
    )

    soup = loadUserWorksPage(
        username,
        pseud=pseud,
        page=resolvedPage,
        sortColumn=resolvedColumn,
        sortDirection=sortDirection,
    )

    if soup.select_one("#main.works-index") is None:
        msg = "Works page is missing the expected public index"
        raise ValueError(msg)

    blurbEls = soup.select("ol.work.index > li.work.blurb")
    works = tuple(parseWorkBlurb(innerHtml(el)) for el in blurbEls)

    heading = _selectText(soup, "#main.works-index h2.heading")
    totalMatch = _WORKS_TOTAL_RE.search(heading)
    totalResults = int(totalMatch.group(1).replace(",", "")) if totalMatch is not None else 0

    return UserWorks(
        filters=filters,
        totalResults=totalResults,
        pages=PageInfo(
            total=max(1, getPagesCount(soup)) if works else 0,
            current=resolvedPage,
        ),
        works=works,
    )
