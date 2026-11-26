"""Tests for getWorkContent and toPlainText (ported from AO3.js tests/works-content.test.ts)."""

from __future__ import annotations

from dataclasses import asdict

import pytest
from mock_archive import (
    MockArchiveServer,
    assertHtmlEqual,
    assertMatchesHtmlSnapshot,
    assertMatchesTextSnapshot,
    expectUnlocked,
)

import ao3fetch


def _workFieldsWithoutContent(work: ao3fetch.WorkWithText) -> dict[str, object]:
    data = asdict(work)
    data.pop("content")
    return data


def test_fetch_work_content_with_author_and_end_notes() -> None:
    """getWorkContent matches summary, chapter start/end notes, and body snapshots for 29046888."""
    workContent = expectUnlocked(ao3fetch.getWorkContent(29046888))

    assertMatchesHtmlSnapshot(workContent.summary, "ao3/works/29046888/chapter-1-summary.html")
    assertMatchesHtmlSnapshot(
        workContent.content.chapters[0].notes.start,
        "ao3/works/29046888/chapter-1-start-notes.html",
    )
    assertMatchesHtmlSnapshot(
        workContent.content.chapters[0].notes.end,
        "ao3/works/29046888/chapter-1-end-notes.html",
    )
    assertMatchesHtmlSnapshot(
        workContent.content.chapters[0].html,
        "ao3/works/29046888/chapter-1-content.html",
    )


def test_oneshot_notes_go_on_work_not_chapter() -> None:
    """Oneshot works put start notes on work.content.notes and leave chapter notes null."""
    workContent = expectUnlocked(ao3fetch.getWorkContent(323217))

    assertMatchesHtmlSnapshot(workContent.summary, "ao3/works/323217/chapter-1-summary.html")
    assertMatchesHtmlSnapshot(workContent.content.notes.start, "ao3/works/323217/work-start-notes.html")
    assert workContent.content.notes.end is None
    assert workContent.content.chapters[0].summary is None
    assert workContent.content.chapters[0].notes == ao3fetch.ContentNotes(start=None, end=None)
    assertMatchesHtmlSnapshot(workContent.content.chapters[0].html, "ao3/works/323217/chapter-1-content.html")


def test_fetch_content_from_multi_chapter_work() -> None:
    """Multi-chapter first page exposes both work notes and chapter 1 notes plus plain text."""
    workContent = expectUnlocked(ao3fetch.getWorkContent(17793689))

    assertMatchesHtmlSnapshot(workContent.summary, "ao3/works/17793689/chapter-1-summary.html")
    assertMatchesHtmlSnapshot(
        workContent.content.chapters[0].notes.start,
        "ao3/works/17793689/chapter-1-start-notes.html",
    )
    assertMatchesHtmlSnapshot(workContent.content.notes.start, "ao3/works/17793689/work-start-notes.html")
    assertMatchesHtmlSnapshot(
        workContent.content.chapters[0].html,
        "ao3/works/17793689/chapter-1-content.html",
    )
    assertMatchesTextSnapshot(
        ao3fetch.toPlainText(workContent.content.chapters[0].html),
        "ao3/works/17793689/chapter-1-content.txt",
    )
    assertMatchesHtmlSnapshot(
        workContent.content.chapters[0].notes.end,
        "ao3/works/17793689/chapter-1-end-notes.html",
    )


def test_fetch_content_from_non_first_chapter() -> None:
    """Non-first chapter pages have null work summary/start notes and preserve chapter notes."""
    workContent = expectUnlocked(ao3fetch.getWorkContent(17793689, chapterId=42035519))

    assert workContent.summary is None
    assert workContent.content.notes.start is None
    assert workContent.content.chapters[0].summary is not None
    assertMatchesHtmlSnapshot(
        workContent.content.chapters[0].notes.start,
        "ao3/works/17793689/chapter-2-start-notes.html",
    )
    assertMatchesHtmlSnapshot(
        workContent.content.chapters[0].html,
        "ao3/works/17793689/chapter-2-content.html",
    )
    assert workContent.content.chapters[0].notes.end is None


def test_chapter_urls() -> None:
    """Chapter URLs link to the work for oneshots and to the specific chapter for multi-chapter works."""
    oneshot = expectUnlocked(ao3fetch.getWorkContent(323217))
    assert oneshot.content.chapters[0].url == "https://archiveofourown.org/works/323217"
    assert oneshot.content.chapters[0].shortUrl == "https://ao3.org/works/323217"

    firstChapter = expectUnlocked(ao3fetch.getWorkContent(17793689))
    assert firstChapter.content.chapters[0].url == "https://archiveofourown.org/works/17793689/chapters/41980418"

    secondChapter = expectUnlocked(ao3fetch.getWorkContent(17793689, chapterId=42035519))
    assert secondChapter.content.chapters[0].url == "https://archiveofourown.org/works/17793689/chapters/42035519"
    assert secondChapter.content.chapters[0].shortUrl == "https://ao3.org/works/17793689/chapters/42035519"


