"""Shared type aliases, typing re-exports, and sentinels."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Final, Literal, NamedTuple, Protocol, cast, override

__all__ = [
    "TYPE_CHECKING",
    "UNSET",
    "Any",
    "Callable",
    "Final",
    "Iterable",
    "Literal",
    "Mapping",
    "NamedTuple",
    "Protocol",
    "Sequence",
    "Unset",
    "cast",
    "override",
]


class _UnsetType:
    """Sentinel type for omitted optional arguments where None is meaningful."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"


UNSET: Final[_UnsetType] = _UnsetType()
type Unset = _UnsetType
