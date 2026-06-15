"""The guarded single-origin static mount serves the built SPA without breaking the API."""

from __future__ import annotations


def test_static_mount_serves_spa(api_system, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from backend.app.api.app import create_app
    from backend.app.core.config import get_settings

    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><div id='root'>portal</div>")
    (dist / "assets" / "app.js").write_text("// built bundle")
    (dist / "favicon.svg").write_text("<svg/>")

    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    get_settings.cache_clear()
    client = TestClient(create_app(system=api_system))

    assert client.get("/health").json()["status"] == "ok"  # health untouched
    assert client.get("/api/me").status_code == 200  # API untouched
    assert "portal" in client.get("/").text  # index at root
    assert "portal" in client.get("/dashboard").text  # SPA deep-link -> index
    assert client.get("/assets/app.js").status_code == 200  # built asset
    assert client.get("/favicon.svg").status_code == 200  # root static file


def test_no_static_mount_in_default_test_env(client):
    # conftest points FRONTEND_DIST at a nonexistent path, so there is no SPA fallback:
    # an unknown, non-API GET returns 404 rather than index.html.
    assert client.get("/definitely-not-a-real-route").status_code == 404
