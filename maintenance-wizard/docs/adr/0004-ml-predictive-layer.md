# ADR 0004: ML predictive layer

- **Status:** Accepted
- **Date:** 2026-06-06
- **Phase:** 3 (ML Predictive Layer)

## Context

Phase 3 adds real prediction models exposed as agent tools: anomaly detection,
remaining useful life (RUL), and a process-defect classifier; plus dynamic risk
in prioritization and catastrophic-failure early warning. Everything must be
deterministic, offline, and explainable (no black-box point estimates), and must
honor the planted hero stories.

## Decisions

1. **RUL: classical robust degradation-trend extrapolation, not an NN.** A
   Theil-Sen line (robust to transient spikes, deterministic, with a slope CI) is
   fit on the degradation portion of the governing channel and extrapolated to a
   failure threshold. This is the correct model for a piecewise-linear degradation
   signal: explainable (slope, fit window, threshold), dependable, torch-free. An
   LSTM/NN would be opaque, data-hungry, and cannot beat a correct linear
   extrapolation on a linear signal -- it loses on both explainability and
   dependability.

2. **RUL targets the ISO 10816-3 damage threshold (4.5 mm/s), not action.** RUL =
   time to the fracture-equivalent end of life (damage-zone onset). The earlier
   ISO action crossing (2.8) is reported separately as the "plan the repair"
   horizon. This is the correct P-F-curve framing and lands the F3 gearbox at
   ~12 weeks (action ~2 weeks), consistent with the planted story. Extrapolating
   to action would have given ~2 weeks and contradicted the 8-14 week RUL.

3. **RUL interval is a +/- degradation-rate planning allowance** (default 40%),
   not the statistical slope CI. The clean synthetic trend's statistical CI is
   unrealistically tight; a planning band is more honest and is what makes the
   conservative procurement logic meaningful. F3: 12.3 wk -> [7.4, 17.3] wk.

4. **Early-warning procurement trigger compares the RUL interval LOWER BOUND to
   spare lead time** (not the central RUL). Conservative "plan against worst-case
   RUL" logic: F3's lower bound 7.4 wk <= 8 wk lead time fires "order now".

5. **Anomaly detection: robust residual z-score (decision) + IsolationForest
   (corroboration), with channel attribution.** The z-score against a per-asset
   baseline (median + scaled MAD) is transparent and reliably flags the designed
   anomalies; IsolationForest adds a recognized multivariate score. Attribution
   names the channels by |z|. The z threshold (6.0) sits well above baseline
   max-of-many-samples noise (~4) and far below real signals (z ~30-140). Severity
   for the risk_modifier is mapped from the ISO zone of the worst sample,
   reconciling with the existing `regime` column.

6. **Process-defect classifier: HistGradientBoostingClassifier.** Native
   missing-value handling, `class_weight="balanced"` for the 4.88% imbalance,
   StratifiedKFold CV, decision threshold tuned for a target recall (default 0.90).
   We report the ACTUAL CV numbers (ROC-AUC 0.86, recall 0.92 @ precision 0.10) --
   never the original 100%/>90% target, which is unachievable here. Pushing recall
   to 1.0 was rejected: it craters precision on 4.88% positives. Top drivers from
   permutation importance (no SHAP). X-features stay unlabeled.

7. **Dynamic risk wired into priority as a transparent additive component.**
   `risk = max(rul_risk, anomaly_severity)` (worst signal drives urgency);
   `priority = min(base_4dim + risk_weight*risk*100, 100)`. A `dynamic_risk`
   `ScoreComponent` is shown; when the 100 cap is hit it is flagged so the
   "components exceed score" case stays transparent. Default behavior is unchanged
   when no risk_modifier is supplied (Phase 2 tests stay green).

8. **assess_early_warning is a separate (4th) tool**, mapping to the spec's "early
   warning of catastrophic failures" output -- a distinct combined verdict
   (acute anomaly OR imminent RUL OR procurement-at-risk).

9. **SourceRef extended with structured `model`/`drivers` fields** so the UI can
   cite model provenance rather than parsing a detail string.

10. **Artifacts in `models/` (gitignored), rebuilt by `train_models`.** Fixed
    seeds make training deterministic. RUL needs no artifact (fit at query time).
    sklearn only -- no torch, no downloads.

## Consequences

- `train_models` writes `models/anomaly/<asset>.joblib` and
  `models/alpha_defect/{model.joblib,metrics.json,importances.json}`.
- `build_default_registry` now exposes 16 tools and wires the risk_modifier.
- Default `pytest` trains the small models in a session fixture (offline, ~14 s);
  the suite stays green and `-m slow` still covers the retrieval models.
- Phase 4 can consume these tools and the early-warning verdict in the proactive
  engine and specialist agents.
