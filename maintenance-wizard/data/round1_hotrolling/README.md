> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

# Round 1 Hot-Rolling Data (real)

This directory holds Tata Steel's Round 1 "Defect Detection in Hot Rolling"
dataset. It is **real, anonymized data** and is used as the grounding for the
process-defect detection capability (Story C). It is not modified by this
project; the files are read only.

## Shape

- `train.csv`: 1352 rows x 51 columns =
  `CoilID` + `X1..X49` + `Y`.
- `test.csv`: 339 rows x 50 columns =
  `CoilID` + `X1..X49` (no label).

## Features

`X1..X49` are **anonymized continuous process parameters** captured across
multiple rolling stages. The published dataset gives them no per-feature
semantic meaning, so this project does not invent one: they are treated as
real, unlabeled multi-stage process measurements.

## Target

`Y` is the binary **Alpha-defect** label (`1` = defect, `0` = no defect),
present only in `train.csv`. The class is severely imbalanced:
66 positive rows (4.88% of the training set). Defect detection therefore
prioritizes recall; the original challenge metric was
100% recall with >90% precision (recall-prioritized defect detection).

## Missing values

249 cells are missing across 12 feature columns in the
training set. Imputation is deferred to Phase 3.

## Narrative mapping

Each `CoilID` is treated as a coil produced through the down-coiler
([[ASSET:HSM-DC-MND]]) in the simulated Hot Strip Mill. Every Coil ID is mapped
into `data/raw/structured/coil_log.csv` with a synthetic production time, grade,
and dimensions. A handful of defect-positive coils (for example 1015, 1080, 1083, 1110, 1153, 1181, 1182, 126)
are referenced from maintenance history and failure report FR-2025-002 to keep
the process-defect story traceable.

## Phase 3 (not done here)

The actual Alpha-defect classifier is trained in Phase 3 and exposed as an agent
tool that returns a defect-risk score (and top contributing features) for an
arbitrary coil's process parameters, evaluated against `test.csv`. Phase 1 only
places, profiles, and narratively binds this data.
