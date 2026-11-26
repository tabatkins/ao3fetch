"""Tests for URL builders and parsers (ported from AO3.js tests/urls.test.ts and tests/tag-works-feed.test.ts)."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlparse

import pytest

import ao3fetch


def _queryDict(url: str) -> dict[str, str]:
    return dict(parse_qsl(urlparse(url).query, keep_blank_values=True))


@pytest.mark.parametrize(
    ("tagType", "expectedParam"),
    [
        ("character", "Character"),
        ("fandom", "Fandom"),
        ("relationship", "Relationship"),
        ("freeform", "Freeform"),
        ("any", ""),
    ],
)
def test_search_url_type_parameter_casing(
    tagType: ao3fetch.TagSearchType,
    expectedParam: str,
) -> None:
    """getSearchUrlFromTagFilters title-cases non-'any' tag types and leaves 'any' blank."""
    url = ao3fetch.getSearchUrlFromTagFilters(
        ao3fetch.TagSearchFilters(
            type=tagType,
            tagName=None,
            fandoms=(),
            wranglingStatus="any",
            sortColumn="name",
            sortDirection="asc",
            page=1,
        ),
    )

    assert _queryDict(url) == {
        "page": "1",
        "commit": "Search Tags",
        "tag_search[name]": "",
        "tag_search[fandoms]": "",
        "tag_search[type]": expectedParam,
        "tag_search[wrangling_status]": "any",
        "tag_search[sort_column]": "name",
        "tag_search[sort_direction]": "asc",
    }


def test_search_url_other_parameters() -> None:
    """getSearchUrlFromTagFilters maps page, tagName, fandoms, wranglingStatus, and sortColumn."""
    pageUrl = ao3fetch.getSearchUrlFromTagFilters(
        ao3fetch.TagSearchFilters(type="character", page=3),
    )
    assert _queryDict(pageUrl) == {
        "page": "3",
        "commit": "Search Tags",
        "tag_search[name]": "",
        "tag_search[fandoms]": "",
        "tag_search[type]": "Character",
        "tag_search[wrangling_status]": "any",
        "tag_search[sort_column]": "name",
        "tag_search[sort_direction]": "asc",
    }

    nameUrl = ao3fetch.getSearchUrlFromTagFilters(
        ao3fetch.TagSearchFilters(type="character", tagName="test tag"),
    )
    assert _queryDict(nameUrl)["tag_search[name]"] == "test tag"

    fandomsUrl = ao3fetch.getSearchUrlFromTagFilters(
        ao3fetch.TagSearchFilters(type="character", fandoms=("Hazbin Hotel (Cartoon)",)),
    )
    assert _queryDict(fandomsUrl)["tag_search[fandoms]"] == "Hazbin Hotel (Cartoon)"

    canonicalUrl = ao3fetch.getSearchUrlFromTagFilters(
        ao3fetch.TagSearchFilters(type="character", wranglingStatus="canonical"),
    )
    assert _queryDict(canonicalUrl)["tag_search[wrangling_status]"] == "canonical"

    canonSynUrl = ao3fetch.getSearchUrlFromTagFilters(
        ao3fetch.TagSearchFilters(type="character", wranglingStatus="canonical_or_synonymous"),
    )
    assert _queryDict(canonSynUrl)["tag_search[wrangling_status]"] == "canonical_synonymous"

    nonCanonUrl = ao3fetch.getSearchUrlFromTagFilters(
        ao3fetch.TagSearchFilters(type="character", wranglingStatus="noncanonical_and_nonsynonymous"),
    )
    assert _queryDict(nonCanonUrl)["tag_search[wrangling_status]"] == "noncanonical_nonsynonymous"

    sortUrl = ao3fetch.getSearchUrlFromTagFilters(
        ao3fetch.TagSearchFilters(type="character", sortColumn="works_count", sortDirection="desc"),
    )
    assert _queryDict(sortUrl)["tag_search[sort_column]"] == "uses"
    assert _queryDict(sortUrl)["tag_search[sort_direction]"] == "desc"


@pytest.mark.parametrize(
    ("tagName", "expectedPath"),
    [
        ("M/M", "/tags/M*s*M/"),
        ("Tom & Jerry", "/tags/Tom%20*a*%20Jerry/"),
        ("Dr. Who", "/tags/Dr*d*%20Who/"),
        ("C#", "/tags/C*h*/"),
        ("What If?", "/tags/What%20If*q*/"),
        ("A/B & C.D", "/tags/A*s*B%20*a*%20C*d*D/"),
        ("Simple Tag", "/tags/Simple%20Tag/"),
    ],
)
def test_get_tag_url_special_character_replacements(tagName: str, expectedPath: str) -> None:
    """getTagUrl encodes AO3's special tag tokens and ends with a trailing slash."""
    assert urlparse(ao3fetch.getTagUrl(tagName)).path == expectedPath


