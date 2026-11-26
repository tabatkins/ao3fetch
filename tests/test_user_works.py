"""Tests for getUserWorks (ported from AO3.js tests/user-works.test.ts)."""

from __future__ import annotations

import pytest
from mock_archive import MockArchiveServer, assertDriftingCount

import ao3fetch


def test_fetch_first_page_of_users_works() -> None:
    """getUserWorks fetches the first page of astolat's works with pagination counts."""
    result = ao3fetch.getUserWorks("astolat")

    assert len(result.works) == 20
    assert result.pages.current == 1
    assertDriftingCount(result.pages.total, atLeast=27, atMost=40)
    assertDriftingCount(result.totalResults, atLeast=535, atMost=800)
    assert [work.title for work in result.works] == [
        "Research",
        "Inheritance",
        "Looking At Stone",
        "Hallelujah",
        "Tourney Field",
        "Oubliette",
        "Entrapment",
        "Press Gang",
        "Common Knowledge",
        "The Pack Survives",
        "The Price of Bread and Salt",
        "A Man of Honor",
        "Let The River Run",
        "Winter's Crown",
        "Royal Flush",
        "Lifeline",
        "Heal Thyself",
        "Raised By Wolves",
        "Paying Debts",
        "The Next Time",
    ]


def test_fetch_details_of_work_in_list() -> None:
    """getUserWorks parses complete blurb metadata for a work in the listing."""
    result = ao3fetch.getUserWorks("astolat")
    work = next((w for w in result.works if w.id == 43703871), None)
    assert work is not None

    assertDriftingCount(work.stats.bookmarks, atLeast=1255, atMost=1381)
    assertDriftingCount(work.stats.hits, atLeast=111695, atMost=122991)
    assertDriftingCount(work.stats.kudos, atLeast=5685, atMost=6256)

    assert work.adult is False
    assert work.authors == (ao3fetch.Author(username="astolat", pseud="astolat", anonymous=False),)
    assert work.chapters == ao3fetch.WorkChaptersCount(published=9, total=9)
    assert work.complete is True
    assert work.fandoms == ("Game of Thrones (TV)",)
    assert work.host == "archiveofourown.org"
    assert work.id == 43703871
    assert work.language == "English"
    assert work.shortUrl == "https://ao3.org/works/43703871"
    assert work.source == "website"
    assert work.summary == (
        "<p>The deep satisfaction of having made the right choice; of having found a "
        + "clear-flowing wellspring of true honor to protect.</p>"
    )
    assert work.tags == ao3fetch.WorkBlurbTags(
        additional=(
            "Red Wedding",
            "Riverlands",
            "Grief",
            "Recovery",
            "Suicidal Thoughts",
        ),
        characters=(
            "Brienne of Tarth",
            "Robb Stark",
            "Jaime Lannister",
            "Tyrion Lannister",
            "Sansa Stark",
            "Arya Stark",
            "Catelyn Tully Stark",
            "Daenerys Targaryen",
        ),
        relationships=(
            "Jaime Lannister/Robb Stark/Brienne of Tarth",
            "Jaime Lannister/Brienne of Tarth",
            "Jaime Lannister/Robb Stark",
            "Tyrion Lannister & Sansa Stark",
            "pre-Tyrion Lannister/Sansa Stark",
            "Robb Stark & Brienne of Tarth",
            "Jaime Lannister & Tyrion Lannister",
            "Arya Stark & Robb Stark",
            "Robb Stark/Daenerys Targaryen",
        ),
    )
    assert work.title == "Let The River Run"
    assert work.updatedAt == "2022-12-25"
    assert work.url == "https://archiveofourown.org/works/43703871"
    assert work.words == 61498


def test_return_requested_filters_and_title_desc_sort() -> None:
    """getUserWorks reflects explicit sortColumn/sortDirection filters and listing order."""
    result = ao3fetch.getUserWorks("chemicalcain", sortColumn="title", sortDirection="desc")

    assert result.filters == ao3fetch.UserWorksFilters(sortColumn="title", sortDirection="desc", page=1)
    assert [work.title for work in result.works] == [
        "Who Can I Turn To?",
        "What do you want?",
        "Visceral",
        "Trust",
        "Toy Soldier",
        "Thirty Clove",
        "Something to focus on...",
        "Self-Reflection",
        "Reckless Recreational Spell Use",
        "One for One",
        "olin lipu",
        "Nothing is Whole and Nothing is Broken",
        "Nightmare Horse",
        "Mountains",
        "The Mega-Blast Dick Breaker",
        "Love Me or Leave Me",
        "Keeping Warm",
        "Jaunt",
        "Inflict Wounds",
        "Impossible Claims",
    ]


def test_fetch_empty_list_for_user_with_no_works() -> None:
    """getUserWorks returns empty works, zero totalResults, and pages.total=0 when user has no works."""
    result = ao3fetch.getUserWorks("franzeska")

    assert result == ao3fetch.UserWorks(
        filters=ao3fetch.UserWorksFilters(sortColumn="updated_at", sortDirection="desc", page=1),
        works=(),
        pages=ao3fetch.PageInfo(total=0, current=1),
        totalResults=0,
    )


def test_throw_archive_page_request_error_for_missing_user(mockServer: MockArchiveServer) -> None:
    """getUserWorks raises ArchivePageRequestError with exact URL when user returns 404."""
    mockServer.overrideStatus(
        lambda url: url.startswith("https://archiveofourown.org/users/missinguser/works"),
        404,
    )
    expectedMsg = (
        "Archive request failed with status 404: "
        + "https://archiveofourown.org/users/missinguser/works?page=1&work_search%5Bsort_column%5D=revised_at"
    )
    with pytest.raises(ao3fetch.ArchivePageRequestError) as excInfo:
        ao3fetch.getUserWorks("missinguser")
    assert str(excInfo.value) == expectedMsg


