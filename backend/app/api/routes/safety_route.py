from fastapi import APIRouter, Query
from app.services.data_service import get_safety_data
from app.agents.multi_agent import run_safety_analysis

router = APIRouter()


@router.get("/incidents")
async def get_incidents(plant_id: str = "ALL", severity: str = None, limit: int = Query(100, le=300)):
    df = get_safety_data(plant_id=plant_id, last_n=limit)
    if severity:
        df = df[df["severity"] == severity.upper()]

    records = df.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if hasattr(v, "item"):
                r[k] = v.item()
            if hasattr(v, "isoformat"):
                r[k] = str(v)
    return {"incidents": records, "total": len(records)}


@router.get("/analytics")
async def get_safety_analytics(plant_id: str = "ALL"):
    df = get_safety_data(plant_id=plant_id, last_n=300)

    severity_counts = df["severity"].value_counts().to_dict()
    incident_types  = df["incident_type"].value_counts().to_dict()
    resolution_rate = float(df["resolved"].mean() * 100)
    avg_risk        = float(df["risk_score"].mean())
    safety_score    = round((1 - avg_risk) * 100, 1)
    avg_response    = float(df["response_time_minutes"].mean())

    # Risk by plant
    plant_risk = df.groupby("plant_id")["risk_score"].mean().round(3).to_dict()

    # Monthly trend (use timestamp if available)
    if "timestamp" in df.columns:
        df["month"] = df["timestamp"].dt.to_period("M").astype(str)
        monthly = df.groupby("month")["risk_score"].mean().round(3).to_dict()
    else:
        monthly = {}

    return {
        "severity_counts": severity_counts,
        "incident_types": incident_types,
        "resolution_rate": round(resolution_rate, 1),
        "avg_risk_score": round(avg_risk, 3),
        "safety_score": safety_score,
        "avg_response_time_minutes": round(avg_response, 1),
        "plant_risk": plant_risk,
        "monthly_risk_trend": monthly,
        "unresolved_count": int((df["resolved"] == 0).sum()),
        "critical_count": int((df["severity"] == "CRITICAL").sum()),
    }


@router.post("/analyze")
async def analyze_safety(plant_id: str = "ALL"):
    return run_safety_analysis(plant_id=plant_id)
