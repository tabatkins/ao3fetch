"""Work, chapter, and blurb scrapers ported from FujoWebDev/AO3.js."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from . import t
from .entities import (
    ArchiveId,
    Author,
    BasicSeries,
    Chapter,
    ChapterText,
    ContentNotes,
    LockedWorkSummary,
    WorkBlurbStats,
    WorkBlurbSummary,
    WorkBlurbTags,
    WorkCategory,
    WorkChaptersCount,
    WorkRatings,
    WorkStats,
    WorkSummary,
    WorkTags,
    WorkText,
    WorkWarnings,
    WorkWithChapters,
    WorkWithText,
)
from .pageLoaders import loadChaptersIndexPage, loadFullWorkChapter, loadWorkPage
from .urls import (
    getArchiveBaseUrl,
    getAsShortUrl,
    getAuthorFromUrl,
    getSeriesUrl,
    getWorkDetailsFromUrl,
    getWorkUrl,
)
from .utils import InvalidIDError, innerHtml, isValidArchiveId, parseArchiveId, parseBlurbDate

ANONYMOUS_AUTHOR: t.Final[Author] = Author(username="Anonymous", pseud="Anonymous", anonymous=True)

_ADULT_RATINGS: t.Final[frozenset[WorkRatings]] = frozenset(
    {
        WorkRatings.EXPLICIT,
        WorkRatings.MATURE,
        WorkRatings.NOT_RATED,
    },
)
_VALID_RATINGS: t.Final[dict[str, WorkRatings]] = {item.value: item for item in WorkRatings}
_VALID_CATEGORIES: t.Final[dict[str, WorkCategory]] = {item.value: item for item in WorkCategory}
_VALID_WARNINGS: t.Final[dict[str, WorkWarnings]] = {item.value: item for item in WorkWarnings}
_DIGITS_RE: t.Final[re.Pattern[str]] = re.compile(r"\d+")
_BY_ANON_RE: t.Final[re.Pattern[str]] = re.compile(r"\bby\s+Anonymous\s*$")
_PARENS_RE: t.Final[re.Pattern[str]] = re.compile(r"[()]")


def isWorkRating(value: str) -> bool:
    """Return True if value is a canonical AO3 WorkRatings string."""
    return value in _VALID_RATINGS


def isWorkCategory(value: str) -> bool:
    """Return True if value is a canonical AO3 WorkCategory string."""
    return value in _VALID_CATEGORIES


def isWorkWarning(value: str) -> bool:
    """Return True if value is a canonical AO3 WorkWarnings string."""
    return value in _VALID_WARNINGS


def isAdultRating(rating: WorkRatings) -> bool:
    """Return True if the rating triggers AO3's adult content warning banner."""
    return rating in _ADULT_RATINGS


def isDefaultChapterTitle(title: str, index: int) -> bool:
    """Return True when a chapter heading matches AO3's default 'Chapter N' placeholder."""
    return title == f"Chapter {index}"


def _parseIntCount(text: str, *, default: int = 0) -> int:
    cleaned = text.replace(",", "").strip()
    return int(cleaned) if cleaned else default


def _selectText(soup: BeautifulSoup, selector: str) -> str:
    el = soup.select_one(selector)
    return el.get_text().strip() if el is not None else ""


def _selectInnerHtml(soup: BeautifulSoup, selector: str) -> str | None:
    el = soup.select_one(selector)
    if el is None:
        return None
    html = innerHtml(el).strip()
    return html or None


def getWorkAuthors(soup: BeautifulSoup) -> tuple[Author, ...]:
    """Extract author/pseud credits from a work page."""
    byline = soup.select_one("h3.byline")
    if byline is not None and byline.get_text().strip() == "Anonymous":
        return (ANONYMOUS_AUTHOR,)
    authors: list[Author] = []
    for link in soup.select("h3.byline a[rel='author']"):
        href = link.get("href")
        if isinstance(href, str):
            authors.append(getAuthorFromUrl(href))
    return tuple(authors)


def getWorkTitle(soup: BeautifulSoup) -> str:
    """Extract the work title from a work page."""
    return _selectText(soup, "h2.title")


def getWorkWordCount(soup: BeautifulSoup) -> int:
    """Extract the integer word count from a work page or blurb."""
    return _parseIntCount(_selectText(soup, "dd.words"))


def getWorkLanguage(soup: BeautifulSoup) -> str:
    """Extract the language display name from a work page or blurb."""
    return _selectText(soup, "dd.language")


