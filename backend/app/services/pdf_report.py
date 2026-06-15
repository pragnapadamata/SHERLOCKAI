"""
pdf_report.py — Board-level PDF report generation using ReportLab
==================================================================
Generates a professional PDF containing:
  - Tata Steel header with Sherlock branding
  - Executive summary from AI
  - Cross-domain KPI table
  - Plant status summary
  - Priority actions table
  - Confidentiality footer with timestamp
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Colour palette matching the dark UI theme ─────────────────────────────────
_STEEL_BLUE  = colors.HexColor("#4f46e5")   # primary brand
_DARK_BG     = colors.HexColor("#0f1117")
_CARD_BG     = colors.HexColor("#1a1d2e")
_WHITE       = colors.white
_LIGHT_GREY  = colors.HexColor("#9ca3af")
_GREEN       = colors.HexColor("#10b981")
_AMBER       = colors.HexColor("#f59e0b")
_RED         = colors.HexColor("#ef4444")
_BORDER      = colors.HexColor("#2d3154")
_TEXT_DARK   = colors.HexColor("#1f2937")


def _status_colour(status: str) -> colors.Color:
    s = status.upper()
    if s in ("CRITICAL", "HIGH"):  return _RED
    if s in ("WARNING",  "MEDIUM"): return _AMBER
    return _GREEN


def _delta_colour(delta: float) -> colors.Color:
    return _GREEN if delta >= 0 else _RED


def generate_board_pdf(
    kpis:        dict[str, Any],
    ai_summary:  str,
    maint_data:  dict[str, Any] | None = None,
    safety_data: dict[str, Any] | None = None,
    energy_data: dict[str, Any] | None = None,
) -> bytes:
    """
    Build a full board report PDF and return raw bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=20*mm,  bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Style definitions ──────────────────────────────────────────────────────
    h1 = ParagraphStyle("H1", fontSize=20, fontName="Helvetica-Bold",
                         textColor=_STEEL_BLUE, spaceAfter=4)
    h2 = ParagraphStyle("H2", fontSize=13, fontName="Helvetica-Bold",
                         textColor=_TEXT_DARK,  spaceBefore=14, spaceAfter=4)
    h3 = ParagraphStyle("H3", fontSize=10, fontName="Helvetica-Bold",
                         textColor=_TEXT_DARK,  spaceBefore=8,  spaceAfter=2)
    body = ParagraphStyle("Body", fontSize=9, fontName="Helvetica",
                           textColor=_TEXT_DARK, leading=14, spaceAfter=6)
    small = ParagraphStyle("Small", fontSize=7.5, fontName="Helvetica",
                            textColor=_LIGHT_GREY, leading=11)
    centre = ParagraphStyle("Centre", fontSize=8, fontName="Helvetica",
                             textColor=_LIGHT_GREY, alignment=TA_CENTER)

    ts = datetime.now(timezone.utc)
    ts_str = ts.strftime("%d %B %Y, %H:%M UTC")

    # ─── HEADER ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Tata Steel Group", h1))
    story.append(Paragraph(
        "Autonomous Plant Intelligence System (Sherlock) — Board Intelligence Report",
        ParagraphStyle("Sub", fontSize=11, fontName="Helvetica",
                       textColor=_LIGHT_GREY, spaceAfter=2),
    ))
    story.append(Paragraph(
        f"Generated: {ts_str}  |  Classification: CONFIDENTIAL",
        ParagraphStyle("Meta", fontSize=8, fontName="Helvetica",
                       textColor=_LIGHT_GREY, spaceAfter=6),
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=_STEEL_BLUE, spaceAfter=16))

    # ─── EXECUTIVE SUMMARY ────────────────────────────────────────────────────
    story.append(Paragraph("1. Executive Summary", h2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=8))

    # Strip markdown-style headers/bullets from AI text for clean PDF rendering
    clean_summary = (
        ai_summary
        .replace("**", "")
        .replace("──────────────────────────────────────────────────────────", "")
        .replace("─", "")
        .strip()
    )
    # Split into paragraphs; skip blank lines
    for para in clean_summary.split("\n"):
        para = para.strip()
        if not para:
            continue
        if para.startswith(("#", "##", "###")):
            para = para.lstrip("#").strip()
            story.append(Paragraph(para, h3))
        else:
            story.append(Paragraph(para, body))

    story.append(Spacer(1, 10))

    # ─── KPI SUMMARY TABLE ────────────────────────────────────────────────────
    summary = kpis.get("summary", {})
    story.append(Paragraph("2. Key Performance Indicators", h2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=8))

    kpi_rows = [
        ["KPI", "Current Value", "Status", "Benchmark"],
        ["Safety Score",          f"{summary.get('safety_score', 0):.1f} / 100",
         _rating(summary.get('safety_score', 0), 80, 60),       "≥ 85"],
        ["Energy Efficiency",     f"{summary.get('energy_score', 0):.1f} / 100",
         _rating(summary.get('energy_score', 0), 80, 65),       "≥ 85"],
        ["Production KPI",        f"{summary.get('production_kpi', 0):.1f}%",
         _rating(summary.get('production_kpi', 0), 90, 75),     "≥ 95%"],
        ["Downtime Risk",         f"{summary.get('downtime_prediction_pct', 0):.1f}%",
         _risk_rating(summary.get('downtime_prediction_pct', 0), 30, 50), "< 20%"],
        ["Active Alerts",         str(summary.get('active_alerts', 0)),
         "HIGH" if summary.get('active_alerts', 0) > 5 else "NORMAL",    "0"],
        ["Overdue Maintenance",   str(summary.get('overdue_maintenance', 0)),
         "HIGH" if summary.get('overdue_maintenance', 0) > 3 else "NORMAL","0"],
        ["CO₂ Emissions",         f"{summary.get('total_co2_tonnes', 0):.0f} tonnes",
         "MONITOR", "Baseline"],
        ["Energy Savings Potential",
         f"{summary.get('potential_savings_kwh', 0) / 1000:.0f} MWh",
         "OPPORTUNITY", "—"],
    ]

    kpi_table = Table(kpi_rows, colWidths=[55*mm, 42*mm, 38*mm, 35*mm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0),  _STEEL_BLUE),
        ("TEXTCOLOR",   (0,0), (-1,0),  _WHITE),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#f9fafb"), _WHITE]),
        ("GRID",        (0,0), (-1,-1), 0.4, _BORDER),
        ("TOPPADDING",  (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # ─── PLANT STATUS TABLE ───────────────────────────────────────────────────
    plant_summaries = kpis.get("plant_summaries", [])
    if plant_summaries:
        story.append(Paragraph("3. Plant Status Overview", h2))
        story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=8))

        plant_rows = [["Plant", "Status", "Failure Risk", "Safety", "Energy Eff.", "Production", "Downtime"]]
        for p in plant_summaries:
            plant_rows.append([
                p.get("plant_id", ""),
                p.get("status", ""),
                f"{p.get('failure_probability', 0)*100:.0f}%",
                f"{p.get('safety_score', 0):.0f}",
                f"{p.get('energy_efficiency', 0):.1f}%",
                f"{p.get('production_rate', 0):.0f} t/d",
                f"{p.get('downtime_hours', 0)}h",
            ])

        col_w = [35*mm, 25*mm, 25*mm, 22*mm, 25*mm, 28*mm, 22*mm]
        ptable = Table(plant_rows, colWidths=col_w)
        ptable.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0),  _STEEL_BLUE),
            ("TEXTCOLOR",    (0,0), (-1,0),  _WHITE),
            ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.HexColor("#f9fafb"), _WHITE]),
            ("GRID",         (0,0), (-1,-1), 0.4, _BORDER),
            ("TOPPADDING",   (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
            ("LEFTPADDING",  (0,0), (-1,-1), 5),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ]))

        # Colour-code status column
        status_col_map = {"CRITICAL": _RED, "WARNING": _AMBER, "NORMAL": _GREEN}
        for row_idx, p in enumerate(plant_summaries, start=1):
            col = status_col_map.get(p.get("status", ""), _LIGHT_GREY)
            ptable.setStyle(TableStyle([("TEXTCOLOR", (1, row_idx), (1, row_idx), col)]))

        story.append(ptable)
        story.append(Spacer(1, 14))

    # ─── PRIORITY ACTIONS ─────────────────────────────────────────────────────
    story.append(Paragraph("4. Priority Actions", h2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=8))

    actions = _derive_priority_actions(summary, plant_summaries)
    action_rows = [["#", "Priority", "Action", "Domain", "Impact (INR)", "Timeline"]]
    for a in actions:
        action_rows.append([
            str(a["rank"]), a["priority"], a["action"],
            a["domain"], a["impact"], a["timeline"],
        ])

    atbl = Table(action_rows, colWidths=[8*mm, 20*mm, 65*mm, 28*mm, 28*mm, 22*mm])
    atbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  _STEEL_BLUE),
        ("TEXTCOLOR",    (0,0), (-1,0),  _WHITE),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 7.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.HexColor("#f9fafb"), _WHITE]),
        ("GRID",         (0,0), (-1,-1), 0.4, _BORDER),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING",  (0,0), (-1,-1), 5),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("WORDWRAP",     (2,1), (2,-1),  "WORD"),
    ]))
    # Colour-code priority
    priority_colours = {"CRITICAL": _RED, "HIGH": _AMBER, "MEDIUM": _GREEN}
    for row_i, a in enumerate(actions, 1):
        col = priority_colours.get(a["priority"], _TEXT_DARK)
        atbl.setStyle(TableStyle([("TEXTCOLOR", (1, row_i), (1, row_i), col),
                                   ("FONTNAME",  (1, row_i), (1, row_i), "Helvetica-Bold")]))
    story.append(atbl)
    story.append(Spacer(1, 14))

    # ─── DOMAIN HIGHLIGHTS ────────────────────────────────────────────────────
    story.append(Paragraph("5. Domain Highlights", h2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=8))

    highlights = []
    if maint_data:
        highlights.append(("Maintenance", [
            f"Total work orders: {maint_data.get('total_tasks', 0)}",
            f"Overdue tasks: {maint_data.get('by_status', {}).get('Overdue', 0)}",
            f"Total maintenance cost: USD {maint_data.get('total_cost_usd', 0):,.0f}",
            f"Average prediction confidence: {maint_data.get('avg_confidence', 0)*100:.0f}%",
        ]))
    if safety_data:
        highlights.append(("Safety", [
            f"Total incidents: {safety_data.get('total_incidents', 0)}",
            f"Unresolved incidents: {safety_data.get('unresolved', 0)}",
            f"Safety score: {safety_data.get('safety_score', 0):.1f}/100",
            f"Average response time: {safety_data.get('avg_response_time_min', 0):.0f} minutes",
        ]))
    if energy_data:
        highlights.append(("Energy", [
            f"Average efficiency: {energy_data.get('avg_efficiency', 0)*100:.1f}%",
            f"Total consumption: {energy_data.get('total_consumption_kwh', 0)/1000:.0f} MWh",
            f"CO₂ emissions: {energy_data.get('total_co2_tonnes', 0):.0f} tonnes",
            f"Savings potential: ₹{energy_data.get('estimated_savings_inr', 0):.0f}L",
        ]))

    for domain, bullets in highlights:
        story.append(Paragraph(domain, h3))
        for b in bullets:
            story.append(Paragraph(f"• {b}", body))
        story.append(Spacer(1, 4))

    # ─── FOOTER ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"CONFIDENTIAL — Tata Steel Group Internal Use Only  |  "
        f"Generated by Sherlock v1.0 on {ts_str}  |  "
        f"Do not distribute without authorisation from the Plant Director.",
        centre,
    ))

    doc.build(story)
    return buf.getvalue()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rating(value: float, good: float, warn: float) -> str:
    if value >= good: return "GOOD"
    if value >= warn: return "WARNING"
    return "CRITICAL"


