"""Repository layer over the SQLite tables. Read-mostly; logbook/feedback append.

Repositories return plain dicts (record + ids) so the runtime stays decoupled
from the generation spec. Tools turn these into provenance-bearing results.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from backend.app.data_access import db

_STOPWORDS = {"the", "and", "for", "with", "from", "this", "that", "are", "was",
              "has", "have", "due", "see", "any", "all", "not"}


def _terms(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 3 and w not in _STOPWORDS]


class EquipmentRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def all(self) -> list[dict]:
        return db.query(self.conn, "SELECT * FROM equipment_master ORDER BY equipment_id")

    def get(self, equipment_id: str) -> dict | None:
        return db.query_one(
            self.conn, "SELECT * FROM equipment_master WHERE equipment_id = ?", (equipment_id,)
        )


class SpareRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def all(self) -> list[dict]:
        return db.query(self.conn, "SELECT * FROM spare_parts_master ORDER BY part_id")

    def by_equipment(self, equipment_id: str) -> list[dict]:
        return db.query(
            self.conn, "SELECT * FROM spare_parts_master WHERE equipment_id = ? ORDER BY part_id",
            (equipment_id,),
        )

    def by_part(self, part_id: str) -> dict | None:
        return db.query_one(
            self.conn, "SELECT * FROM spare_parts_master WHERE part_id = ?", (part_id,)
        )


class FaultRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def all(self) -> list[dict]:
        return db.query(self.conn, "SELECT * FROM fault_catalog ORDER BY fault_code")

    def by_code(self, fault_code: str) -> dict | None:
        return db.query_one(
            self.conn, "SELECT * FROM fault_catalog WHERE fault_code = ?", (fault_code,)
        )

    def by_equipment(self, equipment_id: str) -> list[dict]:
        return db.query(
            self.conn, "SELECT * FROM fault_catalog WHERE equipment_id = ? ORDER BY fault_code",
            (equipment_id,),
        )

    def search_symptoms(self, symptoms: str, equipment_id: str | None = None) -> list[dict]:
        """Transparent lexical match over title/meaning/likely_cause.

        Returns matching faults with the matched terms attached (provenance),
        highest overlap first.
        """

        wanted = set(_terms(symptoms))
        if not wanted:
            return []
        candidates = self.by_equipment(equipment_id) if equipment_id else self.all()
        scored: list[dict] = []
        for fault in candidates:
            haystack = " ".join(
                str(fault.get(f, "")) for f in ("title", "meaning", "likely_cause")
            )
            matched = sorted(wanted.intersection(_terms(haystack)))
            if matched:
                scored.append({**fault, "_matched_terms": matched, "_match_score": len(matched)})
        scored.sort(key=lambda f: f["_match_score"], reverse=True)
        return scored


def _filtered(conn, table, equipment_id, since, extra_col=None, extra_val=None, limit=None):
    sql = f"SELECT * FROM {table}"
    clauses, params = [], []
    if equipment_id:
        clauses.append("equipment_id = ?")
        params.append(equipment_id)
    if since:
        clauses.append("date >= ?")
        params.append(since)
    if extra_col and extra_val:
        clauses.append(f"{extra_col} = ?")
        params.append(extra_val)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY date DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return db.query(conn, sql, params)


class HistoryRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def query(self, equipment_id=None, since=None, type=None, limit=None) -> list[dict]:
        return _filtered(self.conn, "maintenance_history", equipment_id, since,
                         extra_col="type", extra_val=type, limit=limit)


class DelayRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def query(self, equipment_id=None, since=None, limit=None) -> list[dict]:
        return _filtered(self.conn, "delay_logs", equipment_id, since, limit=limit)


class IncidentRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def query(self, equipment_id=None, since=None, limit=None) -> list[dict]:
        return _filtered(self.conn, "incident_records", equipment_id, since, limit=limit)


class ProcessRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def by_equipment(self, equipment_id: str | None = None) -> list[dict]:
        if equipment_id:
            return db.query(
                self.conn,
                "SELECT * FROM process_conditions WHERE equipment_id = ? ORDER BY indicator",
                (equipment_id,),
            )
        return db.query(self.conn, "SELECT * FROM process_conditions ORDER BY equipment_id, indicator")


class UserRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def all(self) -> list[dict]:
        return db.query(self.conn, "SELECT * FROM users ORDER BY user_id")

    def get(self, user_id: str) -> dict | None:
        return db.query_one(self.conn, "SELECT * FROM users WHERE user_id = ?", (user_id,))

    def upsert(self, *, user_id: str, name: str, role: str, area: str,
               email: str | None = None) -> str:
        """Insert the user if absent (provisions Microsoft Entra SSO users); returns the id."""
        if self.get(user_id) is None:
            db.execute(
                self.conn,
                "INSERT INTO users (user_id, name, role, area, email, can_write_logbook, "
                "can_acknowledge_alerts) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, name, role, area, email or user_id, 1, 1),
            )
        return user_id


def _next_id(conn, table, id_col, prefix) -> str:
    rows = db.query(conn, f"SELECT {id_col} AS i FROM {table}")
    nums = [int(m.group(1)) for r in rows if (m := re.search(r"(\d+)$", str(r["i"])))]
    return f"{prefix}{(max(nums) + 1) if nums else 1:04d}"


class LogbookRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def query(self, equipment_id: str | None = None, limit: int | None = None) -> list[dict]:
        sql = "SELECT * FROM logbook"
        params: list = []
        if equipment_id:
            sql += " WHERE equipment_id = ?"
            params.append(equipment_id)
        sql += " ORDER BY timestamp DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        return db.query(self.conn, sql, params)

    def has_entry(self, *, equipment_id: str, entry_type: str, timestamp: str) -> bool:
        """True if an entry of this type already exists for this asset at this time.

        Used by the autonomous monitor to avoid logging the same alert event twice.
        """
        row = db.query_one(
            self.conn,
            "SELECT 1 FROM logbook WHERE equipment_id = ? AND entry_type = ? "
            "AND timestamp = ? LIMIT 1",
            (equipment_id, entry_type, timestamp),
        )
        return row is not None

    def append(self, *, equipment_id, author_user_id, entry_type, text,
               related_fault_code, timestamp) -> dict:
        entry_id = _next_id(self.conn, "logbook", "entry_id", "LB-")
        record = {
            "entry_id": entry_id, "timestamp": timestamp, "equipment_id": equipment_id,
            "author_user_id": author_user_id, "entry_type": entry_type, "text": text,
            "related_fault_code": related_fault_code,
        }
        db.execute(
            self.conn,
            "INSERT INTO logbook (entry_id, timestamp, equipment_id, author_user_id, "
            "entry_type, text, related_fault_code) VALUES (?, ?, ?, ?, ?, ?, ?)",
            tuple(record.values()),
        )
        return record


class FeedbackRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def all(self) -> list[dict]:
        return db.query(self.conn, "SELECT * FROM feedback ORDER BY feedback_id")

    def by_targets(self, target_ids: list[str]) -> list[dict]:
        """Feedback whose target_id is any of the given ids (asset id or fault codes)."""

        ids = [t for t in target_ids if t]
        if not ids:
            return []
        placeholders = ",".join("?" * len(ids))
        return db.query(
            self.conn,
            f"SELECT * FROM feedback WHERE target_id IN ({placeholders}) ORDER BY created_at DESC",
            ids,
        )

    def append(self, *, target_type, target_id, feedback_type, rating,
               correction, author_user_id, notes, created_at) -> dict:
        feedback_id = _next_id(self.conn, "feedback", "feedback_id", "FB-")
        record = {
            "feedback_id": feedback_id, "created_at": created_at, "target_type": target_type,
            "target_id": target_id, "feedback_type": feedback_type, "rating": rating,
            "correction": correction, "author_user_id": author_user_id, "notes": notes,
        }
        db.execute(
            self.conn,
            "INSERT INTO feedback (feedback_id, created_at, target_type, target_id, "
            "feedback_type, rating, correction, author_user_id, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            tuple(record.values()),
        )
        return record


@dataclass
class Repositories:
    conn: sqlite3.Connection
    equipment: EquipmentRepo
    spares: SpareRepo
    faults: FaultRepo
    history: HistoryRepo
    delays: DelayRepo
    incidents: IncidentRepo
    process: ProcessRepo
    users: UserRepo
    logbook: LogbookRepo
    feedback: FeedbackRepo


def build_repositories(conn: sqlite3.Connection) -> Repositories:
    return Repositories(
        conn=conn, equipment=EquipmentRepo(conn), spares=SpareRepo(conn), faults=FaultRepo(conn),
        history=HistoryRepo(conn), delays=DelayRepo(conn), incidents=IncidentRepo(conn),
        process=ProcessRepo(conn), users=UserRepo(conn), logbook=LogbookRepo(conn),
        feedback=FeedbackRepo(conn),
    )
