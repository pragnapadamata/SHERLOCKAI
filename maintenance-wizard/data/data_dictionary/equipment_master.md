> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# `equipment_master.csv`

**Purpose.** Master record of every monitored and supporting asset with the four prioritization dimensions.

**Source class.** programmatic (generate_structured.py)

**Location.** `data/raw/structured/equipment_master.csv`

**Rows.** 10

## Schema

| Field | Type | Unit | Nullable | Description |
| --- | --- | --- | --- | --- |
| `equipment_id` | str | - | no | Stable asset identifier (primary key). |
| `name` | str | - | no | Human-readable asset name. |
| `area` | str | - | no | Plant area. |
| `type` | str | - | no | Equipment type. |
| `manufacturer_code` | str | - | no | Synthetic OEM tag (OEM-A/B/C). |
| `model_no` | str | - | no | Synthetic model number. |
| `install_date` | date | - | no | Commissioning date. |
| `service_hours` | int | h | no | Hours in service. |
| `mtbf_hours` | int | h | no | Mean time between failures for the family. |
| `monitored` | bool | - | no | True for the three hero assets with sensor data. |
| `process_criticality` | str | - | no | Prioritization: low|medium|high|critical. |
| `typical_delay_severity_min` | int | min | no | Prioritization: typical minutes lost per failure. |
| `spare_availability` | str | - | no | Prioritization: in_stock|on_order|none. |
| `procurement_lead_time_weeks` | int | week | no | Prioritization: spare lead time. |
| `notes` | str | - | no | Engineer note. |

## Notes

The four prioritization dimensions are populated for all ten assets.
