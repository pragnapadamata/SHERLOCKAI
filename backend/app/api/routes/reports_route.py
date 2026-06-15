from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.data_service import compute_dashboard_kpis, get_plant_data, get_safety_data, get_energy_data, get_maintenance_data
from app.services.pdf_report import generate_board_pdf
from app.agents.multi_agent import run_multi_agent
from datetime import datetime
import io

router = APIRouter()


@router.get("/executive-summary")
async def get_executive_summary():
    """Generate a full executive summary report."""
    kpis = compute_dashboard_kpis()
    result = run_multi_agent(
        "Generate a comprehensive executive summary report covering all operational domains including safety, maintenance, energy, and production performance."
    )
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "kpis": kpis,
        "ai_summary": result["response"],
        "confidence": result["confidence"],
        "impact": result["impact"],
    }


@router.get("/maintenance-report")
async def get_maintenance_report():
    df = get_maintenance_data(last_n=300)
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_tasks": len(df),
        "by_status": df["status"].value_counts().to_dict(),
        "by_type": df["maintenance_type"].value_counts().to_dict(),
        "total_cost_usd": round(float(df["cost_usd"].sum()), 2),
        "overdue_tasks": df[df["status"] == "Overdue"].to_dict(orient="records")[:10],
        "avg_confidence": round(float(df["confidence_score"].mean()), 3),
    }


@router.get("/safety-report")
async def get_safety_report():
    df = get_safety_data(last_n=300)
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_incidents": len(df),
        "by_severity": df["severity"].value_counts().to_dict(),
        "by_type": df["incident_type"].value_counts().to_dict(),
        "unresolved": int((df["resolved"] == 0).sum()),
        "avg_risk_score": round(float(df["risk_score"].mean()), 3),
        "safety_score": round((1 - float(df["risk_score"].mean())) * 100, 1),
        "avg_response_time_min": round(float(df["response_time_minutes"].mean()), 1),
    }


@router.get("/energy-report")
async def get_energy_report():
    df = get_energy_data(last_n=300)
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "avg_efficiency": round(float(df["efficiency_ratio"].mean()), 3),
        "total_consumption_kwh": round(float(df["total_energy_kwh"].sum()), 1),
        "total_co2_tonnes": round(float(df["co2_tonnes"].sum()), 2),
        "potential_savings_kwh": round(float(df["potential_savings_kwh"].sum()), 1),
        "estimated_savings_inr": round(float(df["potential_savings_kwh"].sum()) * 0.008, 2),
        "by_plant": df.groupby("plant_id")["efficiency_ratio"].mean().round(3).to_dict(),
    }


@router.get("/board-pdf")
async def get_board_pdf():
    """
    Generate and stream a board-level PDF report.
    Returns application/pdf for direct browser download.
    """
    # Gather all data in parallel (sequential for simplicity — fast enough)
    kpis = compute_dashboard_kpis()

    ai_result = run_multi_agent(
        "Generate a comprehensive executive summary report for the Tata Steel board covering "
        "safety, maintenance, energy, and production performance with strategic recommendations."
    )

    maint_df = get_maintenance_data(last_n=300)
    maint_data = {
        "total_tasks":      len(maint_df),
        "by_status":        maint_df["status"].value_counts().to_dict(),
        "total_cost_usd":   round(float(maint_df["cost_usd"].sum()), 2),
        "avg_confidence":   round(float(maint_df["confidence_score"].mean()), 3),
    }

    safety_df = get_safety_data(last_n=300)
    safety_data = {
        "total_incidents":       len(safety_df),
        "unresolved":            int((safety_df["resolved"] == 0).sum()),
        "safety_score":          round((1 - float(safety_df["risk_score"].mean())) * 100, 1),
        "avg_response_time_min": round(float(safety_df["response_time_minutes"].mean()), 1),
    }

    energy_df = get_energy_data(last_n=300)
    energy_data = {
        "avg_efficiency":          round(float(energy_df["efficiency_ratio"].mean()), 3),
        "total_consumption_kwh":   round(float(energy_df["total_energy_kwh"].sum()), 1),
        "total_co2_tonnes":        round(float(energy_df["co2_tonnes"].sum()), 2),
        "potential_savings_kwh":   round(float(energy_df["potential_savings_kwh"].sum()), 1),
        "estimated_savings_inr":   round(float(energy_df["potential_savings_kwh"].sum()) * 0.008, 2),
    }

    pdf_bytes = generate_board_pdf(
        kpis=kpis,
        ai_summary=ai_result["response"],
        maint_data=maint_data,
        safety_data=safety_data,
        energy_data=energy_data,
    )

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename  = f"TataSteel_Sherlock_BoardReport_{timestamp}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