def test_fetch_users_works_sorted_by_most_recently_updated() -> None:
    """getUserWorks defaults to updated_at desc."""
    result = ao3fetch.getUserWorks("chemicalcain")

    assert result.filters == ao3fetch.UserWorksFilters(sortColumn="updated_at", sortDirection="desc", page=1)
    assert len(result.works) == 20
    assert [work.title for work in result.works[:5]] == [
        "Mountains",
        "Nightmare Horse",
        "Toy Soldier",
        "One for One",
        "Blasphemy",
    ]


def test_fetch_users_works_sorted_by_hits() -> None:
    """getUserWorks supports sortColumn='hits'."""
    result = ao3fetch.getUserWorks("chemicalcain", sortColumn="hits")

    assert result.filters == ao3fetch.UserWorksFilters(sortColumn="hits", sortDirection="desc", page=1)
    assert len(result.works) == 20
    assert [work.title for work in result.works[:5]] == [
        "As Sweet As A Song, As Right As A Wrong",
        "Cravats For Kravitz",
        "Self-Reflection",
        "Thirty Clove",
        "Hey Jealousy",
    ]


def test_fetch_only_works_posted_under_pseud() -> None:
    """getUserWorks scopes listing to a single pseud."""
    result = ao3fetch.getUserWorks("astolat", pseud="shalott")

    assert len(result.works) > 0
    expectedAuthor = ao3fetch.Author(username="astolat", pseud="shalott", anonymous=False)
    for work in result.works:
        assert expectedAuthor in work.authors
    assert result.totalResults == 1


def test_fetch_works_of_pseud_with_spaces() -> None:
    """getUserWorks handles pseud names containing spaces."""
    result = ao3fetch.getUserWorks("astolat", pseud="the lady of shalott")

    assert len(result.works) == 18
    assert result.pages == ao3fetch.PageInfo(total=1, current=1)
    assert result.totalResults == 18
    expectedAuthor = ao3fetch.Author(username="astolat", pseud="the lady of shalott", anonymous=False)
    for work in result.works:
        assert work.authors == (expectedAuthor,)


def test_fetch_first_page_of_pseuds_works_across_many_pages() -> None:
    """getUserWorks paginates a pseud with many works."""
    result = ao3fetch.getUserWorks("astolat", pseud="astolat")

    assert len(result.works) == 20
    assert result.pages.current == 1
    assertDriftingCount(result.pages.total, atLeast=26, atMost=40)
    assertDriftingCount(result.totalResults, atLeast=516, atMost=800)
    expectedAuthor = ao3fetch.Author(username="astolat", pseud="astolat", anonymous=False)
    for work in result.works:
        assert expectedAuthor in work.authors


def test_fetch_pseuds_works_sorted_by_hits() -> None:
    """getUserWorks combines pseud filtering and sortColumn."""
    result = ao3fetch.getUserWorks("chemicalcain", pseud="chemicalcain", sortColumn="hits")

    assert result.filters == ao3fetch.UserWorksFilters(sortColumn="hits", sortDirection="desc", page=1)
    assert len(result.works) == 20
    assert result.pages == ao3fetch.PageInfo(total=2, current=1)
    assert result.totalResults == 34
    assert [work.title for work in result.works[:5]] == [
        "As Sweet As A Song, As Right As A Wrong",
        "Cravats For Kravitz",
        "Self-Reflection",
        "Thirty Clove",
        "Hey Jealousy",
    ]


def test_list_same_works_for_users_only_pseud() -> None:
    """getUserWorks returns identical works for a user and their sole pseud."""
    userWorks = ao3fetch.getUserWorks("chemicalcain")
    pseudWorks = ao3fetch.getUserWorks("chemicalcain", pseud="chemicalcain")

    assert pseudWorks.works == userWorks.works
    assert pseudWorks.totalResults == userWorks.totalResults


def test_fetch_users_works_sorted_by_title() -> None:
    """getUserWorks defaults sortDirection to 'asc' when sorting by title."""
    result = ao3fetch.getUserWorks("chemicalcain", sortColumn="title")

    assert result.filters == ao3fetch.UserWorksFilters(sortColumn="title", sortDirection="asc", page=1)
    assert len(result.works) == 20
    assert [work.title for work in result.works[:5]] == [
        "Armadillidiidae",
        "As Sweet As A Song, As Right As A Wrong",
        "Beauty",
        "Blasphemy",
        "Bold",
    ]


def test_fetch_users_works_sorted_by_date_posted() -> None:
    """getUserWorks supports sortColumn='created_at'."""
    result = ao3fetch.getUserWorks("chemicalcain", sortColumn="created_at")

    assert result.filters.sortColumn == "created_at"
    assert len(result.works) == 20
    assert [work.title for work in result.works[:5]] == [
        "Mountains",
        "Nightmare Horse",
        "Toy Soldier",
        "One for One",
        "Blasphemy",
    ]


def test_fetch_users_works_sorted_by_word_count() -> None:
    """getUserWorks supports sortColumn='word_count'."""
    result = ao3fetch.getUserWorks("chemicalcain", sortColumn="word_count")

    assert result.filters.sortColumn == "word_count"
    assert len(result.works) == 20
    assert [work.title for work in result.works[:5]] == [
        "What do you want?",
        "Something to focus on...",
        "Inflict Wounds",
        "Nothing is Whole and Nothing is Broken",
        "Who Can I Turn To?",
    ]
