> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# `fault_catalog.csv`

**Purpose.** Canonical fault/error codes with cause, action, and cross-links to SOPs and spares.

**Source class.** programmatic (generate_structured.py)

**Location.** `data/raw/structured/fault_catalog.csv`

**Rows.** 24

## Schema

| Field | Type | Unit | Nullable | Description |
| --- | --- | --- | --- | --- |
| `fault_code` | str | - | no | Fault code (primary key). |
| `equipment_id` | str | - | no | Affected asset. |
| `title` | str | - | no | Short title. |
| `meaning` | str | - | no | What the fault indicates. |
| `likely_cause` | str | - | no | Probable root cause. |
| `recommended_action` | str | - | no | Recommended response. |
| `related_sops` | str | - | no | Semicolon-separated SOP ids. |
| `related_spares` | str | - | no | Semicolon-separated spare part ids. |
| `severity` | str | - | no | low|medium|high|critical. |

## Notes

related_sops and related_spares resolve to SOP documents and spare_parts_master rows.