def getWorkRating(soup: BeautifulSoup) -> WorkRatings:
    """Extract and validate the work rating."""
    raw = _selectText(soup, "dd.rating a.tag")
    rating = _VALID_RATINGS.get(raw)
    if rating is None:
        msg = f"An unknown rating was found on the page: {raw}"
        raise ValueError(msg)
    return rating


def getWorkCategory(soup: BeautifulSoup) -> tuple[WorkCategory, ...] | None:
    """Extract relationship categories, or None if none are listed."""
    links = soup.select("dd.category a.tag")
    if not links:
        return None
    categories: list[WorkCategory] = []
    for link in links:
        raw = link.get_text().strip()
        category = _VALID_CATEGORIES.get(raw)
        if category is None:
            msg = f"An unknown category was found on the page: {raw}"
            raise ValueError(msg)
        categories.append(category)
    return tuple(categories)


def getWorkFandoms(soup: BeautifulSoup) -> tuple[str, ...]:
    """Extract fandom tag names."""
    return tuple(el.get_text().strip() for el in soup.select("dd.fandom a.tag"))


def getWorkWarnings(soup: BeautifulSoup) -> tuple[WorkWarnings, ...]:
    """Extract and validate archive warnings."""
    warnings: list[WorkWarnings] = []
    for el in soup.select("dd.warning a.tag"):
        raw = el.get_text().strip()
        warning = _VALID_WARNINGS.get(raw)
        if warning is None:
            msg = f"An unknown warning was found on the page: {raw}"
            raise ValueError(msg)
        warnings.append(warning)
    return tuple(warnings)


def getWorkCharacters(soup: BeautifulSoup) -> tuple[str, ...]:
    """Extract character tag names."""
    return tuple(el.get_text().strip() for el in soup.select("dd.character a.tag"))


def getWorkRelationships(soup: BeautifulSoup) -> tuple[str, ...]:
    """Extract relationship tag names."""
    return tuple(el.get_text().strip() for el in soup.select("dd.relationship a.tag"))


def getWorkAdditionalTags(soup: BeautifulSoup) -> tuple[str, ...]:
    """Extract freeform / additional tag names."""
    return tuple(el.get_text().strip() for el in soup.select("dd.freeform ul.commas li"))


def getWorkUpdateDate(soup: BeautifulSoup) -> str | None:
    """Extract the Updated/Completed ISO date string if present."""
    updated = _selectText(soup, "dd.status")
    return updated or None


def getWorkPublishDate(soup: BeautifulSoup) -> str:
    """Extract the Published ISO date string."""
    return _selectText(soup, "dd.published")


def getWorkPublishedChapters(soup: BeautifulSoup) -> int:
    """Extract the number of published chapters."""
    raw = _selectText(soup, "dd.chapters")
    return int(raw.split("/", 1)[0])


def getWorkTotalChapters(soup: BeautifulSoup) -> int | None:
    """Extract the planned total chapter count, or None if '?'."""
    raw = _selectText(soup, "dd.chapters")
    parts = raw.split("/", 1)
    if len(parts) < 2 or parts[1].strip() == "?":
        return None
    return int(parts[1].strip())


def getWorkSummary(soup: BeautifulSoup) -> str | None:
    """Extract the work-level summary HTML."""
    return _selectInnerHtml(soup, ".preface .summary blockquote.userstuff")


def getWorkSeries(soup: BeautifulSoup) -> tuple[BasicSeries, ...]:
    """Extract series membership entries from a work page."""
    seriesList: list[BasicSeries] = []
    for seriesEl in soup.select("dd.series span.series"):
        link = seriesEl.select_one("a:not(.next, .previous)")
        if link is None:
            continue
        href = link.get("href")
        if not isinstance(href, str):
            continue
        rawId = href.replace("/series/", "")
        if not isValidArchiveId(rawId):
            msg = f"Found non-numerical series id in work: {rawId}"
            raise ValueError(msg)
        seriesId = parseArchiveId(rawId)
        url = getSeriesUrl(seriesId)
        numMatch = _DIGITS_RE.search(seriesEl.get_text().strip())
        position = int(numMatch.group(0)) if numMatch is not None else -1
        seriesList.append(
            BasicSeries(
                id=seriesId,
                url=url,
                shortUrl=getAsShortUrl(url),
                index=position,
                name=link.get_text().strip(),
            ),
        )
    return tuple(seriesList)


def getWorkCommentCount(soup: BeautifulSoup) -> int:
    """Extract comment count."""
    return _parseIntCount(_selectText(soup, "dd.comments"))


def getWorkKudosCount(soup: BeautifulSoup) -> int:
    """Extract kudos count."""
    return _parseIntCount(_selectText(soup, "dd.kudos"))


