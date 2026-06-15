"""SQLite connection and query helpers (stdlib sqlite3, dict rows).

Thread-safety: the API shares one connection across the async threadpool and the
(triggered) proactive engine. A process-wide lock serializes every access to the
shared connection, and the connection is opened with check_same_thread=False +
WAL + a busy timeout. The lock is held only for the microsecond DB call, never
across the long LLM work, so contention is negligible. SQLite is single-writer;
this is the pragmatic prototype approach -- a pool / Postgres is a later concern.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Sequence
from typing import Any

from backend.app.core.config import Settings, get_settings

_DB_LOCK = threading.RLock()


def connect(path: str | None = None, settings: Settings | None = None) -> sqlite3.Connection:
    """Open a connection usable across threads (serialized by the module lock)."""

    settings = settings or get_settings()
    db_path = path or settings.sqlite_path
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def query(conn: sqlite3.Connection, sql: str, params: Sequence[Any] = ()) -> list[dict]:
    with _DB_LOCK:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return [dict(r) for r in rows]


def query_one(conn: sqlite3.Connection, sql: str, params: Sequence[Any] = ()) -> dict | None:
    with _DB_LOCK:
        row = conn.execute(sql, tuple(params)).fetchone()
    return dict(row) if row is not None else None


def execute(conn: sqlite3.Connection, sql: str, params: Sequence[Any] = ()) -> None:
    with _DB_LOCK:
        conn.execute(sql, tuple(params))
        conn.commit()
