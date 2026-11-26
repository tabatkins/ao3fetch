"""Tests for getUser (ported from AO3.js tests/user.test.ts)."""

from __future__ import annotations

import re

from mock_archive import assertHtmlEqual

import ao3fetch

_ASTOLAT_BIO_HTML = (
    '<p>I <a href="https://astolat.dreamwidth.org/125056.html" rel="nofollow">built this city</a>.</p>\n'
    + "<p>I&apos;m also: "
    + '<a href="https://astolat.tumblr.com" rel="nofollow">astolat @ Tumblr</a> and '
    + '<a href="https://www.youtube.com/user/astolatvids" rel="nofollow">astolatvids on YouTube</a>.</p>\n'
    + "<p><strong>Blanket Permission Policy</strong><br>"
    + "I love transformative works based on my work. As long as it&apos;s noncommercial and credit is given, "
    + "you don&apos;t need to ask permission. More than one person is welcome to "
    + "podfic/translate/sequel/illustrate/etc any given story. Please post your work here and cite my original "
    + "story as a related work, so I can link back!</p>\n"
    + "<p>A note on ficbindings: I&apos;m delighted for you to make a binding for yourself or as a gift and to "
    + "post photos of the work, but I do have a hard line on noncommerciality: no money should change hands, "
    + "not even for expenses.</p>\n"
    + "<p><strong>Warnings</strong><br>"
    + "My work is labeled Choose Not To Warn unless I am confident it is safe. Most of my work is not! I do add "
    + "more specific warnings sometimes, but my judgement may not align with yours. I don&apos;t tag exhaustively "
    + "for every story element that appears in my work.</p>\n"
    + "<p><strong>Collections</strong><br>"
    + "If you want to add one of my stories to a collection, please bookmark it and add your bookmark to the "
    + "collection instead. I had to block collection requests because of abuse, sorry. :/</p>\n"
    + "<p><strong>Personal</strong><br>"
    + "I&#x2019;m a pro writer IRL and my identity is a fairly open secret in fandom, but I prefer not crossing "
    + "the streams. It&#x2019;s fine to share it privately, but please don&#x2019;t out me in public and "
    + "googleable places. That includes comments and tumblr posts/comments! Thank you!</p>\n"
    + "<p><strong>Pronouns:</strong> she/her</p>"
)


def test_fetch_user_data_using_username() -> None:
    """getUser fetches core profile metadata for astolat."""
    user = ao3fetch.getUser("astolat")

    assert user.username == "astolat"
    assert user.id == 8
    assert user.url == "https://archiveofourown.org/users/astolat/profile"
    assert user.shortUrl == "https://ao3.org/users/astolat/profile"
    assert user.pseuds == "astolat, shalott, the lady of shalott"
    assert user.joined == "2008-09-13"


def test_fetch_html_bio_from_profile_fields() -> None:
    """getUser extracts HTML bio matching AO3.js snapshot."""
    astolat = ao3fetch.getUser("astolat")
    assertHtmlEqual(astolat.bioHtml, _ASTOLAT_BIO_HTML)


def test_fetch_user_data_from_optional_profile_fields() -> None:
    """getUser reads canonical username casing, icon URL, and profile header."""
    franzeska = ao3fetch.getUser("franzeska")

    assert franzeska.username == "Franzeska"
    assert franzeska.id == 87
    assert re.match(
        r"^https://archiveofourown\.org/rails/active_storage/representations/proxy/[^/]+/[^/]+/original\.jpg$",
        franzeska.icon,
    )
    assert franzeska.header == "Yes, it's really spelled with a Z"
