"""Real-server smoke: a genuine uvicorn process builds the System at startup and serves
the data endpoints, including concurrent first requests.

This covers the path the in-process TestClient never exercised -- the lazy build under a
real event loop, which previously raced (concurrent ChromaDB init) and hung/500'd. It
loads the real models + vector store (no LLM calls, zero tokens), so it is marked slow.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from backend.app.core.config import REPO_ROOT


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.mark.slow
def test_real_server_builds_at_startup_and_serves_concurrent_requests():
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app",
         "--host", "127.0.0.1", "--port", str(port), "--no-access-log"],
        cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        # /health returns 200 only after the lifespan startup build completes.
        start = time.monotonic()
        deadline = start + 120
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise AssertionError(f"server exited early:\n{proc.stdout.read() if proc.stdout else ''}")
            try:
                if httpx.get(f"{base}/health", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.5)
        else:
            raise AssertionError("server never became healthy")
        startup_s = time.monotonic() - start
        print(f"\nreal-server startup (build at lifespan): {startup_s:.1f}s")

        # Fire the data endpoints concurrently -- the combination that previously raced
        # the lazy build. With the startup build they all hit the prebuilt System.
        endpoints = ["/api/users", "/api/me", "/api/dashboard/priority", "/api/dashboard/equipment"]
        with httpx.Client(base_url=base, timeout=30) as client:

            def fetch(ep: str):
                return ep, client.get(ep)

            with ThreadPoolExecutor(max_workers=len(endpoints)) as ex:
                responses = dict(ex.map(fetch, endpoints))

        for ep, r in responses.items():
            assert r.status_code == 200, f"{ep} -> {r.status_code}: {r.text[:200]}"

        users = responses["/api/users"].json()
        assert any(u["user_id"] == "U-ENG-01" for u in users)
        priority = responses["/api/dashboard/priority"].json()
        assert priority and priority[0]["equipment_id"] == "HSM-F3-GBX"  # F3 ranks first
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
