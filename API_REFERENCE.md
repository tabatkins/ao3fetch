# `ao3fetch` API Reference

Complete reference for all public functions, classes, enums, type aliases, exceptions, and constants exported by `ao3fetch`.

All symbols documented below are re-exported directly from the top-level `ao3fetch` package (e.g. `import ao3fetch; ao3fetch.getWorkContent(...)`).

## Table of Contents

- [Works & Chapters](#works--chapters)
  - [Functions](#works-functions)
  - [Data Classes](#works-data-classes)
  - [Enums](#works-enums)
- [EPUB Downloads](#epub-downloads)
  - [Functions](#epub-functions)
  - [Data Classes](#epub-data-classes)
- [Series](#series)
  - [Functions](#series-functions)
  - [Data Classes](#series-data-classes)
- [Users](#users)
  - [Functions](#users-functions)
  - [Data Classes](#users-data-classes)
  - [Type Aliases](#users-type-aliases)
- [Tags & Tag Search](#tags--tag-search)
  - [Functions](#tags-functions)
  - [Data Classes](#tags-data-classes)
  - [Type Aliases](#tags-type-aliases)
- [Pagination](#pagination)
  - [Functions](#pagination-functions)
  - [Protocol & Data Class](#pagination-protocol--data-class)
- [HTML Conversion](#html-conversion)
- [URLs, Archive Base URL & IDs](#urls-archive-base-url--ids)
  - [Constants & Submodule](#urls-constants--submodule)
  - [Archive Base URL Configuration](#archive-base-url-configuration)
  - [URL Builders](#url-builders)
  - [URL Parsers & Data Classes](#url-parsers--data-classes)
  - [Archive ID Helpers & Types](#archive-id-helpers--types)
- [HTTP Fetcher, Retry & Caching](#http-fetcher-retry--caching)
  - [Fetcher Configuration](#fetcher-configuration)
  - [Middleware & Helpers](#middleware--helpers)
  - [Classes & Type Aliases](#fetcher-classes--type-aliases)
- [Exceptions, Constants & Shared Types](#exceptions-constants--shared-types)
  - [Exceptions](#exceptions)
  - [Constants](#constants)
  - [Shared Type Aliases](#shared-type-aliases)

---

## Works & Chapters

<a id="works-functions"></a>
### Functions

#### `getWork(workId: str | int) -> WorkSummary | LockedWorkSummary`
Fetch metadata for an archive work by ID.

- Automatically appends `view_adult=true` and sends `Cookie: view_adult=true;` to bypass adult content warning gates.
- Returns `LockedWorkSummary` (`locked == True`) if the work is restricted to logged-in users rather than raising an error. To scrape restricted works, install a custom fetcher via [`setFetcher`](#setfetcher) that attaches a session `Cookie`.
- `WorkSummary.summary` is only populated when AO3 renders the work summary on the loaded page (one-shots or chapter 1).
- Raises [`InvalidIDError`](#invalididerror) if `workId` is not a valid archive ID, [`ArchivePageRequestError`](#archivepagerequesterror) on non-2xx HTTP responses, or `ValueError` if an unrecognized rating/category/warning is encountered.

#### `getWorkContent(workId: str | int, *, chapterId: str | int | None = None, fullWork: bool = False) -> WorkWithText | LockedWorkSummary`
Fetch work metadata together with one chapter or full-work chapter HTML and author's notes.

- Set `fullWork=True` to load every chapter of a multi-chapter work in a single HTTP request (`?view_full_work=true`).
- When `fullWork=False`, fetches either the work root (chapter 1 / one-shot) or the specific `chapterId`. If a requested `chapterId` does not match the chapter AO3 actually served, raises `ValueError`.
- Removes screen-reader `.landmark` headings (e.g. `"Work Text"`, `"Chapter Text"`) from returned chapter HTML.
- Returns `LockedWorkSummary` if the work is restricted.
- Raises [`InvalidIDError`](#invalididerror) for invalid `workId` or `chapterId`, [`ArchivePageRequestError`](#archivepagerequesterror) on HTTP errors, or `ValueError` if no content body is present on the page.

#### `getWorkWithChapters(workId: str | int) -> WorkWithChapters`
Fetch work title, authors, and chapter list (including per-chapter publication dates) from `/works/<id>/navigate`.

- Chapters using AO3's default `"Chapter N"` placeholder have `Chapter.title` normalized to `None`.
- Raises [`InvalidIDError`](#invalididerror) if `workId` is invalid or [`ArchivePageRequestError`](#archivepagerequesterror) on HTTP errors.

#### `parseWorkBlurb(blurbHtml: str) -> WorkBlurbSummary`
Parse one work blurb HTML fragment (`<li class="work blurb">`) from a series or user works listing page.

- Converts AO3 blurb dates like `"01 Jan 2026"` into ISO `"2026-01-01"`.
- `WorkBlurbSummary.adult` is always `False` because listing blurbs do not include the adult-gate indicator.
- Raises `ValueError` if the blurb is missing its title, URL, author, or has an unrecognized date format.

<a id="works-data-classes"></a>
### Data Classes

All data classes use `@dataclass(slots=True)`.

#### `WorkSummary`
Full metadata for a publicly accessible work.

- `id: ArchiveId`
- `source: Literal["website"]`
- `host: str`
- `url: str`
- `shortUrl: str | None`
- `title: str`
- `category: tuple[WorkCategory, ...] | None`
- `publishedAt: str`
- `updatedAt: str | None`
- `summary: str | None` — inner HTML fragment, or `None` if absent
- `rating: WorkRatings`
- `adult: bool` — `True` for `Mature`, `Explicit`, or `Not Rated`
- `fandoms: tuple[str, ...]`
- `tags: WorkTags`
- `authors: tuple[Author, ...]`
- `language: str`
- `words: int`
- `chapters: WorkChaptersCount`
- `series: tuple[BasicSeries, ...]`
- `complete: bool` — `True` when `chapters.total is not None` and `chapters.total == chapters.published`
- `stats: WorkStats`
- `locked: Literal[False] = False`

#### `WorkWithText`
A work's full metadata together with its HTML text and notes. Has all the same fields as [`WorkSummary`](#worksummary) plus:

- `content: WorkText`
- `locked: Literal[False] = False`

#### `LockedWorkSummary`
Summary returned by `getWork` / `getWorkContent` when a work is restricted to logged-in users.

- `id: ArchiveId`
- `source: Literal["website"]`
- `host: str`
- `url: str`
- `shortUrl: str | None`
- `locked: Literal[True] = True`

#### `WorkWithChapters`
Work title, authors, and chapter list returned by [`getWorkWithChapters`](#getworkwithchaptersworkid-str--int---workwithchapters).

- `title: str`
- `authors: tuple[Author, ...]`
- `workId: ArchiveId`
- `chapters: tuple[Chapter, ...]`

#### `WorkBlurbSummary`
A work as rendered in AO3 listing pages (series, user works).

- `id: ArchiveId`
- `source: Literal["website"]`
- `host: str`
- `url: str`
- `shortUrl: str | None`
- `title: str`
- `updatedAt: str | None`
- `summary: str | None` — inner HTML fragment
- `adult: bool`
- `fandoms: tuple[str, ...]`
- `tags: WorkBlurbTags`
- `authors: tuple[Author, ...]`
- `language: str`
- `words: int`
- `chapters: WorkChaptersCount`
- `complete: bool`
- `stats: WorkBlurbStats`

#### `WorkText`
Work-level author's notes and chapter contents.

- `notes: ContentNotes`
- `chapters: tuple[ChapterText, ...]`

#### `ChapterText`
A single chapter's HTML content, summary, and notes.

- `id: ArchiveId | None` — `None` for one-shots or EPUB-parsed chapters
- `url: str | None` — `None` for EPUB-parsed chapters
- `shortUrl: str | None`
- `index: int` — 1-based chapter number
- `title: str | None` — custom chapter title, or `None` if untitled / default `"Chapter N"`
- `summary: str | None` — inner HTML fragment
- `notes: ContentNotes`
- `html: str` — chapter body HTML

#### `Chapter`
Chapter index entry from `/works/<id>/navigate`.

- `id: ArchiveId`
- `workId: ArchiveId`
- `index: int` — 1-based chapter number
- `title: str | None`
- `publishedAt: str` — ISO `"YYYY-MM-DD"` date string (or `""` if missing)
- `url: str`
- `shortUrl: str | None`

#### `ContentNotes`
Start and end author's notes HTML fragments.

- `start: str | None = None`
- `end: str | None = None`

#### `WorkTags`
Structured tag lists on a work page or EPUB download.

- `warnings: tuple[WorkWarnings, ...]`
- `characters: tuple[str, ...]`
- `relationships: tuple[str, ...]`
- `additional: tuple[str, ...]`

#### `WorkBlurbTags`
Tag lists visible on a work blurb card.

- `characters: tuple[str, ...]`
- `relationships: tuple[str, ...]`
- `additional: tuple[str, ...]`

#### `WorkChaptersCount`
Published and planned total chapter counts (`total` is `None` when displayed as `?`).

- `published: int`
- `total: int | None`

#### `WorkStats`
Engagement statistics on a full work page.

- `bookmarks: int`
- `comments: int`
- `kudos: int`
- `hits: int`

#### `WorkBlurbStats`
Engagement statistics visible on a listing blurb.

- `bookmarks: int`
- `kudos: int`
- `hits: int`

#### `Author`
An author or pseud credit on a work or series.

- `username: str`
- `pseud: str`
- `anonymous: bool = False`

#### `BasicSeries`
Series membership reference shown on a work page.

- `id: ArchiveId`
- `url: str`
- `shortUrl: str | None`
- `index: int` — 1-based position in the series (or `-1` if not parsed)
- `name: str`

<a id="works-enums"></a>
### Enums

All enums inherit from `enum.StrEnum`.

#### `WorkRatings`
Canonical AO3 rating labels:

- `NOT_RATED = "Not Rated"`
- `GENERAL_AUDIENCES = "General Audiences"`
- `TEEN_AND_UP_AUDIENCES = "Teen And Up Audiences"`
- `MATURE = "Mature"`
- `EXPLICIT = "Explicit"`

#### `WorkCategory`
Canonical AO3 relationship category labels:

- `FF = "F/F"`
- `FM = "F/M"`
- `GEN = "Gen"`
- `MM = "M/M"`
- `MULTI = "Multi"`
- `OTHER = "Other"`

#### `WorkWarnings`
Canonical AO3 archive warning labels:

- `GRAPHIC_VIOLENCE = "Graphic Depictions Of Violence"`
- `MAJOR_CHARACTER_DEATH = "Major Character Death"`
- `NO_WARNINGS_APPLY = "No Archive Warnings Apply"`
- `NONCON = "Rape/Non-Con"`
- `UNDERAGE = "Underage Sex"`
- `CHOOSE_NOT_TO_WARN = "Creator Chose Not To Use Archive Warnings"`

#### `WorkWarningStatus`
High-level archive warning status enum:

- `NO_WARNINGS_APPLY = "Author indicated no warnings apply"`
- `CHOOSE_NOT_TO_WARN = "Author chose not to warn"`
- `EXTERNAL = "External work"`
- `HAS_WARNING = "Work has one or more warning"`

---

## EPUB Downloads

<a id="epub-functions"></a>
### Functions

#### `parseEpubWork(epub: bytes, *, filePath: str | None = None) -> DownloadedWork`
Parse a downloaded AO3 `.epub` file (raw bytes) into a [`DownloadedWork`](#downloadedwork) completely offline.

- Embeds relative `<img>` assets from inside the EPUB archive as base64 `data:` URIs.
- Sanitizes chapter and note HTML: strips attributes/classes/styles, removes `.endnote-link` anchors, unwraps links whose `href` is not `http:`, `https:`, or `mailto:`, and retains only `https:` `<iframe>` sources.
- Maps the EPUB preface warning `"Choose Not To Use Archive Warnings"` to `WorkWarnings.CHOOSE_NOT_TO_WARN`.
- Resolves language from the preface `Language:` metadata or falls back to `<dc:language>` looked up in [`AO3_LANGUAGES`](#ao3_languages).
- Uses the currently configured archive base URL (see [`setArchiveBaseUrl`](#setarchivebaseurlurl-str---none)) when building the canonical `url`/`host`/`shortUrl`.
- Raises `ValueError` if `epub` is not a valid ZIP/EPUB, does not look like an AO3 download, or is missing required metadata/chapters.

<a id="epub-data-classes"></a>
### Data Classes

#### `DownloadedWork`
Metadata and full text parsed from a downloaded AO3 EPUB file.

- `id: ArchiveId`
- `source: Literal["file"]`
- `file: DownloadedFileInfo`
- `host: str`
- `url: str`
- `shortUrl: str | None`
- `title: str`
- `authors: tuple[Author, ...]`
- `rating: WorkRatings`
- `adult: bool`
- `category: tuple[WorkCategory, ...] | None`
- `fandoms: tuple[str, ...]`
- `tags: WorkTags`
- `language: str`
- `summary: str | None`
- `publishedAt: str`
- `updatedAt: str | None`
- `words: int`
- `chapters: WorkChaptersCount`
- `complete: bool`
- `stats: None` — EPUB downloads do not contain engagement stats
- `content: WorkText`

#### `DownloadedFileInfo`
Source format and optional file path for a downloaded work.

- `format: Literal["epub"]`
- `filePath: str | None`

---

## Series

<a id="series-functions"></a>
### Functions

#### `getSeries(seriesId: str | int, *, page: int | None = None) -> Series`
Fetch metadata and one page of work blurbs for an archive series.

- `page` is 1-based (`None` fetches page 1). Compatible with [`getAllPages`](#getallpagesr-pagedresultgetter-callable-r-kwargs-any---iterabler) and [`collectAllPages`](#collectallpagesr-pagedresultgetter-callable-r-kwargs-any---listr).
- `Series.pages.total` is `0` when the series contains no visible works, otherwise `>= 1`.
- Raises [`InvalidIDError`](#invalididerror) if `seriesId` is invalid or [`ArchivePageRequestError`](#archivepagerequesterror) on HTTP errors.

<a id="series-data-classes"></a>
### Data Classes

#### `Series`
Metadata and one page of works for an archive series.

- `id: ArchiveId`
- `url: str`
- `shortUrl: str | None`
- `name: str`
- `startedAt: str`
- `updatedAt: str`
- `authors: tuple[Author, ...]`
- `description: str | None` — inner HTML fragment
- `notes: str | None` — inner HTML fragment
- `words: int`
- `bookmarks: int`
- `complete: bool`
- `workCount: int`
- `pages: PageInfo`
- `works: tuple[WorkBlurbSummary, ...]`

---

## Users

<a id="users-functions"></a>
### Functions

#### `getUser(username: str) -> User`
Fetch public profile details for an archive username (`/users/<username>/profile`).

- `User.pseuds` is a comma-separated string of all pseuds listed on the profile.
- Raises [`ArchivePageRequestError`](#archivepagerequesterror) on HTTP errors or `ValueError` if expected profile markup (such as the profile icon) is missing.

#### `getUserWorks(username: str, *, pseud: str | None = None, page: int | None = None, sortColumn: UserWorksSortColumn | None = None, sortDirection: SortDirection | None = None) -> UserWorks`
Fetch one page of a user's public works (optionally scoped to a specific `pseud`).

- Defaults `sortColumn` to `"updated_at"`. When `sortDirection` is `None`, `filters.sortDirection` resolves to `"asc"` for `"authors"` and `"title"`, and `"desc"` for all other columns (matching AO3's default sort order).
- Compatible with [`getAllPages`](#getallpagesr-pagedresultgetter-callable-r-kwargs-any---iterabler) and [`collectAllPages`](#collectallpagesr-pagedresultgetter-callable-r-kwargs-any---listr).
- Raises [`ArchivePageRequestError`](#archivepagerequesterror) on HTTP errors or `ValueError` if the public works index is missing.

<a id="users-data-classes"></a>
### Data Classes

#### `User`
Public profile information for an archive user.

- `id: ArchiveId`
- `username: str`
- `pseuds: str`
- `url: str`
- `shortUrl: str | None`
- `icon: str` — profile icon image URL
- `header: str | None`
- `joined: str` — ISO `"YYYY-MM-DD"` join date
- `location: str | None`
- `birthday: str | None`
- `works: int`
- `series: int`
- `bookmarks: int`
- `collections: int`
- `gifts: int`
- `bioHtml: str | None` — inner HTML fragment

#### `UserWorks`
One page of a user's public works.

- `filters: UserWorksFilters`
- `totalResults: int`
- `pages: PageInfo`
- `works: tuple[WorkBlurbSummary, ...]`

#### `UserWorksFilters`
Normalized filter parameters for a user's public works listing.

- `sortColumn: UserWorksSortColumn = "updated_at"`
- `sortDirection: SortDirection = "desc"`
- `page: int = 1`

<a id="users-type-aliases"></a>
### Type Aliases

#### `UserWorksSortColumn`
```python
Literal[
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
```

---

## Tags & Tag Search

<a id="tags-functions"></a>
### Functions

#### `getTag(tagName: str) -> Tag`
Fetch full wrangling status, parent/child/subtag hierarchy, and synonyms for an AO3 tag.

- Makes **two** HTTP requests: the tag profile page (`/tags/<tag>/`) and its works feed page (`/tags/<tag>/works`) to read the numeric tag ID from the RSS/Atom link (`Tag.id` is `None` if no feed link exists).
- Raises [`ArchivePageRequestError`](#archivepagerequesterror) on HTTP errors or `ValueError` if the tag category or ID cannot be parsed.

#### `getTagNameById(tagId: str | int) -> str | None`
Resolve a canonical tag name from its numeric tag ID via `/tags/<tagId>/feed.atom`.

- Returns `None` if the Atom feed does not contain a matching `"AO3 works tagged '...'"` title.
- Raises [`ArchivePageRequestError`](#archivepagerequesterror) on HTTP errors.

#### `searchTags(*, tagName: str | None = None, fandoms: Sequence[str] = (), tagType: TagSearchType = "any", wranglingStatus: TagWranglingStatus = "any", sortColumn: TagSearchSortColumn = "name", sortDirection: SortDirection = "asc", page: int = 1) -> TagSearchResultSummary`
Search AO3 tags with filters and pagination (`/tags/search`).

- Maps AO3's `"UnsortedTag"` result label to `"unsorted"`.
- Compatible with [`getAllPages`](#getallpagesr-pagedresultgetter-callable-r-kwargs-any---iterabler) and [`collectAllPages`](#collectallpagesr-pagedresultgetter-callable-r-kwargs-any---listr).
- Raises [`ArchivePageRequestError`](#archivepagerequesterror) on HTTP errors or `ValueError` on unexpected tag type markup.

<a id="tags-data-classes"></a>
### Data Classes

#### `Tag`
Detailed AO3 tag wrangling and hierarchy information.

- `name: str`
- `id: ArchiveId | None`
- `category: TagCategory`
- `canonical: bool`
- `common: bool`
- `canonicalName: str | None` — set to the displayed name if canonical, the merger target if synonymous, or `None` otherwise
- `parentTags: tuple[str, ...]`
- `childTags: tuple[ChildTag, ...]`
- `subTags: tuple[SubTag, ...]`
- `tagsWithSameMeaning: tuple[str, ...]`

#### `ChildTag`
A child tag listed under a parent tag page.

- `tagName: str`
- `category: TagCategory`

#### `SubTag`
A subtag in a tag's subtag hierarchy.

- `tagName: str`
- `parentSubTag: str | None` — `None` for top-level subtags, or the immediate parent subtag name for nested subtags

#### `TagSearchFilters`
Normalized filter parameters for AO3 tag search.

- `tagName: str | None = None`
- `fandoms: tuple[str, ...] = ()`
- `type: TagSearchType = "any"`
- `wranglingStatus: TagWranglingStatus = "any"`
- `sortColumn: TagSearchSortColumn = "name"`
- `sortDirection: SortDirection = "asc"`
- `page: int = 1`

#### `TagSearchResult`
A single tag row returned from AO3 tag search.

- `name: str`
- `type: TagSearchResultType`
- `canonical: bool`
- `worksCount: int`

#### `TagSearchResultSummary`
One page of AO3 tag search results.

- `filters: TagSearchFilters`
- `totalResults: int`
- `pages: PageInfo`
- `tags: tuple[TagSearchResult, ...]`

<a id="tags-type-aliases"></a>
### Type Aliases

#### `TagCategory`
```python
Literal["fandom", "character", "relationship", "archive warning", "additional tags"]
```

#### `TagSearchType`
```python
Literal["fandom", "character", "relationship", "freeform", "any"]
```

#### `TagSearchResultType`
```python
Literal["fandom", "character", "relationship", "freeform", "unsorted"]
```

#### `TagWranglingStatus`
```python
Literal[
    "canonical",
    "noncanonical",
    "synonymous",
    "canonical_or_synonymous",
    "noncanonical_and_nonsynonymous",
    "any",
]
```

#### `TagSearchSortColumn`
```python
Literal["name", "created_at", "works_count"]
```

---

## Pagination

<a id="pagination-functions"></a>
### Functions

#### `getAllPages[R: PagedResult](getter: Callable[..., R], **kwargs: Any) -> Iterable[R]`
Lazily yield every page of a paginated getter (`getSeries`, `getUserWorks`, `searchTags`), fetching one page per iteration.

- Always calls `getter(page=1, **kwargs)` first, then continues while `page <= result.pages.total` (so empty listings with `pages.total == 0` yield the single empty page 1 and stop).
- Forward any required getter parameters as keyword arguments (e.g. `getAllPages(ao3fetch.getSeries, seriesId=77)`).

#### `collectAllPages[R: PagedResult](getter: Callable[..., R], **kwargs: Any) -> list[R]`
Eagerly fetch every page from [`getAllPages`](#getallpagesr-pagedresultgetter-callable-r-kwargs-any---iterabler) and return them as a `list`.

<a id="pagination-protocol--data-class"></a>
### Protocol & Data Class

#### `PagedResult`
`Protocol` implemented by paginated response types (`Series`, `UserWorks`, `TagSearchResultSummary`):

- `pages: PageInfo`

#### `PageInfo`
Pagination metadata for multi-page archive responses.

- `total: int`
- `current: int`

---

## HTML Conversion

#### `toPlainText(html: str) -> str`
Convert AO3 work/note HTML into plain text matching AO3.js formatting.

- Drops `<img>`, `<script>`, and `<style>` elements.
- Separates block elements with blank lines, turns `<br>` into `\n`, `<hr>` into `---`, and prefixes `<ul><li>` items with `- `.
- Collapses runs of whitespace within lines and normalizes consecutive blank lines.

#### `toMarkdown(html: str) -> str`
Convert AO3 HTML content (prose, summaries, or author's notes) into clean CommonMark Markdown.

- Preserves `_italics_`, `**bold**` (keeping outer spaces/breaks outside emphasis markers), links, images, inline `` `code` ``, fenced `<pre>` blocks (with indentation and internal spaces intact), ATX headings (`<h1>`–`<h6>`), blockquotes (including multi-paragraph quotes), ordered/unordered lists (including continuation indentation), `<hr>` scene breaks (`---`), and safe inline HTML tags (`<u>`, `<s>`, `<del>`, `<sup>`, `<sub>`).
- Collapses HTML source whitespace (`[ \t\r\n]+`) in text nodes outside `<pre>`/`<code>` so source-wrapped HTML does not introduce spurious line breaks.
- Preserves `<br>` (including `<br />\n`) as a single Markdown hard line break (`  \n`), turns consecutive `<br>` tags into clean paragraph breaks without dangling trailing spaces, and omits trailing two-space breaks immediately before setext heading underlines (`---` / `===`) so underlined Markdown headings round-trip cleanly.

---

## URLs, Archive Base URL & IDs

<a id="urls-constants--submodule"></a>
### Constants & Submodule

<a id="default_base_url"></a>
#### `DEFAULT_BASE_URL: Final[str]`
Default archive base URL read from the `ARCHIVE_BASE_URL` environment variable at import time, defaulting to `"https://archiveofourown.org"`.

#### `urls`
The `ao3fetch.urls` submodule itself (also re-exported at top level for compatibility with code referencing `ao3fetch.urls.*`).

<a id="archive-base-url-configuration"></a>
### Archive Base URL Configuration

Base URL state is process-global (not thread-local). If temporarily targeting another OTW/AO3-compatible archive, restore the previous URL in a `try ... finally` block.

#### `setArchiveBaseUrl(url: str) -> None`
Set the active archive base URL used by all URL builders and scrapers (e.g. `"https://superlove.sayitditto.net"`).

#### `getArchiveBaseUrl() -> str`
Return the currently active archive base URL.

#### `resetArchiveBaseUrl() -> None`
Reset the active archive base URL back to [`DEFAULT_BASE_URL`](#default_base_url).

<a id="url-builders"></a>
### URL Builders

#### `getWorkUrl(workId: str | int, *, chapterId: str | int | None = None, collectionName: str | None = None, fullWork: bool = False) -> str`
Construct the canonical URL for a work or specific chapter (optionally under a collection or with `?view_full_work=true`). Raises [`InvalidIDError`](#invalididerror) for invalid IDs.

#### `getWorkIndexUrl(workId: str | int) -> str`
Construct the `/works/<workId>/navigate` chapter index URL. Raises [`InvalidIDError`](#invalididerror) if `workId` is invalid.

#### `getSeriesUrl(seriesId: str | int, *, page: int | None = None) -> str`
Construct a series URL (with optional `?page=<n>`). Raises [`InvalidIDError`](#invalididerror) if `seriesId` is invalid.

#### `getAsShortUrl(url: str) -> str | None`
Convert an `archiveofourown.org` URL to `ao3.org`, preserving path/query/port. Returns `None` for any other host.

#### `getDownloadUrls(workId: ArchiveId, title: str, *, publishedAt: str, updatedAt: str | None = None) -> dict[str, str]`
Build AO3 download URLs keyed by format (`"azw3"`, `"epub"`, `"mobi"`, `"html"`, `"pdf"`).

- Uses `updatedAt` (falling back to `publishedAt`) as an ISO-8601 date/datetime to compute the `updated_at` millisecond timestamp query parameter; naive timestamps are treated as UTC.

#### `getUserProfileUrl(username: str) -> str`
Construct a user profile URL (`/users/<username>/profile`).

#### `getUserWorksUrl(username: str, *, pseud: str | None = None, page: int | None = None, sortColumn: UserWorksSortColumn | None = None, sortDirection: SortDirection | None = None) -> str`
Construct a user's public works listing URL (optionally scoped to `pseud` with pagination and sort query parameters).

#### `getTagUrl(tagName: str) -> str`
Construct a tag URL using AO3's special character token encoding (`/`, `&`, `.`, `#`, `?` → `*s*`, `*a*`, `*d*`, `*h*`, `*q*`) followed by percent-encoding.

#### `getTagWorksFeedUrl(tagName: str) -> str`
Construct the recent works listing URL for a tag (`/tags/<encoded>/works`).

#### `getTagWorksFeedAtomUrl(tagId: str | int) -> str`
Construct the Atom feed URL for a numeric tag ID (`/tags/<tagId>/feed.atom`).

#### `getSearchUrlFromTagFilters(filters: TagSearchFilters) -> str`
Construct an AO3 `/tags/search` URL with query parameters derived from [`TagSearchFilters`](#tagsearchfilters).

<a id="url-parsers--data-classes"></a>
### URL Parsers & Data Classes

#### `getWorkDetailsFromUrl(url: str) -> ParsedWorkUrl`
Extract work ID, optional chapter ID, optional collection name, and origin `baseUrl` from an archive work URL (relative or absolute).

- Normalizes `ao3.org` short URLs so `ParsedWorkUrl.baseUrl` is `"https://archiveofourown.org"`.
- Raises `ValueError` if no `/works/<id>` segment is found, or [`InvalidIDError`](#invalididerror) if matched IDs are invalid.

#### `getUserDetailsFromUrl(url: str) -> ParsedUserUrl`
Extract `username` and optional percent-decoded `pseud` from a `/users/<username>` or `/users/<username>/pseuds/<pseud>` URL. Raises `ValueError` on invalid user URLs.

#### `getAuthorFromUrl(url: str) -> Author`
Parse an AO3 author link (`/users/<username>/pseuds/<pseud>`) into an [`Author`](#author). Raises `ValueError` if the URL does not include a `/pseuds/...` segment.

#### `ParsedWorkUrl`
Work URL components returned by [`getWorkDetailsFromUrl`](#getworkdetailsfromurlurl-str---parsedworkurl).

- `workId: ArchiveId`
- `chapterId: ArchiveId | None = None`
- `collectionName: str | None = None`
- `baseUrl: str | None = None`

#### `ParsedUserUrl`
User URL components returned by [`getUserDetailsFromUrl`](#getuserdetailsfromurlurl-str---parseduserurl).

- `username: str`
- `pseud: str | None = None`

<a id="archive-id-helpers--types"></a>
### Archive ID Helpers & Types

#### `ArchiveId`
```python
type ArchiveId = int
```

#### `isValidArchiveId(rawId: str | int | None) -> bool`
Return `True` if `rawId` is a non-negative `int` (excluding `bool`) or an ASCII base-10 digit string (`^\d+$`).

#### `parseArchiveId(rawId: str | int) -> ArchiveId`
Convert a validated archive ID (`int` or digit `str`) into an `ArchiveId` (`int`).

---

## HTTP Fetcher, Retry & Caching

<a id="fetcher-configuration"></a>
### Fetcher Configuration

Fetcher state is process-global (not thread-local). Restore the default or previous fetcher when overriding temporarily (e.g. in tests or CLI wrappers).

#### `defaultFetch(url: str, headers: Mapping[str, str] | None = None) -> FetchResponse`
Default HTTP `GET` fetcher built on Python's stdlib `urllib.request`.

- Accepts only `https://` and `http://` URLs (raises `ValueError` for other schemes).
- Sends a default `ao3fetch` `User-Agent` header (overridable via `headers`) and uses a 30-second timeout.
- Returns `4xx`/`5xx` HTTP errors as `FetchResponse` objects (with `response.ok == False`) rather than raising `urllib.error.HTTPError`. Network/transport failures raise `OSError`.

#### `getFetcher() -> Fetcher`
Return the active fetcher, defaulting to [`defaultFetch`](#defaultfetchurl-str-headers-mappingstr-str--none--none---fetchresponse).

<a id="setfetcher"></a>
#### `setFetcher(newFetcher: Fetcher) -> None`
Override the HTTP fetcher used by all archive page loaders.

#### `resetFetcher() -> None`
Restore [`defaultFetch`](#defaultfetchurl-str-headers-mappingstr-str--none--none---fetchresponse) as the active fetcher.

<a id="middleware--helpers"></a>
### Middleware & Helpers

#### `withRetry(baseFetcher: Fetcher, *, maxRetries: int = 3, maxRateLimitRetries: int = 10, baseDelaySeconds: float = 1.0, maxDelaySeconds: float = 180.0, maxRetryAfterSeconds: float | None = None, onRetry: OnRetryCallback | None = None, sleepFunc: Callable[[float], None] = time.sleep) -> Fetcher`
Wrap a fetcher to automatically retry HTTP `429` rate limits, `5xx` server errors, and `OSError` network failures.

- Tracks rate-limit retries (`maxRateLimitRetries`) and server/network error retries (`maxRetries`) independently.
- Uses the server's `Retry-After` header (via [`getRetryAfterSeconds`](#getretryaftersecondsheader-str--none--now-float--none--none---float--none)) when present, aborting retries immediately if `maxRetryAfterSeconds` is set and exceeded. Otherwise uses exponential backoff with 50%–100% random jitter capped at `maxDelaySeconds`.
- Calls `onRetry(RetryEvent(...))` before sleeping on each retry attempt.
- When retries are exhausted, re-raises the final `OSError` (for network errors) or returns the final non-2xx `FetchResponse` (for HTTP errors).

#### `withCache(baseFetcher: Fetcher, *, ttlSeconds: float = 300.0, maxEntries: int = 500, clock: Callable[[], float] = time.monotonic) -> Fetcher`
Wrap a fetcher with an in-memory LRU+TTL cache.

- Caches only successful (`response.ok`, i.e. `2xx`) responses, keyed by `(url, sorted_lowercase_nonempty_headers)`.
- Compose as `withCache(withRetry(defaultFetch))` so cached responses skip retry overhead and transient failures are retried before caching.

#### `getRetryAfterSeconds(header: str | None, *, now: float | None = None) -> float | None`
Parse an HTTP `Retry-After` header value (either non-negative numeric seconds or an RFC 7231 HTTP-date) into delay seconds (clamped to `>= 0.0`). Returns `None` if empty or unparseable.

<a id="fetcher-classes--type-aliases"></a>
### Classes & Type Aliases

#### `FetchResponse`
Lightweight HTTP response returned by fetchers.

- `status: int`
- `headers: dict[str, str]`
- `body: bytes`
- `url: str`
- `ok -> bool` *(property)*: `True` for `200 <= status < 300`.
- `text -> str` *(property)*: `body` decoded as UTF-8 (`errors="replace"`).
- `header(name: str) -> str | None`: Case-insensitive response header lookup.

#### `RetryEvent`
Details passed to `onRetry` callbacks before sleeping on a retry attempt.

- `attempt: int` — cumulative retry count (`rateLimitCount + errorCount`)
- `delaySeconds: float`
- `response: FetchResponse | None = None`
- `error: Exception | None = None`

#### `Fetcher`
```python
type Fetcher = Callable[[str, Mapping[str, str] | None], FetchResponse]
```

#### `OnRetryCallback`
```python
type OnRetryCallback = Callable[[RetryEvent], None]
```

---

## Exceptions, Constants & Shared Types

<a id="exceptions"></a>
### Exceptions

<a id="invalididerror"></a>
#### `InvalidIDError(rawId: str | int, kind: Literal["work", "chapter", "series"])`
Subclass of `ValueError` raised when an invalid work, chapter, or series ID is supplied.

- `rawId: str | int` — the invalid input value
- `kind: Literal["work", "chapter", "series"]` — which entity ID failed validation

<a id="archivepagerequesterror"></a>
#### `ArchivePageRequestError(url: str, status: int)`
Subclass of `RuntimeError` raised when an archive HTTP request returns a non-2xx status code.

- `url: str` — requested URL
- `status: int` — HTTP status code

<a id="constants"></a>
### Constants

<a id="ao3_languages"></a>
#### `AO3_LANGUAGES: Final[dict[str, str]]`
Mapping from AO3 language codes (e.g. `"en"`, `"ja"`, `"ptBR"`) to AO3 display language names (e.g. `"English"`, `"日本語"`, `"Português brasileiro"`). Used as a fallback when parsing EPUB `<dc:language>` tags.

<a id="shared-type-aliases"></a>
### Shared Type Aliases

#### `SortDirection`
```python
Literal["asc", "desc"]
```
