"""
live_sensor.py — Real-time sensor simulation for Sherlock demo
===========================================================
Runs a background thread that updates sensor readings every 10 seconds
using random walks around realistic base values.

Public API
----------
  get_live_readings()           → dict  current sensor snapshot per plant/unit
  get_live_events()             → list  last 20 events (alerts, anomalies)
  inject_demo_alert(plant, type) → dict  injected event (for demo button)
  get_live_kpi_deltas()         → dict  KPI trend vs baseline
"""

from __future__ import annotations

import math
import random
import threading
import time
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Deque

logger = logging.getLogger(__name__)

# ── Base values per unit (realistic steel plant parameters) ──────────────────

_BASE_SENSORS: dict[str, dict] = {
    "Blast-Furnace-1": {
        "vibration": 3.2, "temperature": 1420.0, "pressure": 8.5,
        "plant": "Plant-A", "status": "NORMAL",
    },
    "Blast-Furnace-2": {
        "vibration": 2.8, "temperature": 1380.0, "pressure": 7.9,
        "plant": "Plant-B", "status": "NORMAL",
    },
    "Rolling-Mill": {
        "vibration": 4.1, "temperature": 950.0, "pressure": 12.3,
        "plant": "Plant-A", "status": "NORMAL",
    },
    "Coke-Oven": {
        "vibration": 1.9, "temperature": 1100.0, "pressure": 4.2,
        "plant": "Plant-B", "status": "NORMAL",
    },
    "Sinter-Plant": {
        "vibration": 2.5, "temperature": 820.0, "pressure": 5.8,
        "plant": "Plant-C", "status": "NORMAL",
    },
    "BOF-Converter": {
        "vibration": 3.7, "temperature": 1600.0, "pressure": 9.1,
        "plant": "Plant-D", "status": "NORMAL",
    },
}

# ── Live state ───────────────────────────────────────────────────────────────

_lock    = threading.RLock()
_sensors: dict[str, dict] = {
    unit: {**data, "failure_probability": 0.15, "production_rate": 2100.0}
    for unit, data in _BASE_SENSORS.items()
}
_events: Deque[dict] = deque(maxlen=20)
_tick    = 0          # how many update cycles have run
_running = False
_thread: threading.Thread | None = None

# KPI baselines (used to compute deltas)
_KPI_BASELINE = {
    "safety_score":    62.2,
    "energy_score":    76.0,
    "production_kpi":  77.7,
    "downtime_risk":   47.3,
}


# ── Random-walk helpers ──────────────────────────────────────────────────────

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _walk(value: float, step: float, lo: float, hi: float) -> float:
    return _clamp(value + random.gauss(0, step), lo, hi)


def _failure_prob(vib: float, temp: float, pres: float) -> float:
    v_norm = vib  / 10.0
    t_norm = (temp - 200.0) / 1800.0
    p_norm = pres / 20.0
    raw = 0.35 * v_norm + 0.40 * t_norm + 0.25 * p_norm
    return _clamp(round(raw + random.gauss(0, 0.02), 3), 0.01, 0.99)


# ── Update loop ──────────────────────────────────────────────────────────────

def _update_once() -> None:
    global _tick
    _tick += 1
    with _lock:
        for unit, s in _sensors.items():
            # Random-walk each sensor
            s["vibration"]   = round(_walk(s["vibration"],   0.15, 0.3, 9.8),  3)
            s["temperature"] = round(_walk(s["temperature"], 8.0,  200, 1650), 1)
            s["pressure"]    = round(_walk(s["pressure"],    0.3,  1.0, 18.0), 2)
            s["production_rate"] = round(_walk(s["production_rate"], 30.0, 600, 3200), 1)

            # Recompute failure probability from sensor values
            fp_new = _failure_prob(s["vibration"], s["temperature"], s["pressure"])
            fp_old = s["failure_probability"]
            s["failure_probability"] = fp_new

            # Determine status
            if fp_new > 0.75:
                s["status"] = "CRITICAL"
            elif fp_new > 0.50:
                s["status"] = "WARNING"
            else:
                s["status"] = "NORMAL"

            # Emit an event if failure probability crossed a threshold
            if fp_old <= 0.60 and fp_new > 0.60:
                _events.appendleft({
                    "id":        f"EVT-{_tick:05d}-{unit[:3].upper()}",
                    "type":      "THRESHOLD_BREACH",
                    "plant":     s["plant"],
                    "unit":      unit,
                    "severity":  "HIGH" if fp_new < 0.75 else "CRITICAL",
                    "message":   f"{unit} failure probability crossed 60% → {fp_new:.1%}",
                    "metric":    "failure_probability",
                    "value":     fp_new,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "is_live":   True,
                })
                logger.info("Live event: %s FP=%.2f", unit, fp_new)

        # Occasionally emit a random mild event for demo liveliness (every ~90 s)
        if _tick % 9 == 0:
            unit = random.choice(list(_sensors.keys()))
            s    = _sensors[unit]
            evt_types = [
                ("VIBRATION_SPIKE",  f"{unit} vibration spike detected: {s['vibration']:.2f} m/s²"),
                ("TEMP_ANOMALY",     f"{unit} temperature anomaly: {s['temperature']:.0f}°C"),
                ("PRESSURE_FLUCTUATION", f"{unit} pressure fluctuation: {s['pressure']:.2f} bar"),
            ]
            etype, msg = random.choice(evt_types)
            _events.appendleft({
                "id":        f"EVT-{_tick:05d}-RND",
                "type":      etype,
                "plant":     s["plant"],
                "unit":      unit,
                "severity":  "MEDIUM",
                "message":   msg,
                "metric":    etype.lower(),
                "value":     round(random.uniform(0.2, 0.7), 3),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_live":   True,
            })


