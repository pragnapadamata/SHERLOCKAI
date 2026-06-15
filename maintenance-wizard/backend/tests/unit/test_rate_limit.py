"""Capture rate-limit survival: pacing + patient 429 backoff (simulated, zero tokens)."""

from __future__ import annotations

import pytest

from backend.app.llm.messages import ChatResult
from backend.app.llm.rate_limit import Pacer, RateLimitedClient, is_rate_limit, retry_delay


class _Boom(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class _FakeInner:
    provider = "openai"
    model = "gemini-2.0-flash"
    api_key = "k"
    tier = "large"

    def __init__(self, fail_times: int, exc: Exception | None) -> None:
        self.calls = 0
        self._fail_times = fail_times
        self._exc = exc

    def chat(self, messages, tools=None, *, temperature=None, max_tokens=None) -> ChatResult:
        self.calls += 1
        if self._exc is not None and self.calls <= self._fail_times:
            raise self._exc
        return ChatResult(content="ok", tool_calls=[], provenance=None, raw=None)


def _no_pace() -> Pacer:
    return Pacer(0)


def test_is_rate_limit_detection():
    assert is_rate_limit(_Boom("boom", status_code=429))
    assert is_rate_limit(_Boom("Error code: 429 RESOURCE_EXHAUSTED"))
    assert is_rate_limit(_Boom("rate limit exceeded"))
    assert not is_rate_limit(ValueError("a real bug"))


def test_retry_delay_parsing():
    assert retry_delay(_Boom('... "retryDelay": "42s" ...'), default=9) == 42.0
    assert retry_delay(_Boom("please retry in 30s"), default=9) == 30.0
    assert retry_delay(_Boom("no hint"), default=9) == 9.0


def test_429_then_success_waits_and_retries():
    slept: list[float] = []
    err = _Boom('429 RESOURCE_EXHAUSTED {"retryDelay": "42s"}', status_code=429)
    inner = _FakeInner(fail_times=2, exc=err)
    client = RateLimitedClient(inner, pacer=_no_pace(), max_retries=5, max_wait=60, sleep=slept.append)
    result = client.chat([], tools=None)
    assert result.content == "ok"
    assert inner.calls == 3          # two 429s + one success
    assert slept == [42.0, 42.0]     # honored RetryInfo each time, never gave up


def test_retry_delay_is_capped_at_max_wait():
    slept: list[float] = []
    inner = _FakeInner(fail_times=1, exc=_Boom('429 {"retryDelay": "300s"}', status_code=429))
    client = RateLimitedClient(inner, pacer=_no_pace(), max_retries=3, max_wait=60, sleep=slept.append)
    client.chat([])
    assert slept == [60.0]


def test_non_rate_limit_error_reraises_without_retry():
    inner = _FakeInner(fail_times=1, exc=ValueError("a genuine bug"))
    client = RateLimitedClient(inner, pacer=_no_pace(), max_retries=5, max_wait=60, sleep=lambda _s: None)
    with pytest.raises(ValueError):
        client.chat([])
    assert inner.calls == 1          # genuine errors are not retried (the loop then degrades)


def test_exhausts_retries_then_reraises():
    inner = _FakeInner(fail_times=99, exc=_Boom("429 too many", status_code=429))
    client = RateLimitedClient(inner, pacer=_no_pace(), max_retries=3, max_wait=5, sleep=lambda _s: None)
    with pytest.raises(_Boom):
        client.chat([])
    assert inner.calls == 4          # initial + 3 retries


def test_pacer_spaces_calls():
    slept: list[float] = []
    pacer = Pacer(7, sleep=slept.append, monotonic=lambda: 100.0)  # frozen clock -> gap always 0
    pacer.wait()  # first call: no prior -> no sleep
    pacer.wait()  # sleep 7
    pacer.wait()  # sleep 7
    assert slept == [7, 7]
