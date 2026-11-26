"""AO3 EPUB download parser ported from FujoWebDev/AO3.js."""

from __future__ import annotations

import base64
import io
import re
import warnings
import zipfile
from dataclasses import dataclass
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag, XMLParsedAsHTMLWarning

from . import t
from .entities import (
    Author,
    ChapterText,
    ContentNotes,
    DownloadedFileInfo,
    DownloadedWork,
    WorkCategory,
    WorkChaptersCount,
    WorkRatings,
    WorkTags,
    WorkText,
    WorkWarnings,
)
from .languages import AO3_LANGUAGES
from .urls import getAsShortUrl, getAuthorFromUrl, getWorkDetailsFromUrl, getWorkUrl
from .utils import cleanText, innerHtml
from .works import (
    ANONYMOUS_AUTHOR,
    isAdultRating,
    isDefaultChapterTitle,
    isWorkCategory,
    isWorkRating,
    isWorkWarning,
)

_SAFE_LINK_RE: t.Final[re.Pattern[str]] = re.compile(r"^(?:https?:|mailto:)", re.IGNORECASE)
_PUBLISHED_RE: t.Final[re.Pattern[str]] = re.compile(r"Published:\s*(\S+)")
_UPDATED_RE: t.Final[re.Pattern[str]] = re.compile(r"(?:Completed|Updated):\s*(\S+)")
_WORDS_RE: t.Final[re.Pattern[str]] = re.compile(r"Words:\s*([\d,]+)")
_CHAPTERS_RE: t.Final[re.Pattern[str]] = re.compile(r"Chapters:\s*(\d+)/(\d+|\?)")
_AUTHOR_PARENS_RE: t.Final[re.Pattern[str]] = re.compile(r"^(.+?)\s+\((.+)\)$")

_PREFACE_LABELS: t.Final[dict[str, tuple[str, ...]]] = {
    "rating": ("Rating",),
    "warnings": ("Archive Warning", "Archive Warnings"),
    "categories": ("Category", "Categories"),
    "fandoms": ("Fandom", "Fandoms"),
    "relationships": ("Relationship", "Relationships"),
    "characters": ("Character", "Characters"),
    "additional": ("Additional Tag", "Additional Tags"),
    "language": ("Language",),
    "stats": ("Stats",),
}
_RENAMED_WARNINGS: t.Final[dict[str, WorkWarnings]] = {
    "Choose Not To Use Archive Warnings": WorkWarnings.CHOOSE_NOT_TO_WARN,
}
_LANGUAGE_NAMES: t.Final[frozenset[str]] = frozenset(AO3_LANGUAGES.values())


@dataclass(slots=True)
class _ParsedStats:
    publishedAt: str
    updatedAt: str | None
    words: int
    chapters: WorkChaptersCount | None


@dataclass(slots=True)
class _RawChapter:
    heading: str
    summary: str | None
    notes: ContentNotes
    html: str


def _resolveZipPath(fromFile: str, href: str) -> str:
    segments = fromFile.split("/")[:-1]
    for segment in unquote(href).split("/"):
        if segment == "..":
            if segments:
                segments.pop()
        elif segment not in {".", ""}:
            segments.append(segment)
    return "/".join(segments)


def _readZipBytes(zf: zipfile.ZipFile, fromFile: str, href: str) -> tuple[str, bytes]:
    filePath = _resolveZipPath(fromFile, href)
    try:
        return (filePath, zf.read(filePath))
    except KeyError as exc:
        msg = f"The EPUB doesn't have the file {filePath}"
        raise ValueError(msg) from exc


