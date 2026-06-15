> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# Data dictionary

Field-level documentation for every artifact in the data substrate. All entries
are generated from the single source of truth
(`backend/scripts/data_substrate/spec.py`), so they always match the data.

## Files

- [Equipment master schema](equipment_master.md)
- [Spare-parts master schema](spare_parts_master.md)
- [Fault catalog schema](fault_catalog.md)
- [Maintenance history schema](maintenance_history.md)
- [Delay logs schema](delay_logs.md)
- [Incident records schema](incident_records.md)
- [Process condition reference schema](process_conditions.md)
- [Coil log schema (Round 1 bridge)](coil_log.md)
- [Users and logbook seed schemas](users_and_logbook.md)
- [Sensor parquet schema and ISO zones](sensors_schema.md)
- [Document set and reference grammar](documents.md)
- [Round 1 real data profile](round1_hotrolling.md)

## Cross-reference map

Coherence across sources is enforced by `validate_coherence.py`. This is the
human-readable mirror of what it checks: which artifacts reference each entity
class, all by stable id.

| Entity class | Defined in | Referenced by |
| --- | --- | --- |
| Asset (`equipment_id`) | `equipment_master.csv` | spares, fault_catalog, maintenance_history, delay_logs, incident_records, process_conditions, coil_log, sensors, manuals, failure reports, logbook |
| Fault code | `fault_catalog.csv` | maintenance_history, incident_records, logbook, manuals, SOPs, failure reports, fault catalog doc |
| Spare part (`part_id`) | `spare_parts_master.csv` | fault_catalog (related_spares), maintenance_history (parts_used), manuals, SOPs, failure reports |
| SOP | `data/raw/documents/sops/` | fault_catalog (related_sops), manuals, failure reports |
| Failure report | `data/raw/documents/failure_reports/` | incident_records (related_failure_report) |
