"""Token bucket rate limiter for Telegram API calls."""

from __future__ import annotations

import asyncio
import time


class RateLimiter:
    """Global token bucket rate limiter.

    Limits outgoing Telegram API calls to `rate` requests per second.
    Callers await `acquire()` before each API call; it returns immediately
    if a token is available, otherwise sleeps until one refills.
    """

    def __init__(self, rate: int = 30) -> None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        self._rate = rate
        self._tokens = float(rate)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a token is available, then consume it."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                # Calculate wait time for next token
                wait_time = (1.0 - self._tokens) / self._rate
            # Sleep outside the lock so other coroutines can check too
            await asyncio.sleep(wait_time)

    def _refill(self) -> None:
        """Add tokens based on elapsed time since last refill."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(float(self._rate), self._tokens + elapsed * self._rate)
        self._last_refill = now
