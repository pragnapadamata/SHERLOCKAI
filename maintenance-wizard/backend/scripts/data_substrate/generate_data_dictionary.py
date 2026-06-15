"""Render the data dictionary from the spec so docs and data cannot drift.

Every structured table, the sensor parquet schema, the document set, and the
Round 1 profile are documented here from the same single source of truth. Field
lists come straight from ``spec.TABLE_SCHEMAS`` and the sensor plans, so a schema
change is reflected automatically.
"""

from __future__ import annotations

from backend.scripts.data_substrate import round1, spec

SOURCE_BY_NAME = {
    "equipment_master": "programmatic (generate_structured.py)",
    "spare_parts_master": "programmatic (generate_structured.py)",
    "fault_catalog": "programmatic (generate_structured.py)",
    "maintenance_history": "programmatic (generate_structured.py)",
    "delay_logs": "programmatic (generate_structured.py)",
    "incident_records": "programmatic (generate_structured.py)",
    "process_conditions": "programmatic (generate_structured.py)",
    "coil_log": "programmatic (generate_structured.py)",
    "users": "programmatic (generate_structured.py)",
    "logbook_seed": "programmatic (generate_structured.py)",
}


def _row_count(filename: str) -> str:
    path = spec.RAW_STRUCTURED / filename
    if not path.exists():
        return "(generated at build time)"
    return str(sum(1 for _ in path.open()) - 1)


def _columns_table(schema: spec.TableSchema) -> str:
    lines = ["| Field | Type | Unit | Nullable | Description |",
             "| --- | --- | --- | --- | --- |"]
    for c in schema.columns:
        lines.append(
            f"| `{c.name}` | {c.dtype} | {c.unit} | {'yes' if c.nullable else 'no'} | {c.description} |"
        )
    return "\n".join(lines)


def _table_md(schema: spec.TableSchema) -> str:
    return f"""{spec.PROTOTYPE_HEADER}

# `{schema.filename}`

**Purpose.** {schema.purpose}

**Source class.** {SOURCE_BY_NAME.get(schema.name, schema.source_class)}

**Location.** `data/raw/structured/{schema.filename}`

**Rows.** {_row_count(schema.filename)}

## Schema

{_columns_table(schema)}

## Notes

{schema.notes}
"""


def _users_and_logbook_md() -> str:
    users = next(t for t in spec.TABLE_SCHEMAS if t.name == "users")
    logbook = next(t for t in spec.TABLE_SCHEMAS if t.name == "logbook_seed")
    return f"""{spec.PROTOTYPE_HEADER}

# `users.csv` and `logbook_seed.csv`

These two tables support the optional role-based-views and digital-logbook
enhancements.

## `users.csv`

**Purpose.** {users.purpose}

**Rows.** {_row_count(users.filename)}

{_columns_table(users)}

**Notes.** {users.notes}

## `logbook_seed.csv`

**Purpose.** {logbook.purpose}

**Rows.** {_row_count(logbook.filename)}

{_columns_table(logbook)}

**Notes.** {logbook.notes}
"""


def _sensors_md() -> str:
    sections = [
        spec.PROTOTYPE_HEADER,
        "\n# Sensor time-series (`data/raw/sensors/*.parquet`)",
        (
            "\n**Source class.** programmatic (generate_sensors.py)\n\n"
            f"**Sampling.** {spec.SENSOR_PERIOD_MINUTES}-minute aggregated features "
            f"({spec.SAMPLES_PER_DAY} samples/day).\n\n"
            f"**Window.** {spec.WINDOW_WEEKS} weeks ending at the simulation anchor "
            f"{spec.SIMULATION_NOW.isoformat()} "
            f"(first sample {spec.window_start().isoformat()}).\n\n"
            "**Common columns.** `timestamp_utc` (datetime), `equipment_id` (str), the "
            "asset-specific channels below, `regime` "
            "(baseline|degrading|alert|action), `anomaly_flag` (bool), `note` (str).\n"
        ),
        (
            "## ISO 10816-3 velocity RMS zones (mm/s)\n\n"
            f"- baseline / good: RMS <= {spec.ISO_RMS_ALERT}\n"
            f"- alert (zone B/C): {spec.ISO_RMS_ALERT} < RMS <= {spec.ISO_RMS_ACTION}\n"
            f"- action (zone C/D): {spec.ISO_RMS_ACTION} < RMS <= {spec.ISO_RMS_DAMAGE}\n"
            f"- damage onset: RMS > {spec.ISO_RMS_DAMAGE}\n\n"
            "`regime` is derived from the primary RMS channel against these "
            "boundaries; `degrading` marks samples in the degradation window that are "
            "still below the alert zone. `anomaly_flag` is true for scripted anomalies "
            "and for any sample in the alert or action zone.\n"
        ),
    ]
    for plan in spec.SENSOR_PLANS:
        asset = spec.ASSETS_BY_ID[plan.equipment_id]
        rows = ["| Channel | Unit | Baseline | Degrades to | Description |",
                "| --- | --- | --- | --- | --- |"]
        for c in plan.channels:
            end = "flat" if c.end_value is None else f"{c.end_value} {c.unit}"
            rows.append(f"| `{c.name}` | {c.unit} | {c.baseline} | {end} | {c.description} |")
        anomalies = "; ".join(
            f"day {a.day}: {a.note}" for a in plan.anomalies
        ) or "none scripted"
        sections.append(
            f"## {plan.equipment_id} - {asset.name}\n\n"
            f"Baseline {plan.baseline_weeks} weeks, degradation {plan.degradation_weeks} weeks. "
            f"Scripted anomalies: {anomalies}.\n\n" + "\n".join(rows) + "\n"
        )
    return "\n".join(sections)


