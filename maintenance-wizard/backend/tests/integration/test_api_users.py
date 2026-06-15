"""GET /api/users: the dummy-SSO persona picker reads the users table."""

from __future__ import annotations


def test_list_users_returns_seed_personas(client):
    r = client.get("/api/users")
    assert r.status_code == 200
    users = r.json()
    assert users and all({"user_id", "name", "role", "area"} <= set(u) for u in users)
    ids = {u["user_id"] for u in users}
    assert "U-ENG-01" in ids
    roles = {u["role"] for u in users}
    assert "engineer" in roles and "supervisor" in roles
