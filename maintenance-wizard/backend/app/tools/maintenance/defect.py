"""assess_alpha_defect_risk -- Round 1 process-defect classifier as a tool."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, ClassVar

from backend.app.ml.alpha_defect import AlphaDefectModel
from backend.app.tools.results import DataTool, ExpectedToolError, SourceRef, ToolResult


class AssessAlphaDefectRiskTool(DataTool):
    name: ClassVar[str] = "assess_alpha_defect_risk"
    description: ClassVar[str] = (
        "Assess Alpha surface-defect risk for a coil using the classifier trained on "
        "the real Round 1 hot-rolling data. Provide a coil_id (resolved from the Round 1 "
        "data) or an explicit coil_features map of X1..X49. Returns a risk score, the "
        "top driver features, and the model's cross-validated metrics. X-features are "
        "anonymized; metrics are CV on train.csv (test.csv is unlabeled)."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "coil_id": {"type": "string", "description": "A Round 1 CoilID."},
            "coil_features": {"type": "object", "description": "Map of X1..X49 to numeric values."},
        },
        "additionalProperties": False,
    }

    def __init__(self, model: AlphaDefectModel) -> None:
        self._model = model

    def execute(self, coil_id: str | None = None, coil_features: dict | None = None) -> ToolResult:
        if not self._model.available():
            raise ExpectedToolError("Alpha-defect model is not trained; run train_models.")
        if coil_id is None and coil_features is None:
            raise ExpectedToolError("Provide coil_id or coil_features.")
        try:
            result = self._model.predict(coil_id=coil_id, coil_features=coil_features)
        except KeyError as exc:
            raise ExpectedToolError(str(exc)) from exc

        drivers = [d["feature"] for d in result.top_driver_features]
        m = result.cv_metrics
        sources = [
            SourceRef.computation(
                method=f"{m.get('cv')} on train.csv; threshold tuned for recall>={m.get('target_recall')}",
                model=m.get("model"), drivers=drivers,
                detail=f"CV ROC-AUC {m.get('roc_auc')}, PR-AUC {m.get('pr_auc')}, "
                       f"recall {m.get('recall_at_threshold')} @ precision {m.get('precision_at_threshold')}",
            )
        ]
        if coil_id is not None:
            sources.append(SourceRef.record(table="coil_log", id=str(coil_id)))

        label = "defect-likely" if result.risk_label else "low-risk"
        return ToolResult(
            tool=self.name, data=asdict(result), sources=sources,
            summary=f"coil {coil_id or '(features)'}: risk {result.risk_score} -> {label} "
                    f"(threshold {result.threshold}); top drivers {', '.join(drivers)}",
        )
