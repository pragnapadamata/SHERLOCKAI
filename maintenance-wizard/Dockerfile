# Backend image: API + data + trained ML, self-contained. The frontend deploys
# separately (Vercel). Builds the runtime stores and trains ML at image build time.
FROM python:3.11-slim

# uv for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy APP_ENV=prod

# pyproject declares readme = "README.md"; create it so the project build never
# fails even if README.md is not in the build context.
COPY pyproject.toml uv.lock ./
RUN touch README.md
COPY backend ./backend
COPY data ./data

RUN uv sync --frozen --no-dev \
 && uv run python -m backend.scripts.build_index \
 && uv run python -m backend.scripts.train_models

EXPOSE 8000
# Bind to the platform-injected $PORT (Render) when present, else 8000 locally.
CMD uv run uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