def test_chapter_details_and_redirect_mismatch(mockServer: MockArchiveServer) -> None:
    """getWorkContent reads chapter id/index/title and raises when AO3 redirects to another chapter."""
    firstWork = expectUnlocked(ao3fetch.getWorkContent(17793689))
    assert len(firstWork.content.chapters) == 1
    assert firstWork.content.chapters[0].id == 41980418
    assert firstWork.content.chapters[0].index == 1

    secondWork = expectUnlocked(ao3fetch.getWorkContent(17793689, chapterId=42035519))
    assert secondWork.content.chapters[0].id == 42035519
    assert secondWork.content.chapters[0].index == 2
    assert secondWork.content.chapters[0].title == "The College of Enchanters: New Haven"

    mockServer.overrideRedirect(
        lambda url: url.startswith("https://archiveofourown.org/works/17793689/chapters/1"),
        "https://archiveofourown.org/works/17793689/chapters/41980418",
        status=302,
    )
    with pytest.raises(ValueError, match=r"Chapter 1 was not found: AO3 showed chapter 41980418 instead"):
        ao3fetch.getWorkContent(17793689, chapterId=1)

    fullFlag: bool = True
    fullWork = expectUnlocked(ao3fetch.getWorkContent(17793689, fullWork=fullFlag))
    assert len(fullWork.content.chapters) > 1


def test_work_content_details_match_get_work() -> None:
    """getWorkContent returns the exact same work metadata fields as getWork."""
    content290 = expectUnlocked(ao3fetch.getWorkContent(29046888))
    work290 = ao3fetch.getWork(29046888)
    assert not isinstance(work290, ao3fetch.LockedWorkSummary)
    assert _workFieldsWithoutContent(content290) == asdict(work290)

    contentCh2 = expectUnlocked(ao3fetch.getWorkContent(17793689, chapterId=42035519))
    work177 = ao3fetch.getWork(17793689)
    assert not isinstance(work177, ao3fetch.LockedWorkSummary)
    expected = asdict(work177)
    expected["summary"] = None
    assert _workFieldsWithoutContent(contentCh2) == expected

    contentFull = expectUnlocked(ao3fetch.getWorkContent(17793689, fullWork=True))
    assert _workFieldsWithoutContent(contentFull) == asdict(work177)


def test_full_work_returns_all_chapters_matching_individual_pages() -> None:
    """getWorkContent(fullWork=True) returns every chapter matching individual chapter pages."""
    fullWork = expectUnlocked(ao3fetch.getWorkContent(17793689, fullWork=True))
    chapter1 = expectUnlocked(ao3fetch.getWorkContent(17793689, chapterId=41980418))
    chapter2 = expectUnlocked(ao3fetch.getWorkContent(17793689, chapterId=42035519))

    assert fullWork.summary is not None
    assert fullWork.content.notes.start is not None
    assertHtmlEqual(fullWork.content.notes.end, "<p>Placeholder work end notes.</p>")
    assert [(ch.id, ch.index) for ch in fullWork.content.chapters] == [
        (41980418, 1),
        (42035519, 2),
    ]

    first, second = fullWork.content.chapters
    assert first.title == "The Guild"
    assert isinstance(first.summary, str)
    assert first.notes == chapter1.content.chapters[0].notes
    assert first.html == chapter1.content.chapters[0].html

    assert isinstance(second.title, str)
    assert isinstance(second.summary, str)
    assert second.notes == ao3fetch.ContentNotes(start=chapter2.content.chapters[0].notes.start, end=None)
    assert second.html == chapter2.content.chapters[0].html


def test_full_work_returns_single_chapter_for_oneshot() -> None:
    """getWorkContent(fullWork=True) matches regular getWorkContent for a oneshot."""
    fullWork = expectUnlocked(ao3fetch.getWorkContent(323217, fullWork=True))
    regular = expectUnlocked(ao3fetch.getWorkContent(323217))

    assert fullWork.summary == regular.summary
    assert fullWork.content.notes == regular.content.notes
    assert fullWork.content.notes.start is not None
    assert fullWork.content.chapters == regular.content.chapters

    chapter = fullWork.content.chapters[0]
    assert chapter.id is None
    assert chapter.index == 1
    assert chapter.title is None
    assert chapter.summary is None
    assert chapter.notes == ao3fetch.ContentNotes(start=None, end=None)
    assert chapter.url == "https://archiveofourown.org/works/323217"


def test_locked_work_content_returns_locked_summary() -> None:
    """getWorkContent returns the same LockedWorkSummary as getWork without throwing."""
    workContent = ao3fetch.getWorkContent(15461226)
    assert workContent == ao3fetch.getWork(15461226)
    assert isinstance(workContent, ao3fetch.LockedWorkSummary)
    assert workContent.locked is True
