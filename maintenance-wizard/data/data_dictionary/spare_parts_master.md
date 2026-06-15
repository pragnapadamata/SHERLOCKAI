> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# `spare_parts_master.csv`

**Purpose.** Spare parts mapped to equipment, with stock, availability, and lead time.

**Source class.** programmatic (generate_structured.py)

**Location.** `data/raw/structured/spare_parts_master.csv`

**Rows.** 18

## Schema

| Field | Type | Unit | Nullable | Description |
| --- | --- | --- | --- | --- |
| `part_id` | str | - | no | Spare part identifier (primary key). |
| `description` | str | - | no | Part description. |
| `equipment_id` | str | - | no | Mapped asset (foreign key to equipment_master). |
| `on_hand_qty` | int | ea | no | Quantity on hand. |
| `spare_availability` | str | - | no | in_stock|on_order|none. |
| `procurement_lead_time_weeks` | int | week | no | Procurement lead time. |
| `supplier_code` | str | - | no | Synthetic supplier tag. |
| `unit_cost_inr` | int | INR | no | Synthetic unit cost. |

## Notes

GBX-GEAR-SET-01 (lead 8 weeks, on_order) and BRG-F2-TRB-01 (in_stock) are story-critical.