def _documents_md() -> str:
    grammar = "\n".join(
        f"- `[[{k}:id]]` -> {v}" for k, v in spec.REFERENCE_PREFIXES.items()
    )
    rows = ["| Doc id | Type | Title | Path | Required references |",
            "| --- | --- | --- | --- | --- |"]
    for d in spec.DOCS:
        refs = ", ".join(f"`{r}`" for r in d.required_refs)
        if len(refs) > 90:
            refs = refs[:87] + "..."
        rows.append(
            f"| `{d.doc_id}` | {d.doc_type.value} | {d.title} | `{d.rel_path}` | {refs} |"
        )
    return f"""{spec.PROTOTYPE_HEADER}

# Documents (`data/raw/documents/`)

**Source class.** LLM-drafted (generate_documents.py) from spec slices, validated
for cross-reference coherence, then frozen as committed source artifacts.

## Reference grammar

Documents cross-reference entities with machine-checkable tokens that the
validator resolves against the spec:

{grammar}

## Document set

{chr(10).join(rows)}
"""


def _round1_md() -> str:
    profile = round1.profile()
    rows = ["| Column | Mean | Std | Min | Max | Missing |",
            "| --- | --- | --- | --- | --- | --- |"]
    for col, stats in profile["feature_stats"].items():
        rows.append(
            f"| `{col}` | {stats['mean']} | {stats['std']} | {stats['min']} | "
            f"{stats['max']} | {stats['missing']} |"
        )
    return f"""{spec.PROTOTYPE_HEADER}

# Round 1 hot-rolling data (`data/round1_hotrolling/`)

**Source class.** real (Tata Steel Round 1 - Defect Detection in Hot Rolling),
read-only, profiled by profile_round1.py.

- `train.csv`: {profile['train_rows']} x {profile['train_cols']} (`CoilID` + `X1..X49` + `Y`)
- `test.csv`: {profile['test_rows']} x {profile['test_cols']} (`CoilID` + `X1..X49`)
- Target `Y`: {profile['target_positives']} positives
  ({profile['target_positive_fraction']:.2%}); original metric {profile['original_metric']}.
- Missing: {profile['total_missing_cells_train']} cells across
  {profile['columns_with_missing_count']} feature columns.

`X1..X49` are anonymized continuous multi-stage process parameters with no
published per-feature semantics; this project does not invent any. Each `CoilID`
maps to the down-coiler [[ASSET:HSM-DC-MND]] via `coil_log.csv`. See
`data/round1_hotrolling/README.md` for the full narrative and the Phase 3 plan.

## Per-feature statistics (training set)

{chr(10).join(rows)}
"""


def _readme_md() -> str:
    files = [
        ("equipment_master.md", "Equipment master schema"),
        ("spare_parts_master.md", "Spare-parts master schema"),
        ("fault_catalog.md", "Fault catalog schema"),
        ("maintenance_history.md", "Maintenance history schema"),
        ("delay_logs.md", "Delay logs schema"),
        ("incident_records.md", "Incident records schema"),
        ("process_conditions.md", "Process condition reference schema"),
        ("coil_log.md", "Coil log schema (Round 1 bridge)"),
        ("users_and_logbook.md", "Users and logbook seed schemas"),
        ("sensors_schema.md", "Sensor parquet schema and ISO zones"),
        ("documents.md", "Document set and reference grammar"),
        ("round1_hotrolling.md", "Round 1 real data profile"),
    ]
    index = "\n".join(f"- [{desc}]({fn})" for fn, desc in files)
    xref = """| Entity class | Defined in | Referenced by |
| --- | --- | --- |
| Asset (`equipment_id`) | `equipment_master.csv` | spares, fault_catalog, maintenance_history, delay_logs, incident_records, process_conditions, coil_log, sensors, manuals, failure reports, logbook |
| Fault code | `fault_catalog.csv` | maintenance_history, incident_records, logbook, manuals, SOPs, failure reports, fault catalog doc |
| Spare part (`part_id`) | `spare_parts_master.csv` | fault_catalog (related_spares), maintenance_history (parts_used), manuals, SOPs, failure reports |
| SOP | `data/raw/documents/sops/` | fault_catalog (related_sops), manuals, failure reports |
| Failure report | `data/raw/documents/failure_reports/` | incident_records (related_failure_report) |"""
    return f"""{spec.PROTOTYPE_HEADER}

# Data dictionary

Field-level documentation for every artifact in the data substrate. All entries
are generated from the single source of truth
(`backend/scripts/data_substrate/spec.py`), so they always match the data.

## Files

{index}

## Cross-reference map

Coherence across sources is enforced by `validate_coherence.py`. This is the
human-readable mirror of what it checks: which artifacts reference each entity
class, all by stable id.

{xref}
"""


def generate_all() -> list[str]:
    spec.DATA_DICT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    def write(name: str, content: str) -> None:
        (spec.DATA_DICT_DIR / name).write_text(content)
        written.append(name)

    for schema in spec.TABLE_SCHEMAS:
        if schema.name in ("users", "logbook_seed"):
            continue
        write(f"{schema.name}.md", _table_md(schema))

    write("users_and_logbook.md", _users_and_logbook_md())
    write("sensors_schema.md", _sensors_md())
    write("documents.md", _documents_md())
    write("round1_hotrolling.md", _round1_md())
    write("README.md", _readme_md())
    return written


if __name__ == "__main__":
    for name in generate_all():
        print(f"data_dictionary/{name}")
