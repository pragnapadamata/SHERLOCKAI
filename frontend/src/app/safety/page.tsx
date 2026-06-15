"use client";
import { useEffect, useState, useCallback } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { AIAnalysisCard } from "@/components/dashboard/AIAnalysisCard";
import { IncidentPieChart, SimpleBarChart } from "@/components/charts/Charts";
import { safetyAPI } from "@/lib/api";
import { SafetyIncident, SEVERITY_COLORS } from "@/types";
import {
  ShieldAlert, AlertTriangle, CheckCircle, Clock,
  Filter, Users, TrendingDown, ShieldCheck,
} from "lucide-react";

const PLANTS  = ["ALL", "Plant-A", "Plant-B", "Plant-C", "Plant-D"];
const SEV_OPTS = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"];

const SEV_BADGE: Record<string, string> = {
  CRITICAL: "badge-critical",
  HIGH:     "badge-high",
  MEDIUM:   "badge-medium",
  LOW:      "badge-low",
};

// Risk heatmap: plant × incident type grid
function RiskHeatmap({ incidents }: { incidents: SafetyIncident[] }) {
  const plants = ["Plant-A", "Plant-B", "Plant-C", "Plant-D"];
  const types  = [...new Set(incidents.map(i => i.incident_type))].slice(0, 6);

  if (incidents.length === 0) return (
    <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">Loading heatmap…</div>
  );

  const grid: Record<string, Record<string, number>> = {};
  plants.forEach(p => {
    grid[p] = {};
    types.forEach(t => { grid[p][t] = 0; });
  });
  incidents.forEach(inc => {
    if (grid[inc.plant_id]?.[inc.incident_type] !== undefined) {
      grid[inc.plant_id][inc.incident_type] += inc.risk_score;
    }
  });

  // Normalize
  const allVals = plants.flatMap(p => types.map(t => grid[p][t]));
  const maxVal  = Math.max(...allVals, 0.001);

  const cellColor = (v: number) => {
    const norm = v / maxVal;
    if (norm > 0.75) return "bg-red-500/80 text-white";
    if (norm > 0.5)  return "bg-amber-500/70 text-white";
    if (norm > 0.25) return "bg-yellow-500/50 text-gray-900";
    if (norm > 0)    return "bg-green-500/30 text-gray-300";
    return "bg-surface-50 text-gray-600";
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr>
            <th className="text-left text-muted-foreground py-2 pr-3 font-medium w-20">Plant</th>
            {types.map(t => (
              <th key={t} className="text-center text-muted-foreground py-2 px-1 font-medium">
                {t.length > 10 ? t.slice(0, 10) + "…" : t}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {plants.map(p => (
            <tr key={p}>
              <td className="text-white font-medium py-1.5 pr-3 text-xs">{p}</td>
              {types.map(t => {
                const v = grid[p][t];
                return (
                  <td key={t} className="px-1 py-1">
                    <div className={`rounded text-center py-1 px-1 font-mono text-xs ${cellColor(v)}`}>
                      {v > 0 ? v.toFixed(2) : "—"}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center gap-3 mt-3 pt-3 border-t border-card-border/30">
        <span className="text-xs text-muted-foreground">Risk scale:</span>
        {[
          { color: "bg-green-500/30", label: "Low" },
          { color: "bg-yellow-500/50", label: "Medium" },
          { color: "bg-amber-500/70", label: "High" },
          { color: "bg-red-500/80", label: "Critical" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1">
            <div className={`w-3 h-3 rounded ${color}`} />
            <span className="text-xs text-muted-foreground">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Safety score dial
function SafetyDial({ score }: { score: number }) {
  const pct   = score / 100;
  const size  = 120;
  const r     = 46;
  const cx    = size / 2;
  const cy    = size / 2;
  const circum = 2 * Math.PI * r;
  // Arc from bottom-left to bottom-right (220° sweep)
  const sweepDeg = 220;
  const startRad = (180 + (360 - sweepDeg) / 2) * (Math.PI / 180);
  const progress  = pct * sweepDeg;
  const progRad   = (180 + (360 - sweepDeg) / 2 + progress) * (Math.PI / 180);

  const arcPath = (startAngle: number, endAngle: number, inset = 0) => {
    const rr = r - inset;
    const sx = cx + rr * Math.cos(startAngle);
    const sy = cy + rr * Math.sin(startAngle);
    const ex = cx + rr * Math.cos(endAngle);
    const ey = cy + rr * Math.sin(endAngle);
    const large = endAngle - startAngle > Math.PI ? 1 : 0;
    return `M ${sx} ${sy} A ${rr} ${rr} 0 ${large} 1 ${ex} ${ey}`;
  };

  const endRad = (180 + (360 - sweepDeg) / 2 + sweepDeg) * (Math.PI / 180);
  const fillColor = score > 80 ? "#10b981" : score > 60 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Track */}
        <path d={arcPath(startRad, endRad)} fill="none" stroke="#2d3154" strokeWidth="8" strokeLinecap="round" />
        {/* Fill */}
        <path d={arcPath(startRad, progRad)} fill="none" stroke={fillColor} strokeWidth="8" strokeLinecap="round" />
        {/* Score text */}
        <text x={cx} y={cy + 4} textAnchor="middle" fontSize="20" fontWeight="700" fill="white">
          {score.toFixed(0)}
        </text>
        <text x={cx} y={cy + 18} textAnchor="middle" fontSize="9" fill="#6b7280">
          /100
        </text>
      </svg>
      <div className="text-xs text-muted-foreground -mt-2">Safety Score</div>
    </div>
  );
}

export default function SafetyPage() {
  const [incidents, setIncidents]   = useState<SafetyIncident[]>([]);
  const [analytics, setAnalytics]   = useState<any>(null);
  const [aiResult, setAiResult]     = useState<any>(null);
  const [loading, setLoading]       = useState(true);
  const [aiLoading, setAiLoading]   = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPlant, setSelectedPlant] = useState("ALL");
  const [sevFilter, setSevFilter]   = useState("ALL");
  const [showResolved, setShowResolved] = useState(false);
  const [page, setPage]             = useState(0);
  const PAGE_SIZE = 12;

  const fetchData = useCallback(async () => {
    try {
      const [incRes, analyticsRes] = await Promise.all([
        safetyAPI.getIncidents(selectedPlant, sevFilter === "ALL" ? undefined : sevFilter),
        safetyAPI.getAnalytics(selectedPlant),
      ]);
      setIncidents(incRes.data.incidents || []);
      setAnalytics(analyticsRes.data);
    } catch (e) {
      console.error("Safety fetch error:", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedPlant, sevFilter]);

  const fetchAI = useCallback(async () => {
    setAiLoading(true);
    try {
      const res = await safetyAPI.analyze(selectedPlant);
      setAiResult(res.data);
    } catch (e) {
      console.error("AI safety error:", e);
    } finally {
      setAiLoading(false);
    }
  }, [selectedPlant]);

  useEffect(() => {
    setLoading(true);
    setPage(0);
    fetchData();
  }, [fetchData]);

  useEffect(() => { fetchAI(); }, [fetchAI]);

  const handleRefresh = () => { setRefreshing(true); fetchData(); fetchAI(); };

  const filtered = incidents.filter(i => showResolved ? true : i.resolved === 0);
  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);

  // Pie chart data from analytics
  const sevPieData = analytics
    ? Object.entries(analytics.severity_counts || {}).map(([name, value]) => ({ name, value: value as number }))
    : [];
  const typePieData = analytics
    ? Object.entries(analytics.incident_types || {}).slice(0, 7).map(([name, value]) => ({ name, value: value as number }))
    : [];

  // Plant risk bar chart
  const plantRiskData = analytics
    ? Object.entries(analytics.plant_risk || {}).map(([name, value]) => ({ name, risk: Number((value as number * 100).toFixed(1)) }))
    : [];

  return (
    <AppShell>
      <Header
        title="Safety Monitoring"
        subtitle="Incident tracking, risk scoring, and preventive action management"
        onRefresh={handleRefresh}
        isRefreshing={refreshing}
      />

      <div className="p-6 space-y-6">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1 bg-card border border-card-border rounded-lg p-1">
            {PLANTS.map(p => (
              <button key={p} onClick={() => setSelectedPlant(p)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${selectedPlant === p ? "bg-steel-600 text-white" : "text-muted-foreground hover:text-white"}`}>
                {p}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <Filter size={13} className="text-muted-foreground" />
            <select value={sevFilter} onChange={e => setSevFilter(e.target.value)}
              className="bg-card border border-card-border rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-steel-500">
              {SEV_OPTS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <div
              onClick={() => setShowResolved(v => !v)}
              className={`w-8 h-4 rounded-full transition-colors ${showResolved ? "bg-steel-600" : "bg-surface-50"} relative`}
            >
              <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-all ${showResolved ? "left-4" : "left-0.5"}`} />
            </div>
            <span className="text-xs text-muted-foreground">Show resolved</span>
          </label>
        </div>

        {/* KPI row */}
        {loading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => <div key={i} className="h-28 bg-card rounded-xl animate-pulse" />)}
          </div>
        ) : analytics && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Safety Score"
              value={analytics.safety_score.toFixed(0)}
              unit="/100"
              icon={ShieldCheck}
              iconColor="text-green-400"
              status={analytics.safety_score > 80 ? "good" : analytics.safety_score > 60 ? "warning" : "critical"}
              subValue="Composite risk index"
            />
            <MetricCard
              title="Unresolved Incidents"
              value={analytics.unresolved_count}
              icon={AlertTriangle}
              iconColor="text-red-400"
              status={analytics.unresolved_count === 0 ? "good" : analytics.unresolved_count < 5 ? "warning" : "critical"}
              subValue={`${analytics.critical_count} critical severity`}
            />
            <MetricCard
              title="Resolution Rate"
              value={analytics.resolution_rate.toFixed(1)}
              unit="%"
              icon={CheckCircle}
              iconColor="text-green-400"
              status={analytics.resolution_rate > 85 ? "good" : analytics.resolution_rate > 65 ? "warning" : "critical"}
              subValue="Incidents resolved"
            />
            <MetricCard
              title="Avg Response Time"
              value={analytics.avg_response_time_minutes.toFixed(0)}
              unit=" min"
              icon={Clock}
              iconColor="text-amber-400"
              status={analytics.avg_response_time_minutes < 30 ? "good" : analytics.avg_response_time_minutes < 90 ? "warning" : "critical"}
              subValue="Mean time to respond"
            />
          </div>
        )}

        {/* Score + charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

          {/* Safety dial + plant risk */}
          <div className="card-glass rounded-xl p-5 border border-card-border flex flex-col gap-5">
            <div className="flex items-center justify-center pt-2">
              <SafetyDial score={analytics?.safety_score ?? 0} />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">Risk by Plant</h4>
              {plantRiskData.length > 0 ? (
                <SimpleBarChart
                  data={plantRiskData}
                  xKey="name"
                  bars={[{ key: "risk", color: "#ef4444", label: "Risk %" }]}
                  height={130}
                />
              ) : <div className="h-32 flex items-center justify-center text-muted-foreground text-xs">Loading…</div>}
            </div>
          </div>

          {/* Severity distribution pie */}
          <div className="card-glass rounded-xl p-5 border border-card-border">
            <h3 className="font-semibold text-white mb-1">Severity Breakdown</h3>
            <p className="text-xs text-muted-foreground mb-3">Distribution of incident severity</p>
            {sevPieData.length > 0 ? (
              <IncidentPieChart data={sevPieData} height={230} />
            ) : <div className="h-56 flex items-center justify-center text-muted-foreground text-sm">Loading…</div>}
          </div>

          {/* Incident type pie */}
          <div className="card-glass rounded-xl p-5 border border-card-border">
            <h3 className="font-semibold text-white mb-1">Incident Types</h3>
            <p className="text-xs text-muted-foreground mb-3">Most frequent incident categories</p>
            {typePieData.length > 0 ? (
              <IncidentPieChart data={typePieData} height={230} />
            ) : <div className="h-56 flex items-center justify-center text-muted-foreground text-sm">Loading…</div>}
          </div>
        </div>

        {/* Risk heatmap */}
        <div className="card-glass rounded-xl p-5 border border-card-border">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-white">Risk Heatmap</h3>
              <p className="text-xs text-muted-foreground">Cumulative risk score — plant × incident type</p>
            </div>
            <ShieldAlert size={15} className="text-muted-foreground" />
          </div>
          <RiskHeatmap incidents={incidents} />
        </div>

        {/* Incident table */}
        <div className="card-glass rounded-xl border border-card-border overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-card-border/40">
            <div>
              <h3 className="font-semibold text-white">Incident Log</h3>
              <p className="text-xs text-muted-foreground">
                {filtered.length} incidents · {showResolved ? "including resolved" : "unresolved only"}
              </p>
            </div>
            <span className="text-xs font-mono text-muted-foreground">Page {page + 1}/{Math.max(totalPages, 1)}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full data-table">
              <thead>
                <tr className="border-b border-card-border/40 bg-surface-50/50">
                  <th className="text-left">Timestamp</th>
                  <th className="text-left">Plant / Unit</th>
                  <th className="text-left">Incident Type</th>
                  <th className="text-left">Severity</th>
                  <th className="text-left">Risk Score</th>
                  <th className="text-left">Response</th>
                  <th className="text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  [...Array(8)].map((_, i) => (
                    <tr key={i}>
                      {[...Array(7)].map((_, j) => (
                        <td key={j}><div className="h-3 bg-card rounded animate-pulse w-16" /></td>
                      ))}
                    </tr>
                  ))
                ) : paginated.map((inc, i) => (
                  <tr key={i}>
                    <td><span className="text-xs font-mono text-muted-foreground">{String(inc.timestamp).slice(0, 16).replace("T", " ")}</span></td>
                    <td>
                      <div className="text-xs font-medium text-white">{inc.plant_id}</div>
                      <div className="text-xs text-muted-foreground">{inc.unit_id}</div>
                    </td>
                    <td><span className="text-xs text-gray-300">{inc.incident_type}</span></td>
                    <td><span className={SEV_BADGE[inc.severity]}>{inc.severity}</span></td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-12 h-1.5 bg-surface-50 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{
                            width: `${inc.risk_score * 100}%`,
                            background: inc.risk_score > 0.7 ? "#ef4444" : inc.risk_score > 0.4 ? "#f59e0b" : "#10b981",
                          }} />
                        </div>
                        <span className={`text-xs font-mono ${SEVERITY_COLORS[inc.severity]}`}>
                          {(inc.risk_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td><span className="text-xs text-muted-foreground">{inc.response_time_minutes} min</span></td>
                    <td>
                      {inc.resolved ? (
                        <span className="flex items-center gap-1 text-xs text-green-400">
                          <CheckCircle size={11} /> Resolved
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-red-400">
                          <AlertTriangle size={11} /> Open
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-card-border/40">
              <span className="text-xs text-muted-foreground">{page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} of {filtered.length}</span>
              <div className="flex gap-2">
                <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                  className="px-3 py-1 text-xs rounded bg-card border border-card-border text-muted-foreground hover:text-white disabled:opacity-40 disabled:cursor-not-allowed">Previous</button>
                <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
                  className="px-3 py-1 text-xs rounded bg-card border border-card-border text-muted-foreground hover:text-white disabled:opacity-40 disabled:cursor-not-allowed">Next</button>
              </div>
            </div>
          )}
        </div>

        {/* AI analysis */}
        <div>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">AI Safety Analysis</h2>
          <AIAnalysisCard
            agent={aiResult?.agent || "SAFETY"}
            response={aiResult?.response || ""}
            confidence={aiResult?.confidence || 0}
            reasoning={aiResult?.reasoning || ""}
            impact={aiResult?.impact || ""}
            loading={aiLoading && !aiResult}
          />
        </div>
      </div>
    </AppShell>
  );
}
