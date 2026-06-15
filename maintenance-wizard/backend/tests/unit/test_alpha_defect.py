"""Alpha defect classifier: CV metrics, recall target, top drivers (offline)."""

from __future__ import annotations

import pandas as pd

from backend.app.core.config import ROUND1_DIR


def _a_positive_coil_id() -> str:
    train = pd.read_csv(ROUND1_DIR / "train.csv")
    return str(train.loc[train["Y"] == 1, "CoilID"].iloc[0])


def test_cv_metrics_present_and_recall_target_met(alpha_model):
    result = alpha_model.predict(coil_id=_a_positive_coil_id())
    m = result.cv_metrics
    assert m["model"] == "HistGradientBoostingClassifier"
    assert m["roc_auc"] > 0.6  # real discriminative signal, not random
    assert m["recall_at_threshold"] >= m["target_recall"] - 1e-9
    assert 0.0 <= m["precision_at_threshold"] <= 1.0  # reported honestly, not claimed
    assert m["n_positives"] == 66


def test_predicts_known_coil_with_drivers(alpha_model):
    coil_id = _a_positive_coil_id()
    result = alpha_model.predict(coil_id=coil_id)
    assert result.coil_id == coil_id
    assert 0.0 <= result.risk_score <= 1.0
    assert len(result.top_driver_features) >= 3
    assert all(d["feature"].startswith("X") for d in result.top_driver_features)


def test_unknown_coil_raises(alpha_model):
    import pytest

    with pytest.raises(KeyError):
        alpha_model.predict(coil_id="NOT-A-COIL")


def test_explicit_features_accepted(alpha_model):
    result = alpha_model.predict(coil_features={"X1": 0.5, "X2": 0.5})
    assert 0.0 <= result.risk_score <= 1.0  # missing features handled natively
