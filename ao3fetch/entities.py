"""Data entities and enums ported from FujoWebDev/AO3.js."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

type ArchiveId = int

type TagCategory = Literal[
    "fandom",
    "character",
    "relationship",
    "archive warning",
    "additional tags",
]

type TagSearchType = Literal[
    "fandom",
    "character",
    "relationship",
    "freeform",
    "any",
]

type TagSearchResultType = Literal[
    "fandom",
    "character",
    "relationship",
    "freeform",
    "unsorted",
]

type TagWranglingStatus = Literal[
    "canonical",
    "noncanonical",
    "synonymous",
    "canonical_or_synonymous",
    "noncanonical_and_nonsynonymous",
    "any",
]

type TagSearchSortColumn = Literal["name", "created_at", "works_count"]

type UserWorksSortColumn = Literal[
    "authors",
    "title",
    "created_at",
    "updated_at",
    "word_count",
    "hits",
    "kudos_count",
    "comments_count",
    "bookmarks_count",
]

type SortDirection = Literal["asc", "desc"]


class WorkRatings(StrEnum):
    """Canonical AO3 rating labels."""

    NOT_RATED = "Not Rated"
    GENERAL_AUDIENCES = "General Audiences"
    TEEN_AND_UP_AUDIENCES = "Teen And Up Audiences"
    MATURE = "Mature"
    EXPLICIT = "Explicit"


class WorkCategory(StrEnum):
    """Canonical AO3 relationship category labels."""

    FF = "F/F"
    FM = "F/M"
    GEN = "Gen"
    MM = "M/M"
    MULTI = "Multi"
    OTHER = "Other"


class WorkWarningStatus(StrEnum):
    """High-level archive warning status."""

    NO_WARNINGS_APPLY = "Author indicated no warnings apply"
    CHOOSE_NOT_TO_WARN = "Author chose not to warn"
    EXTERNAL = "External work"
    HAS_WARNING = "Work has one or more warning"


class WorkWarnings(StrEnum):
    """Canonical AO3 archive warning labels."""

    GRAPHIC_VIOLENCE = "Graphic Depictions Of Violence"
    MAJOR_CHARACTER_DEATH = "Major Character Death"
    NO_WARNINGS_APPLY = "No Archive Warnings Apply"
    NONCON = "Rape/Non-Con"
    UNDERAGE = "Underage Sex"
    CHOOSE_NOT_TO_WARN = "Creator Chose Not To Use Archive Warnings"


@dataclass(slots=True)
class PageInfo:
    """Pagination metadata for multi-page AO3 responses."""

    total: int
    current: int


@dataclass(slots=True)
class ChildTag:
    """A child tag listed under a parent tag page."""

    tagName: str
    category: TagCategory


@dataclass(slots=True)
class SubTag:
    """A subtag in a tag's subtag hierarchy."""

    tagName: str
    parentSubTag: str | None


@dataclass(slots=True)
class Tag:
    """Detailed AO3 tag information."""

    name: str
    id: ArchiveId | None
    category: TagCategory
    canonical: bool
    common: bool
    canonicalName: str | None
    parentTags: tuple[str, ...]
    childTags: tuple[ChildTag, ...]
    subTags: tuple[SubTag, ...]
    tagsWithSameMeaning: tuple[str, ...]


@dataclass(slots=True)
class TagSearchFilters:
    """Normalized filter parameters for AO3 tag search."""

    tagName: str | None = None
    fandoms: tuple[str, ...] = ()
    type: TagSearchType = "any"
    wranglingStatus: TagWranglingStatus = "any"
    sortColumn: TagSearchSortColumn = "name"
    sortDirection: SortDirection = "asc"
    page: int = 1


@dataclass(slots=True)
class TagSearchResult:
    """A single tag row returned from AO3 tag search."""

    name: str
    type: TagSearchResultType
    canonical: bool
    worksCount: int


@dataclass(slots=True)
class TagSearchResultSummary:
    """One page of AO3 tag search results."""

    filters: TagSearchFilters
    totalResults: int
    pages: PageInfo
    tags: tuple[TagSearchResult, ...]


@dataclass(slots=True)
class User:
    """Public profile information for an archive user."""

    id: ArchiveId
    username: str
    pseuds: str
    url: str
    shortUrl: str | None
    icon: str
    header: str | None
    joined: str
    location: str | None
    birthday: str | None
    works: int
    series: int
    bookmarks: int
    collections: int
    gifts: int
    bioHtml: str | None


@dataclass(slots=True)
class UserWorksFilters:
    """Normalized filter parameters for a user's public works listing."""

    sortColumn: UserWorksSortColumn = "updated_at"
    sortDirection: SortDirection = "desc"
    page: int = 1


@dataclass(slots=True)
class Author:
    """An author or pseud credit on a work or series."""

    username: str
    pseud: str
    anonymous: bool = False


@dataclass(slots=True)
class BasicSeries:
    """Series membership reference shown on a work page."""

    id: ArchiveId
    url: str
    shortUrl: str | None
    index: int
    name: str


@dataclass(slots=True)
class ContentNotes:
    """Start and end author's notes HTML fragments."""

    start: str | None = None
    end: str | None = None


@dataclass(slots=True)
class Chapter:
    """Chapter index entry from a work's /navigate page."""

    id: ArchiveId
    workId: ArchiveId
    index: int
    title: str | None
    publishedAt: str
    url: str
    shortUrl: str | None


