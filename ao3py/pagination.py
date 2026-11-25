"""Pagination helpers for iterating through multi-page AO3 listings."""

from __future__ import annotations

from . import t
from .entities import PageInfo


class PagedResult(t.Protocol):
    """Protocol implemented by paginated AO3 responses (Series, UserWorks, TagSearchResultSummary)."""

    pages: PageInfo


def getAllPages[R: PagedResult](getter: t.Callable[..., R], **kwargs: t.Any) -> t.Iterable[R]:
    """Yield every page of a paginated getter one request at a time."""
    page = 1
    total = 1
    while page <= total:
        result = getter(page=page, **kwargs)
        total = result.pages.total
        yield result
        page += 1


def collectAllPages[R: PagedResult](getter: t.Callable[..., R], **kwargs: t.Any) -> list[R]:
    """Fetch every page of a paginated getter and return them as a list."""
    return list(getAllPages(getter, **kwargs))
