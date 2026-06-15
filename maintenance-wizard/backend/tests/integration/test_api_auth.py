"""Auth routes degrade gracefully without Entra creds (offline; never calls Microsoft).

conftest forces ENTRA_CLIENT_ID/SECRET empty, so /login and /callback take the
unconfigured path and redirect straight to the default engineer -- no network.
"""

from __future__ import annotations


def test_login_without_creds_falls_back_to_default_engineer(client):
    r = client.get("/api/auth/login", follow_redirects=False)
    assert r.status_code in (302, 303, 307)
    assert "uid=U-ENG-01" in r.headers["location"]


def test_callback_without_creds_falls_back_to_default_engineer(client):
    r = client.get("/api/auth/callback", follow_redirects=False)
    assert r.status_code in (302, 303, 307)
    assert "uid=U-ENG-01" in r.headers["location"]
