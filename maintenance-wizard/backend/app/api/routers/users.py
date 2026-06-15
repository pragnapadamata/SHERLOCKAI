"""User endpoints: the current user (/api/me) and the persona list (/api/users).

Phase 7 dummy SSO sets X-User-Id; /api/users backs the login persona picker, read
straight from the users table (single source of truth, no drift from the seed).
Roles are UI-level personas for the demo, not a security boundary -- auth is stubbed.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.app.api.deps import UserContext, get_current_user, get_system
from backend.app.api.schemas import UserOut

router = APIRouter()


@router.get("/api/me")
def me(user: UserContext = Depends(get_current_user)) -> UserOut:
    return UserOut(user_id=user.user_id, name=user.name, role=user.role, area=user.area)


@router.get("/api/users")
def users(system: Any = Depends(get_system)) -> list[UserOut]:
    """List the seed users for the dummy-SSO persona picker. The login UI filters out
    the autonomous system user (role 'system')."""

    return [
        UserOut(user_id=r["user_id"], name=r["name"], role=r["role"], area=r["area"])
        for r in system.repos.users.all()
    ]
