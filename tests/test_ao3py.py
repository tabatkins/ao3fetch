"""Tests for ao3py (Python port of FujoWebDev/AO3.js)."""

from __future__ import annotations

import io
import zipfile
from collections.abc import Mapping

import pytest

import ao3py

_WORK_SINGLE_HTML = """<!DOCTYPE html>
<html><body>
<div id="workskin">
  <div class="preface group">
    <h2 class="title heading">and she burned the sky</h2>
    <h3 class="byline heading"><a rel="author" href="/users/melo/pseuds/melo">melo</a></h3>
    <div class="summary module">
      <blockquote class="userstuff"><p>Life after the wolves.</p></blockquote>
    </div>
    <div class="notes module">
      <blockquote class="userstuff"><p>Work start note.</p></blockquote>
    </div>
  </div>
  <dl class="work meta group">
    <dd class="rating tags"><a class="tag">Teen And Up Audiences</a></dd>
    <dd class="warning tags"><a class="tag">Creator Chose Not To Use Archive Warnings</a></dd>
    <dd class="category tags"><a class="tag">F/F</a></dd>
    <dd class="fandom tags"><a class="tag">Batgirl</a><a class="tag">Teen Titans</a></dd>
    <dd class="relationship tags"><a class="tag">Cassandra Cain/Rose Wilson</a></dd>
    <dd class="character tags"><a class="tag">Cassandra Cain</a><a class="tag">Rose Wilson</a></dd>
    <dd class="freeform tags"><ul class="commas"><li><a class="tag">Moving On</a></li><li><a class="tag">Past Trauma</a></li></ul></dd>
    <dd class="language">English</dd>
    <dd class="stats"><dl class="stats">
      <dd class="published">2025-08-23</dd>
      <dd class="words">500</dd>
      <dd class="chapters">1/1</dd>
      <dd class="comments">4</dd>
      <dd class="kudos">42</dd>
      <dd class="bookmarks"><a>10</a></dd>
      <dd class="hits">1,234</dd>
    </dl></dd>
  </dl>
  <div id="chapters">
    <div class="userstuff module" role="article">
      <h3 class="landmark heading">Work Text</h3>
      <p>The sky was <em>bright</em>.</p>
      <hr />
      <p>Then it faded.</p>
    </div>
  </div>
  <div id="work_endnotes"><div class="userstuff"><p>Work end note.</p></div></div>
</div>
</body></html>
"""

_WORK_MULTI_FULL_HTML = """<!DOCTYPE html>
<html><body>
<div id="workskin">
  <div class="preface group">
    <h2 class="title heading">Two Parts</h2>
    <h3 class="byline heading"><a rel="author" href="/users/alice/pseuds/ally">ally</a></h3>
    <div class="summary module"><blockquote class="userstuff"><p>Main summary.</p></blockquote></div>
    <div class="notes module"><blockquote class="userstuff"><p>Global start note.</p></blockquote></div>
  </div>
  <dl class="work meta group">
    <dd class="rating tags"><a class="tag">General Audiences</a></dd>
    <dd class="warning tags"><a class="tag">No Archive Warnings Apply</a></dd>
    <dd class="category tags"><a class="tag">F/F</a></dd>
    <dd class="fandom tags"><a class="tag">Original Work</a></dd>
    <dd class="language">English</dd>
    <dd class="series"><span class="series">Part 2 of <a href="/series/77">Great Series</a></span></dd>
    <dd class="stats"><dl class="stats">
      <dd class="published">2026-01-10</dd>
      <dd class="status">2026-02-15</dd>
      <dd class="words">2,100</dd>
      <dd class="chapters">2/?</dd>
      <dd class="kudos">9</dd>
      <dd class="hits">100</dd>
    </dl></dd>
  </dl>
  <div id="chapters">
    <div class="chapter" id="chapter-1">
      <div class="chapter preface group">
        <h3 class="title"><a href="/works/555/chapters/1001">Chapter 1</a>: Dawn</h3>
        <div class="summary module"><blockquote class="userstuff"><p>Ch1 sum.</p></blockquote></div>
        <div id="notes" class="notes module"><blockquote class="userstuff"><p>Ch1 start.</p></blockquote></div>
      </div>
      <div class="userstuff module" role="article">
        <h3 class="landmark heading">Chapter Text</h3>
        <p>First chapter body.</p>
      </div>
      <div class="chapter preface group">
        <div class="end notes module"><blockquote class="userstuff"><p>Ch1 end.</p></blockquote></div>
      </div>
    </div>
    <div class="chapter" id="chapter-2">
      <div class="chapter preface group">
        <h3 class="title"><a href="/works/555/chapters/1002">Chapter 2</a></h3>
      </div>
      <div class="userstuff module" role="article">
        <h3 class="landmark heading">Chapter Text</h3>
        <p>Second chapter body.</p>
      </div>
    </div>
  </div>
  <div id="work_endnotes"><div class="userstuff"><p>Global end note.</p></div></div>
</div>
</body></html>
"""

