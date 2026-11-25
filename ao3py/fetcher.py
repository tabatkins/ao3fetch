"""Pluggable HTTP fetcher with retry/rate-limit handling and in-memory LRU caching."""

from __future__ import annotations

import email.utils
import math
import random
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from dataclasses import dataclass

from . import t

_DEFAULT_USER_AGENT: t.Final[str] = "ao3py/0.1 (+https://github.com/tabatkins/ao3py)"
_DEFAULT_TIMEOUT_SECONDS: t.Final[float] = 30.0


@dataclass(slots=True)
class FetchResponse:
    """Lightweight HTTP response returned by archive fetchers."""

    status: int
    headers: dict[str, str]
    body: bytes
    url: str

    @property
    def ok(self) -> bool:
        """Return True for 2xx HTTP responses."""
        return 200 <= self.status < 300

    @property
    def text(self) -> str:
        """Decode response bytes as UTF-8 text."""
        return self.body.decode("utf-8", errors="replace")

    def header(self, name: str) -> str | None:
        """Look up a response header case-insensitively."""
        target = name.lower()
        for key, value in self.headers.items():
            if key.lower() == target:
                return value
        return None


@dataclass(slots=True)
class RetryEvent:
    """Details passed to the optional onRetry callback before waiting."""

    attempt: int
    delaySeconds: float
    response: FetchResponse | None = None
    error: Exception | None = None


type Fetcher = t.Callable[[str, t.Mapping[str, str] | None], FetchResponse]
type OnRetryCallback = t.Callable[[RetryEvent], None]


def defaultFetch(url: str, headers: t.Mapping[str, str] | None = None) -> FetchResponse:
    """Fetch a URL using Python's stdlib urllib.request (supports HTTPS/HTTP only)."""
    if not url.startswith(("https://", "http://")):
        msg = f"Unsupported URL scheme for archive fetch: {url}"
        raise ValueError(msg)
    reqHeaders = {"User-Agent": _DEFAULT_USER_AGENT}
    if headers:
        for key, value in headers.items():
            if value:
                reqHeaders[key] = value
    request = urllib.request.Request(url, headers=reqHeaders, method="GET")  # noqa: S310
    try:
        with urllib.request.urlopen(request, timeout=_DEFAULT_TIMEOUT_SECONDS) as resp:  # noqa: S310
            respHeaders = {k.lower(): v for k, v in resp.headers.items()}
            return FetchResponse(
                status=int(resp.status),
                headers=respHeaders,
                body=resp.read(),
                url=resp.geturl(),
            )
    except urllib.error.HTTPError as err:
        respHeaders = {k.lower(): v for k, v in err.headers.items()} if err.headers else {}
        body = err.read() if err.fp is not None else b""
        return FetchResponse(
            status=int(err.code),
            headers=respHeaders,
            body=body,
            url=err.geturl() or url,
        )


class _FetcherState:
    """Mutable holder for the configured active fetcher."""

    __slots__ = ("fetcher",)

    def __init__(self, fetcher: Fetcher | None) -> None:
        self.fetcher = fetcher


_FETCHER_STATE = _FetcherState(None)


def getFetcher() -> Fetcher:
    """Return the active fetcher, defaulting to defaultFetch."""
    return _FETCHER_STATE.fetcher or defaultFetch


def setFetcher(newFetcher: Fetcher) -> None:
    """Override the HTTP fetcher used by all archive loaders."""
    _FETCHER_STATE.fetcher = newFetcher


def resetFetcher() -> None:
    """Restore the default urllib-based fetcher."""
    _FETCHER_STATE.fetcher = None


def getRetryAfterSeconds(header: str | None, *, now: float | None = None) -> float | None:
    """Parse an HTTP Retry-After header (seconds or HTTP-date) into delay seconds."""
    if not header or not header.strip():
        return None
    stripped = header.strip()
    try:
        seconds = float(stripped)
    except ValueError:
        seconds = float("nan")
    if math.isfinite(seconds):
        return max(0.0, seconds)

    try:
        parsedDt = email.utils.parsedate_to_datetime(stripped)
    except (TypeError, ValueError):
        return None
    currentTime = time.time() if now is None else now
    return max(0.0, parsedDt.timestamp() - currentTime)


