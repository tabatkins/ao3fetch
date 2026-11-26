"""Tests for getWorkWithChapters (ported from AO3.js tests/chapters.test.ts)."""

from __future__ import annotations

import ao3fetch


def test_fetch_chapters_list_from_work_id() -> None:
    """getWorkWithChapters fetches work title, authors, and full /navigate chapter list."""
    workData = ao3fetch.getWorkWithChapters(43703871)

    assert workData.title == "Let The River Run"
    assert workData.authors == (ao3fetch.Author(username="astolat", pseud="astolat", anonymous=False),)
    assert workData.workId == 43703871
    assert workData.chapters == (
        ao3fetch.Chapter(
            id=109896639,
            workId=43703871,
            index=1,
            title="Coming Through The Fog",
            publishedAt="2022-12-19",
            url="https://archiveofourown.org/works/43703871/chapters/109896639",
            shortUrl="https://ao3.org/works/43703871/chapters/109896639",
        ),
        ao3fetch.Chapter(
            id=109943109,
            workId=43703871,
            index=2,
            title="The Darkening Dawn",
            publishedAt="2022-12-20",
            url="https://archiveofourown.org/works/43703871/chapters/109943109",
            shortUrl="https://ao3.org/works/43703871/chapters/109943109",
        ),
        ao3fetch.Chapter(
            id=109984306,
            workId=43703871,
            index=3,
            title="Come Run With Me Now",
            publishedAt="2022-12-20",
            url="https://archiveofourown.org/works/43703871/chapters/109984306",
            shortUrl="https://ao3.org/works/43703871/chapters/109984306",
        ),
        ao3fetch.Chapter(
            id=110032191,
            workId=43703871,
            index=4,
            title="Trembling, Shaking",
            publishedAt="2022-12-21",
            url="https://archiveofourown.org/works/43703871/chapters/110032191",
            shortUrl="https://ao3.org/works/43703871/chapters/110032191",
        ),
        ao3fetch.Chapter(
            id=110083590,
            workId=43703871,
            index=5,
            title="Stand On A Star",
            publishedAt="2022-12-22",
            url="https://archiveofourown.org/works/43703871/chapters/110083590",
            shortUrl="https://ao3.org/works/43703871/chapters/110083590",
        ),
        ao3fetch.Chapter(
            id=110133096,
            workId=43703871,
            index=6,
            title="Blaze A Trail Of Desire",
            publishedAt="2022-12-23",
            url="https://archiveofourown.org/works/43703871/chapters/110133096",
            shortUrl="https://ao3.org/works/43703871/chapters/110133096",
        ),
        ao3fetch.Chapter(
            id=110186152,
            workId=43703871,
            index=7,
            title="Sirens Call Them On",
            publishedAt="2022-12-24",
            url="https://archiveofourown.org/works/43703871/chapters/110186152",
            shortUrl="https://ao3.org/works/43703871/chapters/110186152",
        ),
        ao3fetch.Chapter(
            id=110240500,
            workId=43703871,
            index=8,
            title="Running On The Water",
            publishedAt="2022-12-25",
            url="https://archiveofourown.org/works/43703871/chapters/110240500",
            shortUrl="https://ao3.org/works/43703871/chapters/110240500",
        ),
        ao3fetch.Chapter(
            id=110242083,
            workId=43703871,
            index=9,
            title="Epilogue (Silver Cities Rise)",
            publishedAt="2022-12-25",
            url="https://archiveofourown.org/works/43703871/chapters/110242083",
            shortUrl="https://ao3.org/works/43703871/chapters/110242083",
        ),
    )
