> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# `maintenance_history.csv`

**Purpose.** Past work orders per asset, including the story-critical anchor events.

**Source class.** programmatic (generate_structured.py)

**Location.** `data/raw/structured/maintenance_history.csv`

**Rows.** 85

## Schema

| Field | Type | Unit | Nullable | Description |
| --- | --- | --- | --- | --- |
| `work_order_id` | str | - | no | Work order id (primary key). |
| `equipment_id` | str | - | no | Asset. |
| `date` | date | - | no | Work order date. |
| `type` | str | - | no | preventive|corrective|inspection|lubrication|oil_sample|alert. |
| `description` | str | - | no | What was done or observed. |
| `technician` | str | - | no | User id of the technician. |
| `fault_code` | str | - | yes | Related fault code, if any. |
| `parts_used` | str | - | yes | Spare part id used, if any. |
| `downtime_min` | int | min | yes | Downtime incurred. |
| `outcome` | str | - | no | Result. |

## Notes

The F2 lubrication schedule deliberately omits the cycle around 2026-04-20 (Story B root cause).
