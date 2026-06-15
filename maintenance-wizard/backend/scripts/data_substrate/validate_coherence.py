"""Cross-reference coherence validator -- the correctness gate for the substrate.

Loads the spec and every generated artifact and checks that they agree: column
schemas match, foreign keys resolve, documents contain their required references
and only resolvable tokens, sensor parquet shapes are correct, the Round 1 data
is intact, and the hero stories line up across sources. Exits 0 if everything is
coherent, 1 otherwise, printing a precise report.
"""

from __future__ import annotations

import sys

import pandas as pd

from backend.scripts.data_substrate import generate_documents, round1, spec

SCHEMAS_BY_NAME = {t.name: t for t in spec.TABLE_SCHEMAS}


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(spec.RAW_STRUCTURED / SCHEMAS_BY_NAME[name].filename)


def _isval(v) -> bool:
    return v is not None and not (isinstance(v, float) and pd.isna(v)) and str(v) != "nan"


def _check_columns(errors: list[str]) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for name, schema in SCHEMAS_BY_NAME.items():
        path = spec.RAW_STRUCTURED / schema.filename
        if not path.exists():
            errors.append(f"[schema] missing file {schema.filename}")
            continue
        df = pd.read_csv(path)
        frames[name] = df
        expected = [c.name for c in schema.columns]
        if list(df.columns) != expected:
            errors.append(
                f"[schema] {schema.filename} columns {list(df.columns)} != documented {expected}"
            )
    return frames


def _check_foreign_keys(frames: dict[str, pd.DataFrame], errors: list[str]) -> None:
    asset_ids = set(spec.ASSETS_BY_ID)
    spare_ids = set(spec.SPARES_BY_ID)
    fault_ids = set(spec.FAULTS_BY_CODE)
    user_ids = {u.user_id for u in spec.USERS}

    def fk(name: str, col: str, valid: set, *, nullable: bool = False) -> None:
        if name not in frames:
            return
        for v in frames[name][col].tolist():
            if not _isval(v):
                if not nullable:
                    errors.append(f"[fk] {name}.{col} has empty non-nullable value")
                continue
            if str(v) not in valid:
                errors.append(f"[fk] {name}.{col} value {v!r} not found")

    fk("spare_parts_master", "equipment_id", asset_ids)
    fk("fault_catalog", "equipment_id", asset_ids)
    fk("maintenance_history", "equipment_id", asset_ids)
    fk("maintenance_history", "technician", user_ids)
    fk("maintenance_history", "fault_code", fault_ids, nullable=True)
    fk("maintenance_history", "parts_used", spare_ids | {"GREASE-EP2-DRUM"}, nullable=True)
    fk("delay_logs", "equipment_id", asset_ids)
    fk("incident_records", "equipment_id", asset_ids)
    fk("incident_records", "fault_code", fault_ids, nullable=True)
    fk("incident_records", "related_failure_report", spec.FAILURE_REPORT_IDS, nullable=True)
    fk("process_conditions", "equipment_id", asset_ids)
    fk("coil_log", "assigned_asset_id", asset_ids)
    fk("logbook_seed", "equipment_id", asset_ids)
    fk("logbook_seed", "author_user_id", user_ids)
    fk("logbook_seed", "related_fault_code", fault_ids, nullable=True)

    # fault_catalog list columns resolve
    if "fault_catalog" in frames:
        fc = frames["fault_catalog"]
        for _, row in fc.iterrows():
            for sop in str(row["related_sops"]).split(";"):
                if sop and sop not in spec.SOP_IDS:
                    errors.append(f"[fk] fault {row['fault_code']} related SOP {sop} unknown")
            for part in str(row["related_spares"]).split(";"):
                if part and part not in spare_ids:
                    errors.append(f"[fk] fault {row['fault_code']} related spare {part} unknown")


def _check_documents(errors: list[str]) -> None:
    for doc in spec.DOCS:
        path = spec.RAW_DOCS / doc.rel_path
        if not path.exists():
            errors.append(f"[doc] missing {doc.rel_path}")
            continue
        text = path.read_text()
        if spec.PROTOTYPE_HEADER not in text:
            errors.append(f"[doc] {doc.doc_id} missing prototype header")
        for problem in generate_documents._check(doc, text):
            errors.append(f"[doc] {doc.doc_id}: {problem}")


