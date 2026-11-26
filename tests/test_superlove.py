"""Tests for alternative OTW archive Superlove (ported from AO3.js tests/superlove.test.ts)."""

from __future__ import annotations

from mock_archive import assertMatchesHtmlSnapshot, expectUnlocked, expectUnlockedSummary

import ao3fetch


def test_superlove_work_information_in_its_entirety() -> None:
    """getWork fetches complete metadata from superlove.sayitditto.net."""
    ao3fetch.setArchiveBaseUrl("https://superlove.sayitditto.net/")
    work = expectUnlockedSummary(ao3fetch.getWork("1269"))

    assert work.adult is False
    assert work.authors == (ao3fetch.Author(username="melo", pseud="melo", anonymous=False),)
    assert work.category == (ao3fetch.WorkCategory.FF,)
    assert work.chapters == ao3fetch.WorkChaptersCount(published=1, total=1)
    assert work.complete is True
    assert work.fandoms == ("Batgirl", "Teen Titans")
    assert work.host == "superlove.sayitditto.net"
    assert work.id == 1269
    assert work.language == "English"
    assert work.locked is False
    assert work.publishedAt == "2025-08-23"
    assert work.rating == ao3fetch.WorkRatings.TEEN_AND_UP_AUDIENCES
    assert not work.series
    assert work.shortUrl is None
    assert work.source == "website"
    assert work.summary == "<p>Life after the wolves.</p>"
    assert work.tags == ao3fetch.WorkTags(
        additional=(
            "Moving On",
            "Past Trauma",
            "Grief/Mourning",
            "Cassandra Cain's Evil Arc (DCU)",
            "Power Rangers Megaforce: S20E13 - Dream Snatcher",
        ),
        characters=("Cassandra Cain", "Rose Wilson"),
        relationships=("Cassandra Cain/Rose Wilson",),
        warnings=(ao3fetch.WorkWarnings.CHOOSE_NOT_TO_WARN,),
    )
    assert work.title == "and she burned the sky"
    assert work.updatedAt is None
    assert work.url == "https://superlove.sayitditto.net/works/1269"
    assert work.words == 500


def test_superlove_work_content_snapshots() -> None:
    """getWorkContent on Superlove matches AO3.js summary and chapter HTML snapshots."""
    ao3fetch.setArchiveBaseUrl("https://superlove.sayitditto.net/")
    workContent = expectUnlocked(ao3fetch.getWorkContent("1269"))

    assert workContent.summary is not None
    assertMatchesHtmlSnapshot(workContent.summary, "superlove/works/1269/chapter-1-summary.html")
    assertMatchesHtmlSnapshot(
        workContent.content.chapters[0].html,
        "superlove/works/1269/chapter-1-content.html",
    )
    assert workContent.content.chapters[0].notes.start is None
    assert workContent.content.chapters[0].notes.end is None
