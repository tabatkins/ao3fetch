"""Tests for searchTags (ported from AO3.js tests/tag-search.test.ts)."""

from __future__ import annotations

from mock_archive import assertDriftingCount

import ao3fetch


def test_fetch_canonical_characters_first_page() -> None:
    """searchTags fetches page 1 of canonical characters in a fandom."""
    result = ao3fetch.searchTags(
        tagType="character",
        wranglingStatus="canonical",
        fandoms=("Hazbin Hotel (Cartoon)",),
    )

    assert result.filters == ao3fetch.TagSearchFilters(
        sortColumn="name",
        sortDirection="asc",
        tagName=None,
        type="character",
        wranglingStatus="canonical",
        page=1,
        fandoms=("Hazbin Hotel (Cartoon)",),
    )
    assert result.pages == ao3fetch.PageInfo(total=3, current=1)
    assert [tag.name for tag in result.tags] == [
        "Abel (Hazbin Hotel)",
        "Adam (Hazbin Hotel)",
        "Alastor (Hazbin Hotel)",
        "Alastor's Father (Hazbin Hotel)",
        "Alastor's Grandmother (Hazbin Hotel)",
        "Alastor's Microphone (Hazbin Hotel)",
        "Alastor's Minions (Hazbin Hotel)",
        "Alastor's Mother (Hazbin Hotel)",
        "Alastor's Parents (Hazbin Hotel)",
        "Alastor's Shadow (Hazbin Hotel)",
        "Alastor's Sibling (Hazbin Hotel)",
        "Angel Dust (Hazbin Hotel)",
        "Angel Dust's Family (Hazbin Hotel)",
        "Angel Dust's Father (Hazbin Hotel)",
        "Angel Dust's Mother (Hazbin Hotel)",
        "Angel Dust's Shadow (Hazbin Hotel)",
        "Angels (Hazbin Hotel)",
        "Animal Show Host from Brighter (Hazbin Hotel)",
        "Arackniss (Hazbin Hotel)",
        "Baxter (Hazbin Hotel)",
        "Belphegor (Helluva Boss)",
        "Bethesda Von Eldritch",
        "Blonde News Anchor from Brighter (Hazbin Hotel)",
        "Bryrin (Hazbin Hotel)",
        "Cannibal Child Vaggi | Vaggie Spares in Flashback (Hazbin Hotel)",
        "Cannibal Town Ensemble (Hazbin Hotel)",
        "Captive Alastor's Swivel Chair (Hazbin Hotel)",
        "Carmilla Carmine (Hazbin Hotel)",
        "Carmilla Carmine's Daughters (Hazbin Hotel)",
        "Charlie Magne | Morningstar",
        "Cherri Bomb (Hazbin Hotel)",
        "Clara (Hazbin Hotel)",
        "Cooking Show Host from Brighter (Hazbin Hotel)",
        "Crymini (Hazbin Hotel)",
        "Dazzle (Hazbin Hotel)",
        "Demons (Hazbin Hotel & Helluva Boss)",
        "Dia (Hazbin Hotel)",
        "Egg Boi #11 (Hazbin Hotel)",
        "Egg Boi #23 (Hazbin Hotel)",
        "Elders of Heaven (Hazbin Hotel)",
        "Emily (Hazbin Hotel)",
        "Ethan | Vox's Assistant (Hazbin Hotel)",
        "Eve (Hazbin Hotel)",
        "Ewe Demon (Hazbin Hotel)",
        "Exorcist Angels (Hazbin Hotel)",
        "Fat Nuggets (Hazbin Hotel)",
        "Frank (Hazbin Hotel)",
        "Franklin (Hazbin Hotel)",
        "Frederick Von Eldritch",
        "Gambling Rabbit Demon (Hazbin Hotel)",
    ]


