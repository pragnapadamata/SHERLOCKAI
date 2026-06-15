from fastapi import APIRouter, Depends
from app.services.data_service import compute_dashboard_kpis, get_plant_data, get_energy_data
from app.services.live_sensor import get_live_readings, get_live_events, get_live_kpi_deltas
from app.core.security import get_current_user
import pandas as pd

router = APIRouter()


@router.get("/kpis")
async def get_dashboard_kpis(current_user: dict = Depends(get_current_user)):
    """Get all executive dashboard KPIs."""
    return compute_dashboard_kpis()


@router.get("/timeseries")
async def get_timeseries(plant_id: str = "ALL", metric: str = "failure_probability"):
    """Get time-series data for charting."""
    df = get_plant_data(plant_id=plant_id, last_n=200)
    energy_df = get_energy_data(plant_id=plant_id, last_n=200)

    plant_series = []
    if "timestamp" in df.columns:
        temp = df[["timestamp", "failure_probability", "production_rate", "vibration", "temperature"]].copy()
        temp["timestamp"] = temp["timestamp"].astype(str)
        plant_series = temp.to_dict(orient="records")

    energy_series = []
    if "timestamp" in energy_df.columns:
        temp2 = energy_df[["timestamp", "total_energy_kwh", "efficiency_ratio", "co2_tonnes"]].copy()
        temp2["timestamp"] = temp2["timestamp"].astype(str)
        energy_series = temp2.to_dict(orient="records")

    return {
        "plant_series": plant_series[-100:],
        "energy_series": energy_series[-100:],
    }


@router.get("/plants")
async def get_plant_list():
    """Return list of plants with status."""
    df = get_plant_data(last_n=200)
    plants = []
    for p in ["Plant-A", "Plant-B", "Plant-C", "Plant-D"]:
        subset = df[df["plant_id"] == p]
        if len(subset) == 0:
            continue
        avg_fp = float(subset["failure_probability"].mean())
        status = "CRITICAL" if avg_fp > 0.7 else "WARNING" if avg_fp > 0.45 else "NORMAL"
        plants.append({
            "id": p,
            "name": p,
            "status": status,
            "failure_probability": round(avg_fp, 3),
            "production_rate": round(float(subset["production_rate"].mean()), 1),
            "units": subset["unit_id"].unique().tolist(),
        })
    return plants


@router.get("/live")
async def get_live_dashboard():
    """
    Live sensor data for real-time dashboard polling (every 10 s).
    Returns current sensor readings, recent events, and KPI deltas.
    """
    return {
        "readings":   get_live_readings(),
        "events":     get_live_events()[:5],   # last 5 for banner
        "kpi_deltas": get_live_kpi_deltas(),
    }


@router.get("/live-events")
async def get_live_events_feed():
    """Full live event feed — last 20 events."""
    return {"events": get_live_events()}