def getWorkBookmarkCount(soup: BeautifulSoup) -> int:
    """Extract bookmark count."""
    return _parseIntCount(_selectText(soup, "dd.bookmarks a"))


def getWorkHits(soup: BeautifulSoup) -> int:
    """Extract hit count."""
    return _parseIntCount(_selectText(soup, "dd.hits"))


def getWorkLocked(soup: BeautifulSoup) -> bool:
    """Return True if the page shows AO3's login gate for a restricted work."""
    return bool(_selectText(soup, "#signin > .heading"))


def getWorkContentBody(soup: BeautifulSoup) -> str:
    """Extract chapter/work prose HTML with screen-reader .landmark headings removed."""
    content = soup.select_one('.userstuff.module[role="article"]')
    if content is None:
        content = soup.select_one("#chapters .userstuff")
    if content is None:
        msg = "No content found on work page"
        raise ValueError(msg)
    bodySoup = BeautifulSoup(innerHtml(content), "html.parser")
    for landmark in bodySoup.select(".landmark"):
        landmark.decompose()
    return innerHtml(bodySoup).strip()


def getChapterStartNotes(soup: BeautifulSoup) -> str | None:
    """Extract chapter-level start notes HTML."""
    return _selectInnerHtml(soup, ".chapter.preface #notes.notes.module .userstuff")


def getChapterEndNotes(soup: BeautifulSoup) -> str | None:
    """Extract chapter-level end notes HTML."""
    return _selectInnerHtml(soup, ".chapter.preface .end.notes.module .userstuff")


def getWorkLevelNotes(soup: BeautifulSoup) -> ContentNotes:
    """Extract work-level start and end notes HTML."""
    return ContentNotes(
        start=_selectInnerHtml(soup, "#workskin > .preface.group > .notes.module .userstuff"),
        end=_selectInnerHtml(soup, "#work_endnotes .userstuff"),
    )


def getMultiChapterId(soup: BeautifulSoup) -> ArchiveId | None:
    """Extract the chapter ID from a multi-chapter page, or None for one-shots."""
    link = soup.select_one("#chapters h3.title a")
    if link is None:
        return None
    href = link.get("href")
    if not isinstance(href, str):
        return None
    return getWorkDetailsFromUrl(href).chapterId


def getChapterIndex(soup: BeautifulSoup) -> int:
    """Extract the 1-based chapter index from a chapter page, or -1 if absent."""
    text = _selectText(soup, "#chapters h3.title a")
    if not text:
        return -1
    return int(text.replace("Chapter ", "").strip())


def getChapterName(soup: BeautifulSoup) -> str | None:
    """Extract the custom chapter title after 'Chapter N: ', or None if untitled."""
    title = _selectText(soup, "#chapters h3.title")
    if title and ":" in title:
        sepIndex = title.find(": ")
        if sepIndex != -1:
            return title[sepIndex + 2 :]
    return None


def getChapterSummary(soup: BeautifulSoup) -> str | None:
    """Extract chapter-level summary HTML."""
    return _selectInnerHtml(soup, ".chapter .summary blockquote.userstuff")


def _extractWorkDetails(soup: BeautifulSoup, workId: ArchiveId) -> WorkSummary | LockedWorkSummary:
    """Build a WorkSummary or LockedWorkSummary from a parsed work page."""
    host = urlparse(getArchiveBaseUrl()).hostname or ""
    url = getWorkUrl(workId)
    shortUrl = getAsShortUrl(url)

    if getWorkLocked(soup):
        return LockedWorkSummary(id=workId, source="website", host=host, url=url, shortUrl=shortUrl)

    totalChapters = getWorkTotalChapters(soup)
    publishedChapters = getWorkPublishedChapters(soup)
    chapterIndex = getChapterIndex(soup)
    rating = getWorkRating(soup)

    return WorkSummary(
        id=workId,
        source="website",
        host=host,
        url=url,
        shortUrl=shortUrl,
        authors=getWorkAuthors(soup),
        title=getWorkTitle(soup),
        words=getWorkWordCount(soup),
        language=getWorkLanguage(soup),
        rating=rating,
        category=getWorkCategory(soup),
        adult=isAdultRating(rating),
        fandoms=getWorkFandoms(soup),
        tags=WorkTags(
            warnings=getWorkWarnings(soup),
            characters=getWorkCharacters(soup),
            relationships=getWorkRelationships(soup),
            additional=getWorkAdditionalTags(soup),
        ),
        publishedAt=getWorkPublishDate(soup),
        updatedAt=getWorkUpdateDate(soup),
        chapters=WorkChaptersCount(published=publishedChapters, total=totalChapters),
        complete=totalChapters is not None and totalChapters == publishedChapters,
        series=getWorkSeries(soup),
        summary=getWorkSummary(soup) if (chapterIndex == 1 or totalChapters == 1) else None,
        stats=WorkStats(
            bookmarks=getWorkBookmarkCount(soup),
            comments=getWorkCommentCount(soup),
            hits=getWorkHits(soup),
            kudos=getWorkKudosCount(soup),
        ),
    )