def test_get_tag_works_feed_url() -> None:
    """getTagWorksFeedUrl appends /works to the encoded tag URL."""
    assert urlparse(ao3fetch.getTagWorksFeedUrl("M/M")).path == "/tags/M*s*M/works"
    assert urlparse(ao3fetch.getTagWorksFeedUrl("Tom & Jerry")).path == "/tags/Tom%20*a*%20Jerry/works"


def test_get_user_works_url() -> None:
    """getUserWorksUrl encodes path segments and work_search[] query parameters."""
    reserved = urlparse(ao3fetch.getUserWorksUrl("a/b?#&", pseud="c/d?#&"))
    assert reserved.path == "/users/a%2Fb%3F%23%26/pseuds/c%2Fd%3F%23%26/works"
    assert reserved.query == ""
    assert reserved.fragment == ""

    basic = urlparse(ao3fetch.getUserWorksUrl("astolat"))
    assert basic.path == "/users/astolat/works"
    assert basic.query == ""

    pseud = urlparse(ao3fetch.getUserWorksUrl("astolat", pseud="the lady of shalott"))
    assert pseud.path == "/users/astolat/pseuds/the%20lady%20of%20shalott/works"

    paged = ao3fetch.getUserWorksUrl("astolat", page=2)
    assert _queryDict(paged)["page"] == "2"

    sortedUrl = ao3fetch.getUserWorksUrl("astolat", sortColumn="kudos_count", sortDirection="asc")
    assert _queryDict(sortedUrl)["work_search[sort_column]"] == "kudos_count"
    assert _queryDict(sortedUrl)["work_search[sort_direction]"] == "asc"

    dirOnly = ao3fetch.getUserWorksUrl("astolat", sortDirection="desc")
    assert _queryDict(dirOnly)["work_search[sort_direction]"] == "desc"
    assert "work_search[sort_column]" not in _queryDict(dirOnly)

    spaced = urlparse(ao3fetch.getUserWorksUrl("a user"))
    assert spaced.path == "/users/a%20user/works"


@pytest.mark.parametrize(
    ("sortColumn", "ao3Column"),
    [
        ("authors", "authors_to_sort_on"),
        ("title", "title_to_sort_on"),
        ("updated_at", "revised_at"),
        ("created_at", "created_at"),
    ],
)
def test_get_user_works_url_sort_column_mapping(
    sortColumn: ao3fetch.UserWorksSortColumn,
    ao3Column: str,
) -> None:
    """getUserWorksUrl translates friendly sortColumn names to AO3 query values."""
    url = ao3fetch.getUserWorksUrl("astolat", sortColumn=sortColumn)
    assert _queryDict(url)["work_search[sort_column]"] == ao3Column


def test_get_author_from_url() -> None:
    """getAuthorFromUrl parses pseud URLs and rejects missing pseud or non-user URLs."""
    assert ao3fetch.getAuthorFromUrl("/users/astolat/pseuds/astolat") == ao3fetch.Author(
        username="astolat",
        pseud="astolat",
        anonymous=False,
    )
    assert ao3fetch.getAuthorFromUrl("/users/franzeska/pseuds/Franzeska%20Ewart") == ao3fetch.Author(
        username="franzeska",
        pseud="Franzeska Ewart",
        anonymous=False,
    )
    with pytest.raises(ValueError, match=r"Unexpected author URL: /users/astolat"):
        ao3fetch.getAuthorFromUrl("/users/astolat")
    with pytest.raises(ValueError, match=r"Invalid user URL: /works/12345"):
        ao3fetch.getAuthorFromUrl("/works/12345")


