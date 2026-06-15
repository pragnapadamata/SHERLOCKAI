> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# `process_conditions.csv`

**Purpose.** Reference normal/alert/action operating values per asset indicator.

**Source class.** programmatic (generate_structured.py)

**Location.** `data/raw/structured/process_conditions.csv`

**Rows.** 14

## Schema

| Field | Type | Unit | Nullable | Description |
| --- | --- | --- | --- | --- |
| `equipment_id` | str | - | no | Asset. |
| `indicator` | str | - | no | Condition indicator name. |
| `nominal_value` | float | varies | no | Normal operating value. |
| `alert_value` | float | varies | no | Alert threshold. |
| `action_value` | float | varies | no | Action threshold. |
| `unit` | str | - | no | Unit of measure. |
| `reference` | str | - | no | Source of the threshold. |

## Notes

Vibration thresholds follow ISO 10816-3; others follow synthetic OEM manuals.