def getWork(workId: str | int) -> WorkSummary | LockedWorkSummary:
    """Fetch metadata for an archive work by ID."""
    if not isValidArchiveId(workId):
        raise InvalidIDError(workId, "work")
    parsedId = parseArchiveId(workId)
    soup = loadWorkPage(parsedId)
    return _extractWorkDetails(soup, parsedId)


def _extractChapterText(chapterSoup: BeautifulSoup, workId: ArchiveId, index: int) -> ChapterText:
    chapterId = getMultiChapterId(chapterSoup)
    url = getWorkUrl(workId, chapterId=chapterId)
    return ChapterText(
        id=chapterId,
        url=url,
        shortUrl=getAsShortUrl(url),
        index=index,
        title=getChapterName(chapterSoup),
        summary=getChapterSummary(chapterSoup),
        notes=ContentNotes(
            start=getChapterStartNotes(chapterSoup),
            end=getChapterEndNotes(chapterSoup),
        ),
        html=getWorkContentBody(chapterSoup),
    )


def _extractPageChapter(
    soup: BeautifulSoup,
    workId: ArchiveId,
    chapterId: ArchiveId | None,
) -> ChapterText:
    pageChapterId = getMultiChapterId(soup)
    if chapterId is not None and pageChapterId != chapterId:
        shown = "the work" if pageChapterId is None else f"chapter {pageChapterId}"
        msg = f"Chapter {chapterId} was not found: AO3 showed {shown} instead"
        raise ValueError(msg)
    index = 1 if pageChapterId is None else getChapterIndex(soup)
    return _extractChapterText(soup, workId, index)


def _extractFullWorkChapters(soup: BeautifulSoup, workId: ArchiveId) -> tuple[ChapterText, ...]:
    chapterEls = soup.select("#chapters > .chapter")
    if not chapterEls:
        return (_extractChapterText(soup, workId, 1),)
    return tuple(
        _extractChapterText(loadFullWorkChapter(str(chapterEl)), workId, position + 1)
        for position, chapterEl in enumerate(chapterEls)
    )


def getWorkContent(
    workId: str | int,
    *,
    chapterId: str | int | None = None,
    fullWork: bool = False,
) -> WorkWithText | LockedWorkSummary:
    """Fetch work metadata together with one chapter or full-work chapter HTML."""
    if not isValidArchiveId(workId):
        raise InvalidIDError(workId, "work")
    if chapterId is not None and not isValidArchiveId(chapterId):
        raise InvalidIDError(chapterId, "chapter")

    parsedWorkId = parseArchiveId(workId)
    parsedChapterId = parseArchiveId(chapterId) if chapterId is not None else None

    soup = loadWorkPage(parsedWorkId, chapterId=parsedChapterId, fullWork=fullWork)
    work = _extractWorkDetails(soup, parsedWorkId)
    if isinstance(work, LockedWorkSummary):
        return work

    chapters = (
        _extractFullWorkChapters(soup, work.id) if fullWork else (_extractPageChapter(soup, work.id, parsedChapterId),)
    )
    return WorkWithText(
        id=work.id,
        source=work.source,
        host=work.host,
        url=work.url,
        shortUrl=work.shortUrl,
        title=work.title,
        category=work.category,
        publishedAt=work.publishedAt,
        updatedAt=work.updatedAt,
        summary=work.summary,
        rating=work.rating,
        adult=work.adult,
        fandoms=work.fandoms,
        tags=work.tags,
        authors=work.authors,
        language=work.language,
        words=work.words,
        chapters=work.chapters,
        series=work.series,
        complete=work.complete,
        stats=work.stats,
        content=WorkText(notes=getWorkLevelNotes(soup), chapters=chapters),
    )


