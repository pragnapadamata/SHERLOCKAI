"""Run the API server.

    uv run python -m backend.scripts.serve
    # or: uv run uvicorn backend.app.main:app --reload
"""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
