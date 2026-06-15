> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# `users.csv` and `logbook_seed.csv`

These two tables support the optional role-based-views and digital-logbook
enhancements.

## `users.csv`

**Purpose.** Role metadata for later role-based views and logbook permissions.

**Rows.** 7

| Field | Type | Unit | Nullable | Description |
| --- | --- | --- | --- | --- |
| `user_id` | str | - | no | User id (primary key). |
| `name` | str | - | no | Display name. |
| `role` | str | - | no | engineer|supervisor|plant_manager|analyst. |
| `area` | str | - | no | Area of responsibility. |
| `email` | str | - | no | Synthetic contact. |
| `can_write_logbook` | bool | - | no | Logbook write permission. |
| `can_acknowledge_alerts` | bool | - | no | Alert acknowledge permission. |

**Notes.** Two engineers, two supervisors, one plant manager, one read-only analyst, and one autonomous system user (U-SYS-AMDC) for machine-generated entries.

## `logbook_seed.csv`

**Purpose.** Pre-populated digital logbook entries seeding the optional logbook enhancement.

**Rows.** 15

| Field | Type | Unit | Nullable | Description |
| --- | --- | --- | --- | --- |
| `entry_id` | str | - | no | Entry id (primary key). |
| `timestamp` | datetime | - | no | Entry timestamp. |
| `equipment_id` | str | - | no | Asset. |
| `author_user_id` | str | - | no | Author (foreign key to users). |
| `entry_type` | str | - | no | observation|action|confirmation. |
| `text` | str | - | no | Entry text. |
| `related_fault_code` | str | - | yes | Related fault code, if any. |

**Notes.** Entries reference the hero stories and the same fault codes used elsewhere.
