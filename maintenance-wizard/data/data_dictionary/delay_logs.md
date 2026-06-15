> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# `delay_logs.csv`

**Purpose.** Equipment delay events supporting delay-severity prioritization.

**Source class.** programmatic (generate_structured.py)

**Location.** `data/raw/structured/delay_logs.csv`

**Rows.** 77

## Schema

| Field | Type | Unit | Nullable | Description |
| --- | --- | --- | --- | --- |
| `delay_id` | str | - | no | Delay id (primary key). |
| `equipment_id` | str | - | no | Asset. |
| `date` | date | - | no | Date of delay. |
| `duration_min` | int | min | no | Delay duration. |
| `category` | str | - | no | mechanical|electrical|hydraulic|process|inspection. |
| `description` | str | - | no | Delay description. |
| `shift` | str | - | no | Shift A|B|C. |

## Notes

Recent F3 inspection delays and F2 alarms are anchor events tied to the hero stories.
