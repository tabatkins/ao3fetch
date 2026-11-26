"""Additional tests covering AO3.js behaviors without upstream tests and ao3fetch-specific features."""

from __future__ import annotations

import io
import zipfile
from collections.abc import Mapping

import pytest
from mock_archive import MockArchiveServer, expectUnlockedSummary

import ao3fetch


def _makeEpub(
    *,
    containerXml: str | None = (
        '<?xml version="1.0"?><container><rootfiles>'
        + '<rootfile full-path="OEBPS/content.opf"/></rootfiles></container>'
    ),
    opfXml: str | None = None,
    xhtmlFiles: dict[str, str] | None = None,
    binaryFiles: dict[str, bytes] | None = None,
) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        if containerXml is not None:
            zf.writestr("META-INF/container.xml", containerXml)
        if opfXml is not None:
            zf.writestr("OEBPS/content.opf", opfXml)
        if xhtmlFiles:
            for path, content in xhtmlFiles.items():
                zf.writestr(path, content)
        if binaryFiles:
            for path, data in binaryFiles.items():
                zf.writestr(path, data)
    return buf.getvalue()


def test_pagination_get_all_pages_and_collect_all_pages(mockServer: MockArchiveServer) -> None:
    """getAllPages lazily yields every page and collectAllPages gathers multi-page & empty listings."""
    # Multi-page tag search (Hazbin Hotel canonical characters spans 3 pages in AO3.js mocks).
    pages = ao3fetch.collectAllPages(
        ao3fetch.searchTags,
        tagType="character",
        wranglingStatus="canonical",
        fandoms=("Hazbin Hotel (Cartoon)",),
    )
    assert [p.pages.current for p in pages] == [1, 2, 3]
    assert all(p.pages.total == 3 for p in pages)
    assert sum(len(p.tags) for p in pages) == 141

    # Lazy early break stops fetching further pages.
    mockServer.requestedUrls.clear()
    seen: list[int] = []
    for page in ao3fetch.getAllPages(
        ao3fetch.searchTags,
        tagType="character",
        wranglingStatus="canonical",
        fandoms=("Hazbin Hotel (Cartoon)",),
    ):
        seen.append(page.pages.current)
        if page.pages.current == 1:
            break
    assert seen == [1]
    assert len(mockServer.requestedUrls) == 1

    # Empty listing (pages.total == 0) yields page 1 once and stops.
    emptyPages = ao3fetch.collectAllPages(ao3fetch.getUserWorks, username="franzeska")
    assert len(emptyPages) == 1
    assert emptyPages[0].works == ()
    assert emptyPages[0].pages == ao3fetch.PageInfo(total=0, current=1)


def test_get_retry_after_seconds() -> None:
    """getRetryAfterSeconds parses integer/float seconds, HTTP-dates, and rejects invalid headers."""
    assert ao3fetch.getRetryAfterSeconds(None) is None
    assert ao3fetch.getRetryAfterSeconds("") is None
    assert ao3fetch.getRetryAfterSeconds("   ") is None
    assert ao3fetch.getRetryAfterSeconds("12") == 12.0
    assert ao3fetch.getRetryAfterSeconds(" 2.5 ") == 2.5
    assert ao3fetch.getRetryAfterSeconds("-3") == 0.0
    assert ao3fetch.getRetryAfterSeconds("NaN") is None
    assert ao3fetch.getRetryAfterSeconds("Infinity") is None
    assert ao3fetch.getRetryAfterSeconds("not-a-date") is None

    # Wed, 21 Oct 2015 07:28:00 GMT == 1445412480.0 UTC
    assert ao3fetch.getRetryAfterSeconds("Wed, 21 Oct 2015 07:28:00 GMT", now=1445412470.0) == 10.0
    assert ao3fetch.getRetryAfterSeconds("Wed, 21 Oct 2015 07:28:00 GMT", now=1445412500.0) == 0.0


