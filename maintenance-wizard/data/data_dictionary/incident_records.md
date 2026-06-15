> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# `incident_records.csv`

**Purpose.** Historical breakdown summaries, cross-linked to failure reports.

**Source class.** programmatic (generate_structured.py)

**Location.** `data/raw/structured/incident_records.csv`

**Rows.** 39

## Schema

| Field | Type | Unit | Nullable | Description |
| --- | --- | --- | --- | --- |
| `incident_id` | str | - | no | Incident id (primary key). |
| `equipment_id` | str | - | no | Asset. |
| `date` | date | - | no | Incident date. |
| `severity` | str | - | no | low|medium|high|critical. |
| `description` | str | - | no | Incident description. |
| `fault_code` | str | - | yes | Related fault code. |
| `resolved` | bool | - | no | Whether resolved. |
| `related_failure_report` | str | - | yes | Related failure report id. |

## Notes

related_failure_report resolves to a document under raw/documents/failure_reports.
