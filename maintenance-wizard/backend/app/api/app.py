"""FastAPI application factory over the build_system composition root."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.app.api.routers import (
    alerts,
    auth,
    chat,
    dashboard,
    feedback,
    logbook,
    proactive,
    reports,
    tickets,
    users,
)
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging

_ROUTERS = (
    users.router, auth.router, chat.router, dashboard.router, alerts.router, tickets.router,
    feedback.router, reports.router, logbook.router, proactive.router,
)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Build the heavy System ONCE, at startup, before the server accepts traffic and
    off the event loop. Tests inject a System via ``create_app(system=...)``, so this is
    a no-op there. Building here (not lazily inside a request) avoids both the inline
    build latency on the first request and the concurrent-first-request build race
    (multiple threads constructing ChromaDB/onnxruntime at once)."""

    if getattr(app.state, "system", None) is None:
        from backend.app.container import build_system

        app.state.system = await run_in_threadpool(build_system)
    yield


def _mount_frontend(app: FastAPI, dist: Path) -> None:
    """Serve the built SPA from one origin (the recorded demo runs the whole app on
    :8000). Guarded: if the build is absent (dev with the Vite proxy, tests, CI) this
    is a no-op and the API behaves exactly as before."""

    index = dist / "index.html"
    if not index.is_file():
        return

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        # API and health are served by their routers (registered first); everything
        # else falls back to index.html so client-side routes deep-link correctly.
        if full_path.startswith("api/") or full_path == "health":
            raise HTTPException(status_code=404)
        candidate = dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(index))


def create_app(system: Any | None = None) -> FastAPI:
    """Build the app. Pass a System to inject one (tests); otherwise the real System is
    built once at startup by the lifespan (see ``_lifespan``)."""

    settings = get_settings()
    configure_logging(settings.log_level, dev=settings.app_env != "prod")

    app = FastAPI(title="Maintenance Wizard API", version="0.7.2", lifespan=_lifespan)
    if system is not None:
        app.state.system = system

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware, allow_origins=origins, allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )
    # Signed-cookie session for the Entra OAuth state/nonce between /login and /callback.
    app.add_middleware(
        SessionMiddleware, secret_key=settings.session_secret,
        same_site="lax", https_only=False,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.app_env}

    for router in _ROUTERS:
        app.include_router(router)

    _mount_frontend(app, Path(settings.frontend_dist))
    return app
