"""Tests for getSeries (ported from AO3.js tests/series.test.ts)."""

from __future__ import annotations

import re

import pytest
from mock_archive import assertDriftingCount

import ao3fetch


def test_throw_invalid_id_error_for_invalid_series_id() -> None:
    """getSeries raises InvalidIDError with matching message for invalid series ID."""
    with pytest.raises(ao3fetch.InvalidIDError, match=r"invalid-id is not a valid series id"):
        ao3fetch.getSeries("invalid-id")


def test_fetch_series_top_level_fields() -> None:
    """getSeries extracts top-level metadata for series 2270465."""
    series = ao3fetch.getSeries("2270465")

    assert series.id == 2270465
    assert series.url == "https://archiveofourown.org/series/2270465"
    assert series.shortUrl == "https://ao3.org/series/2270465"
    assert series.name == "OG Titan"
    assert series.startedAt == "2021-04-11"
    assert series.updatedAt == "2026-04-18"
    assert series.authors == (ao3fetch.Author(username="MyHero", pseud="MyHero", anonymous=False),)
    assert series.description == (
        "<p>My potentially related stories about the relationship between the OG Titans. "
        + "Probably focused on Dick Grayson.</p>"
    )
    assert series.notes is None
    assert series.words == 32451
    assertDriftingCount(series.bookmarks, atLeast=260, atMost=300)
    assert series.complete is False
    assert series.workCount == 6


