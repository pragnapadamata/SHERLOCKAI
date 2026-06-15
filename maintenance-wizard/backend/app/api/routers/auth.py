"""Microsoft Entra ID OAuth (authorization-code flow) via Authlib.

Real SSO when ENTRA_* is configured; otherwise the routes degrade to the default
engineer so the portal still runs without OAuth. Both the OAuth result and the persona
picker converge on the SAME client-side AuthContext login: the flow ends by redirecting
the browser to /login?uid=<user_id>, which the SPA resolves (GET /api/me) and logs in --
there is no parallel server-side session system for app auth.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from backend.app.api.deps import get_system
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger

router = APIRouter(prefix="/api/auth")
log = get_logger(__name__)

_oauth = OAuth()
_registered = False
_DEFAULT_UID = "U-ENG-01"


def _entra():
    """Return the registered Entra OAuth client, or None when not configured."""

    global _registered
    settings = get_settings()
    if not (settings.entra_client_id and settings.entra_client_secret):
        return None
    if not _registered:
        _oauth.register(
            name="entra",
            client_id=settings.entra_client_id,
            client_secret=settings.entra_client_secret,
            server_metadata_url=(
                f"https://login.microsoftonline.com/{settings.entra_tenant_id}"
                "/v2.0/.well-known/openid-configuration"
            ),
            client_kwargs={"scope": "openid profile email User.Read"},
        )
        _registered = True
    return _oauth.entra


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """Redirect to Microsoft to begin sign-in; degrade to the default engineer if the
    Microsoft credentials are not configured."""

    client = _entra()
    if client is None:
        return RedirectResponse(url=f"/login?uid={_DEFAULT_UID}")
    try:
        return await client.authorize_redirect(request, get_settings().entra_redirect_uri)
    except Exception as exc:  # noqa: BLE001 -- any Microsoft/network error keeps the app usable
        log.warning("entra_login_failed", error=str(exc))
        return RedirectResponse(url="/login?autherror=1")


@router.get("/callback")
async def callback(request: Request, system: Any = Depends(get_system)) -> RedirectResponse:
    """Exchange the code, read the profile from the token, provision the user, and hand the
    resolved user_id back to the SPA so AuthContext logs in (same path as a persona pick)."""

    client = _entra()
    if client is None:
        return RedirectResponse(url=f"/login?uid={_DEFAULT_UID}")
    try:
        token = await client.authorize_access_token(request)
        info = token.get("userinfo") or {}
        email = info.get("preferred_username") or info.get("email") or info.get("sub")
        if not email:
            raise ValueError("no identity claim in token")
        user_id = system.repos.users.upsert(
            user_id=email, name=info.get("name") or email, role="engineer",
            area="Finishing", email=email,
        )
        log.info("entra_login", user_id=user_id)
        return RedirectResponse(url=f"/login?uid={quote(user_id, safe='')}")
    except Exception as exc:  # noqa: BLE001 -- surface a clean error; persona cards still work
        log.warning("entra_callback_failed", error=str(exc))
        return RedirectResponse(url="/login?autherror=1")