_WORK_NAVIGATE_HTML = """<!DOCTYPE html>
<html><body>
<div class="works-navigate">
  <h2><a href="/works/555">Two Parts</a> by <a rel="author" href="/users/alice/pseuds/ally">ally</a></h2>
  <ol class="chapter index group">
    <li><a href="/works/555/chapters/1001">1. Dawn</a> <span class="datetime">(2026-01-10)</span></li>
    <li><a href="/works/555/chapters/1002">2. Chapter 2</a> <span class="datetime">(2026-02-15)</span></li>
  </ol>
</div>
</body></html>
"""

_WORK_LOCKED_HTML = '<html><body><div id="signin"><h3 class="heading">Log In</h3></div></body></html>'

_SERIES_PAGE_1_HTML = """<!DOCTYPE html>
<html><body>
<h2 class="heading">Great Series</h2>
<dl class="series meta group">
  <dt>Creator:</dt><dd><a rel="author" href="/users/alice/pseuds/alice">alice</a></dd>
  <dt>Series Begun:</dt><dd>2026-01-01</dd>
  <dt>Series Updated:</dt><dd>2026-02-01</dd>
  <dt>Description:</dt><dd><blockquote class="userstuff"><p>Series desc.</p></blockquote></dd>
  <dt>Notes:</dt><dd><p>Series note.</p></dd>
  <dt>Stats:</dt><dd><dl class="stats">
    <dt>Words:</dt><dd>1,500</dd>
    <dt>Works:</dt><dd>2</dd>
    <dt>Complete:</dt><dd>Yes</dd>
    <dt>Bookmarks:</dt><dd>5</dd>
  </dl></dd>
</dl>
<ol class="pagination actions"><li>1</li><li><a>2</a></li><li class="next">Next</li></ol>
<ul class="series work index group">
  <li class="work blurb">
    <h4 class="heading"><a href="/works/101">First Work</a> by <a rel="author" href="/users/alice/pseuds/alice">alice</a></h4>
    <h5 class="fandoms"><a class="tag">Fandom A</a></h5>
    <p class="datetime">01 Jan 2026</p>
    <ul class="tags"><li class="characters"><a class="tag">Char A</a></li></ul>
    <blockquote class="summary"><p>Summary 1.</p></blockquote>
    <dl class="stats"><dd class="language">English</dd><dd class="words">500</dd><dd class="chapters">1/1</dd><dd class="kudos">3</dd><dd class="bookmarks"><a>1</a></dd><dd class="hits">10</dd></dl>
  </li>
</ul>
</body></html>
"""

_SERIES_PAGE_2_HTML = _SERIES_PAGE_1_HTML.replace("/works/101", "/works/102").replace("First Work", "Second Work")

_USER_PROFILE_HTML = """<!DOCTYPE html>
<html><body>
<div id="dashboard">
  <a href="/users/astolat/works">Works (25)</a>
  <a href="/users/astolat/series">Series (3)</a>
  <a href="/users/astolat/bookmarks">Bookmarks (10)</a>
  <a href="/users/astolat/collections">Collections (1)</a>
  <a href="/users/astolat/gifts">Gifts (2)</a>
</div>
<div class="user home profile">
  <div class="header"><h2>astolat</h2><img class="icon" src="https://example.com/icon.png" /></div>
  <h3 class="heading">Profile Header</h3>
  <dl class="meta">
    <dt>My pseuds:</dt><dd class="pseuds"><a href="/users/astolat/pseuds/astolat">astolat</a>, <a href="/users/astolat/pseuds/shalott">shalott</a></dd>
    <dt>I joined on:</dt><dd>2008-09-13</dd>
    <dt>My user ID is:</dt><dd>1</dd>
    <dt class="location">I live in:</dt><dd>NYC</dd>
    <dt>My birthday:</dt><dd class="birthday">Jan 1</dd>
  </dl>
  <div class="bio"><div class="userstuff"><p>Bio text.</p></div></div>
</div>
</body></html>
"""

