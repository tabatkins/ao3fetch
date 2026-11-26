"""Tests for chapter-specific work scraping (ported from AO3.js tests/work-chapter.test.ts)."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlparse

from mock_archive import (
    MockArchiveServer,
    assertDriftingCount,
    assertHtmlEqual,
    assertMatchesHtmlSnapshot,
    expectUnlocked,
    expectUnlockedSummary,
)

import ao3fetch


def test_single_chapter_work_summary() -> None:
    """getWork fetches complete metadata for single-chapter anonymous work 168768."""
    work = expectUnlockedSummary(ao3fetch.getWork(168768))

    assert work.id == 168768
    assert work.authors == (ao3fetch.Author(username="Anonymous", pseud="Anonymous", anonymous=True),)
    assert work.title == "Fill"
    assert work.words == 447
    assert work.language == "English"
    assert work.rating == ao3fetch.WorkRatings.TEEN_AND_UP_AUDIENCES
    assert work.category == (ao3fetch.WorkCategory.GEN,)
    assert work.adult is False
    assert work.fandoms == ("Homestuck",)
    assert work.tags == ao3fetch.WorkTags(
        warnings=(ao3fetch.WorkWarnings.CHOOSE_NOT_TO_WARN,),
        characters=("Equius Zahhak",),
        relationships=(
            "Nepeta Lejion\u2666Equius Zahhak",
            "Equius Zahhak\u2665Aradia Megido",
        ),
        additional=("Prompt Fill",),
    )
    assert work.publishedAt == "2011-02-08"
    assert work.updatedAt is None
    assert work.chapters == ao3fetch.WorkChaptersCount(published=1, total=1)
    assert work.complete is True
    assert not work.series
    assert work.locked is False

    assert work.stats.bookmarks == 2
    assert work.stats.comments == 1
    assertDriftingCount(work.stats.hits, atLeast=841, atMost=1551)
    assert work.stats.kudos == 49


def test_different_work_summary_and_chapter_summary() -> None:
    """getWorkContent keeps work.summary distinct from chapter.summary on chapter 1."""
    work = expectUnlocked(ao3fetch.getWorkContent(17793689, chapterId=41980418))

    assertMatchesHtmlSnapshot(work.summary, "ao3/works/17793689/chapter-1-summary.html")
    assertHtmlEqual(
        work.content.chapters[0].summary,
        "<p>Fenina Lavellan&apos;s MMO guild discovers they all live closer than they thought and decides to meet up.</p>",
    )


def test_confirm_reader_is_over_18_when_loading_chapter(mockServer: MockArchiveServer) -> None:
    """getWorkContent passes view_adult=true query parameter when fetching a chapter."""
    ao3fetch.getWorkContent(48582418, chapterId=122861680)

    chapterReq = next(
        (
            urlparse(reqUrl)
            for reqUrl in mockServer.requestedUrls
            if urlparse(reqUrl).path == "/works/48582418/chapters/122861680"
        ),
        None,
    )
    assert chapterReq is not None
    assert dict(parse_qsl(chapterReq.query)).get("view_adult") == "true"


def test_fetch_work_and_chapter_object_with_all_fields() -> None:
    """getWorkContent returns full work metadata and chapter fields for chapter 2 of 48582418."""
    work = expectUnlocked(ao3fetch.getWorkContent(48582418, chapterId=122861680))

    assert work.id == 48582418
    assert work.authors == (ao3fetch.Author(username="rejected_bisexual", pseud="rejected_bisexual", anonymous=False),)
    assert work.title == "5 times Gotham (and everyone else except Bruce and Alfred) were Confused."
    assert work.words == 4444
    assert work.language == "English"
    assert work.rating == ao3fetch.WorkRatings.NOT_RATED
    assert work.category is None
    assert work.adult is True
    assert work.fandoms == ("Batman - All Media Types",)
    assert work.tags == ao3fetch.WorkTags(
        warnings=(ao3fetch.WorkWarnings.CHOOSE_NOT_TO_WARN,),
        characters=(
            "Bruce Wayne",
            "Damian Wayne",
            "Tim Drake",
            "Cassandra Cain",
            "Jason Todd",
            "Dick Grayson",
            "Alfred Pennyworth",
        ),
        relationships=(
            "Bruce Wayne & Damian Wayne",
            "Tim Drake & Bruce Wayne",
            "Cassandra Cain & Bruce Wayne",
            "Jason Todd & Bruce Wayne",
            "Dick Grayson & Bruce Wayne",
            "Alfred Pennyworth & Bruce Wayne",
        ),
        additional=(
            "Fluff",
            "Misunderstandings",
            "Family Fluff",
            "Family Bonding",
            "Brotherly Bonding",
            "Inspired by Twitter",
            "Twitter",
            "Favorite child",
            "first fic be kind",
            "I'm Bad at Tagging",
            "no beta we die like jason todd",
            "Bruce Wayne is a Good Parent",
            "Crack Treated Seriously",
            "Crack that Tracks",
        ),
    )
    assert work.publishedAt == "2023-07-14"
    assert work.updatedAt == "2023-10-30"
    assert work.chapters == ao3fetch.WorkChaptersCount(published=6, total=6)
    assert work.complete is True
    assert not work.series
    assert work.locked is False
    assertDriftingCount(work.stats.bookmarks, atLeast=85, atMost=115)
    assertDriftingCount(work.stats.comments, atLeast=60, atMost=77)
    assertDriftingCount(work.stats.hits, atLeast=6000, atMost=6815)
    assertDriftingCount(work.stats.kudos, atLeast=585, atMost=665)

    chapter = work.content.chapters[0]
    assert chapter.id == 122861680
    assert chapter.url == "https://archiveofourown.org/works/48582418/chapters/122861680"
    assert chapter.shortUrl == "https://ao3.org/works/48582418/chapters/122861680"
    assert chapter.index == 2
    assert chapter.title == "2. Tim"
    assert chapter.summary == "<p>Bruce is in a Silly Goofy Mood.<br>Gotham is frustrated.<br>Tim needs love.</p>"


def test_fetch_chapter_object_without_title_or_summary() -> None:
    """getWorkContent returns title=None and summary=None for untitled chapters without summary."""
    work = expectUnlocked(ao3fetch.getWorkContent(37214506, chapterId=92848687))

    assert work.id == 37214506
    assert work.authors == (ao3fetch.Author(username="Anonymous", pseud="Anonymous", anonymous=True),)
    assert work.title == "AvengersGC"
    assert work.words == 11466
    assert work.language == "English"
    assert work.rating == ao3fetch.WorkRatings.TEEN_AND_UP_AUDIENCES
    assert work.category == (ao3fetch.WorkCategory.GEN,)
    assert work.adult is False
    assert work.fandoms == ("Marvel Cinematic Universe",)
    assert work.tags == ao3fetch.WorkTags(
        warnings=(ao3fetch.WorkWarnings.NO_WARNINGS_APPLY,),
        characters=(
            "Tony Stark",
            "Steve Rogers",
            "Natasha Romanov (Marvel)",
            "Clint Barton",
            "Bruce Banner",
            "Thor (Marvel)",
            'James "Rhodey" Rhodes',
            "Vision (Marvel)",
            "Wanda Maximoff",
            "T'Challa (Marvel)",
            "Scott Lang",
            "Sam Wilson (Marvel)",
            'James "Bucky" Barnes',
            "Peter Parker",
            "Shuri (Marvel)",
            "Kate Bishop",
            "Loki (Marvel)",
            "Sylvie (Loki TV)",
        ),
        relationships=("Avengers Team & Avengers Team",),
        additional=(
            "Alternate Universe - Everyone Lives/Nobody Dies",
            "Fluff",
            "Chaos",
            "Chatting & Messaging",
            "Timeline What Timeline",
            "Texting",
            "I removed Pietro I'm sorry",
        ),
    )
    assert work.publishedAt == "2022-02-18"
    assert work.updatedAt == "2022-06-26"
    assert work.chapters == ao3fetch.WorkChaptersCount(published=20, total=None)
    assert work.complete is False
    assert work.series == (
        ao3fetch.BasicSeries(
            id=2946579,
            url="https://archiveofourown.org/series/2946579",
            shortUrl="https://ao3.org/series/2946579",
            name="Twitterchat Saga",
            index=1,
        ),
    )
    assertDriftingCount(work.stats.comments, atLeast=27, atMost=44)
    assertDriftingCount(work.stats.bookmarks, atLeast=14, atMost=40)
    assertDriftingCount(work.stats.kudos, atLeast=131, atMost=184)
    assertDriftingCount(work.stats.hits, atLeast=3110, atMost=3675)
    assert work.locked is False

    chapter = work.content.chapters[0]
    assert chapter.id == 92848687
    assert chapter.url == "https://archiveofourown.org/works/37214506/chapters/92848687"
    assert chapter.shortUrl == "https://ao3.org/works/37214506/chapters/92848687"
    assert chapter.index == 1
    assert chapter.title is None
    assert chapter.summary is None
