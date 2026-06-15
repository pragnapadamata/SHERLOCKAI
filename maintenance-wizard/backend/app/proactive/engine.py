"""The autonomous monitoring loop -- the autonomy showcase.

Each poll, per monitored asset:
  - ACUTE ALARM: detect_anomaly on the live window; on a genuine, debounced
    crossing (severity >= gate or ISO action regime) open a high/critical ticket
    and run the full orchestrator analysis.
  - PREDICTIVE ADVISORY: if not acute, run assess_early_warning (local); when it
    fires (debounced), open a lower-severity advisory ticket + full analysis.
Every autonomous response also raises an Alert and auto-logs to the digital
logbook as the system user. The orchestrator (the only token cost) is invoked
only on a genuine, debounced trigger.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd

from backend.app.core.logging import get_logger
from backend.app.tickets.models import Severity, TicketKind
from backend.app.tickets.presentation import autonomous_logbook_text

log = get_logger(__name__)


def _wallclock() -> str:
    """Real wall-clock time for the 'last scan' liveness display, distinct from the
    synthetic stream cursor used for the replayed data."""

    return datetime.now(UTC).isoformat(timespec="seconds")


COMPREHENSIVE = (
    "AUTONOMOUS ALERT -- {kind} on {name} ({equipment_id}) at {timestamp}. {message} "
    "Provide a comprehensive maintenance analysis: probable fault diagnosis, root cause, "
    "remaining useful life and early warning, risk and priority, and recommended immediate "
    "and long-term actions."
)


@dataclass
class MonitorState:
    acute_active: bool = False
    advisory_active: bool = False
    normal_streak: int = 0


@dataclass
class ProactiveOutcome:
    kind: str
    equipment_id: str
    alert_id: str
    ticket_id: str
    severity: str
    tokens_in: int = 0
    tokens_out: int = 0


@dataclass
class ProactiveEngine:
    stream: Any
    detector: Any
    early_warning: Any
    orchestrator: Any
    ticket_service: Any
    alert_service: Any
    repos: Any
    settings: Any
    monitored_assets: list[str]
    system_user_id: str = "U-SYS-AMDC"
    last_polled_at: str | None = None
    _states: dict[str, MonitorState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._states = {a: MonitorState() for a in self.monitored_assets}
        self.last_polled_at = _wallclock()

    def reset(self) -> None:
        """Demo/ops: rewind the stream cursor and clear debounce so a scenario re-fires."""
        self.stream.reset()
        self._states = {a: MonitorState() for a in self.monitored_assets}
        self.last_polled_at = _wallclock()

    def _now(self) -> str:
        return self.stream.now.isoformat()

    def _name(self, equipment_id: str) -> str:
        row = self.repos.equipment.get(equipment_id)
        return row["name"] if row else equipment_id

    @staticmethod
    def _fault_from_findings(findings: list[dict]) -> str | None:
        for f in findings:
            code = (f.get("key_facts") or {}).get("probable_fault_code")
            if code:
                return code
        return None

    def poll(self, assets: list[str] | None = None) -> list[ProactiveOutcome]:
        self.last_polled_at = _wallclock()
        outcomes: list[ProactiveOutcome] = []
        lookback = timedelta(days=self.settings.monitor_lookback_days)
        start, end = self.stream.window_bounds(lookback)

        targets = assets if assets is not None else self.monitored_assets
        for asset in targets:
            state = self._states.get(asset)
            if state is None:
                continue  # not a monitored asset

            result = None
            try:
                result = self.detector.score(asset, start=start.isoformat(), end=end.isoformat())
            except Exception as exc:  # noqa: BLE001 -- detection must not crash the loop
                log.warning("detect_failed", asset=asset, error=str(exc))

            injected = self.stream.is_injected(asset)
            acute = injected or (
                result is not None and result.is_anomaly
                and (result.severity >= self.settings.proactive_min_severity
                     or result.iso_regime.get("at_anomaly") == "action")
            )

            if acute:
                if not state.acute_active:
                    state.acute_active = True
                    state.normal_streak = 0
                    outcomes.append(self._raise_acute(asset, result, injected))
                continue  # acute supersedes advisory for this asset this poll

            # falling edge / recovery for the acute tier
            state.normal_streak += 1
            if state.acute_active and state.normal_streak >= self.settings.recovery_polls:
                state.acute_active = False

            # PREDICTIVE ADVISORY tier
            ew = self.early_warning.assess(asset)
            if ew.early_warning:
                if not state.advisory_active:
                    state.advisory_active = True
                    outcomes.append(self._raise_advisory(asset, ew))
            else:
                state.advisory_active = False

        return outcomes

    def _raise_acute(self, asset: str, result: Any, injected: bool) -> ProactiveOutcome:
        score = result.anomaly_score if result else None
        channels = [c["channel"] for c in result.contributing_channels] if result else []
        severity = Severity.CRITICAL if (injected or (result and result.severity >= 0.9)) else Severity.HIGH
        message = (f"Acute anomaly on {self._name(asset)}: score {score}, "
                   f"channels {channels}." if not injected
                   else f"Injected demo anomaly on {self._name(asset)}.")
        return self._respond(asset, kind=TicketKind.ACUTE_ALARM, severity=severity,
                             message=message, anomaly_score=score, channels=channels)

    def _raise_advisory(self, asset: str, ew: Any) -> ProactiveOutcome:
        triggers = [t["type"] for t in ew.triggers]
        message = (f"Predictive advisory on {self._name(asset)}: {triggers}. "
                   f"{ew.recommended_horizon or ''}".strip())
        return self._respond(asset, kind=TicketKind.PREDICTIVE_ADVISORY, severity=Severity.MEDIUM,
                             message=message, anomaly_score=None, channels=[])

    def _respond(self, asset: str, *, kind: TicketKind, severity: Severity, message: str,
                 anomaly_score: float | None, channels: list[str]) -> ProactiveOutcome:
        timestamp = self._now()
        name = self._name(asset)

        ticket = self.ticket_service.create(
            equipment_id=asset, severity=severity, kind=kind,
            title=f"{kind.value.replace('_', ' ').title()} on {name}",
            originating_event={"type": "alert", "kind": kind.value, "timestamp": timestamp},
            author=self.system_user_id,
        )

        query = COMPREHENSIVE.format(kind=kind.value, name=name, equipment_id=asset,
                                     timestamp=timestamp, message=message)
        result = self.orchestrator.run(query, session_id=ticket.ticket_id)

        self.ticket_service.attach_analysis(
            ticket.ticket_id, answer=result.answer, findings=result.findings,
            provenance=result.provenance, recommended_actions=result.answer,
        )
        alert = self.alert_service.create(
            equipment_id=asset, severity=severity, kind=kind, message=message,
            ticket_id=ticket.ticket_id, anomaly_score=anomaly_score,
            contributing_channels=channels, analysis_summary=result.answer[:500],
        )

        try:  # auto-log to the digital logbook as the system user, once per event
            already_logged = self.repos.logbook.has_entry(
                equipment_id=asset, entry_type="alert", timestamp=timestamp
            )
            if not already_logged:
                self.repos.logbook.append(
                    equipment_id=asset, author_user_id=self.system_user_id, entry_type="alert",
                    text=autonomous_logbook_text(
                        equipment_name=name, kind=kind.value, ticket_id=ticket.ticket_id
                    ),
                    related_fault_code=self._fault_from_findings(result.findings),
                    timestamp=timestamp,
                )
        except Exception as exc:  # noqa: BLE001 -- logging must not break the response
            log.warning("autolog_failed", asset=asset, error=str(exc))

        log.info("proactive_response", kind=kind.value, asset=asset, ticket=ticket.ticket_id,
                 alert=alert.alert_id, tokens_in=result.tokens_in)
        return ProactiveOutcome(
            kind=kind.value, equipment_id=asset, alert_id=alert.alert_id,
            ticket_id=ticket.ticket_id, severity=severity.value,
            tokens_in=result.tokens_in, tokens_out=result.tokens_out,
        )

    def run_until(self, when: str | datetime) -> list[ProactiveOutcome]:
        target = pd.Timestamp(when).to_pydatetime()
        outcomes = list(self.poll())
        while self.stream.now < target and not self.stream.at_end():
            self.stream.advance()
            outcomes.extend(self.poll())
        return outcomes

    def run_ticks(self, n: int) -> list[ProactiveOutcome]:
        outcomes: list[ProactiveOutcome] = []
        for _ in range(n):
            self.stream.advance()
            outcomes.extend(self.poll())
        return outcomes
