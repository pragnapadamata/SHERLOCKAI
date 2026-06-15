# Backend image: API + data + trained ML, self-contained. The frontend deploys
# separately (Vercel); for the LOCAL recorded demo, build the SPA into frontend/dist
# and FastAPI serves it on one origin (see `make demo`).
FROM python:3.11-slim

# uv for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy APP_ENV=prod

# Source + data (build context excludes node_modules, the SPA build, and the
# rebuildable stores via .dockerignore).
COPY pyproject.toml uv.lock README.md ./
COPY backend ./backend
COPY data ./data

# Install dependencies + the project, then build the runtime stores and train the
# ML artifacts so the image needs no external state at runtime.
RUN uv sync --frozen --no-dev \
 && uv run python -m backend.scripts.build_index \
 && uv run python -m backend.scripts.train_models

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