def test_fetch_series_works() -> None:
    """getSeries parses every work blurb in series 2270465."""
    series = ao3fetch.getSeries("2270465")
    myHero = (ao3fetch.Author(username="MyHero", pseud="MyHero", anonymous=False),)

    # Work 1
    w1 = series.works[0]
    assert w1.id == 30604247
    assert w1.title == "Away from all of Reality"
    assert w1.updatedAt == "2021-04-11"
    assert w1.adult is False
    assert w1.fandoms == (
        "Batman - All Media Types",
        "Teen Titans (Comics)",
        "Nightwing (Comics)",
    )
    assert w1.tags == ao3fetch.WorkBlurbTags(
        characters=("Dick Grayson", "Donna Troy"),
        relationships=(
            "Dick Grayson & Donna Troy",
            "Dick Grayson & Damian Wayne",
        ),
        additional=(
            "Dick Grayson Deserves Better",
            "Hurt No Comfort",
            "Protective Donna Troy",
            "BAMF Donna Troy",
            "Dick Grayson doesn't have a super - He has Ma and Pa Kent",
            "Dick Grayson is Not Okay",
            "Donna Troy is president of the",
            "#DickGraysonProtectionSquad",
            "Bruce Wayne is a Bad Parent",
            "Author might have some unresolved issues with Babs",
            "You'll see what I mean",
            "There are events in cannon that I can't get over and it shows",
            "Same with Bruce",
            "Wally West would be their secret keeper",
            "Damian would have an open invite to visit",
            "Daydreaming",
            "Donna Troy POV",
            "wonder twins",
            "Hurt Dick Grayson",
            "Dick Grayson-centric",
            "Garth and Wally will still come for brunch twice a month",
        ),
    )
    assert w1.authors == myHero
    assert w1.language == "English"
    assert w1.words == 2733
    assert w1.chapters == ao3fetch.WorkChaptersCount(published=1, total=1)
    assert w1.complete is True
    assertDriftingCount(w1.stats.bookmarks, atLeast=247, atMost=290)
    assertDriftingCount(w1.stats.kudos, atLeast=1581, atMost=1808)
    assertDriftingCount(w1.stats.hits, atLeast=13598, atMost=15741)

    # Work 2
    w2 = series.works[1]
    assert w2.id == 30794750
    assert w2.title == "Code B"
    assert w2.updatedAt is not None
    assert re.match(r"^(2023-01-31|2023-02-01)$", w2.updatedAt)
    assert w2.adult is False
    assert w2.fandoms == (
        "Batman - All Media Types",
        "Nightwing (Comics)",
        "Teen Titans (Comics)",
        "Red Hood and the Outlaws (Comics)",
    )
    assert w2.tags == ao3fetch.WorkBlurbTags(
        characters=(
            "Dick Grayson",
            "Garth (DCU)",
            "Donna Troy",
            "Wally West",
            "Roy Harper",
            "Jason Todd",
            "Alfred Pennyworth",
        ),
        relationships=(
            "Dick Grayson & Donna Troy",
            "Dick Grayson & Wally West",
            "Garth & Dick Grayson & Roy Harper & Donna Troy & Wally West",
            "Garth & Dick Grayson",
            "Roy Harper & Jason Todd",
            "Dick Grayson & Damian Wayne",
            "Alfred Pennyworth & Jason Todd",
            "Dick Grayson & Roy Harper",
            "Dick Grayson & Amy Rohrbach",
            "Catalina Flores/Dick Grayson",
        ),
        additional=(
            "Hurt Dick Grayson",
            "Dick Grayson Needs a Hug",
            "Protective Wally West",
            "Team as Family",
            "Roy Harper Needs a Hug",
            "Bruce Wayne is a Bad Parent",
            "The problem with not getting all the information is you don't have all the information",
            "A moment of clarity by Roy Harper",
            "wonder twins",
            "Jason Todd Needs A Hug",
            "Dick Grayson Did Not Fake His Death",
            "Dick Grayson is Not Okay",
            "Dick Grayson-centric",
            "Alfred Pennyworth isn\u2019t perfect but is trying his best and is significantly better than Bruce",
            "Former drug addict Roy Harper",
            "Mentioned Catalina Flores",
            "Dick Grayson & Wally West Friendship",
            "Protective Team",
            "Past Rape/Non-con",
            "Amy Rohrbach is a good friend",
            "Roy Harper needs a swear jar",
            "Blink and you miss it reference to...",
            "Evil Slade Wilson",
            "Creepy Slade Wilson",
            "Implied/Referenced Rape/Non-con",
            "Like the city of Rome your positive mental health cant be built in a day",
            "Also like Rome your mental health can be destroyed in hours",
            "All about Dick Grayson and he doesn't even show up until chapter 11",
            "Dick Grayson & Donna Troy Friendship",
        ),
    )
    assert w2.authors == myHero
    assert w2.language == "English"
    assert w2.words == 17141
    assert w2.chapters == ao3fetch.WorkChaptersCount(published=12, total=None)
    assert w2.complete is False
    assertDriftingCount(w2.stats.bookmarks, atLeast=749, atMost=862)
    assertDriftingCount(w2.stats.kudos, atLeast=3496, atMost=3940)
    assertDriftingCount(w2.stats.hits, atLeast=69968, atMost=78653)

    # Work 3
    w3 = series.works[2]
    assert w3.id == 30914645
    assert w3.title == "Donna Troy Loves You"
    assert w3.updatedAt == "2021-04-26"
    assert w3.adult is False
    assert w3.fandoms == (
        "Nightwing (Comics)",
        "Batman - All Media Types",
        "Teen Titans (Comics)",
    )
    assert w3.tags == ao3fetch.WorkBlurbTags(
        characters=("Dick Grayson", "Donna Troy", "Cassandra Cain"),
        relationships=(
            "Dick Grayson & Donna Troy",
            "Cassandra Cain & Dick Grayson",
            "Dick Grayson & Alfred Pennyworth",
            "Batfamily Members & Dick Grayson",
        ),
        additional=(
            "Protective Donna Troy",
            "Good Sibling Cassandra Cain",
            "Caring Cassandra Cain",
            "Dick Grayson is Nightwing",
            "Dick Grayson Needs a Hug",
            "BAMF Dick Grayson",
            "Dick Grayson Gets a Hug",
            "Bruce Wayne Tries to Be a Good Parent",
            "Good Grandparent Alfred Pennyworth",
            "Mentioned Catalina Flores",
            "Implied/Referenced Rape/Non-con",
            "Jealous Barbara Gordon",
            "Dick Grayson Needs Therapy",
            "Hurt Dick Grayson",
            "#DickGraysonProtectionSquad",
            "Bruce Wayne C+ Parenting",
            "Alfred Pennyworth is a Saint",
            "Dick Grayson-centric",
        ),
    )
    assert w3.authors == myHero
    assert w3.language == "English"
    assert w3.words == 3021
    assert w3.chapters == ao3fetch.WorkChaptersCount(published=1, total=1)
    assert w3.complete is True
    assertDriftingCount(w3.stats.bookmarks, atLeast=306, atMost=361)
    assertDriftingCount(w3.stats.kudos, atLeast=1959, atMost=2232)
    assertDriftingCount(w3.stats.hits, atLeast=16419, atMost=18864)

    # Work 4
    w4 = series.works[3]
    assert w4.id == 31221131
    assert w4.title == "Rockin Robin"
    assert w4.updatedAt == "2021-05-11"
    assert w4.adult is False
    assert w4.fandoms == ("Teen Titans (Comics)", "Batman - All Media Types")
    assert w4.tags == ao3fetch.WorkBlurbTags(
        characters=(
            "Garth (DCU)",
            "Dick Grayson",
            "Donna Troy",
            "Roy Harper",
            "Wally West",
            "Guest staring:",
            "Barbara Gordon",
            "Tim Drake",
        ),
        relationships=("Garth & Dick Grayson & Roy Harper & Donna Troy & Wally West",),
        additional=(
            "The Titans were a band",
            "Dick on vocals and guitar",
            "Donna on vocals and guitar",
            "Roy on bass guitar",
            "Wally on drums",
            "Garth on piano",
            "Twitter",
            "Will there be more? Probably",
            "Team as Family",
            "wonder twins",
        ),
    )
    assert w4.authors == myHero
    assert w4.language == "English"
    assert w4.words == 832
    assert w4.chapters == ao3fetch.WorkChaptersCount(published=1, total=1)
    assert w4.complete is True
    assertDriftingCount(w4.stats.bookmarks, atLeast=95, atMost=134)
    assertDriftingCount(w4.stats.kudos, atLeast=873, atMost=1017)
    assertDriftingCount(w4.stats.hits, atLeast=7846, atMost=9279)

    # Work 5
    w5 = series.works[4]
    assert w5.id == 35757790
    assert w5.title == "Realistic Exit Strategy"
    assert w5.updatedAt == "2026-04-18"
    assert w5.adult is False
    assert w5.fandoms == (
        "Teen Titans (Comics)",
        "Nightwing (Comics)",
        "Batman - All Media Types",
    )
    assert w5.tags == ao3fetch.WorkBlurbTags(
        characters=(
            "Dick Grayson",
            "Donna Troy",
            "Wally West",
            "Garth (DCU)",
            "Diana (Wonder Woman)",
            "Clark Kent",
            "Roy Harper",
        ),
        relationships=(
            "Dick Grayson & Donna Troy",
            "Garth & Dick Grayson & Roy Harper & Donna Troy & Wally West",
            "Diana (Wonder Woman) & Dick Grayson",
            "Dick Grayson & Clark Kent",
        ),
        additional=(
            "Dick Grayson Needs a Hug",
            "Dick Grayson Needs Help",
            "Dick Grayson Has Issues",
            "Illnesses",
            "Hurt/Comfort",
            "Unhealthy Coping Mechanisms",
            "Dick Grayson Deserves Better",
            "Protective Donna Troy",
            "Good Friend Donna Troy",
            "Jason Todd is Bad at Feelings",
            "Tim Drake is Bad at Feelings",
            "No Beta",
            "no beta we die like robins",
            "Lack of Communication",
            "Hurt Dick Grayson",
            "wonder twins",
            "Dick Grayson-centric",
            "Team as Family",
            "Medical Inaccuracies",
            "Protective Wally West",
            "Protective Garth (DCU)",
            "Good Uncle Clark Kent",
            "Good Aunt Diana Prince",
            "Roy Harper comes around",
            "Good Friend Roy Harper",
            "Medical inaccuracies like whoa",
            "Don't need to read part one",
            "but it might help.",
        ),
    )
    assert w5.authors == myHero
    assert w5.language == "English"
    assert w5.words == 8134
    assert w5.chapters == ao3fetch.WorkChaptersCount(published=3, total=4)
    assert w5.complete is False
    assertDriftingCount(w5.stats.bookmarks, atLeast=249, atMost=307)
    assertDriftingCount(w5.stats.kudos, atLeast=1524, atMost=1744)
    assertDriftingCount(w5.stats.hits, atLeast=15304, atMost=17915)

    # Work 6
    w6 = series.works[5]
    assert w6.id == 44149795
    assert w6.title == "You starting down the road leaving me again"
    assert w6.updatedAt is not None
    assert re.match(r"^(2023-01-08|2023-01-09)$", w6.updatedAt)
    assert w6.adult is False
    assert w6.fandoms == (
        "Batman - All Media Types",
        "Nightwing (Comics)",
        "Titans (Comics)",
    )
    assert w6.tags == ao3fetch.WorkBlurbTags(
        characters=(
            "Dick Grayson",
            "Donna Troy",
            "Garth (DCU)",
            "Roy Harper",
            "Wally West",
        ),
        relationships=("Garth & Dick Grayson & Roy Harper & Donna Troy & Wally West",),
        additional=(
            "Teen Titans as Family",
            "Titans",
            "Team as Family",
            "Karaoke",
            "Dick Grayson Needs a Hug",
            "Bl\u00fcdhaven",
            "Hurt Dick Grayson",
            "Emotional Hurt",
            "Found Family",
            "Parent Roy Harper",
            "Mentioned Linda Park",
            "would this count as",
            "Dick Grayson-centric",
            "What do you think they sing?",
            "The boys probably do a boy band",
            "They lost a bet to Donna",
            "No actual singing",
            "No Plot/Plotless",
            "Random & Short",
            "Author Is Sleep Deprived",
            "Author needed something sweet",
        ),
    )
    assert w6.authors == myHero
    assert w6.language == "English"
    assert w6.words == 590
    assert w6.chapters == ao3fetch.WorkChaptersCount(published=1, total=1)
    assert w6.complete is True
    assertDriftingCount(w6.stats.bookmarks, atLeast=52, atMost=87)
    assertDriftingCount(w6.stats.kudos, atLeast=459, atMost=546)
    assertDriftingCount(w6.stats.hits, atLeast=2680, atMost=3468)