_TAG_PAGE_HTML = """<!DOCTYPE html>
<html><body>
<div class="tag profile">
  <h2>Sherlock Holmes</h2>
  <p>This tag belongs to the Character Category. It's a common tag. It's a canonical tag.</p>
  <div class="parent"><ul class="tags"><li>Sherlock (TV)</li></ul></div>
  <div class="child"><div class="freeforms"><ul><li><a>Deduction</a></li></ul></div></div>
  <div class="sub"><ul class="tags"><li><a>Teen Sherlock</a><ul class="tags"><li><a>Young Sherlock</a></li></ul></li></ul></div>
  <div class="synonym"><ul class="tags"><li>Sherlock</li></ul></div>
</div>
</body></html>
"""

_TAG_WORKS_FEED_HTML = '<html><body><a class="rss" href="/tags/12345/feed.atom">RSS</a></body></html>'
_TAG_ATOM_XML = "<?xml version='1.0'?><feed><title>AO3 works tagged 'Sherlock Holmes'</title></feed>"


def _makeRouteFetcher(routes: dict[str, tuple[int, str]]) -> ao3py.Fetcher:
    def _fetch(url: str, _headers: Mapping[str, str] | None = None) -> ao3py.FetchResponse:
        if url in routes:
            status, body = routes[url]
            return ao3py.FetchResponse(status=status, headers={}, body=body.encode("utf-8"), url=url)
        return ao3py.FetchResponse(status=404, headers={}, body=b"Not Found", url=url)

    return _fetch


def _buildTestEpub() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container><rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles></container>',
        )
        zf.writestr(
            "OEBPS/content.opf",
            '<?xml version="1.0"?><package><metadata><dc:language>en</dc:language></metadata>'
            + '<manifest><item id="c1" href="text/ch.xhtml" media-type="application/xhtml+xml"/>'
            + '<item id="img1" href="images/dot.png" media-type="image/png"/></manifest>'
            + '<spine><itemref idref="c1"/></spine></package>',
        )
        zf.writestr("OEBPS/images/dot.png", b"\x89PNG\r\n\x1a\n")
        zf.writestr(
            "OEBPS/text/ch.xhtml",
            "<html><body>"
            + '<div id="preface">'
            + '<p class="message">Posted originally on the <a href="https://archiveofourown.org/works/999">AO3</a></p>'
            + "<h1>EPUB Story</h1>"
            + '<div class="byline">by <a rel="author" href="https://archiveofourown.org/users/u1/pseuds/p1">p1</a></div>'
            + '<dl class="tags">'
            + "<dt>Rating:</dt><dd><a>General Audiences</a></dd>"
            + "<dt>Archive Warning:</dt><dd><a>Choose Not To Use Archive Warnings</a></dd>"
            + "<dt>Category:</dt><dd><a>F/F</a></dd>"
            + "<dt>Fandom:</dt><dd><a>Test Fandom</a></dd>"
            + "<dt>Additional Tags:</dt><dd><a>Cozy</a><a>Short</a></dd>"
            + "<dt>Stats:</dt><dd>Published: 2026-05-01 Words: 42</dd>"
            + "</dl>"
            + "<p>Summary</p><blockquote><p>EPUB summary.</p></blockquote>"
            + "<p>Notes</p><blockquote><p>EPUB top note.</p></blockquote>"
            + "</div>"
            + '<div id="chapters">'
            + "<div><h2>EPUB Story</h2></div>"
            + '<div><p class="styled">Hello <a href="https://example.com">world</a> <img src="../images/dot.png" alt="dot"/></p></div>'
            + "</div>"
            + '<div id="afterword"><p>End Notes</p><blockquote><p>EPUB end note.</p></blockquote></div>'
            + "</body></html>",
        )
    return buf.getvalue()


