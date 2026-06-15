from fastapi import APIRouter, Query
from app.services.data_service import get_plant_data, get_maintenance_data
from app.agents.multi_agent import run_maintenance_analysis
import pandas as pd

router = APIRouter()


@router.get("/predictions")
async def get_maintenance_predictions(plant_id: str = "ALL", limit: int = Query(50, le=200)):
    """Get predictive maintenance results."""
    df = get_plant_data(plant_id=plant_id, last_n=limit)

    records = []
    for _, row in df.iterrows():
        fp = float(row["failure_probability"])
        severity = "CRITICAL" if fp > 0.75 else "HIGH" if fp > 0.55 else "MEDIUM" if fp > 0.35 else "LOW"
        action_map = {
            "CRITICAL": "Immediate shutdown and inspection required",
            "HIGH": "Schedule maintenance within 24 hours",
            "MEDIUM": "Monitor closely, schedule within 1 week",
            "LOW": "Continue normal operation, routine check",
        }
        records.append({
            "timestamp": str(row["timestamp"]),
            "plant_id": row["plant_id"],
            "unit_id": row["unit_id"],
            "vibration": round(float(row["vibration"]), 3),
            "temperature": round(float(row["temperature"]), 1),
            "pressure": round(float(row["pressure"]), 2),
            "failure_probability": round(fp, 3),
            "severity": severity,
            "recommended_action": action_map[severity],
            "confidence": round(0.75 + fp * 0.20, 3),
        })

    # Sort by failure probability descending
    records.sort(key=lambda x: x["failure_probability"], reverse=True)
    return {"predictions": records, "total": len(records)}


@router.get("/tasks")
async def get_maintenance_tasks(plant_id: str = "ALL", status: str = None, limit: int = 100):
    """Get maintenance task list."""
    df = get_maintenance_data(plant_id=plant_id, last_n=limit)
    if status:
        df = df[df["status"] == status]

    records = df.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if hasattr(v, "item"):
                r[k] = v.item()
    return {"tasks": records, "total": len(records)}


@router.get("/analytics")
async def get_maintenance_analytics(plant_id: str = "ALL"):
    """Aggregated maintenance analytics."""
    df = get_maintenance_data(plant_id=plant_id, last_n=200)
    plant_df = get_plant_data(plant_id=plant_id, last_n=200)

    status_counts = df["status"].value_counts().to_dict()
    type_costs = df.groupby("maintenance_type")["cost_usd"].sum().to_dict()
    component_failures = df[df["status"] == "Overdue"]["component"].value_counts().head(8).to_dict()
    avg_confidence = float(df["confidence_score"].mean())

    # Failure probability distribution
    bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    labels = ["Very Low", "Low", "Medium", "High", "Critical"]
    plant_df["fp_bucket"] = pd.cut(plant_df["failure_probability"], bins=bins, labels=labels)
    fp_dist = plant_df["fp_bucket"].value_counts().to_dict()

    return {
        "status_counts": status_counts,
        "type_costs": {k: round(v, 2) for k, v in type_costs.items()},
        "component_failures": component_failures,
        "failure_probability_distribution": fp_dist,
        "avg_confidence": round(avg_confidence, 3),
        "total_cost": round(float(df["cost_usd"].sum()), 2),
        "avg_duration_hours": round(float(df["duration_hours"].mean()), 1),
    }


@router.post("/analyze")
async def analyze_maintenance(plant_id: str = "ALL"):
    """Run AI maintenance analysis."""
    result = run_maintenance_analysis(plant_id=plant_id)
    return result
