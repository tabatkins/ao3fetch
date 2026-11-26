"""Tests for getWork (ported from AO3.js tests/works.test.ts)."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlparse

import pytest
from mock_archive import (
    MockArchiveServer,
    assertDriftingCount,
    assertHtmlEqual,
    expectUnlockedSummary,
)

import ao3fetch


def test_works_parse_and_url_helpers() -> None:
    """getWorkDetailsFromUrl and getWorkUrl handle works, chapters, and collections."""
    workData = ao3fetch.getWorkDetailsFromUrl("https://archiveofourown.org/works/36667228")
    assert workData.workId == 36667228
    assert ao3fetch.getWorkUrl(workData.workId) == "https://archiveofourown.org/works/36667228"

    chapterData = ao3fetch.getWorkDetailsFromUrl("https://archiveofourown.org/works/398023/chapters/659774")
    assert chapterData.workId == 398023
    assert chapterData.chapterId == 659774
    assert ao3fetch.getWorkUrl(398023, chapterId=659774) == "https://archiveofourown.org/works/398023/chapters/659774"

    collectionData = ao3fetch.getWorkDetailsFromUrl(
        "https://archiveofourown.org/collections/YJ_Prompts/works/30216801",
    )
    assert collectionData.workId == 30216801
    assert collectionData.collectionName == "YJ_Prompts"
    assert (
        ao3fetch.getWorkUrl(30216801, collectionName="YJ_Prompts")
        == "https://archiveofourown.org/collections/YJ_Prompts/works/30216801"
    )


def test_throw_invalid_id_error_for_invalid_work_id() -> None:
    """getWork raises InvalidIDError with matching message for invalid work IDs."""
    with pytest.raises(ao3fetch.InvalidIDError, match=r"invalid-id is not a valid work id"):
        ao3fetch.getWork("invalid-id")


def test_throw_archive_page_request_error_on_archive_error(mockServer: MockArchiveServer) -> None:
    """getWork raises ArchivePageRequestError with exact URL when the archive returns 404."""
    mockServer.overrideStatus(lambda url: url.startswith("https://archiveofourown.org/"), 404)
    with pytest.raises(ao3fetch.ArchivePageRequestError) as excInfo:
        ao3fetch.getWork(1)
    assert (
        str(excInfo.value)
        == "Archive request failed with status 404: https://archiveofourown.org/works/1?view_adult=true"
    )


def test_confirm_reader_is_over_18_when_loading_work(mockServer: MockArchiveServer) -> None:
    """getWork sends view_adult=true query parameter when fetching a work page."""
    ao3fetch.getWork(29046888)

    workReq = next(
        (urlparse(reqUrl) for reqUrl in mockServer.requestedUrls if urlparse(reqUrl).path == "/works/29046888"),
        None,
    )
    assert workReq is not None
    assert dict(parse_qsl(workReq.query)).get("view_adult") == "true"


def test_fetch_work_information_in_its_entirety() -> None:
    """getWork parses every metadata field for work 29046888."""
    work = expectUnlockedSummary(ao3fetch.getWork(29046888))

    assert work.id == 29046888
    assert work.source == "website"
    assert work.host == "archiveofourown.org"
    assert work.authors == (ao3fetch.Author(username="KBstories", pseud="KBstories", anonymous=False),)
    assert work.title == "waiting//wishing"
    assert work.words == 36352
    assert work.language == "English"
    assert work.rating == ao3fetch.WorkRatings.MATURE
    assert work.category == (ao3fetch.WorkCategory.GEN, ao3fetch.WorkCategory.FM)
    assert work.fandoms == (
        "\u50d5\u306e\u30d2\u30fc\u30ed\u30fc\u30a2\u30ab\u30c7\u30df\u30a2 | Boku no Hero Academia | My Hero Academia",
    )
    assert work.tags == ao3fetch.WorkTags(
        warnings=(ao3fetch.WorkWarnings.GRAPHIC_VIOLENCE,),
        characters=(
            "Kaminari Denki",
            "Bakugou Katsuki",
            "Kirishima Eijirou",
            "Jirou Kyouka",
            "Sero Hanta",
            "Ashido Mina",
            "Yamada Hizashi | Present Mic",
            "Class 1-A (My Hero Academia)",
        ),
        relationships=(
            "Bakugou Katsuki/Kirishima Eijirou",
            "Jirou Kyouka/Kaminari Denki",
            "Bakugou Katsuki & Kaminari Denki",
            "Ashido Mina & Bakugou Katsuki & Jirou Kyouka & Kaminari Denki & Kirishima Eijirou & Sero Hanta",
        ),
        additional=(
            "Post-Paranormal Liberation War Arc (My Hero Academia)",
            "Developing Friendships",
            "Character Study",
            "Injury Recovery",
            "Protective Bakusquad (My Hero Academia)",
            "Queerplatonic Relationships",
            "POV Kaminari Denki",
            "the romance is There but it's not the point (the point is found family)",
            "Medical Inaccuracies",
            "Some Fluff",
            "Asexual Bakugou Katsuki",
            "Post-Traumatic Stress Disorder - PTSD",
            "@ U.A. give these kids proper therapy or die by my sword",
            "Hurt/Comfort",
            "Angst with a Happy Ending",
            "Bakusquad-centric (My Hero Academia)",
            "Hospitals",
            "Anxiety",
            "POV Bakugou Katsuki",
            "(epilogue only)",
            "Canon compliant up to CH306",
            "Hurt Bakugou Katsuki",
        ),
    )
    assert work.publishedAt == "2021-01-28"
    assert work.updatedAt == "2021-03-03"
    assert work.chapters == ao3fetch.WorkChaptersCount(published=7, total=7)
    expectedSummary = (
        "<p>&#x201c;<i>Bakugou will know what to do</i>. Top of the class, always quick on his feet "
        + "and possessing the strongest nerves in all of 1-A &#x2013; all of U.A., possibly. They&#x2019;re "
        + "at their most invincible with Bakugou there to hone their focus, to push them forward with that "
        + "unique kind of teeth-bared tenacity Kaminari has come to rely on in the past year. When Kaminari "
        + "looks, he sees&#x2013;</p><p>Iida, helmet off, severe face twisted with agitation as he argues "
        + "with the medics on the scene. Blood, so much blood, staining the gleaming chrome of his armor up "
        + "to his neck in wet, intersecting streaks of crimson.</p><p>And in his arms, mask torn and body "
        + "limp, is Bakugou Katsuki.&#x201d;</p><p>In which disaster strikes, the Bakusquad comes together "
        + "as a family once more, and Kaminari Denki is the MVP all the way through.</p>"
    )
    assertHtmlEqual(work.summary, expectedSummary)
    assertDriftingCount(work.stats.bookmarks, atLeast=268, atMost=310)
    assertDriftingCount(work.stats.comments, atLeast=139, atMost=160)
    assertDriftingCount(work.stats.hits, atLeast=20450, atMost=22898)
    assertDriftingCount(work.stats.kudos, atLeast=1101, atMost=1245)


def test_work_authors() -> None:
    """getWork handles default pseuds, anonymous collections, and orphan_account with Anonymous pseud."""
    defaultPseud = expectUnlockedSummary(ao3fetch.getWork(4491333))
    assert defaultPseud.authors == (ao3fetch.Author(username="astolat", pseud="astolat", anonymous=False),)

    anonCollection = expectUnlockedSummary(ao3fetch.getWork(168768))
    assert anonCollection.authors == (ao3fetch.Author(username="Anonymous", pseud="Anonymous", anonymous=True),)

    anonPseud = expectUnlockedSummary(ao3fetch.getWork(23824891))
    assert anonPseud.authors == (
        ao3fetch.Author(username="orphan_account", pseud="Anonymous", anonymous=False),
        ao3fetch.Author(username="Butterfly_Dream", pseud="Butterfly_Dream", anonymous=False),
        ao3fetch.Author(username="orphan_account", pseud="orphan_account", anonymous=False),
    )


def test_work_titles() -> None:
    """getWork preserves spaces, slashes, and punctuation in work titles."""
    assert expectUnlockedSummary(ao3fetch.getWork(23824891)).title == "Sister Dearest"
    assert expectUnlockedSummary(ao3fetch.getWork(29046888)).title == "waiting//wishing"
    assert expectUnlockedSummary(ao3fetch.getWork(323217)).title == "Field Test no.7: Phone Calls & Boundaries"


def test_work_tags_and_categories() -> None:
    """getWork extracts warnings, fandoms, relationships, characters, additional tags, and categories."""
    work323 = expectUnlockedSummary(ao3fetch.getWork(323217))
    assert work323.tags.warnings == (ao3fetch.WorkWarnings.CHOOSE_NOT_TO_WARN,)
    assert work323.fandoms == ("The Mentalist",)
    assert work323.tags.relationships == ("Patrick Jane/Kimball Cho",)
    assert work323.tags.characters == ("Jane", "Kimball Cho", "The rest of the team")
    assert not work323.tags.additional
    assert work323.category == (ao3fetch.WorkCategory.MM,)

    work373 = expectUnlockedSummary(ao3fetch.getWork(3738184))
    assert work373.tags.warnings == (
        ao3fetch.WorkWarnings.CHOOSE_NOT_TO_WARN,
        ao3fetch.WorkWarnings.GRAPHIC_VIOLENCE,
        ao3fetch.WorkWarnings.MAJOR_CHARACTER_DEATH,
        ao3fetch.WorkWarnings.NO_WARNINGS_APPLY,
        ao3fetch.WorkWarnings.NONCON,
        ao3fetch.WorkWarnings.UNDERAGE,
    )
    assert work373.category == (
        ao3fetch.WorkCategory.FF,
        ao3fetch.WorkCategory.FM,
        ao3fetch.WorkCategory.GEN,
        ao3fetch.WorkCategory.MM,
        ao3fetch.WorkCategory.MULTI,
        ao3fetch.WorkCategory.OTHER,
    )


def test_work_other_metadata_and_stats() -> None:
    """getWork extracts wordcount, language, rating, dates, chapters, summaries, and stats."""
    work323 = expectUnlockedSummary(ao3fetch.getWork(323217))
    assert work323.words == 5652
    assert work323.language == "English"
    assert work323.rating == ao3fetch.WorkRatings.NOT_RATED
    assert work323.summary == "<p>Jane has had enough.</p>"
    assertDriftingCount(work323.stats.bookmarks, atLeast=109, atMost=160)
    assertDriftingCount(work323.stats.comments, atLeast=22, atMost=43)
    assertDriftingCount(work323.stats.hits, atLeast=9450, atMost=11665)
    assertDriftingCount(work323.stats.kudos, atLeast=918, atMost=1206)

    work238 = expectUnlockedSummary(ao3fetch.getWork(23824891))
    assert work238.updatedAt == "2020-11-30"

    work168 = expectUnlockedSummary(ao3fetch.getWork(168768))
    assert work168.updatedAt is None
    assert work168.publishedAt == "2011-02-08"
    assert work168.chapters.published == 1
    assert work168.chapters.total == 1

    work177 = expectUnlockedSummary(ao3fetch.getWork(17793689))
    expectedWorkSummary = (
        "<p><b>A Modern Thedas AU</b>, in which Fen&apos;Harel and the Second Inquisitor tore down "
        + "the Veil a thousand years ago, reshaping Thedas into something entirely new. Thedas now has "
        + "modern technology powered by magic, and a society still plagued with problems that are all "
        + "too familiar - issues of race, classism, and power.</p>"
        + "<p>Fenina Lavellan, a student at the College of Enchanters: New Haven, often escapes her "
        + "reality by playing the MMORPG Dragon Age (set in the ancient past during the time of the "
        + "Second Inquisition) and is part of the most powerful guild aptly named &quot;TheInquisition&quot; "
        + "- a guild which has been running since the game was released. But when the guild discovers "
        + "that they all live in the same city and decide to meet up, they unknowingly stumble into a "
        + "plot to destroy their world as they know it. Can they navigate the difficulties of actually "
        + "being social in the real world? Will their in-game skills translate into abilities that will "
        + "actually help them in stopping a madman? Or is this the end of the world as they know it?</p>"
    )
    assertHtmlEqual(work177.summary, expectedWorkSummary)

    work412 = expectUnlockedSummary(ao3fetch.getWork(41289660))
    assert work412.stats.comments == 0
    assertDriftingCount(work412.stats.bookmarks, atLeast=2, atMost=33)
    assertDriftingCount(work412.stats.hits, atLeast=1482, atMost=2149)
    assertDriftingCount(work412.stats.kudos, atLeast=30, atMost=80)


def test_restricted_work_returns_locked_summary() -> None:
    """getWork returns LockedWorkSummary for login-restricted work 15461226."""
    work = ao3fetch.getWork(15461226)
    assert work == ao3fetch.LockedWorkSummary(
        id=15461226,
        source="website",
        host="archiveofourown.org",
        url="https://archiveofourown.org/works/15461226",
        shortUrl="https://ao3.org/works/15461226",
        locked=True,
    )