def test_fetch_canonical_characters_middle_page() -> None:
    """searchTags fetches page 2 of canonical characters in a fandom."""
    result = ao3fetch.searchTags(
        tagType="character",
        wranglingStatus="canonical",
        fandoms=("Hazbin Hotel (Cartoon)",),
        page=2,
    )

    assert result.filters == ao3fetch.TagSearchFilters(
        sortColumn="name",
        sortDirection="asc",
        tagName=None,
        type="character",
        wranglingStatus="canonical",
        page=2,
        fandoms=("Hazbin Hotel (Cartoon)",),
    )
    assert result.pages == ao3fetch.PageInfo(total=3, current=2)
    assert [tag.name for tag in result.tags] == [
        "Game Show Host from Brighter (Hazbin Hotel)",
        "God (Hazbin Hotel)",
        "Happy Hotel | Hazbin Hotel Residents",
        "Hatchet (Hazbin Hotel)",
        "Hazbin Hotel Ensemble",
        "Heaven Ensemble (Hazbin Hotel)",
        "Helsa Von Eldritch",
        "Henroin (Hazbin Hotel)",
        "Husk (Hazbin Hotel)",
        "Husk's Father (Hazbin Hotel)",
        "Husk's Mother (Hazbin Hotel)",
        "Huskettes (Hazbin Hotel)",
        "Izzi (Hazbin Hotel)",
        "Katie Killjoy",
        "KeeKee (Hazbin Hotel)",
        "Kitty (Hazbin Hotel)",
        "Leviathan (Helluva Boss)",
        "Lilith (Hazbin Hotel)",
        "Loan Shark Demons (Hazbin Hotel)",
        "Lucifer Magne | Morningstar",
        "Lucifer Magne | Morningstar's Siblings",
        "Lute (Hazbin Hotel)",
        "Maestro (Hazbin Hotel)",
        "Melissa (Hazbin Hotel)",
        "Mimzy (Hazbin Hotel)",
        "Molly (Hazbin Hotel)",
        "Mustached News Anchor from Brighter (Hazbin Hotel)",
        "Myk (Hazbin Hotel)",
        "Niffty (Hazbin Hotel)",
        "Odette (Hazbin Hotel)",
        "Original Children of Adam and Lute (Hazbin Hotel)",
        "Original Children of Alastor and Angel Dust (Hazbin Hotel)",
        "Original Children of Alastor and Charlie Magne | Morningstar",
        "Original Children of Alastor and Lucifer Magne | Morningstar",
        "Original Children of Alastor and Rosie (Hazbin Hotel)",
        "Original Children of Alastor and Vox (Hazbin Hotel)",
        "Original Children of Angel Dust and Husk (Hazbin Hotel)",
        "Original Children of Charlie Magne | Morningstar and Vaggi | Vaggie",
        "Original Children of Valentino and Vox (Hazbin Hotel)",
        "Original Family Member(s) of Alastor (Hazbin Hotel)",
        "Original Hazbin Hotel Character(s)",
        "Original Magne | Morningstar Character(s)",
        "Overlords (Hazbin Hotel)",
        "Prick (Hazbin Hotel)",
        "Purple Porn Studio Demon (Hazbin Hotel)",
        "Queef | Valentino's Pet (Hazbin Hotel)",
        "Razzle (Hazbin Hotel)",
        "Redhead TV Host (Hazbin Hotel)",
        'Robert "Bob" Sinclaire (Hazbin Hotel)',
        "Rocky (Hazbin Hotel)",
    ]