def _risk_rating(value: float, good: float, warn: float) -> str:
    """Lower is better for risk metrics."""
    if value <= good: return "GOOD"
    if value <= warn: return "WARNING"
    return "CRITICAL"


def _derive_priority_actions(summary: dict, plant_summaries: list) -> list[dict]:
    """Derive top 5 priority actions from live KPI data."""
    actions = []

    overdue = summary.get("overdue_maintenance", 0)
    if overdue > 0:
        actions.append({
            "rank": 1, "priority": "CRITICAL",
            "action": f"Address {overdue} overdue maintenance tasks — risk of unplanned failure",
            "domain": "Maintenance",
            "impact": f"₹{overdue * 4.5:.0f}L saved",
            "timeline": "24 hours",
        })

    unresolved_alerts = summary.get("active_alerts", 0)
    if unresolved_alerts > 0:
        actions.append({
            "rank": 2, "priority": "HIGH",
            "action": f"Resolve {unresolved_alerts} unresolved safety incidents across all plants",
            "domain": "Safety",
            "impact": "Risk −0.18 pts",
            "timeline": "48 hours",
        })

    savings_kwh = summary.get("potential_savings_kwh", 0)
    if savings_kwh > 0:
        actions.append({
            "rank": 3, "priority": "HIGH",
            "action": "Implement off-peak load-shifting and BOF heat recovery programme",
            "domain": "Energy",
            "impact": f"₹{savings_kwh*0.008/100000:.1f}L/month",
            "timeline": "1 week",
        })

    prod_kpi = summary.get("production_kpi", 100)
    if prod_kpi < 90:
        actions.append({
            "rank": 4, "priority": "MEDIUM",
            "action": "Rebalance Rolling Mill schedule — shift HRC-250 grade to Night shift",
            "domain": "Production",
            "impact": f"+{(90-prod_kpi)*25:.0f} t/day",
            "timeline": "Next shift",
        })

    critical_plants = [p for p in plant_summaries if p.get("status") == "CRITICAL"]
    if critical_plants:
        names = ", ".join(p["plant_id"] for p in critical_plants)
        actions.append({
            "rank": 5, "priority": "MEDIUM",
            "action": f"Escalate monitoring frequency for {names} — CRITICAL status flagged",
            "domain": "All Domains",
            "impact": "Preventive",
            "timeline": "Immediate",
        })

    # Pad to 5 if fewer actions derived
    while len(actions) < 5:
        actions.append({
            "rank": len(actions) + 1, "priority": "LOW",
            "action": "Continue routine monitoring — no immediate action required",
            "domain": "All Domains",
            "impact": "Ongoing",
            "timeline": "Monthly",
        })

    return actions[:5]
