from fastapi import APIRouter, Query
from app.services.data_service import get_energy_data
from app.agents.multi_agent import run_energy_analysis

router = APIRouter()


@router.get("/consumption")
async def get_energy_consumption(plant_id: str = "ALL", limit: int = Query(100, le=300)):
    df = get_energy_data(plant_id=plant_id, last_n=limit)
    records = df.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if hasattr(v, "item"):
                r[k] = v.item()
            if hasattr(v, "isoformat"):
                r[k] = str(v)
    return {"consumption": records, "total": len(records)}


@router.get("/analytics")
async def get_energy_analytics(plant_id: str = "ALL"):
    df = get_energy_data(plant_id=plant_id, last_n=300)

    avg_efficiency = float(df["efficiency_ratio"].mean())
    total_energy   = float(df["total_energy_kwh"].sum())
    total_co2      = float(df["co2_tonnes"].sum())
    total_savings  = float(df["potential_savings_kwh"].sum())

    # By plant
    plant_efficiency = df.groupby("plant_id")["efficiency_ratio"].mean().round(3).to_dict()
    plant_consumption = df.groupby("plant_id")["total_energy_kwh"].sum().round(1).to_dict()

    # By unit
    unit_efficiency = df.groupby("unit_id")["efficiency_ratio"].mean().round(3).to_dict()

    # Breakdown by type
    avg_elec  = float(df["electricity_kwh"].mean())
    avg_gas   = float(df["gas_m3"].mean())
    avg_steam = float(df["steam_kg"].mean())

    # Time series for chart
    if "timestamp" in df.columns:
        df["hour"] = df["timestamp"].dt.hour
        hourly = df.groupby("hour")["total_energy_kwh"].mean().round(1).to_dict()
    else:
        hourly = {}

    return {
        "avg_efficiency": round(avg_efficiency, 3),
        "energy_score": round(avg_efficiency * 100, 1),
        "total_energy_kwh": round(total_energy, 1),
        "total_co2_tonnes": round(total_co2, 2),
        "total_potential_savings_kwh": round(total_savings, 1),
        "estimated_savings_inr": round(total_savings * 0.008, 2),
        "plant_efficiency": plant_efficiency,
        "plant_consumption": plant_consumption,
        "unit_efficiency": unit_efficiency,
        "avg_electricity_kwh": round(avg_elec, 1),
        "avg_gas_m3": round(avg_gas, 1),
        "avg_steam_kg": round(avg_steam, 1),
        "hourly_consumption": hourly,
    }


@router.post("/analyze")
async def analyze_energy(plant_id: str = "ALL"):
    return run_energy_analysis(plant_id=plant_id)