@dataclass(slots=True)
class ChapterText:
    """A single chapter's HTML content, summary, and notes."""

    id: ArchiveId | None
    url: str | None
    shortUrl: str | None
    index: int
    title: str | None
    summary: str | None
    notes: ContentNotes
    html: str


@dataclass(slots=True)
class WorkText:
    """Work-level notes and chapter contents."""

    notes: ContentNotes
    chapters: tuple[ChapterText, ...]


@dataclass(slots=True)
class WorkTags:
    """Structured tag lists on a work page or download."""

    warnings: tuple[WorkWarnings, ...]
    characters: tuple[str, ...]
    relationships: tuple[str, ...]
    additional: tuple[str, ...]


@dataclass(slots=True)
class WorkBlurbTags:
    """Tag lists visible on a work blurb card."""

    characters: tuple[str, ...]
    relationships: tuple[str, ...]
    additional: tuple[str, ...]


@dataclass(slots=True)
class WorkChaptersCount:
    """Published and total chapter counts (total is None for '?')."""

    published: int
    total: int | None


@dataclass(slots=True)
class WorkStats:
    """Engagement statistics on a full work page."""

    bookmarks: int
    comments: int
    kudos: int
    hits: int


@dataclass(slots=True)
class WorkBlurbStats:
    """Engagement statistics on a listing blurb."""

    bookmarks: int
    kudos: int
    hits: int


@dataclass(slots=True)
class WorkBlurbSummary:
    """A work as rendered in AO3 listing pages (series, user works)."""

    id: ArchiveId
    source: Literal["website"]
    host: str
    url: str
    shortUrl: str | None
    title: str
    updatedAt: str | None
    summary: str | None
    adult: bool
    fandoms: tuple[str, ...]
    tags: WorkBlurbTags
    authors: tuple[Author, ...]
    language: str
    words: int
    chapters: WorkChaptersCount
    complete: bool
    stats: WorkBlurbStats


@dataclass(slots=True)
class UserWorks:
    """One page of a user's public works."""

    filters: UserWorksFilters
    totalResults: int
    pages: PageInfo
    works: tuple[WorkBlurbSummary, ...]


@dataclass(slots=True)
class Series:
    """Metadata and one page of works for an archive series."""

    id: ArchiveId
    url: str
    shortUrl: str | None
    name: str
    startedAt: str
    updatedAt: str
    authors: tuple[Author, ...]
    description: str | None
    notes: str | None
    words: int
    bookmarks: int
    complete: bool
    workCount: int
    pages: PageInfo
    works: tuple[WorkBlurbSummary, ...]


@dataclass(slots=True)
class LockedWorkSummary:
    """Summary returned when a work is restricted to logged-in users."""

    id: ArchiveId
    source: Literal["website"]
    host: str
    url: str
    shortUrl: str | None
    locked: Literal[True] = True


@dataclass(slots=True)
class WorkSummary:
    """Full metadata for a publicly accessible work."""

    id: ArchiveId
    source: Literal["website"]
    host: str
    url: str
    shortUrl: str | None
    title: str
    category: tuple[WorkCategory, ...] | None
    publishedAt: str
    updatedAt: str | None
    summary: str | None
    rating: WorkRatings
    adult: bool
    fandoms: tuple[str, ...]
    tags: WorkTags
    authors: tuple[Author, ...]
    language: str
    words: int
    chapters: WorkChaptersCount
    series: tuple[BasicSeries, ...]
    complete: bool
    stats: WorkStats
    locked: Literal[False] = False


@dataclass(slots=True)
class WorkWithText:
    """A work's metadata together with its HTML text and notes."""

    id: ArchiveId
    source: Literal["website"]
    host: str
    url: str
    shortUrl: str | None
    title: str
    category: tuple[WorkCategory, ...] | None
    publishedAt: str
    updatedAt: str | None
    summary: str | None
    rating: WorkRatings
    adult: bool
    fandoms: tuple[str, ...]
    tags: WorkTags
    authors: tuple[Author, ...]
    language: str
    words: int
    chapters: WorkChaptersCount
    series: tuple[BasicSeries, ...]
    complete: bool
    stats: WorkStats
    content: WorkText
    locked: Literal[False] = False


@dataclass(slots=True)
class WorkWithChapters:
    """Work title, authors, and chapter list from /works/<id>/navigate."""

    title: str
    authors: tuple[Author, ...]
    workId: ArchiveId
    chapters: tuple[Chapter, ...]


@dataclass(slots=True)
class DownloadedFileInfo:
    """Source format and optional file path for a downloaded work."""

    format: Literal["epub"]
    filePath: str | None


@dataclass(slots=True)
class DownloadedWork:
    """Metadata and full text parsed from a downloaded AO3 EPUB file."""

    id: ArchiveId
    source: Literal["file"]
    file: DownloadedFileInfo
    host: str
    url: str
    shortUrl: str | None
    title: str
    authors: tuple[Author, ...]
    rating: WorkRatings
    adult: bool
    category: tuple[WorkCategory, ...] | None
    fandoms: tuple[str, ...]
    tags: WorkTags
    language: str
    summary: str | None
    publishedAt: str
    updatedAt: str | None
    words: int
    chapters: WorkChaptersCount
    complete: bool
    stats: None
    content: WorkText