def test_url_builders_and_parsers() -> None:
    """URL builders, AO3 tag escaping, short URLs, and URL parsers match AO3.js."""
    ao3py.resetArchiveBaseUrl()
    assert ao3py.getWorkUrl(36667228) == "https://archiveofourown.org/works/36667228"
    assert (
        ao3py.getWorkUrl(398023, chapterId=659774, collectionName="YJ_Prompts", fullWork=True)
        == "https://archiveofourown.org/collections/YJ_Prompts/works/398023/chapters/659774?view_full_work=true"
    )
    assert ao3py.getAsShortUrl("https://archiveofourown.org/works/123") == "https://ao3.org/works/123"
    assert ao3py.getAsShortUrl("https://superlove.sayitditto.net/works/1269") is None

    parsed = ao3py.getWorkDetailsFromUrl("https://superlove.sayitditto.net/works/1269/chapters/42")
    assert parsed.workId == 1269
    assert parsed.chapterId == 42
    assert parsed.baseUrl == "https://superlove.sayitditto.net"

    shortParsed = ao3py.getWorkDetailsFromUrl("https://ao3.org/works/323217")
    assert shortParsed.baseUrl == "https://archiveofourown.org"

    assert (
        ao3py.getTagUrl("A/B & C.D#E?F")
        == "https://archiveofourown.org/tags/A%2As%2AB%20%2Aa%2A%20C%2Ad%2AD%2Ah%2AE%2Aq%2AF/"
    )
    assert ao3py.getAuthorFromUrl("/users/astolat/pseuds/the%20lady") == ao3py.Author(
        username="astolat",
        pseud="the lady",
        anonymous=False,
    )


def test_fetcher_retry_and_cache() -> None:
    """withRetry handles 429/5xx retries and withCache reuses successful responses."""
    calls = 0
    delays: list[float] = []

    def _flaky(url: str, _headers: Mapping[str, str] | None = None) -> ao3py.FetchResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ao3py.FetchResponse(status=429, headers={"Retry-After": "2"}, body=b"", url=url)
        if calls == 2:
            return ao3py.FetchResponse(status=503, headers={}, body=b"", url=url)
        return ao3py.FetchResponse(status=200, headers={}, body=b"ok", url=url)

    retried = ao3py.withRetry(
        _flaky,
        baseDelaySeconds=0.1,
        sleepFunc=delays.append,
    )
    cached = ao3py.withCache(retried, ttlSeconds=60.0, maxEntries=10)

    first = cached("https://example.com/a", {"Cookie": "view_adult=true;"})
    second = cached("https://example.com/a", {"Cookie": "view_adult=true;"})
    assert first.text == "ok"
    assert second.text == "ok"
    assert calls == 3
    assert delays[0] == 2.0
    assert len(delays) == 2