def _isRetryableStatus(status: int) -> bool:
    return status == 429 or status >= 500


def _nextDelaySeconds(
    retryAfterSeconds: float | None,
    retryNumber: int,
    baseDelaySeconds: float,
    maxDelaySeconds: float,
) -> float:
    if retryAfterSeconds is not None:
        return retryAfterSeconds
    backoff: float = min(baseDelaySeconds * (2.0 ** (retryNumber - 1)), maxDelaySeconds)
    # Jitter between 50% and 100% of backoff.
    return backoff / 2.0 + (random.random() * backoff / 2.0)  # noqa: S311


def withRetry(
    baseFetcher: Fetcher,
    *,
    maxRetries: int = 3,
    maxRateLimitRetries: int = 10,
    baseDelaySeconds: float = 1.0,
    maxDelaySeconds: float = 180.0,
    maxRetryAfterSeconds: float | None = None,
    onRetry: OnRetryCallback | None = None,
    sleepFunc: t.Callable[[float], None] = time.sleep,
) -> Fetcher:
    """Wrap a fetcher to retry 429 rate limits, 5xx errors, and network failures."""

    def _wrapped(url: str, headers: t.Mapping[str, str] | None = None) -> FetchResponse:
        rateLimitCount = 0
        errorCount = 0

        while True:
            response: FetchResponse | None = None
            caught: Exception | None = None
            try:
                response = baseFetcher(url, headers)
            except OSError as exc:
                caught = exc

            if response is not None and not _isRetryableStatus(response.status):
                return response

            isRateLimit = response is not None and response.status == 429
            retryAfter = getRetryAfterSeconds(response.header("retry-after")) if response is not None else None

            limitExceeded = rateLimitCount >= maxRateLimitRetries if isRateLimit else errorCount >= maxRetries
            waitTooLong = (
                retryAfter is not None and maxRetryAfterSeconds is not None and retryAfter > maxRetryAfterSeconds
            )
            if limitExceeded or waitTooLong:
                if response is None and caught is not None:
                    raise caught
                assert response is not None
                return response

            if isRateLimit:
                rateLimitCount += 1
                retryNum = rateLimitCount
            else:
                errorCount += 1
                retryNum = errorCount

            delay = _nextDelaySeconds(retryAfter, retryNum, baseDelaySeconds, maxDelaySeconds)
            if onRetry is not None:
                onRetry(
                    RetryEvent(
                        attempt=rateLimitCount + errorCount,
                        delaySeconds=delay,
                        response=response,
                        error=caught,
                    ),
                )
            sleepFunc(delay)

    return _wrapped


@dataclass(slots=True)
class _CacheEntry:
    response: FetchResponse
    storedAt: float


def withCache(
    baseFetcher: Fetcher,
    *,
    ttlSeconds: float = 300.0,
    maxEntries: int = 500,
    clock: t.Callable[[], float] = time.monotonic,
) -> Fetcher:
    """Wrap a fetcher with an in-memory LRU+TTL cache for successful responses."""
    cache: OrderedDict[tuple[str, tuple[tuple[str, str], ...]], _CacheEntry] = OrderedDict()

    def _wrapped(url: str, headers: t.Mapping[str, str] | None = None) -> FetchResponse:
        normHeaders = tuple(sorted((k.lower(), v) for k, v in (headers or {}).items() if v))
        key = (url, normHeaders)
        now = clock()

        entry = cache.get(key)
        if entry is not None and (now - entry.storedAt) < ttlSeconds:
            cache.move_to_end(key)
            return entry.response
        if entry is not None:
            del cache[key]

        response = baseFetcher(url, headers)
        if response.ok:
            cache[key] = _CacheEntry(response=response, storedAt=clock())
            cache.move_to_end(key)
            while len(cache) > maxEntries:
                cache.popitem(last=False)
        return response

    return _wrapped
