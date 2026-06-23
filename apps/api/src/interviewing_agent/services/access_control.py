from __future__ import annotations

from collections import deque
from hashlib import sha256
from secrets import compare_digest, token_urlsafe
from threading import Lock
from time import monotonic
from typing import Callable


class SlidingWindowRateLimiter:
    def __init__(
        self,
        limit: int,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = monotonic,
        max_keys: int = 10_000,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self.max_keys = max_keys
        self._requests: dict[str, deque[float]] = {}
        self._lock = Lock()

    def allow(self, key: str = "global") -> bool:
        if self.limit <= 0:
            return True

        now = self.clock()
        cutoff = now - self.window_seconds
        with self._lock:
            self._prune_stale_keys(cutoff)
            requests = self._requests.setdefault(key, deque())
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= self.limit:
                return False
            requests.append(now)
            self._prune_excess_keys()
            return True

    def _prune_stale_keys(self, cutoff: float) -> None:
        stale_keys = [
            key
            for key, requests in self._requests.items()
            if not requests or requests[-1] <= cutoff
        ]
        for key in stale_keys:
            self._requests.pop(key, None)

    def _prune_excess_keys(self) -> None:
        if len(self._requests) <= self.max_keys:
            return

        sorted_keys = sorted(
            self._requests,
            key=lambda key: self._requests[key][-1] if self._requests[key] else 0.0,
        )
        for key in sorted_keys[: len(self._requests) - self.max_keys]:
            self._requests.pop(key, None)


def generate_session_access_token() -> str:
    return token_urlsafe(32)


def hash_session_access_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def verify_session_access_token(supplied_token: str, expected_hash: str | None) -> bool:
    if not supplied_token or not expected_hash:
        return False
    return compare_digest(hash_session_access_token(supplied_token), expected_hash)