def test_work_series_user_and_tag_scrapers() -> None:
    """Works, chapters, locked works, series pagination, users, and tags parse accurately."""
    routes = {
        "https://superlove.sayitditto.net/works/1269?view_adult=true": (200, _WORK_SINGLE_HTML),
        "https://archiveofourown.org/works/555?view_full_work=true&view_adult=true": (200, _WORK_MULTI_FULL_HTML),
        "https://archiveofourown.org/works/555/navigate": (200, _WORK_NAVIGATE_HTML),
        "https://archiveofourown.org/works/9999?view_adult=true": (200, _WORK_LOCKED_HTML),
        "https://archiveofourown.org/series/77?page=1": (200, _SERIES_PAGE_1_HTML),
        "https://archiveofourown.org/series/77?page=2": (200, _SERIES_PAGE_2_HTML),
        "https://archiveofourown.org/users/astolat/profile": (200, _USER_PROFILE_HTML),
        "https://archiveofourown.org/tags/Sherlock%20Holmes/": (200, _TAG_PAGE_HTML),
        "https://archiveofourown.org/tags/Sherlock%20Holmes/works": (200, _TAG_WORKS_FEED_HTML),
        "https://archiveofourown.org/tags/12345/feed.atom": (200, _TAG_ATOM_XML),
    }
    ao3py.setFetcher(_makeRouteFetcher(routes))
    try:
        # AO3-compatible archive (Superlove).
        ao3py.setArchiveBaseUrl("https://superlove.sayitditto.net/")
        single = ao3py.getWorkContent(1269)
        assert not isinstance(single, ao3py.LockedWorkSummary)
        assert single.host == "superlove.sayitditto.net"
        assert single.shortUrl is None
        assert single.title == "and she burned the sky"
        assert single.fandoms == ("Batgirl", "Teen Titans")
        assert single.tags.additional == ("Moving On", "Past Trauma")
        assert single.words == 500
        assert single.content.notes.start == "<p>Work start note.</p>"
        assert single.content.notes.end == "<p>Work end note.</p>"
        assert "Work Text" not in single.content.chapters[0].html
        assert ao3py.toPlainText(single.content.chapters[0].html) == "The sky was bright.\n\n---\n\nThen it faded."

        # Standard AO3 multi-chapter full work + /navigate + locked work.
        ao3py.resetArchiveBaseUrl()
        multi = ao3py.getWorkContent(555, fullWork=True)
        assert not isinstance(multi, ao3py.LockedWorkSummary)
        assert multi.complete is False
        assert multi.chapters.published == 2
        assert multi.chapters.total is None
        assert len(multi.content.chapters) == 2
        assert multi.content.chapters[0].title == "Dawn"
        assert multi.content.chapters[0].notes.start == "<p>Ch1 start.</p>"
        assert multi.content.chapters[0].notes.end == "<p>Ch1 end.</p>"
        assert multi.content.chapters[1].title is None
        assert multi.series[0].name == "Great Series"

        nav = ao3py.getWorkWithChapters(555)
        assert [ch.publishedAt for ch in nav.chapters] == ["2026-01-10", "2026-02-15"]
        assert nav.chapters[0].title == "Dawn"
        assert nav.chapters[1].title is None

        locked = ao3py.getWork(9999)
        assert isinstance(locked, ao3py.LockedWorkSummary)
        assert locked.locked is True

        # Series pagination.
        pages = ao3py.collectAllPages(ao3py.getSeries, seriesId=77)
        assert len(pages) == 2
        assert [w.title for p in pages for w in p.works] == ["First Work", "Second Work"]

        # User profile.
        user = ao3py.getUser("astolat")
        assert user.id == 1
        assert user.pseuds == "astolat, shalott"
        assert user.works == 25
        assert user.location == "NYC"

        # Tag profile + Atom lookup.
        tag = ao3py.getTag("Sherlock Holmes")
        assert tag.id == 12345
        assert tag.canonical is True
        assert tag.category == "character"
        assert tag.parentTags == ("Sherlock (TV)",)
        assert tag.childTags == (ao3py.ChildTag(tagName="Deduction", category="additional tags"),)
        assert tag.subTags == (
            ao3py.SubTag(tagName="Teen Sherlock", parentSubTag=None),
            ao3py.SubTag(tagName="Young Sherlock", parentSubTag="Teen Sherlock"),
        )
        assert ao3py.getTagNameById(12345) == "Sherlock Holmes"
    finally:
        ao3py.resetFetcher()
        ao3py.resetArchiveBaseUrl()


def test_parse_epub_work() -> None:
    """parseEpubWork extracts metadata, chapters, notes, and embedded images from an EPUB."""
    work = ao3py.parseEpubWork(_buildTestEpub(), filePath="story.epub")
    assert work.id == 999
    assert work.title == "EPUB Story"
    assert work.authors == (ao3py.Author(username="u1", pseud="p1", anonymous=False),)
    assert work.tags.warnings == (ao3py.WorkWarnings.CHOOSE_NOT_TO_WARN,)
    assert work.language == "English"
    assert work.summary == "<p>EPUB summary.</p>"
    assert work.content.notes.start == "<p>EPUB top note.</p>"
    assert work.content.notes.end == "<p>EPUB end note.</p>"
    assert "data:image/png;base64," in work.content.chapters[0].html
    assert 'class="styled"' not in work.content.chapters[0].html
    assert work.file.filePath == "story.epub"


def test_invalid_id_raises() -> None:
    """Invalid work/series IDs raise InvalidIDError."""
    with pytest.raises(ao3py.InvalidIDError):
        ao3py.getWork("not-a-number")
    with pytest.raises(ao3py.InvalidIDError):
        ao3py.getSeries("bad")
