> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# `coil_log.csv`

**Purpose.** Maps every Round 1 CoilID to the down-coiler and binds it into the plant narrative.

**Source class.** programmatic (generate_structured.py)

**Location.** `data/raw/structured/coil_log.csv`

**Rows.** 1691

## Schema

| Field | Type | Unit | Nullable | Description |
| --- | --- | --- | --- | --- |
| `coil_id` | str | - | no | Round 1 CoilID (primary key). |
| `source` | str | - | no | Round 1 split: train|test. |
| `produced_at` | datetime | - | no | Synthetic production timestamp. |
| `assigned_asset_id` | str | - | no | Always HSM-DC-MND. |
| `grade` | str | - | no | Synthetic steel grade. |
| `thickness_mm` | float | mm | no | Synthetic coil thickness. |
| `width_mm` | float | mm | no | Synthetic coil width. |
| `alpha_label` | int | - | yes | Round 1 Y (1=defect, 0=no defect); null for test split. |
| `alpha_risk_score` | float | - | yes | Populated by the Phase 3 model; null here. |

## Notes

All 1,691 CoilIDs (1,352 train + 339 test) are mapped. alpha_label comes from real Round 1 Y.