def _check_sensors(errors: list[str]) -> None:
    expected_rows = spec.WINDOW_WEEKS * 7 * spec.SAMPLES_PER_DAY
    for plan in spec.SENSOR_PLANS:
        path = spec.RAW_SENSORS / f"{plan.equipment_id}_sensors.parquet"
        if not path.exists():
            errors.append(f"[sensor] missing {path.name}")
            continue
        df = pd.read_parquet(path)
        expected_cols = (
            ["timestamp_utc", "equipment_id"]
            + [c.name for c in plan.channels]
            + ["regime", "anomaly_flag", "note"]
        )
        if list(df.columns) != expected_cols:
            errors.append(f"[sensor] {path.name} columns {list(df.columns)} != {expected_cols}")
        if len(df) != expected_rows:
            errors.append(f"[sensor] {path.name} has {len(df)} rows, expected {expected_rows}")


def _check_round1(errors: list[str]) -> None:
    train, test = round1.load_train(), round1.load_test()
    if train.shape != (1352, 51):
        errors.append(f"[round1] train shape {train.shape} != (1352, 51)")
    if test.shape != (339, 50):
        errors.append(f"[round1] test shape {test.shape} != (339, 50)")
    if not (spec.PROCESSED_DIR / "round1_profile.json").exists():
        errors.append("[round1] missing processed/round1_profile.json")
    if not (spec.ROUND1_DIR / "README.md").exists():
        errors.append("[round1] missing round1_hotrolling/README.md")


def _check_stories(frames: dict[str, pd.DataFrame], errors: list[str]) -> None:
    # Story A: F3 gear set lead time = 8 weeks, agreeing across sources.
    gear = spec.SPARES_BY_ID["GBX-GEAR-SET-01"]
    if gear.procurement_lead_time_weeks != 8:
        errors.append("[story A] GBX-GEAR-SET-01 lead time != 8 weeks")
    if spec.ASSETS_BY_ID["HSM-F3-GBX"].procurement_lead_time_weeks != 8:
        errors.append("[story A] HSM-F3-GBX lead time != 8 weeks")
    if "GBX-GEAR-SET-01" not in spec.FAULTS_BY_CODE["F3-GBX-002"].related_spares:
        errors.append("[story A] fault F3-GBX-002 does not reference GBX-GEAR-SET-01")
    fr_a = (spec.RAW_DOCS / "failure_reports/FR-2024-002_F3_gear_pitting_fracture.md")
    if fr_a.exists():
        t = fr_a.read_text()
        if "[[PART:GBX-GEAR-SET-01]]" not in t or "[[FAULT:F3-GBX-002]]" not in t:
            errors.append("[story A] FR-2024-002 missing gear-set or fault reference")

    # Story B: F2 bearing in stock, lead 2; lubrication cycle around 2026-04-20 omitted.
    brg = spec.SPARES_BY_ID["BRG-F2-TRB-01"]
    if not (brg.spare_availability.value == "in_stock" and brg.procurement_lead_time_weeks == 2):
        errors.append("[story B] BRG-F2-TRB-01 not in_stock @ 2 weeks")
    if "maintenance_history" in frames:
        mh = frames["maintenance_history"]
        f2_lube = mh[(mh["equipment_id"] == "HSM-F2-WRB") & (mh["type"] == "lubrication")]
        in_gap = f2_lube[(f2_lube["date"] >= "2026-04-13") & (f2_lube["date"] <= "2026-04-27")]
        if len(in_gap) != 0:
            errors.append("[story B] expected missing F2 lubrication cycle around 2026-04-20, found one")

    # Story C: coil_log defect-positive count equals Round 1 positives.
    if "coil_log" in frames:
        positives = int((frames["coil_log"]["alpha_label"] == 1).sum())
        expected = len(round1.positive_coil_ids())
        if positives != expected:
            errors.append(f"[story C] coil_log positives {positives} != Round 1 {expected}")
        if len(frames["coil_log"]) != len(round1.iter_all_coils()):
            errors.append("[story C] coil_log row count != total Round 1 coils")


def validate() -> tuple[bool, list[str]]:
    errors: list[str] = []
    frames = _check_columns(errors)
    _check_foreign_keys(frames, errors)
    _check_documents(errors)
    _check_sensors(errors)
    _check_round1(errors)
    _check_stories(frames, errors)
    return (not errors), errors


def main() -> int:
    ok, errors = validate()
    if ok:
        print("coherence validation: PASS")
        return 0
    print(f"coherence validation: FAIL ({len(errors)} problems)")
    for e in errors:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