def test_with_retry_behavior_and_limits() -> None:
    """withRetry handles Retry-After cap, separate 429/5xx limits, network errors, and 404 pass-through."""
    # Non-retryable 404 returns immediately without sleeping.
    calls404 = 0
    sleeps: list[float] = []

    def _fetch404(url: str, _headers: Mapping[str, str] | None = None) -> ao3fetch.FetchResponse:
        nonlocal calls404
        calls404 += 1
        return ao3fetch.FetchResponse(status=404, headers={}, body=b"nope", url=url)

    resp404 = ao3fetch.withRetry(_fetch404, sleepFunc=sleeps.append)("https://example.com/404", None)
    assert resp404.status == 404
    assert calls404 == 1
    assert not sleeps

    # maxRetryAfterSeconds aborts immediately when Retry-After exceeds threshold.
    def _fetchLong429(url: str, _headers: Mapping[str, str] | None = None) -> ao3fetch.FetchResponse:
        return ao3fetch.FetchResponse(status=429, headers={"Retry-After": "120"}, body=b"", url=url)

    longResp = ao3fetch.withRetry(
        _fetchLong429,
        maxRetryAfterSeconds=30.0,
        sleepFunc=sleeps.append,
    )("https://example.com/slow", None)
    assert longResp.status == 429
    assert not sleeps

    # Network OSError retries up to maxRetries then re-raises.
    events: list[ao3fetch.RetryEvent] = []

    def _alwaysFail(_url: str, _headers: Mapping[str, str] | None = None) -> ao3fetch.FetchResponse:
        msg = "connection reset"
        raise OSError(msg)

    retriedNet = ao3fetch.withRetry(
        _alwaysFail,
        maxRetries=2,
        baseDelaySeconds=0.5,
        onRetry=events.append,
        sleepFunc=sleeps.append,
    )
    with pytest.raises(OSError, match="connection reset"):
        retriedNet("https://example.com/net", None)
    assert len(events) == 2
    assert [e.attempt for e in events] == [1, 2]
    assert all(isinstance(e.error, OSError) for e in events)
    assert len(sleeps) == 2


def test_with_cache_ttl_lru_and_headers() -> None:
    """withCache keys on headers, expires by TTL, evicts LRU entries, and skips non-2xx responses."""
    now = 100.0
    calls: list[tuple[str, Mapping[str, str] | None]] = []

    def _clock() -> float:
        return now

    def _fetcher(url: str, headers: Mapping[str, str] | None = None) -> ao3fetch.FetchResponse:
        calls.append((url, headers))
        status = 500 if url.endswith("/err") else 200
        return ao3fetch.FetchResponse(status=status, headers={}, body=f"resp-{len(calls)}".encode(), url=url)

    cached = ao3fetch.withCache(_fetcher, ttlSeconds=10.0, maxEntries=2, clock=_clock)

    # Distinct headers do not share cache entries.
    r1 = cached("https://example.com/a", {"Cookie": "a=1"})
    r2 = cached("https://example.com/a", {"Cookie": "a=2"})
    r1Again = cached("https://example.com/a", {"cookie": "a=1"})
    assert r1.text == "resp-1"
    assert r2.text == "resp-2"
    assert r1Again.text == "resp-1"
    assert len(calls) == 2

    # LRU eviction drops least-recently-used key (a=2 was used before r1Again refreshed a=1).
    cached("https://example.com/b", None)
    assert len(calls) == 3
    cached("https://example.com/a", {"Cookie": "a=1"})  # still cached
    assert len(calls) == 3
    cached("https://example.com/a", {"Cookie": "a=2"})  # evicted -> refetched
    assert len(calls) == 4

    # TTL expiration triggers refetch.
    now = 115.0
    rExpired = cached("https://example.com/a", {"Cookie": "a=2"})
    assert rExpired.text == "resp-5"

    # Non-2xx responses are never cached.
    cached("https://example.com/err", None)
    cached("https://example.com/err", None)
    assert len(calls) == 7


