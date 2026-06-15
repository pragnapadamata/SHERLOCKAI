.PHONY: dev demo demo-cached capture build-frontend serve test lint

# Dev: backend (:8000) + Vite dev server (:5173, proxying the API) together.
dev:
	./scripts/dev.sh

# Build the SPA into frontend/dist.
build-frontend:
	cd frontend && npm install && npm run build

# Recorded demo: build the SPA, then serve the WHOLE app from FastAPI on one origin (:8000).
demo: build-frontend serve

# Recorded demo with the demo cache: LLM-backed features replay instantly on camera.
demo-cached: build-frontend
	DEMO_MODE=1 uv run uvicorn backend.app.main:app --port 8000

# Capture real hero outputs into the demo cache (needs fresh LLM API quota).
capture:
	uv run python -m backend.scripts.capture_demo_cache

serve:
	uv run uvicorn backend.app.main:app --port 8000

test:
	uv run pytest

lint:
	uv run ruff check
	cd frontend && npm run typecheck && npm run lint
