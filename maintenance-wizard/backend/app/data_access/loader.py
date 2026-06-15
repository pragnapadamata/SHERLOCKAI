"""Load the committed CSVs into a fresh SQLite database.

Deterministic rebuild: the database file is recreated from the CSVs each call.
Ten source tables map 1:1 from CSV (``logbook_seed.csv`` becomes the appendable
``logbook`` table), plus an empty ``feedback`` table for user corrections.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from backend.app.core.config import RAW_STRUCTURED, Settings, get_settings
from backend.app.core.logging import get_logger

log = get_logger(__name__)

# CSV stem -> table name (logbook_seed becomes the appendable logbook table).
TABLE_FILES: dict[str, str] = {
    "equipment_master": "equipment_master.csv",
    "spare_parts_master": "spare_parts_master.csv",
    "fault_catalog": "fault_catalog.csv",
    "maintenance_history": "maintenance_history.csv",
    "delay_logs": "delay_logs.csv",
    "incident_records": "incident_records.csv",
    "process_conditions": "process_conditions.csv",
    "coil_log": "coil_log.csv",
    "users": "users.csv",
    "logbook": "logbook_seed.csv",
}

INDEXES: list[tuple[str, str]] = [
    ("equipment_master", "equipment_id"),
    ("spare_parts_master", "equipment_id"),
    ("spare_parts_master", "part_id"),
    ("fault_catalog", "fault_code"),
    ("fault_catalog", "equipment_id"),
    ("maintenance_history", "equipment_id"),
    ("delay_logs", "equipment_id"),
    ("incident_records", "equipment_id"),
    ("process_conditions", "equipment_id"),
    ("coil_log", "coil_id"),
    ("logbook", "equipment_id"),
]

FEEDBACK_DDL = """
CREATE TABLE feedback (
    feedback_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT,
    feedback_type TEXT NOT NULL,
    rating INTEGER,
    correction TEXT,
    author_user_id TEXT,
    notes TEXT
)
"""


def build_database(
    settings: Settings | None = None,
    *,
    db_path: str | None = None,
    csv_dir: Path | None = None,
) -> dict[str, int]:
    """(Re)build the SQLite database from CSVs. Returns {table: row_count}."""

    settings = settings or get_settings()
    db_file = Path(db_path or settings.sqlite_path)
    csv_dir = csv_dir or RAW_STRUCTURED

    db_file.parent.mkdir(parents=True, exist_ok=True)
    if db_file.exists():
        db_file.unlink()

    counts: dict[str, int] = {}
    conn = sqlite3.connect(db_file)
    try:
        for table, filename in TABLE_FILES.items():
            df = pd.read_csv(csv_dir / filename)
            df.to_sql(table, conn, if_exists="replace", index=False)
            counts[table] = len(df)

        conn.execute(FEEDBACK_DDL)
        counts["feedback"] = 0

        for i, (table, column) in enumerate(INDEXES):
            conn.execute(f"CREATE INDEX idx_{table}_{column}_{i} ON {table}({column})")
        conn.commit()
    finally:
        conn.close()

    log.info("sqlite_built", path=str(db_file), tables=len(counts))
    return counts


if __name__ == "__main__":
    for table, count in build_database().items():
        print(f"{table}: {count} rows")
