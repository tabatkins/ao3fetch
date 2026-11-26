"""Pytest configuration wiring the AO3.js mock archive server for every test."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from mock_archive import MockArchiveServer

import ao3fetch


@pytest.fixture(autouse=True)
def mockServer() -> Iterator[MockArchiveServer]:
    """Install a fresh file-backed mock archive server before each test and clean up after."""
    server = MockArchiveServer()
    ao3fetch.resetArchiveBaseUrl()
    ao3fetch.setFetcher(server.fetch)
    try:
        yield server
    finally:
        server.reset()
        ao3fetch.resetFetcher()
        ao3fetch.resetArchiveBaseUrl()