def test_fetch_series_anonymous_author() -> None:
    """getSeries handles Anonymous series authors."""
    series = ao3fetch.getSeries("2946579")
    assert series.authors == (ao3fetch.Author(username="Anonymous", pseud="Anonymous", anonymous=True),)


def test_fetch_series_titles() -> None:
    """getSeries preserves spaces, slashes, and punctuation in series titles."""
    assert ao3fetch.getSeries("2270465").name == "OG Titan"
    assert ao3fetch.getSeries("1728802").name == "angsty oneshots/short stories"
    assert ao3fetch.getSeries("2817877").name == "*Insert Fandom* but Social Media (one-shots)"


def test_series_pagination() -> None:
    """getSeries supports default page 1, explicit page N, and unpaginated series."""
    page1 = ao3fetch.getSeries(60910)
    assert page1.name == "Fandom Stats"
    assert page1.pages == ao3fetch.PageInfo(total=7, current=1)
    assert [work.id for work in page1.works] == [
        16890957,
        1026780,
        1026854,
        16876149,
        16891416,
        16926933,
        16932096,
        16933218,
        17009412,
        17009619,
        17009676,
        17011452,
        17011545,
        17011641,
        17011701,
        17011803,
        17012055,
        17012217,
        1608254,
        1704926,
    ]

    page2 = ao3fetch.getSeries(60910, page=2)
    assert page2.name == "Fandom Stats"
    assert page2.pages == ao3fetch.PageInfo(total=7, current=2)
    assert [work.id for work in page2.works] == [
        1706072,
        1708259,
        2076084,
        16844275,
        16861600,
        16890750,
        16890834,
        16910946,
        16913802,
        16913982,
        16925628,
        17014116,
        17013705,
        17009067,
        17009250,
        17012409,
        17012583,
        16965927,
        17002176,
        16933407,
    ]

    singlePage = ao3fetch.getSeries(2270465)
    assert singlePage.pages == ao3fetch.PageInfo(total=1, current=1)
    assert len(singlePage.works) == 6