def test_to_plain_text_edge_cases() -> None:
    """toPlainText strips comments, collapses source newlines, handles lists, and preserves headings."""
    html = (
        "<!-- hidden comment -->"
        + "<h1>Chapter Title</h1>"
        + "<p>Line one\nwith source wrap and <a href='https://example.com'>a link</a>.</p>"
        + "<p>First line<br>Second line</p>"
        + "<hr>"
        + "<img src='x.png' alt='ignored'/><script>var x = 1;</script><style>p{}</style>"
        + "<ul><li>Alpha</li><li>Beta</li></ul>"
        + "<ol><li>One</li><li>Two</li></ol>"
    )
    assert ao3fetch.toPlainText(html) == (
        "Chapter Title\n\n"
        + "Line one with source wrap and a link.\n\n"
        + "First line\nSecond line\n\n"
        + "---\n\n"
        + "- Alpha\n- Beta\n\n"
        + "1. One\n2. Two"
    )
    assert ao3fetch.toPlainText("") == ""


def test_to_markdown_ignores_html_comments() -> None:
    """toMarkdown omits HTML comments instead of rendering comment text."""
    assert ao3fetch.toMarkdown("<p>Hello <!-- secret -->world</p>") == "Hello world"


def test_parse_epub_work_multichapter_sanitization_and_errors() -> None:
    """parseEpubWork handles multi-chapter EPUBs, pseud bylines, HTML sanitization, and validation errors."""
    opf = (
        '<?xml version="1.0"?><package><metadata><dc:language>en</dc:language></metadata>'
        + "<manifest>"
        + '<item id="p" href="text/preface.xhtml" media-type="application/xhtml+xml"/>'
        + '<item id="c1" href="text/ch1.xhtml" media-type="application/xhtml+xml"/>'
        + '<item id="c2" href="text/ch2.xhtml" media-type="application/xhtml+xml"/>'
        + "</manifest>"
        + '<spine><itemref idref="p"/><itemref idref="c1"/><itemref idref="c2"/></spine></package>'
    )
    preface = (
        '<html><body><div id="preface">'
        + '<p class="message">Posted on <a href="https://archiveofourown.org/works/4242">AO3</a></p>'
        + "<h1>Multi EPUB</h1>"
        + '<div class="byline">by PenName (realuser), soloauthor</div>'
        + '<dl class="tags">'
        + "<dt>Rating:</dt><dd><a>Mature</a></dd>"
        + "<dt>Archive Warnings:</dt><dd><a>No Archive Warnings Apply</a></dd>"
        + "<dt>Fandom:</dt><dd><a>Original Work</a></dd>"
        + "<dt>Language:</dt><dd>Fran\u00e7ais</dd>"
        + "<dt>Stats:</dt><dd>Published: 2024-01-01 Updated: 2024-02-02 Words: 1,200 Chapters: 2/?</dd>"
        + "</dl></div></body></html>"
    )
    ch1 = (
        '<html><body><div id="chapters">'
        + "<div><h2>Chapter 1</h2>"
        + "<p>Chapter Summary</p><blockquote><p>Sum 1</p></blockquote>"
        + "<p>Chapter Notes</p><blockquote><p>Start 1</p><p class='endnote-link'>See end</p></blockquote></div>"
        + '<div><p class="x">Body 1 <a href="javascript:alert(1)">bad</a> '
        + '<a href="mailto:test@example.com">mail</a> '
        + '<iframe src="https://example.com/embed"></iframe>'
        + '<iframe src="http://insecure.example.com/embed"></iframe></p></div>'
        + '<div id="endnotes1"><p>Chapter End Notes</p><blockquote><p>End 1</p></blockquote></div>'
        + "<div><h2>Custom Title</h2></div>"
        + "<div><p>Body 2<br/></p></div>"
        + "</div></body></html>"
    )
    epub = _makeEpub(
        opfXml=opf,
        xhtmlFiles={
            "OEBPS/text/preface.xhtml": preface,
            "OEBPS/text/ch1.xhtml": ch1,
            "OEBPS/text/ch2.xhtml": "<html><body></body></html>",
        },
    )

    work = ao3fetch.parseEpubWork(epub)
    assert work.id == 4242
    assert work.file == ao3fetch.DownloadedFileInfo(format="epub", filePath=None)
    assert work.adult is True
    assert work.language == "Fran\u00e7ais"
    assert work.authors == (
        ao3fetch.Author(username="realuser", pseud="PenName", anonymous=False),
        ao3fetch.Author(username="soloauthor", pseud="soloauthor", anonymous=False),
    )
    assert work.chapters == ao3fetch.WorkChaptersCount(published=2, total=None)
    assert work.complete is False
    assert work.updatedAt == "2024-02-02"
    assert len(work.content.chapters) == 2
    assert work.content.chapters[0].title is None
    assert work.content.chapters[0].summary == "<p>Sum 1</p>"
    assert work.content.chapters[0].notes == ao3fetch.ContentNotes(start="<p>Start 1</p>", end="<p>End 1</p>")
    assert "javascript:" not in work.content.chapters[0].html
    assert "bad" in work.content.chapters[0].html
    assert 'href="mailto:test@example.com"' in work.content.chapters[0].html
    assert 'src="https://example.com/embed"' in work.content.chapters[0].html
    assert "insecure.example.com" not in work.content.chapters[0].html
    assert work.content.chapters[1].title == "Custom Title"
    assert work.content.chapters[1].html == "<p>Body 2<br></p>"

    with pytest.raises(ValueError, match="Couldn't open the file as an EPUB"):
        ao3fetch.parseEpubWork(b"not a zip")

    nonAo3Epub = _makeEpub(
        opfXml='<?xml version="1.0"?><package><manifest><item id="c" href="c.xhtml"/></manifest><spine><itemref idref="c"/></spine></package>',
        xhtmlFiles={"OEBPS/c.xhtml": "<html><body><p>Plain book</p></body></html>"},
    )
    with pytest.raises(ValueError, match="doesn't look like a work downloaded from AO3"):
        ao3fetch.parseEpubWork(nonAo3Epub)


