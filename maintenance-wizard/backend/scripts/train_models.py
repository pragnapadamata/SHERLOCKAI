"""Train and persist the Phase 3 ML artifacts under models/ (gitignored).

Deterministic (fixed seed). RUL needs no artifact (fit at query time).

    uv run python -m backend.scripts.train_models
"""

from __future__ import annotations

from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.ml.alpha_defect import train_alpha_model
from backend.app.ml.anomaly import train_anomaly_models


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, dev=settings.app_env != "prod")

    print("== anomaly models (baseline + IsolationForest per asset) ==")
    trained = train_anomaly_models(models_dir=settings.models_dir)
    print(f"  trained: {trained}")

    print("== alpha-defect classifier (HistGradientBoosting + CV) ==")
    metrics = train_alpha_model(models_dir=settings.models_dir)
    print(f"  ROC-AUC {metrics['roc_auc']} | PR-AUC {metrics['pr_auc']}")
    print(f"  threshold {metrics['threshold']} (target recall {metrics['target_recall']})")
    print(f"  recall {metrics['recall_at_threshold']} @ precision {metrics['precision_at_threshold']} "
          f"on {metrics['n_positives']}/{metrics['n_total']} positives")


if __name__ == "__main__":
    main()
