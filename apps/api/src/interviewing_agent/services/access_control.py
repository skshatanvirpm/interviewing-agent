from __future__ import annotations

from collections import deque
from threading import Lock
from time import monotonic
from typing import Callable


class SlidingWindowRateLimiter:
    def __init__(
        self,
        limit: int,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self._requests: deque[float] = deque()
        self._lock = Lock()

    def allow(self) -> bool:
        if self.limit <= 0:
            return True

        now = self.clock()
        cutoff = now - self.window_seconds
        with self._lock:
            while self._requests and self._requests[0] <= cutoff:
                self._requests.popleft()
            if len(self._requests) >= self.limit:
                return False
            self._requests.append(now)
            return True
