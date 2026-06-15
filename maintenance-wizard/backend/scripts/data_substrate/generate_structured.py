"""Generate the structured CSVs from the spec. Deterministic and reproducible.

Story-critical rows live in the spec as anchor events; this module renders them
and adds plausible routine filler around them with a fixed-seed RNG. The F2
lubrication schedule deliberately omits the cycle around 2026-04-20, which is the
documented root cause of Story B.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from backend.scripts.data_substrate import round1, spec

SCHEMAS_BY_NAME = {t.name: t for t in spec.TABLE_SCHEMAS}

GRADES = ["HRC-IS2062-E250", "HRC-IS2062-E350", "API-5L-X52", "SAE-1006", "SAE-1018"]
TECHS = [u.user_id for u in spec.USERS if u.role.value in ("engineer", "supervisor")]


def _write(df: pd.DataFrame, name: str) -> int:
    """Reorder columns to the documented schema and write a CSV. Returns row count."""

    schema = SCHEMAS_BY_NAME[name]
    columns = [c.name for c in schema.columns]
    missing = set(columns) - set(df.columns)
    extra = set(df.columns) - set(columns)
    if missing or extra:
        raise ValueError(f"{name}: column mismatch (missing={missing}, extra={extra})")
    df = df[columns]
    spec.RAW_STRUCTURED.mkdir(parents=True, exist_ok=True)
    df.to_csv(spec.RAW_STRUCTURED / schema.filename, index=False)
    return len(df)


def _models_to_frame(models) -> pd.DataFrame:
    return pd.DataFrame([m.model_dump(mode="json") for m in models])


def gen_equipment_master() -> int:
    return _write(_models_to_frame(spec.ASSETS), "equipment_master")


def gen_spare_parts_master() -> int:
    return _write(_models_to_frame(spec.SPARES), "spare_parts_master")


def gen_fault_catalog() -> int:
    rows = []
    for f in spec.FAULTS:
        d = f.model_dump(mode="json")
        d["related_sops"] = ";".join(f.related_sops)
        d["related_spares"] = ";".join(f.related_spares)
        rows.append(d)
    return _write(pd.DataFrame(rows), "fault_catalog")


def gen_process_conditions() -> int:
    return _write(_models_to_frame(spec.PROCESS_INDICATORS), "process_conditions")


def gen_users() -> int:
    return _write(_models_to_frame(spec.USERS), "users")


def gen_logbook_seed() -> int:
    return _write(_models_to_frame(spec.LOGBOOK_SEED), "logbook_seed")


def gen_maintenance_history() -> int:
    rng = np.random.default_rng(spec.RANDOM_SEED)
    rows = [h.model_dump(mode="json") for h in spec.ANCHOR_HISTORY]

    seq = 1

    def wo() -> str:
        nonlocal seq
        wid = f"WO-GEN-{seq:04d}"
        seq += 1
        return wid

    # F2 lubrication schedule every 14 days, skipping the cycle around 2026-04-20.
    start = spec.window_start().date()
    missed_lo = datetime(2026, 4, 13).date()
    missed_hi = datetime(2026, 4, 27).date()
    day = start
    while day <= spec.SIMULATION_NOW.date():
        if not (missed_lo <= day <= missed_hi):
            rows.append({
                "work_order_id": wo(), "equipment_id": "HSM-F2-WRB", "date": day.isoformat(),
                "type": "lubrication", "description": "Scheduled work-roll bearing lubrication.",
                "technician": "U-ENG-01", "fault_code": None,
                "parts_used": "GREASE-EP2-DRUM", "downtime_min": 0, "outcome": "completed",
            })
        day = day + timedelta(days=14)

    # Routine preventive / inspection / oil_sample entries per asset across ~12 months.
    routine_types = ["preventive", "inspection", "oil_sample"]
    for asset in spec.ASSETS:
        n = 8 if asset.monitored else 6
        for k in range(n):
            offset = int(rng.integers(20, 360))
            d = (spec.SIMULATION_NOW - timedelta(days=offset)).date()
            rtype = routine_types[k % len(routine_types)]
            tech = TECHS[int(rng.integers(0, len(TECHS)))]
            rows.append({
                "work_order_id": wo(), "equipment_id": asset.equipment_id, "date": d.isoformat(),
                "type": rtype, "description": f"Routine {rtype.replace('_', ' ')} on {asset.name}.",
                "technician": tech, "fault_code": None, "parts_used": None,
                "downtime_min": 0, "outcome": "normal",
            })

    # Down-coiler investigations citing real defect-positive Coil IDs.
    for cid in round1.positive_coil_ids(3):
        rows.append({
            "work_order_id": wo(), "equipment_id": "HSM-DC-MND",
            "date": (spec.SIMULATION_NOW - timedelta(days=25)).date().isoformat(),
            "type": "inspection",
            "description": f"Coil quality investigation for Alpha-defect coil {cid}.",
            "technician": "U-ENG-02", "fault_code": "DC-PROC-001", "parts_used": None,
            "downtime_min": 0, "outcome": "logged for Phase 3 defect-risk analysis",
        })

    df = pd.DataFrame(rows).sort_values(["equipment_id", "date", "work_order_id"]).reset_index(drop=True)
    return _write(df, "maintenance_history")


def gen_delay_logs() -> int:
    rng = np.random.default_rng(spec.RANDOM_SEED + 1)
    rows = [d.model_dump(mode="json") for d in spec.ANCHOR_DELAYS]
    categories = ["mechanical", "electrical", "hydraulic", "process", "inspection"]
    shifts = ["A", "B", "C"]
    seq = 1
    for asset in spec.ASSETS:
        n = 10 if asset.monitored else 6
        for _ in range(n):
            offset = int(rng.integers(5, 200))
            d = (spec.SIMULATION_NOW - timedelta(days=offset)).date()
            cat = categories[int(rng.integers(0, len(categories)))]
            dur = int(rng.integers(5, 90))
            rows.append({
                "delay_id": f"DL-GEN-{seq:04d}", "equipment_id": asset.equipment_id,
                "date": d.isoformat(), "duration_min": dur, "category": cat,
                "description": f"{cat.capitalize()} delay on {asset.name}.",
                "shift": shifts[int(rng.integers(0, 3))],
            })
            seq += 1
    df = pd.DataFrame(rows).sort_values(["equipment_id", "date", "delay_id"]).reset_index(drop=True)
    return _write(df, "delay_logs")


def gen_incident_records() -> int:
    rng = np.random.default_rng(spec.RANDOM_SEED + 2)
    rows = [i.model_dump(mode="json") for i in spec.ANCHOR_INCIDENTS]
    severities = ["low", "medium", "high"]
    seq = 1
    for asset in spec.ASSETS:
        n = 4 if asset.monitored else 3
        for _ in range(n):
            offset = int(rng.integers(30, 700))
            d = (spec.SIMULATION_NOW - timedelta(days=offset)).date()
            sev = severities[int(rng.integers(0, len(severities)))]
            rows.append({
                "incident_id": f"INC-GEN-{seq:04d}", "equipment_id": asset.equipment_id,
                "date": d.isoformat(), "severity": sev,
                "description": f"{sev.capitalize()} breakdown summary for {asset.name}.",
                "fault_code": None, "resolved": True, "related_failure_report": None,
            })
            seq += 1
    df = pd.DataFrame(rows).sort_values(["equipment_id", "date", "incident_id"]).reset_index(drop=True)
    return _write(df, "incident_records")


def gen_coil_log() -> int:
    rng = np.random.default_rng(spec.RANDOM_SEED + 3)
    train = round1.load_train()
    label_by_id = {
        str(c): int(y)
        for c, y in zip(train[round1.ID_COL], train[round1.TARGET_COL], strict=True)
    }

    coils = round1.iter_all_coils()
    n = len(coils)
    span = timedelta(days=90)
    rows = []
    for idx, (cid, source) in enumerate(coils):
        produced = spec.SIMULATION_NOW - span + timedelta(seconds=int(idx * span.total_seconds() / n))
        rows.append({
            "coil_id": cid,
            "source": source,
            "produced_at": produced.replace(microsecond=0).isoformat(),
            "assigned_asset_id": "HSM-DC-MND",
            "grade": GRADES[int(rng.integers(0, len(GRADES)))],
            "thickness_mm": round(float(rng.uniform(1.8, 12.0)), 2),
            "width_mm": round(float(rng.uniform(900, 1550)), 1),
            "alpha_label": label_by_id.get(cid),
            "alpha_risk_score": None,
        })
    df = pd.DataFrame(rows)
    df["alpha_label"] = df["alpha_label"].astype("Int64")
    df["alpha_risk_score"] = df["alpha_risk_score"].astype("Float64")
    return _write(df, "coil_log")


GENERATORS = [
    gen_equipment_master, gen_spare_parts_master, gen_fault_catalog,
    gen_maintenance_history, gen_delay_logs, gen_incident_records,
    gen_process_conditions, gen_coil_log, gen_users, gen_logbook_seed,
]


def generate_all() -> dict[str, int]:
    counts: dict[str, int] = {}
    for gen in GENERATORS:
        name = gen.__name__.removeprefix("gen_")
        counts[name] = gen()
    return counts


if __name__ == "__main__":
    for name, count in generate_all().items():
        print(f"{name}: {count} rows")