def test_fetch_canonical_characters_last_page() -> None:
    """searchTags fetches page 3 (last page) of canonical characters in a fandom."""
    result = ao3fetch.searchTags(
        tagType="character",
        wranglingStatus="canonical",
        fandoms=("Hazbin Hotel (Cartoon)",),
        page=3,
    )

    assert result.filters == ao3fetch.TagSearchFilters(
        sortColumn="name",
        sortDirection="asc",
        tagName=None,
        type="character",
        wranglingStatus="canonical",
        page=3,
        fandoms=("Hazbin Hotel (Cartoon)",),
    )
    assert result.pages == ao3fetch.PageInfo(total=3, current=3)
    assert [tag.name for tag in result.tags] == [
        "Roo (Hazbin Hotel)",
        "Rooster (Hazbin Hotel)",
        "Rosie (Hazbin Hotel)",
        "Rosie's First Husband (Hazbin Hotel)",
        "Salina (Hazbin Hotel)",
        "Satan (Helluva Boss)",
        "Sera (Hazbin Hotel)",
        "Seviathan Von Eldritch",
        "Shok.wav | Vox's Shark (Hazbin Hotel)",
        "Sir Pentious (Hazbin Hotel)",
        "Sir Pentious's Hat (Hazbin Hotel)",
        "St. Peter (Hazbin Hotel)",
        "Summer (Hazbin Hotel)",
        "Susan (Hazbin Hotel)",
        "The Archangels (Hazbin Hotel)",
        "The Egg Boiz (Hazbin Hotel)",
        "The Seven Deadly Sins (Hazbin Hotel & Helluva Boss)",
        "The Speaker of God (Hazbin Hotel)",
        "The Vees (Hazbin Hotel)",
        "Tiffany Titfucker (Hazbin Hotel)",
        "Tom Trench",
        "Travis (Hazbin Hotel)",
        "Travis's Wife (Hazbin Hotel)",
        "Tree Fangirl Demon (Hazbin Hotel)",
        "Vaggi | Vaggie (Hazbin Hotel)",
        "Vaggi | Vaggie's Father (Hazbin Hotel)",
        "Vaggi | Vaggie's Mother (Hazbin Hotel)",
        "Valentino (Hazbin Hotel)",
        "Valentino's Mother (Hazbin Hotel)",
        "Vark | Vox's Shark (Hazbin Hotel)",
        "Vax (Hazbin Hotel)",
        "Velvette (Hazbin Hotel)",
        "Victor (Daisies - Black Gryph0n & Baasik)",
        "Von Eldritch Family (Hazbin Hotel)",
        "Vox (Hazbin Hotel)",
        "Vox's Father (Hazbin Hotel)",
        "Vox's Mother (Hazbin Hotel)",
        "Vox's Producers (Hazbin Hotel)",
        "White-Haired Exorcist from Vaggi | Vaggie's Flashback (Hazbin Hotel)",
        "Zeezi (Hazbin Hotel)",
        "Zestial (Hazbin Hotel)",
    ]


def test_return_empty_results_when_no_matches() -> None:
    """searchTags returns zero results and empty tags tuple when search has no matches."""
    result = ao3fetch.searchTags(
        tagName="asdfasdfasdfasdfasdfasdf",
        sortColumn="name",
        sortDirection="asc",
        tagType="fandom",
        wranglingStatus="canonical",
    )

    assert result.filters == ao3fetch.TagSearchFilters(
        sortColumn="name",
        sortDirection="asc",
        tagName="asdfasdfasdfasdfasdfasdf",
        type="fandom",
        wranglingStatus="canonical",
        page=1,
        fandoms=(),
    )
    assert result.totalResults == 0
    assert result.pages == ao3fetch.PageInfo(total=0, current=1)
    assert not result.tags


def test_return_different_results_for_different_tag_types() -> None:
    """searchTags distinguishes unsorted, freeform, character, and canonical tag rows."""
    result = ao3fetch.searchTags(tagName="an unusual", page=3)

    assert result.filters == ao3fetch.TagSearchFilters(
        tagName="an unusual",
        fandoms=(),
        type="any",
        wranglingStatus="any",
        sortColumn="name",
        sortDirection="asc",
        page=3,
    )
    assertDriftingCount(result.totalResults, atLeast=223, atMost=250)

    unsortedTag = "Everyone Gets An Unusual Career Except Harry"
    freeformTag = 'even an unusual variation on "Just The Tip"'
    characterTag = "Goddess Who Decides to Answer an Unusual Prayer (Original Work)"
    canonicalTag = "Episode: s02e23 Facing an Unusual Past (Saiki Kusuo no Sai-nan)"

    byName = {tag.name: tag for tag in result.tags}
    assert byName.get(unsortedTag) == ao3fetch.TagSearchResult(
        name=unsortedTag,
        type="unsorted",
        canonical=False,
        worksCount=1,
    )
    assert byName.get(freeformTag) == ao3fetch.TagSearchResult(
        name=freeformTag,
        type="freeform",
        canonical=False,
        worksCount=1,
    )
    assert byName.get(characterTag) == ao3fetch.TagSearchResult(
        name=characterTag,
        type="character",
        canonical=False,
        worksCount=0,
    )
    assert byName.get(canonicalTag) == ao3fetch.TagSearchResult(
        name=canonicalTag,
        type="freeform",
        canonical=True,
        worksCount=0,
    )
