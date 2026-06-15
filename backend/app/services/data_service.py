import pandas as pd
import numpy as np
import os
from functools import lru_cache
from typing import Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_all_data() -> Dict[str, pd.DataFrame]:
    """Load all CSV datasets once and cache them."""
    data = {}
    files = {
        "plant": "sherlock_ai_plant_data.csv",
        "safety": "sherlock_ai_safety_data.csv",
        "energy": "energy_data.csv",
        "maintenance": "maintenance_data.csv",
    }
    for key, filename in files.items():
        path = os.path.join(settings.DATA_DIR, filename)
        try:
            df = pd.read_csv(path)
            # Parse datetime columns
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            data[key] = df
            logger.info(f"Loaded {filename}: {len(df)} rows")
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            data[key] = pd.DataFrame()
    return data


def get_plant_data(plant_id: str = None, last_n: int = 100) -> pd.DataFrame:
    df = load_all_data()["plant"].copy()
    if plant_id and plant_id != "ALL":
        df = df[df["plant_id"] == plant_id]
    return df.tail(last_n)


def get_safety_data(plant_id: str = None, last_n: int = 100) -> pd.DataFrame:
    df = load_all_data()["safety"].copy()
    if plant_id and plant_id != "ALL":
        df = df[df["plant_id"] == plant_id]
    return df.tail(last_n)


def get_energy_data(plant_id: str = None, last_n: int = 100) -> pd.DataFrame:
    df = load_all_data()["energy"].copy()
    if plant_id and plant_id != "ALL":
        df = df[df["plant_id"] == plant_id]
    return df.tail(last_n)


def get_maintenance_data(plant_id: str = None, last_n: int = 100) -> pd.DataFrame:
    df = load_all_data()["maintenance"].copy()
    if plant_id and plant_id != "ALL":
        df = df[df["plant_id"] == plant_id]
    return df.tail(last_n)


def compute_dashboard_kpis() -> Dict[str, Any]:
    """Compute aggregate KPIs for the executive dashboard."""
    all_data = load_all_data()
    # Always copy cached DataFrames before any operation that might mutate them
    plant_df  = all_data["plant"].copy()
    safety_df = all_data["safety"].copy()
    energy_df = all_data["energy"].copy()
    maint_df  = all_data["maintenance"].copy()

    # Downtime prediction
    avg_failure_prob = float(plant_df["failure_probability"].mean())
    downtime_count = int(plant_df["downtime_flag"].sum())
    total_records = len(plant_df)

    # Safety score (inverse of average risk, 0-100)
    avg_risk = float(safety_df["risk_score"].mean())
    safety_score = round((1 - avg_risk) * 100, 1)
    critical_incidents = int(safety_df[safety_df["severity"] == "CRITICAL"].shape[0])
    active_alerts = int(safety_df[safety_df["resolved"] == 0].shape[0])

    # Energy score
    avg_efficiency = float(energy_df["efficiency_ratio"].mean())
    energy_score = round(avg_efficiency * 100, 1)
    total_savings_potential = float(energy_df["potential_savings_kwh"].sum())
    total_co2 = float(energy_df["co2_tonnes"].sum())

    # Production KPI
    avg_production = float(plant_df["production_rate"].mean())
    production_target = 2500.0
    production_kpi = round((avg_production / production_target) * 100, 1)

    # Maintenance stats
    overdue = int(maint_df[maint_df["status"] == "Overdue"].shape[0])
    in_progress = int(maint_df[maint_df["status"] == "In Progress"].shape[0])
    scheduled = int(maint_df[maint_df["status"] == "Scheduled"].shape[0])
    total_maint_cost = float(maint_df["cost_usd"].sum())

    # Per-plant breakdown
    plants = ["Plant-A", "Plant-B", "Plant-C", "Plant-D"]
    plant_summaries = []
    for p in plants:
        p_plant = plant_df[plant_df["plant_id"] == p]
        p_safety = safety_df[safety_df["plant_id"] == p]
        p_energy = energy_df[energy_df["plant_id"] == p]
        if len(p_plant) == 0:
            continue
        plant_summaries.append({
            "plant_id": p,
            "failure_probability": round(float(p_plant["failure_probability"].mean()), 3),
            "safety_score": round((1 - float(p_safety["risk_score"].mean())) * 100, 1) if len(p_safety) > 0 else 85.0,
            "energy_efficiency": round(float(p_energy["efficiency_ratio"].mean()) * 100, 1) if len(p_energy) > 0 else 75.0,
            "production_rate": round(float(p_plant["production_rate"].mean()), 1),
            "downtime_hours": int(p_plant["downtime_flag"].sum()) * 4,
            "status": "CRITICAL" if float(p_plant["failure_probability"].mean()) > 0.7
                      else "WARNING" if float(p_plant["failure_probability"].mean()) > 0.45
                      else "NORMAL",
        })

    # Recent alerts timeline
    recent_safety = safety_df.nlargest(5, "risk_score")
    alerts = []
    for _, row in recent_safety.iterrows():
        alerts.append({
            "id": f"ALT-{np.random.randint(1000,9999)}",
            "plant": row["plant_id"],
            "unit": row["unit_id"],
            "type": row["incident_type"],
            "severity": row["severity"],
            "risk_score": round(float(row["risk_score"]), 3),
            "timestamp": str(row["timestamp"]),
            "resolved": bool(row["resolved"]),
        })

    return {
        "summary": {
            "downtime_prediction_pct": round(avg_failure_prob * 100, 1),
            "safety_score": safety_score,
            "energy_score": energy_score,
            "production_kpi": production_kpi,
            "active_alerts": active_alerts,
            "critical_incidents": critical_incidents,
            "overdue_maintenance": overdue,
            "total_co2_tonnes": round(total_co2, 1),
            "potential_savings_kwh": round(total_savings_potential, 1),
        },
        "plant_summaries": plant_summaries,
        "recent_alerts": alerts,
        "maintenance_status": {
            "overdue": overdue,
            "in_progress": in_progress,
            "scheduled": scheduled,
            "total_cost_usd": round(total_maint_cost, 2),
        },
    }
