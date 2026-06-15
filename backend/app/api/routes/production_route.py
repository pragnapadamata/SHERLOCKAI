from fastapi import APIRouter, Query
from app.services.data_service import get_plant_data, get_maintenance_data
from app.agents.multi_agent import run_production_analysis

router = APIRouter()


@router.get("/summary")
async def get_production_summary(plant_id: str = "ALL"):
    df = get_plant_data(plant_id=plant_id, last_n=200)
    maint_df = get_maintenance_data(plant_id=plant_id, last_n=100)

    production_target = 2500.0
    actual_avg = float(df["production_rate"].mean())
    attainment  = round(actual_avg / production_target * 100, 1)

    by_plant = df.groupby("plant_id")["production_rate"].agg(["mean","min","max"]).round(1).to_dict()
    by_unit  = df.groupby("unit_id")["production_rate"].mean().sort_values(ascending=False).round(1).to_dict()

    downtime_by_plant = df.groupby("plant_id")["downtime_flag"].sum().to_dict()
    downtime_hours    = {k: int(v) * 4 for k, v in downtime_by_plant.items()}

    scheduled_maint = len(maint_df[maint_df["status"].isin(["Scheduled", "In Progress"])])

    if "timestamp" in df.columns:
        df["date"] = df["timestamp"].dt.date.astype(str)
        daily = df.groupby("date")["production_rate"].mean().round(1).to_dict()
    else:
        daily = {}

    return {
        "target": production_target,
        "actual_avg": round(actual_avg, 1),
        "attainment_pct": attainment,
        "downtime_hours": downtime_hours,
        "by_plant": by_plant,
        "by_unit": by_unit,
        "daily_trend": daily,
        "scheduled_maintenance_impacts": scheduled_maint,
    }


@router.get("/schedule")
async def get_production_schedule():
    """Return a mock production schedule."""
    import random
    from datetime import datetime, timedelta

    random.seed(42)
    schedule = []
    shifts = ["Morning (06:00-14:00)", "Afternoon (14:00-22:00)", "Night (22:00-06:00)"]
    grades = ["HRC-250", "HRC-300", "CRC-200", "Plates-350", "Wire-Rod-400", "TMT-Bars"]
    plants = ["Plant-A", "Plant-B", "Plant-C", "Plant-D"]

    base = datetime.now()
    for day in range(7):
        for shift in shifts:
            schedule.append({
                "date": (base + timedelta(days=day)).strftime("%Y-%m-%d"),
                "shift": shift,
                "plant": random.choice(plants),
                "grade": random.choice(grades),
                "target_tonnes": random.randint(400, 900),
                "allocated_crew": random.randint(12, 28),
                "priority": random.choice(["HIGH", "MEDIUM", "LOW"]),
            })
    return {"schedule": schedule}


@router.post("/analyze")
async def analyze_production(plant_id: str = "ALL"):
    return run_production_analysis(plant_id=plant_id)
