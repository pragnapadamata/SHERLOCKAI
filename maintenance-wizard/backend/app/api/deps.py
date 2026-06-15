"""Dependencies: System resolution and a stub current-user (Phase 7 SSO)."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Request

# Serialises the lazy fallback build so concurrent first-requests can never construct the
# System (and ChromaDB/onnxruntime) more than once. In normal operation the lifespan has
# already built it at startup, so this lock is uncontended defence-in-depth.
_build_lock = threading.Lock()


@dataclass
class UserContext:
    user_id: str
    name: str
    role: str
    area: str


def get_system(request: Request) -> Any:
    """Return the System. Normally it is built once at startup (lifespan) and stored on
    ``app.state``; this returns that instance. If it is somehow missing it is built under
    a lock (double-checked) so the heavy build never races across requests."""

    system = getattr(request.app.state, "system", None)
    if system is not None:
        return system

    with _build_lock:
        system = getattr(request.app.state, "system", None)
        if system is None:
            from backend.app.container import build_system

            system = build_system()
            request.app.state.system = system
        return system


def get_current_user(request: Request, system: Any = Depends(get_system)) -> UserContext:
    """Resolve the current user from the X-User-Id header (Phase 7 dummy SSO sets it)."""

    user_id = request.headers.get("X-User-Id") or "U-ENG-01"
    row = system.repos.users.get(user_id) or system.repos.users.get("U-ENG-01")
    if row is None:
        return UserContext(user_id=user_id, name="Unknown", role="engineer", area="")
    return UserContext(user_id=row["user_id"], name=row["name"], role=row["role"], area=row["area"])