def _extractEpubBody(epub: bytes) -> tuple[BeautifulSoup, str]:
    """Combine all EPUB spine XHTML files into one BeautifulSoup document."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(epub))
    except zipfile.BadZipFile as exc:
        msg = "Couldn't open the file as an EPUB"
        raise ValueError(msg) from exc

    with zf, warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
        _, containerBytes = _readZipBytes(zf, "", "META-INF/container.xml")
        containerSoup = BeautifulSoup(containerBytes.decode("utf-8", errors="replace"), "html.parser")
        rootfile = containerSoup.find("rootfile")
        packagePath = rootfile.get("full-path") if isinstance(rootfile, Tag) else None
        if not isinstance(packagePath, str) or not packagePath:
            msg = "The EPUB doesn't say where its package file is"
            raise ValueError(msg)

        _, pkgBytes = _readZipBytes(zf, "", packagePath)
        pkgSoup = BeautifulSoup(pkgBytes.decode("utf-8", errors="replace"), "html.parser")

        items: dict[str, tuple[str, str]] = {}
        mediaTypes: dict[str, str] = {}
        for item in pkgSoup.select("manifest > item"):
            itemId = item.get("id")
            href = item.get("href")
            mediaType = item.get("media-type")
            if isinstance(itemId, str) and isinstance(href, str) and href:
                resolvedMedia = mediaType if isinstance(mediaType, str) else "image/jpeg"
                items[itemId] = (href, resolvedMedia)
                mediaTypes[_resolveZipPath(packagePath, href)] = resolvedMedia

        spinePaths: list[str] = []
        for itemref in pkgSoup.select("spine > itemref"):
            idref = itemref.get("idref")
            if not isinstance(idref, str) or idref not in items:
                msg = "The EPUB's reading order lists a file it doesn't have"
                raise ValueError(msg)
            href, _ = items[idref]
            filePath, _ = _readZipBytes(zf, packagePath, href)
            spinePaths.append(filePath)

        langEl = pkgSoup.find("dc:language")
        languageCode = langEl.get_text().strip() if isinstance(langEl, Tag) else ""

        bodies: list[str] = []
        for filePath in spinePaths:
            docSoup = BeautifulSoup(zf.read(filePath).decode("utf-8", errors="replace"), "html.parser")
            for img in docSoup.select("img"):
                src = img.get("src")
                if not isinstance(src, str) or not src:
                    continue
                parsed = urlparse(src)
                if parsed.scheme:
                    continue
                imgPath, imgBytes = _readZipBytes(zf, filePath, src)
                mtype = mediaTypes.get(imgPath, "image/jpeg")
                encoded = base64.b64encode(imgBytes).decode("ascii")
                img["src"] = f"data:{mtype};base64,{encoded}"
            bodyEl = docSoup.find("body")
            bodies.append(innerHtml(bodyEl) if isinstance(bodyEl, Tag) else "")

    return (BeautifulSoup("\n".join(bodies), "html.parser"), languageCode)


def _sanitizeNodes(nodes: list[Tag | NavigableString]) -> str:
    """Clean EPUB HTML fragments (strip styling/classes, drop endnote links, keep safe links)."""
    rawHtml = "".join(str(node) for node in nodes)
    soup = BeautifulSoup(f"<div>{rawHtml}</div>", "html.parser")
    wrapper = soup.find("div")
    if not isinstance(wrapper, Tag):
        return ""
    for endnoteLink in wrapper.select(".endnote-link"):
        endnoteLink.decompose()
    for element in list(wrapper.find_all(True)):
        if not isinstance(element, Tag):
            continue
        href = element.get("href")
        src = element.get("src")
        alt = element.get("alt")
        element.attrs = {}
        if element.name == "a":
            if isinstance(href, str) and _SAFE_LINK_RE.match(href):
                element["href"] = href
            else:
                element.unwrap()
        elif element.name == "img" and isinstance(src, str) and src:
            element["src"] = src
            if isinstance(alt, str):
                element["alt"] = alt
        elif element.name == "iframe" and isinstance(src, str) and src.startswith("https:"):
            element["src"] = src
    return innerHtml(wrapper).strip()


def _getNotesAfter(scopeNodes: list[Tag], label: str) -> str | None:
    for scope in scopeNodes:
        for para in scope.find_all("p"):
            if not isinstance(para, Tag):
                continue
            if cleanText(para.get_text()) != label:
                continue
            if para.find_parent("blockquote") is not None:
                continue
            bq = para.find_next_sibling("blockquote")
            if isinstance(bq, Tag):
                contents = [c for c in bq.contents if isinstance(c, (Tag, NavigableString))]
                return _sanitizeNodes(contents)
    return None


def _extractPrefaceTags(soup: BeautifulSoup) -> dict[str, list[str]]:
    rawTags: dict[str, list[str]] = {}
    for term in soup.select("#preface dl.tags dt"):
        label = cleanText(term.get_text()).rstrip(":")
        dd = term.find_next_sibling()
        if not isinstance(dd, Tag) or dd.name != "dd":
            continue
        links = dd.find_all("a")
        if links:
            rawTags[label] = [cleanText(link.get_text()) for link in links]
        else:
            rawTags[label] = [cleanText(dd.get_text())]
    return rawTags


def _lookupPreface(tagsMap: dict[str, list[str]], fieldName: str) -> list[str] | None:
    for label in _PREFACE_LABELS[fieldName]:
        if label in tagsMap:
            return tagsMap[label]
    return None


def _parseStats(statsText: str) -> _ParsedStats | None:
    pubMatch = _PUBLISHED_RE.search(statsText)
    wordsMatch = _WORDS_RE.search(statsText)
    if pubMatch is None or wordsMatch is None:
        return None
    updMatch = _UPDATED_RE.search(statsText)
    chMatch = _CHAPTERS_RE.search(statsText)
    chaptersCount = (
        WorkChaptersCount(
            published=int(chMatch.group(1)),
            total=None if chMatch.group(2) == "?" else int(chMatch.group(2)),
        )
        if chMatch is not None
        else None
    )
    return _ParsedStats(
        publishedAt=pubMatch.group(1),
        updatedAt=updMatch.group(1) if updMatch is not None else None,
        words=int(wordsMatch.group(1).replace(",", "")),
        chapters=chaptersCount,
    )


def _extractEpubChapters(soup: BeautifulSoup) -> list[_RawChapter]:
    chaptersRoot = soup.select_one("#chapters")
    if chaptersRoot is None:
        return []
    grouped: list[tuple[str, list[Tag], list[Tag | NavigableString], list[Tag]]] = []
    for part in chaptersRoot.find_all(recursive=False):
        if not isinstance(part, Tag):
            continue
        headingEl = part if part.name == "h2" else part.find("h2")
        partId = part.get("id")
        if isinstance(headingEl, Tag):
            grouped.append((cleanText(headingEl.get_text()), [part], [], []))
        elif isinstance(partId, str) and partId.startswith("endnotes"):
            if grouped:
                grouped[-1][3].append(part)
        elif grouped:
            for child in part.contents:
                if isinstance(child, (Tag, NavigableString)):
                    grouped[-1][2].append(child)

    return [
        _RawChapter(
            heading=heading,
            summary=_getNotesAfter(meta, "Chapter Summary"),
            notes=ContentNotes(
                start=_getNotesAfter(meta, "Chapter Notes"),
                end=_getNotesAfter(endNotes, "Chapter End Notes"),
            ),
            html=_sanitizeNodes(textNodes),
        )
        for heading, meta, textNodes, endNotes in grouped
    ]


def _resolveAuthors(byline: str, authorUrls: list[str], problems: list[str]) -> tuple[Author, ...] | None:
    if not authorUrls:
        if byline == "Anonymous":
            return (ANONYMOUS_AUTHOR,)
        authors: list[Author] = []
        for rawPart in byline.split(","):
            part = rawPart.strip()
            if not part:
                continue
            match = _AUTHOR_PARENS_RE.match(part)
            if match is not None:
                authors.append(Author(username=match.group(2), pseud=match.group(1), anonymous=False))
            else:
                authors.append(Author(username=part, pseud=part, anonymous=False))
        return tuple(authors)
    try:
        return tuple(getAuthorFromUrl(url) for url in authorUrls)
    except ValueError as exc:
        problems.append(str(exc))
        return None


def parseEpubWork(epub: bytes, *, filePath: str | None = None) -> DownloadedWork:
    """Parse an AO3 EPUB download into a DownloadedWork with full metadata and chapters."""
    soup, languageCode = _extractEpubBody(epub)
    tagsMap = _extractPrefaceTags(soup)
    prefaceNodes = [el for el in soup.select("#preface") if isinstance(el, Tag)]
    afterwordNodes = [el for el in soup.select("#afterword") if isinstance(el, Tag)]

    workUrls = [href for link in soup.select("#preface .message a") if isinstance((href := link.get("href")), str)]
    workUrl = next((u for u in workUrls if "/works/" in u), None)
    if workUrl is None:
        msg = "The EPUB doesn't look like a work downloaded from AO3"
        raise ValueError(msg)
    workId = getWorkDetailsFromUrl(workUrl).workId

    titleEl = soup.select_one("#preface h1")
    title = cleanText(titleEl.get_text()) if titleEl is not None else ""
    bylineEl = soup.select_one("#preface .byline")
    byline = re.sub(r"^by\s+", "", cleanText(bylineEl.get_text())) if bylineEl is not None else ""
    authorUrls = [
        href for link in soup.select("#preface .byline a[rel='author']") if isinstance((href := link.get("href")), str)
    ]

    problems: list[str] = []

    rawStatsList = _lookupPreface(tagsMap, "stats")
    rawStats = rawStatsList[0] if rawStatsList else None
    stats = _parseStats(rawStats) if rawStats is not None else None
    if stats is None:
        problems.append(f'Couldn\'t read the "Stats:" list: {rawStats or "(missing)"}')

    rawRatingList = _lookupPreface(tagsMap, "rating")
    rawRating = rawRatingList[0] if rawRatingList else None
    rating: WorkRatings | None = None
    if rawRating is not None and isWorkRating(rawRating):
        rating = WorkRatings(rawRating)
    else:
        problems.append(f"Unknown rating: {rawRating or '(missing)'}")

    rawCategories = _lookupPreface(tagsMap, "categories")
    categories: tuple[WorkCategory, ...] | None = None
    if rawCategories is not None:
        parsedCats: list[WorkCategory] = []
        for item in rawCategories:
            if isWorkCategory(item):
                parsedCats.append(WorkCategory(item))
            else:
                problems.append(f"Unknown category: {item}")
        categories = tuple(parsedCats)

    parsedWarnings: list[WorkWarnings] = []
    for rawWarn in _lookupPreface(tagsMap, "warnings") or []:
        mapped = _RENAMED_WARNINGS.get(rawWarn, rawWarn)
        if isWorkWarning(mapped):
            parsedWarnings.append(WorkWarnings(mapped))
        else:
            problems.append(f"Unknown warning: {rawWarn}")

    rawLangList = _lookupPreface(tagsMap, "language")
    languageName = rawLangList[0] if rawLangList else None
    language: str | None = None
    if languageName is not None:
        if languageName in _LANGUAGE_NAMES:
            language = languageName
        else:
            problems.append(f"Unknown language: {languageName}")
    elif languageCode:
        if languageCode in AO3_LANGUAGES:
            language = AO3_LANGUAGES[languageCode]
        else:
            problems.append(f"Unknown language code: {languageCode}")
    else:
        problems.append("Missing language")

    authors = _resolveAuthors(byline, authorUrls, problems)
    fandoms = tuple(_lookupPreface(tagsMap, "fandoms") or [])
    rawChapters = _extractEpubChapters(soup)

    if not title:
        problems.append("Missing title")
    if not fandoms:
        problems.append("Missing fandoms")
    if authors is not None and not authors:
        problems.append("Missing authors")
    if not rawChapters:
        problems.append("Missing chapters")

    if stats is None or rating is None or authors is None or language is None or not rawChapters or problems:
        msg = "The EPUB isn't a valid AO3 download:\n- " + "\n- ".join(problems)
        raise ValueError(msg)

    isMulti = stats.chapters is not None
    chaptersTuple = tuple(
        ChapterText(
            id=None,
            url=None,
            shortUrl=None,
            index=idx + 1,
            title=None if (not isMulti or isDefaultChapterTitle(ch.heading, idx + 1)) else ch.heading,
            summary=ch.summary,
            notes=ch.notes,
            html=ch.html,
        )
        for idx, ch in enumerate(rawChapters)
    )

    canonicalUrl = getWorkUrl(workId)
    chaptersInfo = stats.chapters or WorkChaptersCount(published=len(chaptersTuple), total=len(chaptersTuple))

    return DownloadedWork(
        id=workId,
        source="file",
        file=DownloadedFileInfo(format="epub", filePath=filePath),
        host=urlparse(canonicalUrl).hostname or "",
        url=canonicalUrl,
        shortUrl=getAsShortUrl(canonicalUrl),
        title=title,
        authors=authors,
        rating=rating,
        adult=isAdultRating(rating),
        category=categories,
        fandoms=fandoms,
        tags=WorkTags(
            warnings=tuple(parsedWarnings),
            relationships=tuple(_lookupPreface(tagsMap, "relationships") or []),
            characters=tuple(_lookupPreface(tagsMap, "characters") or []),
            additional=tuple(_lookupPreface(tagsMap, "additional") or []),
        ),
        language=language,
        summary=_getNotesAfter(prefaceNodes, "Summary"),
        publishedAt=stats.publishedAt,
        updatedAt=stats.updatedAt,
        words=stats.words,
        chapters=chaptersInfo,
        complete=chaptersInfo.published == chaptersInfo.total,
        stats=None,
        content=WorkText(
            notes=ContentNotes(
                start=_getNotesAfter(prefaceNodes, "Notes"),
                end=_getNotesAfter(afterwordNodes, "End Notes"),
            ),
            chapters=chaptersTuple,
        ),
    )