@pytest.mark.parametrize(
    "url",
    [
        "/users/astolat",
        "/users/astolat/",
        "/users/astolat/profile",
        "/users/astolat/works",
        "/users/astolat/works?page=2",
        "https://archiveofourown.org/users/astolat",
        "https://archiveofourown.org/users/astolat/works?work_search%5Bsort_column%5D=hits",
    ],
)
def test_get_user_details_from_url_username_only(url: str) -> None:
    """getUserDetailsFromUrl returns username with pseud=None when URL has no /pseuds/ segment."""
    assert ao3fetch.getUserDetailsFromUrl(url) == ao3fetch.ParsedUserUrl(username="astolat", pseud=None)


@pytest.mark.parametrize(
    "url",
    [
        "/users/astolat/pseuds/astolat",
        "/users/astolat/pseuds/astolat/works",
        "https://archiveofourown.org/users/astolat/pseuds/astolat/works?page=2",
    ],
)
def test_get_user_details_from_url_with_pseud(url: str) -> None:
    """getUserDetailsFromUrl extracts both username and pseud when present."""
    assert ao3fetch.getUserDetailsFromUrl(url) == ao3fetch.ParsedUserUrl(
        username="astolat",
        pseud="astolat",
    )


def test_get_user_details_from_url_roundtrip_and_invalid() -> None:
    """getUserDetailsFromUrl round-trips getUserWorksUrl and raises on non-user URLs."""
    built = ao3fetch.getUserWorksUrl("franzeska", pseud="Franzeska Ewart")
    assert ao3fetch.getUserDetailsFromUrl(built) == ao3fetch.ParsedUserUrl(
        username="franzeska",
        pseud="Franzeska Ewart",
    )
    with pytest.raises(ValueError, match=r"Invalid user URL: /works/12345"):
        ao3fetch.getUserDetailsFromUrl("/works/12345")


def test_get_series_url() -> None:
    """getSeriesUrl builds series URLs with and without an optional page parameter."""
    assert ao3fetch.getSeriesUrl(2270465) == "https://archiveofourown.org/series/2270465"
    assert ao3fetch.getSeriesUrl("2270465", page=2) == "https://archiveofourown.org/series/2270465?page=2"


def test_work_url_parse_build_and_download_links() -> None:
    """Port of AO3.js tests/tag-works-feed.test.ts URL parse, build, and download URL tests."""
    parsedWork = ao3fetch.getWorkDetailsFromUrl("https://archiveofourown.org/works/36667228")
    assert parsedWork.workId == 36667228
    assert ao3fetch.getWorkUrl(parsedWork.workId) == "https://archiveofourown.org/works/36667228"

    parsedChapter = ao3fetch.getWorkDetailsFromUrl("https://archiveofourown.org/works/398023/chapters/659774")
    assert parsedChapter.workId == 398023
    assert parsedChapter.chapterId == 659774
    assert ao3fetch.getWorkUrl(398023, chapterId=659774) == "https://archiveofourown.org/works/398023/chapters/659774"

    parsedCollection = ao3fetch.getWorkDetailsFromUrl(
        "https://archiveofourown.org/collections/YJ_Prompts/works/30216801",
    )
    assert parsedCollection.workId == 30216801
    assert parsedCollection.collectionName == "YJ_Prompts"
    assert (
        ao3fetch.getWorkUrl(30216801, collectionName="YJ_Prompts")
        == "https://archiveofourown.org/collections/YJ_Prompts/works/30216801"
    )

    downloadLinks = ao3fetch.getDownloadUrls(
        168768,
        "Fill",
        publishedAt="2011-02-08",
        updatedAt=None,
    )
    assert downloadLinks == {
        "azw3": "https://archiveofourown.org/downloads/168768/Fill.azw3?updated_at=1297123200000",
        "epub": "https://archiveofourown.org/downloads/168768/Fill.epub?updated_at=1297123200000",
        "html": "https://archiveofourown.org/downloads/168768/Fill.html?updated_at=1297123200000",
        "mobi": "https://archiveofourown.org/downloads/168768/Fill.mobi?updated_at=1297123200000",
        "pdf": "https://archiveofourown.org/downloads/168768/Fill.pdf?updated_at=1297123200000",
    }
