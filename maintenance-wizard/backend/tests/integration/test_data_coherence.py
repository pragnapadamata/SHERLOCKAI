"""Coherence of the committed data substrate.

Runs the cross-reference validator against the committed artifacts and adds
targeted assertions that document the three hero-story coherence guarantees.
Offline: reads files, no network.
"""

from __future__ import annotations

import pandas as pd

from backend.scripts.data_substrate import round1, spec
from backend.scripts.data_substrate.validate_coherence import validate


def _structured(name: str) -> pd.DataFrame:
    filename = next(t.filename for t in spec.TABLE_SCHEMAS if t.name == name)
    return pd.read_csv(spec.RAW_STRUCTURED / filename)


def test_committed_substrate_is_coherent():
    ok, errors = validate()
    assert ok, "coherence errors:\n  - " + "\n  - ".join(errors)


def test_sensor_parquet_shapes():
    expected_rows = spec.WINDOW_WEEKS * 7 * spec.SAMPLES_PER_DAY
    for plan in spec.SENSOR_PLANS:
        df = pd.read_parquet(spec.RAW_SENSORS / f"{plan.equipment_id}_sensors.parquet")
        assert len(df) == expected_rows
        assert "regime" in df.columns and "anomaly_flag" in df.columns


def test_round1_data_is_intact():
    assert round1.load_train().shape == (1352, 51)
    assert round1.load_test().shape == (339, 50)


def test_coil_log_maps_all_round1_coils_to_downcoiler():
    coil = _structured("coil_log")
    assert len(coil) == len(round1.iter_all_coils())
    assert set(coil["assigned_asset_id"].unique()) == {"HSM-DC-MND"}


def test_story_b_lubrication_cycle_is_missing_around_root_cause_date():
    mh = _structured("maintenance_history")
    f2_lube = mh[(mh["equipment_id"] == "HSM-F2-WRB") & (mh["type"] == "lubrication")]
    in_gap = f2_lube[(f2_lube["date"] >= "2026-04-13") & (f2_lube["date"] <= "2026-04-27")]
    assert len(in_gap) == 0  # the missed cycle is Story B's documented root cause


def test_story_c_positive_coils_match_round1():
    coil = _structured("coil_log")
    assert int((coil["alpha_label"] == 1).sum()) == len(round1.positive_coil_ids())