def test_extra_mock_works_and_language_table() -> None:
    """Verify additional AO3.js fixture works and corrected AO3_LANGUAGES Unicode entries."""
    work923 = expectUnlockedSummary(ao3fetch.getWork(923647))
    assert work923.authors == (ao3fetch.Author(username="anafabula", pseud="Alias", anonymous=False),)
    assert work923.series == (
        ao3fetch.BasicSeries(
            id=53653,
            url="https://archiveofourown.org/series/53653",
            shortUrl="https://ao3.org/series/53653",
            index=1,
            name="observe and report",
        ),
    )

    work647 = expectUnlockedSummary(ao3fetch.getWork(6475531))
    assert work647.authors == (
        ao3fetch.Author(username="orphan_account", pseud="orphan_account", anonymous=False),
        ao3fetch.Author(username="user18368", pseud="user18368", anonymous=False),
    )

    locked497 = ao3fetch.getWork(49733128)
    assert isinstance(locked497, ao3fetch.LockedWorkSummary)
    assert locked497.locked is True

    assert len(ao3fetch.AO3_LANGUAGES) == 168
    assert ao3fetch.AO3_LANGUAGES["akk"] == "\U0001201d\U00012157\U0001207a\U00012311"
    assert ao3fetch.AO3_LANGUAGES["sun"] == "\u1b98\u1b9e \u1b9e\u1ba5\u1b94\u1baa\u1b93 | Basa Sunda"
    assert (
        ao3fetch.AO3_LANGUAGES["cop"]
        == "\u03ef\u2c99\u2c89\u2ca7\u2ca3\u2c89\u2c99\u2c9b\u0300\u2cad\u2c8f\u2c99\u2c93"
    )
    assert ao3fetch.AO3_LANGUAGES["en"] == "English"
    assert ao3fetch.AO3_LANGUAGES["ja"] == "\u65e5\u672c\u8a9e"
    assert ao3fetch.AO3_LANGUAGES["ptBR"] == "Portugu\u00eas brasileiro"
