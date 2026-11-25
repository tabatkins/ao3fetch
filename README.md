# ao3py

A typed Python 3.12+ library for scraping [Archive of Our Own (AO3)](https://archiveofourown.org) and AO3-compatible OTW archives (such as Superlove or SquidgeWorld), ported from [FujoWebDev/AO3.js](https://github.com/FujoWebDev/AO3.js). (Currently up-to-date with [Commit 62e3ab8e](https://github.com/FujoWebDev/AO3.js/commit/62e3ab8ed6f0562e131b6f5aeb215c392a571678).)

## Features

- **Works & Chapters:** Fetch work metadata (`getWork`), full work or single-chapter HTML/notes (`getWorkContent`), and `/navigate` chapter indices with publication dates (`getWorkWithChapters`).
- **Series, Users & Tags:** Scrape series metadata & work blurbs (`getSeries`), user profiles & public works (`getUser`, `getUserWorks`), tag wrangling/hierarchies (`getTag`, `getTagNameById`), and tag search (`searchTags`).
- **Pagination:** Iterate or collect multi-page results with `getAllPages` and `collectAllPages`.
- **EPUB Downloads:** Parse downloaded AO3 `.epub` files offline with `parseEpubWork` (extracting metadata, chapters, notes, and embedded images).
- **Text & Markdown Conversion:** Convert AO3 HTML prose/notes to plain text (`toPlainText`) or clean CommonMark Markdown (`toMarkdown`).
- **Archive-Agnostic:** Target any OTW/AO3-compatible archive via `setArchiveBaseUrl(...)` or the `ARCHIVE_BASE_URL` environment variable.
- **Pluggable Fetcher:** Swap the HTTP layer (`setFetcher`), wrap with `429 Retry-After` + `5xx` retry backoff (`withRetry`), and add in-memory LRU+TTL caching (`withCache`).
- **Fully Typed:** Ships with `py.typed` (PEP 561) and slotted dataclasses.

## Installation

```sh
pip install ao3py
```

Requires Python 3.12+ and `beautifulsoup4>=4.12`.

## Quick Start

```python
import ao3py

# Optional: enable retry (respecting 429 Retry-After) and in-memory caching.
ao3py.setFetcher(ao3py.withCache(ao3py.withRetry(ao3py.defaultFetch)))

# Fetch a full work from AO3 (or another AO3-compatible archive).
work = ao3py.getWorkContent(123456, fullWork=True)
if not isinstance(work, ao3py.LockedWorkSummary):
    print(work.title, "by", ", ".join(a.pseud for a in work.authors))
    for chapter in work.content.chapters:
        markdown = ao3py.toMarkdown(chapter.html)
        print(markdown)
```

### Targeting an AO3-Compatible Archive

```python
import ao3py

ao3py.setArchiveBaseUrl("https://superlove.sayitditto.net")
work = ao3py.getWork(1269)
ao3py.resetArchiveBaseUrl()
```

### Parsing a Local AO3 EPUB Download

```python
from pathlib import Path
import ao3py

work = ao3py.parseEpubWork(Path("story.epub").read_bytes(), filePath="story.epub")
print(work.title, len(work.content.chapters))
```

### Iterating Paginated Listings

```python
import ao3py

for page in ao3py.getAllPages(ao3py.getSeries, seriesId=77):
    for blurb in page.works:
        print(blurb.title)
```

## API Overview

See the full [API Reference](API_REFERENCE.md) for complete type signatures, data class fields, enums, and behavioral notes.

| Category | Exports |
| --- | --- |
| Works & Chapters | `getWork`, `getWorkContent`, `getWorkWithChapters`, `parseWorkBlurb` |
| Series | `getSeries` |
| Users | `getUser`, `getUserWorks` |
| Tags | `getTag`, `getTagNameById`, `searchTags` |
| Downloads | `parseEpubWork` |
| Pagination | `getAllPages`, `collectAllPages`, `PagedResult` |
| HTML Conversion | `toPlainText`, `toMarkdown` |
| URLs & Base URL | `DEFAULT_BASE_URL`, `setArchiveBaseUrl`, `getArchiveBaseUrl`, `resetArchiveBaseUrl`, `getWorkUrl`, `getWorkIndexUrl`, `getSeriesUrl`, `getAsShortUrl`, `getDownloadUrls`, `getUserProfileUrl`, `getUserWorksUrl`, `getTagUrl`, `getTagWorksFeedUrl`, `getTagWorksFeedAtomUrl`, `getUserDetailsFromUrl`, `getAuthorFromUrl`, `getWorkDetailsFromUrl`, `getSearchUrlFromTagFilters`, `isValidArchiveId`, `parseArchiveId` |
| Fetcher & Middleware | `defaultFetch`, `getFetcher`, `setFetcher`, `resetFetcher`, `withRetry`, `withCache`, `getRetryAfterSeconds`, `FetchResponse`, `Fetcher`, `RetryEvent`, `OnRetryCallback` |
| Errors | `InvalidIDError`, `ArchivePageRequestError` |
| Entities & Enums | `WorkSummary`, `WorkWithText`, `LockedWorkSummary`, `WorkWithChapters`, `DownloadedWork`, `Series`, `User`, `UserWorks`, `Tag`, `TagSearchResultSummary`, `Author`, `Chapter`, `ChapterText`, `WorkRatings`, `WorkCategory`, `WorkWarnings`, `WorkWarningStatus`, ... |

## Development

```sh
pip install -r requirements-dev.txt
./lint      # runs ruff, black, mypy, pylint (10/10), check-manifest, and pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding conventions.

## License

MIT License — see [LICENSE](LICENSE). Ported from [FujoWebDev/AO3.js](https://github.com/FujoWebDev/AO3.js) (MIT).
