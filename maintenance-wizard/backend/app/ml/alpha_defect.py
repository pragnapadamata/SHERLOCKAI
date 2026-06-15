"""Alpha process-defect classifier trained on the real Round 1 hot-rolling data.

HistGradientBoostingClassifier (native missing-value handling) with
class_weight="balanced" for the ~4.88% imbalance, evaluated by StratifiedKFold CV
on train.csv, with the decision threshold tuned for a target recall. Top drivers
come from permutation importance. The X-features stay honestly unlabeled; test.csv
has no labels, so it is for prediction only -- we report CV metrics, never a test
score.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from backend.app.core.config import ROUND1_DIR, get_settings
from backend.app.core.logging import get_logger

log = get_logger(__name__)

FEATURE_COLS = [f"X{i}" for i in range(1, 50)]
ID_COL = "CoilID"
TARGET_COL = "Y"


@dataclass
class AlphaResult:
    coil_id: str | None
    risk_score: float
    risk_label: bool
    threshold: float
    top_driver_features: list[dict] = field(default_factory=list)
    cv_metrics: dict = field(default_factory=dict)
    note: str = ""


def _select_threshold(precision, recall, thresholds, target_recall: float):
    best = None
    for i in range(len(thresholds)):
        if recall[i] >= target_recall and (best is None or precision[i] > best[2]):
            best = (float(thresholds[i]), float(recall[i]), float(precision[i]))
    if best is None:  # target unreachable -> take the max-recall operating point
        i = int(np.argmax(recall[:-1]))
        best = (float(thresholds[i]), float(recall[i]), float(precision[i]))
    return best


def train_alpha_model(models_dir: str | Path | None = None, round1_dir: Path | None = None,
                      seed: int | None = None, target_recall: float | None = None) -> dict:
    import joblib
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.inspection import permutation_importance
    from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict

    settings = get_settings()
    seed = seed if seed is not None else settings.random_seed
    target_recall = target_recall if target_recall is not None else settings.alpha_target_recall
    round1_dir = round1_dir or ROUND1_DIR
    out_dir = Path(models_dir or settings.models_dir) / "alpha_defect"
    out_dir.mkdir(parents=True, exist_ok=True)

    train = pd.read_csv(round1_dir / "train.csv")
    X = train[FEATURE_COLS]
    y = train[TARGET_COL].astype(int).to_numpy()

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    est = HistGradientBoostingClassifier(class_weight="balanced", random_state=seed)
    oof = cross_val_predict(est, X, y, cv=skf, method="predict_proba")[:, 1]

    roc = float(roc_auc_score(y, oof))
    ap = float(average_precision_score(y, oof))
    precision, recall, thresholds = precision_recall_curve(y, oof)
    threshold, recall_at, precision_at = _select_threshold(precision, recall, thresholds, target_recall)

    final = HistGradientBoostingClassifier(class_weight="balanced", random_state=seed).fit(X, y)
    pi = permutation_importance(final, X, y, n_repeats=5, random_state=seed, scoring="average_precision")
    importances = sorted(
        ({"feature": c, "importance": round(float(m), 5)}
         for c, m in zip(FEATURE_COLS, pi.importances_mean, strict=True)),
        key=lambda d: d["importance"], reverse=True,
    )

    metrics = {
        "model": "HistGradientBoostingClassifier",
        "cv": "StratifiedKFold(5, shuffle=True)",
        "roc_auc": round(roc, 4),
        "pr_auc": round(ap, 4),
        "n_total": int(len(y)),
        "n_positives": int(y.sum()),
        "positive_fraction": round(float(y.mean()), 5),
        "target_recall": target_recall,
        "threshold": round(threshold, 6),
        "recall_at_threshold": round(recall_at, 4),
        "precision_at_threshold": round(precision_at, 4),
    }

    joblib.dump(final, out_dir / "model.joblib")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (out_dir / "importances.json").write_text(json.dumps(importances, indent=2) + "\n")
    log.info("alpha_model_trained", roc_auc=metrics["roc_auc"],
             recall=metrics["recall_at_threshold"], precision=metrics["precision_at_threshold"])
    return metrics


class AlphaDefectModel:
    def __init__(self, models_dir: str | Path | None = None, round1_dir: Path | None = None) -> None:
        settings = get_settings()
        self._dir = Path(models_dir or settings.models_dir) / "alpha_defect"
        self._round1_dir = round1_dir or ROUND1_DIR
        self._model = None
        self._metrics: dict = {}
        self._importances: list[dict] = []
        self._lookup: dict[str, dict] | None = None

    def available(self) -> bool:
        return (self._dir / "model.joblib").exists()

    def _load(self) -> None:
        if self._model is None:
            import joblib

            self._model = joblib.load(self._dir / "model.joblib")
            self._metrics = json.loads((self._dir / "metrics.json").read_text())
            self._importances = json.loads((self._dir / "importances.json").read_text())

    def _coil_lookup(self) -> dict[str, dict]:
        if self._lookup is None:
            frames = []
            for name in ("train.csv", "test.csv"):
                path = self._round1_dir / name
                if path.exists():
                    frames.append(pd.read_csv(path))
            combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
            # Use column-level access: iterrows() would upcast the int CoilID to float.
            ids = combined[ID_COL].astype(str).tolist() if len(combined) else []
            records = combined[FEATURE_COLS].to_dict("records") if len(combined) else []
            self._lookup = dict(zip(ids, records, strict=True))
        return self._lookup

    def predict(self, coil_id: str | None = None, coil_features: dict | None = None) -> AlphaResult:
        self._load()
        if coil_features is not None:
            features = {c: coil_features.get(c, np.nan) for c in FEATURE_COLS}
        elif coil_id is not None:
            found = self._coil_lookup().get(str(coil_id))
            if found is None:
                raise KeyError(f"Coil {coil_id} not found in Round 1 data.")
            features = found
        else:
            raise ValueError("Provide coil_id or coil_features.")

        row = pd.DataFrame([[float(features[c]) if pd.notna(features[c]) else np.nan
                             for c in FEATURE_COLS]], columns=FEATURE_COLS)
        proba = float(self._model.predict_proba(row)[0, 1])
        threshold = float(self._metrics["threshold"])

        top = []
        for imp in self._importances[:6]:
            value = features.get(imp["feature"])
            top.append({
                "feature": imp["feature"],
                "importance": imp["importance"],
                "value": (None if value is None or pd.isna(value) else round(float(value), 4)),
            })

        return AlphaResult(
            coil_id=str(coil_id) if coil_id is not None else None,
            risk_score=round(proba, 4),
            risk_label=proba >= threshold,
            threshold=round(threshold, 4),
            top_driver_features=top,
            cv_metrics=self._metrics,
            note="X1..X49 are real anonymized multi-stage process parameters (no published "
                 "semantics). Metrics are StratifiedKFold CV on train.csv; test.csv is unlabeled.",
        )