def getWorkWithChapters(workId: str | int) -> WorkWithChapters:
    """Fetch work title, authors, and chapter list (with dates) from /navigate."""
    if not isValidArchiveId(workId):
        raise InvalidIDError(workId, "work")
    parsedWorkId = parseArchiveId(workId)
    soup = loadChaptersIndexPage(parsedWorkId)

    title = _selectText(soup, ".works-navigate h2 a[href^='/works/']")

    authorLinks = soup.select(".works-navigate h2 a[rel='author']")
    authors: list[Author] = []
    if authorLinks and authorLinks[0].get_text().strip() == "Anonymous":
        authors = [ANONYMOUS_AUTHOR]
    else:
        for link in authorLinks:
            href = link.get("href")
            if isinstance(href, str):
                authors.append(getAuthorFromUrl(href))

    chapters: list[Chapter] = []
    for idx, li in enumerate(soup.select("ol.index > li")):
        chapterLink = li.select_one("a")
        if chapterLink is None:
            continue
        href = chapterLink.get("href")
        if not isinstance(href, str):
            continue
        details = getWorkDetailsFromUrl(href)
        if details.chapterId is None:
            continue
        rawChapterText = chapterLink.get_text()
        sepPos = rawChapterText.find(". ")
        rawTitle = rawChapterText[sepPos + 2 :] if sepPos != -1 else rawChapterText
        chapterIndex = idx + 1
        chapterTitle = None if isDefaultChapterTitle(rawTitle, chapterIndex) else rawTitle
        dateEl = li.select_one(".datetime")
        publishedAt = _PARENS_RE.sub("", dateEl.get_text()).strip() if dateEl is not None else ""
        url = getWorkUrl(details.workId, chapterId=details.chapterId)
        chapters.append(
            Chapter(
                id=details.chapterId,
                workId=details.workId,
                index=chapterIndex,
                title=chapterTitle,
                publishedAt=publishedAt,
                url=url,
                shortUrl=getAsShortUrl(url),
            ),
        )

    return WorkWithChapters(
        title=title,
        authors=tuple(authors),
        workId=parsedWorkId,
        chapters=tuple(chapters),
    )


def parseWorkBlurb(blurbHtml: str) -> WorkBlurbSummary:
    """Parse one work blurb element from a series or user works listing."""
    soup = BeautifulSoup(blurbHtml, "html.parser")
    headingLink = soup.select_one("h4.heading a[href*='/works/']")
    if headingLink is None:
        msg = "Work blurb is missing its title or URL"
        raise ValueError(msg)
    relativeUrl = headingLink.get("href")
    title = headingLink.get_text().strip()
    if not isinstance(relativeUrl, str) or not title:
        msg = "Work blurb is missing its title or URL"
        raise ValueError(msg)

    workId = getWorkDetailsFromUrl(relativeUrl).workId
    url = getWorkUrl(workId)
    totalChapters = getWorkTotalChapters(soup)
    publishedChapters = getWorkPublishedChapters(soup)

    authorLinks = soup.select("h4.heading a[rel='author']")
    headingText = _selectText(soup, "h4.heading")
    if not authorLinks and _BY_ANON_RE.search(headingText) is not None:
        authors: tuple[Author, ...] = (ANONYMOUS_AUTHOR,)
    else:
        parsedAuthors: list[Author] = []
        for link in authorLinks:
            href = link.get("href")
            if isinstance(href, str):
                parsedAuthors.append(getAuthorFromUrl(href))
        if not parsedAuthors:
            msg = "Work blurb is missing its author"
            raise ValueError(msg)
        authors = tuple(parsedAuthors)

    return WorkBlurbSummary(
        id=workId,
        source="website",
        host=urlparse(url).hostname or "",
        url=url,
        shortUrl=getAsShortUrl(url),
        title=title,
        updatedAt=parseBlurbDate(_selectText(soup, "p.datetime")),
        summary=_selectInnerHtml(soup, "blockquote.summary"),
        adult=False,
        fandoms=tuple(el.get_text().strip() for el in soup.select("h5.fandoms a.tag")),
        tags=WorkBlurbTags(
            characters=tuple(el.get_text().strip() for el in soup.select("li.characters a.tag")),
            relationships=tuple(el.get_text().strip() for el in soup.select("li.relationships a.tag")),
            additional=tuple(el.get_text().strip() for el in soup.select("li.freeforms a.tag")),
        ),
        authors=authors,
        language=getWorkLanguage(soup),
        words=getWorkWordCount(soup),
        chapters=WorkChaptersCount(published=publishedChapters, total=totalChapters),
        complete=totalChapters is not None and totalChapters == publishedChapters,
        stats=WorkBlurbStats(
            bookmarks=getWorkBookmarkCount(soup),
            kudos=getWorkKudosCount(soup),
            hits=getWorkHits(soup),
        ),
    )
