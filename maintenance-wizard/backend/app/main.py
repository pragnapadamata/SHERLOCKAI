"""FastAPI application entrypoint.

The HTTP surface lives in ``backend.app.api``. The app is created via the factory
so ``uvicorn backend.app.main:app`` serves the full API; the System is built
lazily on first request.
"""

from __future__ import annotations

from backend.app.api.app import create_app

app = create_app()
