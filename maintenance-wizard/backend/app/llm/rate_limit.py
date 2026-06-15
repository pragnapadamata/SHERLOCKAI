"""Client-side pacing + patient 429 backoff, wrapping any LLMClient.

For capturing the demo cache against rate-limited free tiers (e.g. Gemini free: 5-10
requests/minute). A heavy run bursts 6 specialists + a final synthesis, which trips the RPM
cap and would make the agent degrade. This wrapper (a) PACES calls under the provider RPM
with a global min-interval, and (b) on a 429 WAITS OUT the server's retry delay (honoring
RetryInfo/Retry-After, capped) and retries many times, so one run can span multiple
per-minute windows.

The waits happen INSIDE chat(), so they never count against the loop's iteration budget, and
there is no run-level wall-clock timeout, so a run only ever degrades on a genuine
non-recoverable error -- never on rate-limit backoff. Off by default (live); the tier registry
enables it from settings (capture).
"""

from __future__ import annotations

import re
import threading
import time
from collections.abc import Sequence

from backend.app.core.logging import get_logger
from backend.app.llm.base import LLMClient
from backend.app.llm.messages import ChatResult, Message, ToolSpec

log = get_logger(__name__)

DEFAULT_RETRY_WAIT_S = 15.0
_RETRY_DELAY_RE = re.compile(r'retrydelay["\']?\s*[:=]\s*["\']?(\d+(?:\.\d+)?)\s*s', re.I)
_RETRY_IN_RE = re.compile(r"(?:retry|try again) in (\d+(?:\.\d+)?)\s*s", re.I)


def is_rate_limit(exc: Exception) -> bool:
    """True for a 429 / rate-limit / RESOURCE_EXHAUSTED error (recoverable by waiting)."""

    code = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
    if code == 429:
        return True
    s = str(exc).lower()
    return "429" in s or "resource_exhausted" in s or ("rate" in s and "limit" in s)


def retry_delay(exc: Exception, default: float = DEFAULT_RETRY_WAIT_S) -> float:
    """Seconds to wait, from a Retry-After header or a RetryInfo/'retry in Ns' message."""

    resp = getattr(exc, "response", None)
    if resp is not None:
        try:
            after = resp.headers.get("retry-after")
            if after:
                return float(after)
        except Exception:  # noqa: BLE001 -- header shape varies; fall through to parsing the body
            pass
    text = str(exc)
    match = _RETRY_DELAY_RE.search(text) or _RETRY_IN_RE.search(text)
    return float(match.group(1)) if match else default


class Pacer:
    """Spaces call starts at least ``interval`` seconds apart (a single provider RPM budget)."""

    def __init__(self, interval: float, *, sleep=time.sleep, monotonic=time.monotonic) -> None:
        self._interval = interval
        self._sleep = sleep
        self._monotonic = monotonic
        self._lock = threading.Lock()
        self._last: float | None = None

    def wait(self) -> None:
        if self._interval <= 0:
            return
        with self._lock:
            now = self._monotonic()
            if self._last is not None and (now - self._last) < self._interval:
                self._sleep(self._interval - (now - self._last))
            self._last = self._monotonic()


class RateLimitedClient(LLMClient):
    """Wrap an LLMClient with pacing + patient 429 retry. Non-429 errors propagate at once."""

    def __init__(self, inner: LLMClient, *, pacer: Pacer, max_retries: int = 8,
                 max_wait: float = 60.0, sleep=time.sleep) -> None:
        super().__init__(model=inner.model, api_key=inner.api_key, tier=inner.tier)
        self._inner = inner
        self._pacer = pacer
        self._max_retries = max_retries
        self._max_wait = max_wait
        self._sleep = sleep

    @property
    def provider(self) -> str:
        return self._inner.provider

    def chat(self, messages: Sequence[Message], tools: Sequence[ToolSpec] | None = None, *,
             temperature: float | None = None, max_tokens: int | None = None) -> ChatResult:
        self._pacer.wait()
        attempt = 0
        while True:
            try:
                return self._inner.chat(messages, tools, temperature=temperature, max_tokens=max_tokens)
            except Exception as exc:  # noqa: BLE001 -- only rate limits are retried; the rest propagate
                if not is_rate_limit(exc) or attempt >= self._max_retries:
                    raise
                attempt += 1
                fallback = min(self._max_wait, DEFAULT_RETRY_WAIT_S)
                delay = min(self._max_wait, retry_delay(exc, default=fallback))
                log.warning("rate_limit_backoff", provider=self._inner.provider,
                            attempt=attempt, max_retries=self._max_retries, delay_s=round(delay, 1))
                self._sleep(delay)
