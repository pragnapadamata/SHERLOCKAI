"""Profile the real Round 1 hot-rolling data and write its narrative README.

Read-only: this never modifies train.csv or test.csv. It writes a machine-readable
profile to data/processed/round1_profile.json and a human-readable narrative to
data/round1_hotrolling/README.md, both derived from the same computed statistics.
"""

from __future__ import annotations

import json

from backend.scripts.data_substrate import round1, spec


def _readme(profile: dict) -> str:
    pos = profile["target_positives"]
    frac = profile["target_positive_fraction"]
    cols_missing = profile["columns_with_missing_count"]
    total_missing = profile["total_missing_cells_train"]
    sample_ids = ", ".join(profile["sample_positive_coil_ids"])
    return f"""{spec.PROTOTYPE_HEADER}

# Round 1 Hot-Rolling Data (real)

This directory holds Tata Steel's Round 1 "Defect Detection in Hot Rolling"
dataset. It is **real, anonymized data** and is used as the grounding for the
process-defect detection capability (Story C). It is not modified by this
project; the files are read only.

## Shape

- `train.csv`: {profile['train_rows']} rows x {profile['train_cols']} columns =
  `CoilID` + `X1..X49` + `Y`.
- `test.csv`: {profile['test_rows']} rows x {profile['test_cols']} columns =
  `CoilID` + `X1..X49` (no label).

## Features

`X1..X49` are **anonymized continuous process parameters** captured across
multiple rolling stages. The published dataset gives them no per-feature
semantic meaning, so this project does not invent one: they are treated as
real, unlabeled multi-stage process measurements.

## Target

`Y` is the binary **Alpha-defect** label (`1` = defect, `0` = no defect),
present only in `train.csv`. The class is severely imbalanced:
{pos} positive rows ({frac:.2%} of the training set). Defect detection therefore
prioritizes recall; the original challenge metric was
{profile['original_metric']}.

## Missing values

{total_missing} cells are missing across {cols_missing} feature columns in the
training set. Imputation is deferred to Phase 3.

## Narrative mapping

Each `CoilID` is treated as a coil produced through the down-coiler
([[ASSET:HSM-DC-MND]]) in the simulated Hot Strip Mill. Every Coil ID is mapped
into `data/raw/structured/coil_log.csv` with a synthetic production time, grade,
and dimensions. A handful of defect-positive coils (for example {sample_ids})
are referenced from maintenance history and failure report FR-2025-002 to keep
the process-defect story traceable.

## Phase 3 (not done here)

The actual Alpha-defect classifier is trained in Phase 3 and exposed as an agent
tool that returns a defect-risk score (and top contributing features) for an
arbitrary coil's process parameters, evaluated against `test.csv`. Phase 1 only
places, profiles, and narratively binds this data.
"""


def run() -> dict:
    profile = round1.profile()
    spec.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    profile_path = spec.PROCESSED_DIR / "round1_profile.json"
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")

    spec.ROUND1_DIR.mkdir(parents=True, exist_ok=True)
    (spec.ROUND1_DIR / "README.md").write_text(_readme(profile))
    return profile


if __name__ == "__main__":
    p = run()
    print(f"train {p['train_rows']}x{p['train_cols']}, test {p['test_rows']}x{p['test_cols']}")
    print(f"positives {p['target_positives']} ({p['target_positive_fraction']:.2%})")
    print(f"missing {p['total_missing_cells_train']} cells across "
          f"{p['columns_with_missing_count']} columns")