def _simulation_loop() -> None:
    logger.info("Live sensor simulation started (10 s interval)")
    while _running:
        try:
            _update_once()
        except Exception as exc:
            logger.error("Simulation error: %s", exc)
        time.sleep(10)
    logger.info("Live sensor simulation stopped")


# ── Public control API ───────────────────────────────────────────────────────

def start_simulation() -> None:
    global _running, _thread
    if _running:
        return
    _running = True
    _thread  = threading.Thread(target=_simulation_loop, daemon=True, name="sensor-sim")
    _thread.start()


def stop_simulation() -> None:
    global _running
    _running = False


# ── Public data API ──────────────────────────────────────────────────────────

def get_live_readings() -> dict:
    """Return current sensor snapshot — safe copy, no lock held by caller."""
    with _lock:
        return {
            "tick":    _tick,
            "updated": datetime.now(timezone.utc).isoformat(),
            "units":   {u: dict(s) for u, s in _sensors.items()},
        }


def get_live_events() -> list[dict]:
    """Return last 20 live events, newest first."""
    with _lock:
        return list(_events)


def get_live_kpi_deltas() -> dict:
    """
    Compute rolling KPI values from current sensor state
    and return deltas vs baseline.
    """
    with _lock:
        units = list(_sensors.values())

    avg_fp   = sum(u["failure_probability"] for u in units) / len(units)
    avg_prod = sum(u["production_rate"]     for u in units) / len(units)
    # Safety inversely correlates with failure probability
    safety   = round((1 - avg_fp) * 100, 1)
    energy   = round(random.uniform(73.0, 79.0), 1)   # simulated efficiency
    prod_kpi = round((avg_prod / 2500.0) * 100, 1)
    downtime = round(avg_fp * 100, 1)

    return {
        "safety_score":    {"value": safety,   "delta": round(safety   - _KPI_BASELINE["safety_score"],   1)},
        "energy_score":    {"value": energy,   "delta": round(energy   - _KPI_BASELINE["energy_score"],   1)},
        "production_kpi":  {"value": prod_kpi, "delta": round(prod_kpi - _KPI_BASELINE["production_kpi"], 1)},
        "downtime_risk":   {"value": downtime, "delta": round(downtime  - _KPI_BASELINE["downtime_risk"],  1)},
    }


def inject_demo_alert(
    plant: str = "Plant-A",
    alert_type: str = "CRITICAL_FAILURE",
) -> dict:
    """
    Inject a dramatic demo alert — used by the 🔴 Simulate Alert button.
    Also spikes the relevant unit's sensors to make KPIs react.
    """
    # Pick unit belonging to the target plant
    plant_units = [u for u, s in _BASE_SENSORS.items() if s["plant"] == plant]
    unit = plant_units[0] if plant_units else "Blast-Furnace-1"

    alert_templates = {
        "CRITICAL_FAILURE": {
            "severity": "CRITICAL",
            "incident_type": "Equipment Failure",
            "message": (
                f"🚨 CRITICAL: {unit} in {plant} has crossed failure threshold. "
                f"Immediate shutdown recommended. Vibration: 8.9 m/s², "
                f"Temperature: 1,580°C. Bearing replacement required within 2 hours."
            ),
            "vib_spike": 8.9, "temp_spike": 1580.0, "fp_spike": 0.91,
        },
        "GAS_LEAK": {
            "severity": "CRITICAL",
            "incident_type": "Gas Leak",
            "message": (
                f"⚠️ GAS LEAK detected near Coke Oven in {plant}. "
                f"Risk score: 0.87. Evacuate Zone B-4 immediately. "
                f"Emergency response team dispatched."
            ),
            "vib_spike": 2.1, "temp_spike": 1150.0, "fp_spike": 0.82,
        },
        "ENERGY_SURGE": {
            "severity": "HIGH",
            "incident_type": "Energy Anomaly",
            "message": (
                f"⚡ ENERGY SURGE: {plant} consumption spiked +34% above baseline. "
                f"Current: 2,840 kWh/h vs normal 2,120 kWh/h. "
                f"BOF Converter drawing excessive load."
            ),
            "vib_spike": 4.5, "temp_spike": 1420.0, "fp_spike": 0.68,
        },
        "PRODUCTION_HALT": {
            "severity": "HIGH",
            "incident_type": "Production Stoppage",
            "message": (
                f"🏭 PRODUCTION HALT: Rolling Mill in {plant} stopped unexpectedly. "
                f"Throughput dropped from 2,200 to 0 t/day. "
                f"Conveyor belt failure suspected."
            ),
            "vib_spike": 6.2, "temp_spike": 960.0, "fp_spike": 0.79,
        },
    }

    tmpl = alert_templates.get(alert_type, alert_templates["CRITICAL_FAILURE"])

    # Spike the unit's sensors
    with _lock:
        if unit in _sensors:
            _sensors[unit]["vibration"]          = tmpl["vib_spike"]
            _sensors[unit]["temperature"]        = tmpl["temp_spike"]
            _sensors[unit]["failure_probability"] = tmpl["fp_spike"]
            _sensors[unit]["status"]             = tmpl["severity"]

    event = {
        "id":           f"DEMO-{int(time.time())}",
        "type":         alert_type,
        "plant":        plant,
        "unit":         unit,
        "severity":     tmpl["severity"],
        "incident_type": tmpl["incident_type"],
        "message":      tmpl["message"],
        "value":        tmpl["fp_spike"],
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "is_live":      True,
        "is_demo":      True,
    }
    with _lock:
        _events.appendleft(event)

    logger.info("Demo alert injected: %s → %s", alert_type, plant)
    return event
