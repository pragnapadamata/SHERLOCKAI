"use client";
import { useEffect, useState, useCallback } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { AIAnalysisCard } from "@/components/dashboard/AIAnalysisCard";
import { ProductionBarChart, SimpleBarChart, SensorLineChart } from "@/components/charts/Charts";
import { productionAPI, dashboardAPI } from "@/lib/api";
import {
  Factory, Clock, AlertTriangle,
  Target, Users, Filter,
} from "lucide-react";

const PLANTS = ["ALL", "Plant-A", "Plant-B", "Plant-C", "Plant-D"];
const PRIORITY_BADGE: Record<string, string> = {
  HIGH:   "badge-critical",
  MEDIUM: "badge-medium",
  LOW:    "badge-low",
};
const PRIORITY_BG: Record<string, string> = {
  HIGH:   "border-l-red-500",
  MEDIUM: "border-l-yellow-500",
  LOW:    "border-l-green-500",
};

function KPIGauge({ label, value, target, unit }: { label: string; value: number; target: number; unit?: string }) {
  const pct = Math.min(100, (value / target) * 100);
  const color = pct >= 90 ? "#10b981" : pct >= 75 ? "#f59e0b" : "#ef4444";
  const r = 38; const cx = 50; const cy = 50;
  const sweepDeg = 220;
  const startAngle = (180 + (360 - sweepDeg) / 2) * (Math.PI / 180);
  const endAngle   = (180 + (360 - sweepDeg) / 2 + sweepDeg) * (Math.PI / 180);
  const fillAngle  = (180 + (360 - sweepDeg) / 2 + (pct / 100) * sweepDeg) * (Math.PI / 180);
  const arc = (a1: number, a2: number) => {
    const sx = cx + r * Math.cos(a1); const sy = cy + r * Math.sin(a1);
    const ex = cx + r * Math.cos(a2); const ey = cy + r * Math.sin(a2);
    const lg = a2 - a1 > Math.PI ? 1 : 0;
    return `M ${sx} ${sy} A ${r} ${r} 0 ${lg} 1 ${ex} ${ey}`;
  };
  return (
    <div className="flex flex-col items-center">
      <svg width={100} height={90} viewBox="0 0 100 100">
        <path d={arc(startAngle, endAngle)} fill="none" stroke="#2d3154" strokeWidth="7" strokeLinecap="round" />
        <path d={arc(startAngle, fillAngle)} fill="none" stroke={color} strokeWidth="7" strokeLinecap="round" />
        <text x={cx} y={cy + 3}  textAnchor="middle" fontSize="14" fontWeight="700" fill="white">{value.toFixed(0)}</text>
        <text x={cx} y={cy + 14} textAnchor="middle" fontSize="7"  fill="#6b7280">{unit || ""}</text>
      </svg>
      <div className="text-xs text-muted-foreground -mt-1 text-center">{label}</div>
      <div className="text-xs font-medium mt-0.5" style={{ color }}>{pct.toFixed(0)}% of target</div>
    </div>
  );
}

export default function ProductionPage() {
  const [summary,   setSummary]   = useState<any>(null);
  const [schedule,  setSchedule]  = useState<any[]>([]);
  const [timeseries,setTimeseries]= useState<any[]>([]);
  const [aiResult,  setAiResult]  = useState<any>(null);
  const [loading,   setLoading]   = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [refreshing,setRefreshing]= useState(false);
  const [selectedPlant, setSelectedPlant] = useState("ALL");
  const [schedPage, setSchedPage] = useState(0);
  const [schedFilter, setSchedFilter] = useState("ALL");
  const SCHED_SIZE = 10;

  const fetchData = useCallback(async () => {
    try {
      const [sumRes, schedRes, tsRes] = await Promise.all([
        productionAPI.getSummary(selectedPlant),
        productionAPI.getSchedule(),
        dashboardAPI.getTimeseries(selectedPlant),
      ]);
      setSummary(sumRes.data);
      setSchedule(schedRes.data.schedule || []);
      setTimeseries(tsRes.data.plant_series || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); setRefreshing(false); }
  }, [selectedPlant]);

  const fetchAI = useCallback(async () => {
    setAiLoading(true);
    try { const r = await productionAPI.analyze(selectedPlant); setAiResult(r.data); }
    catch (e) { console.error(e); }
    finally { setAiLoading(false); }
  }, [selectedPlant]);

  useEffect(() => { setLoading(true); fetchData(); }, [fetchData]);
  useEffect(() => { fetchAI(); }, [fetchAI]);

  const handleRefresh = () => { setRefreshing(true); fetchData(); fetchAI(); };

  // Plant bar chart data
  const plantBarData = summary
    ? Object.entries((summary.by_plant as any)?.mean || {}).map(([name, val]) => ({
        name,
        actual: Number((val as number).toFixed(0)),
        target: summary.target,
      }))
    : [];

  // Unit bar chart
  const unitBarData = summary
    ? Object.entries(summary.by_unit || {}).slice(0, 6).map(([name, val]) => ({
        name: name.length > 14 ? name.slice(0, 14) + "…" : name,
        rate: Number((val as number).toFixed(0)),
      }))
    : [];

  // Downtime bar
  const downtimeData = summary
    ? Object.entries(summary.downtime_hours || {}).map(([name, val]) => ({
        name, hours: val as number,
      }))
    : [];

  // Filtered schedule
  const filteredSched = schedule.filter(s =>
    schedFilter === "ALL" || s.priority === schedFilter
  );
  const schedPages = Math.ceil(filteredSched.length / SCHED_SIZE);
  const schedSlice = filteredSched.slice(schedPage * SCHED_SIZE, (schedPage + 1) * SCHED_SIZE);

  const att = summary ? Math.min(100, (summary.actual_avg / summary.target) * 100) : 0;
  const attColor = att >= 90 ? "text-green-400" : att >= 75 ? "text-amber-400" : "text-red-400";

  return (
    <AppShell>
      <Header
        title="Production & Operations"
        subtitle="Throughput analysis, scheduling, and bottleneck management"
        onRefresh={handleRefresh}
        isRefreshing={refreshing}
      />
      <div className="p-6 space-y-6">

        {/* Plant filter */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1 bg-card border border-card-border rounded-lg p-1">
            {PLANTS.map(p => (
              <button key={p} onClick={() => setSelectedPlant(p)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${selectedPlant === p ? "bg-steel-600 text-white" : "text-muted-foreground hover:text-white"}`}>
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* KPI row */}
        {loading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => <div key={i} className="h-28 bg-card rounded-xl animate-pulse" />)}
          </div>
        ) : summary && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Avg Production Rate"
              value={summary.actual_avg.toFixed(0)}
              unit=" t/day"
              icon={Factory}
              iconColor="text-steel-400"
              status={att >= 90 ? "good" : att >= 75 ? "warning" : "critical"}
              subValue={`Target: ${summary.target} t/day`}
            />
            <MetricCard
              title="KPI Attainment"
              value={att.toFixed(1)}
              unit="%"
              icon={Target}
              iconColor={attColor}
              status={att >= 90 ? "good" : att >= 75 ? "warning" : "critical"}
              subValue={`Gap: ${(summary.target - summary.actual_avg).toFixed(0)} t/day`}
            />
            <MetricCard
              title="Scheduled Tasks"
              value={summary.scheduled_maintenance_impacts}
              icon={Clock}
              iconColor="text-amber-400"
              status={summary.scheduled_maintenance_impacts > 5 ? "warning" : "neutral"}
              subValue="Maintenance overlaps"
            />
            <MetricCard
              title="Downtime Events"
              value={Object.values(summary.downtime_hours || {}).reduce((a: number, b) => a + (b as number), 0)}
              unit=" h"
              icon={AlertTriangle}
              iconColor="text-red-400"
              status="warning"
              subValue="Across all plants"
            />
          </div>
        )}

        {/* Gauges + charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* KPI gauges */}
          <div className="card-glass rounded-xl p-5 border border-card-border">
            <h3 className="font-semibold text-white mb-5">Production Gauges</h3>
            {summary ? (
              <div className="grid grid-cols-2 gap-4">
                <KPIGauge label="Overall Rate" value={summary.actual_avg} target={summary.target} unit="t/day" />
                <KPIGauge label="Attainment"   value={att}              target={100}              unit="%" />
                {Object.entries((summary.by_plant as any)?.mean || {}).slice(0, 2).map(([plant, val]) => (
                  <KPIGauge key={plant} label={plant} value={val as number} target={summary.target} unit="t/day" />
                ))}
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-steel-500 border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>

          {/* Throughput by plant */}
          <div className="card-glass rounded-xl p-5 border border-card-border">
            <h3 className="font-semibold text-white mb-1">Plant Throughput</h3>
            <p className="text-xs text-muted-foreground mb-4">Actual vs target (t/day)</p>
            {plantBarData.length > 0 ? (
              <ProductionBarChart data={plantBarData} height={220} />
            ) : (
              <div className="h-56 flex items-center justify-center text-muted-foreground text-sm">Loading…</div>
            )}
          </div>

          {/* Downtime by plant */}
          <div className="card-glass rounded-xl p-5 border border-card-border">
            <h3 className="font-semibold text-white mb-1">Downtime Hours</h3>
            <p className="text-xs text-muted-foreground mb-4">Accumulated downtime per plant</p>
            {downtimeData.length > 0 ? (
              <SimpleBarChart
                data={downtimeData}
                xKey="name"
                bars={[{ key: "hours", color: "#ef4444", label: "Hours" }]}
                height={220}
              />
            ) : (
              <div className="h-56 flex items-center justify-center text-muted-foreground text-sm">Loading…</div>
            )}
          </div>
        </div>

        {/* Production trend + unit breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card-glass rounded-xl p-5 border border-card-border">
            <h3 className="font-semibold text-white mb-1">Production Trend</h3>
            <p className="text-xs text-muted-foreground mb-4">Rate over time with failure probability overlay</p>
            {timeseries.length > 0 ? (
              <SensorLineChart data={timeseries} height={200} />
            ) : (
              <div className="h-52 flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-steel-500 border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>

          {/* Bottleneck analysis */}
          <div className="card-glass rounded-xl p-5 border border-card-border">
            <h3 className="font-semibold text-white mb-1">Bottleneck Analysis</h3>
            <p className="text-xs text-muted-foreground mb-4">Lowest-throughput units</p>
            {unitBarData.length > 0 ? (
              <SimpleBarChart
                data={unitBarData}
                xKey="name"
                bars={[{ key: "rate", color: "#9f1239", label: "t/day" }]}
                height={200}
              />
            ) : (
              <div className="h-52 flex items-center justify-center text-muted-foreground text-sm">Loading…</div>
            )}
            {/* Bottleneck callout */}
            {unitBarData.length > 0 && (
              <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-center gap-1.5 mb-1">
                  <AlertTriangle size={12} className="text-amber-400" />
                  <span className="text-xs font-semibold text-amber-400">Primary Bottleneck</span>
                </div>
                <p className="text-xs text-gray-400">
                  <span className="text-white font-medium">{unitBarData[0]?.name}</span> is the
                  lowest-throughput unit at {unitBarData[0]?.rate} t/day. Recommend priority
                  maintenance scheduling.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Schedule table */}
        <div className="card-glass rounded-xl border border-card-border overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 border-b border-card-border/40">
            <div>
              <h3 className="font-semibold text-white">7-Day Production Schedule</h3>
              <p className="text-xs text-muted-foreground">{filteredSched.length} shifts planned</p>
            </div>
            <div className="flex items-center gap-2">
              <Filter size={13} className="text-muted-foreground" />
              <select
                value={schedFilter}
                onChange={e => { setSchedFilter(e.target.value); setSchedPage(0); }}
                className="bg-card border border-card-border rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-steel-500"
              >
                {["ALL", "HIGH", "MEDIUM", "LOW"].map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full data-table">
              <thead>
                <tr className="border-b border-card-border/40 bg-surface-50/50">
                  <th className="text-left">Date</th>
                  <th className="text-left">Shift</th>
                  <th className="text-left">Plant</th>
                  <th className="text-left">Grade</th>
                  <th className="text-left">Target (t)</th>
                  <th className="text-left">Crew</th>
                  <th className="text-left">Priority</th>
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
                ) : schedSlice.map((s, i) => (
                  <tr key={i} className={`border-l-2 ${PRIORITY_BG[s.priority] || "border-l-transparent"}`}>
                    <td><span className="text-xs font-mono text-muted-foreground">{s.date}</span></td>
                    <td><span className="text-xs text-gray-300">{s.shift}</span></td>
                    <td><span className="text-xs font-medium text-white">{s.plant}</span></td>
                    <td>
                      <span className="text-xs px-2 py-0.5 rounded bg-steel-600/20 text-steel-300 font-mono border border-steel-600/20">
                        {s.grade}
                      </span>
                    </td>
                    <td><span className="text-xs font-mono text-white">{s.target_tonnes.toLocaleString()}</span></td>
                    <td>
                      <div className="flex items-center gap-1.5">
                        <Users size={11} className="text-muted-foreground" />
                        <span className="text-xs text-gray-300">{s.allocated_crew}</span>
                      </div>
                    </td>
                    <td><span className={PRIORITY_BADGE[s.priority]}>{s.priority}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {schedPages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-card-border/40">
              <span className="text-xs text-muted-foreground">
                {schedPage * SCHED_SIZE + 1}–{Math.min((schedPage + 1) * SCHED_SIZE, filteredSched.length)} of {filteredSched.length}
              </span>
              <div className="flex gap-2">
                <button onClick={() => setSchedPage(p => Math.max(0, p - 1))} disabled={schedPage === 0}
                  className="px-3 py-1 text-xs rounded bg-card border border-card-border text-muted-foreground hover:text-white disabled:opacity-40 disabled:cursor-not-allowed">
                  Previous
                </button>
                <button onClick={() => setSchedPage(p => Math.min(schedPages - 1, p + 1))} disabled={schedPage >= schedPages - 1}
                  className="px-3 py-1 text-xs rounded bg-card border border-card-border text-muted-foreground hover:text-white disabled:opacity-40 disabled:cursor-not-allowed">
                  Next
                </button>
              </div>
            </div>
          )}
        </div>

        {/* AI analysis */}
        <div>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">AI Production Analysis</h2>
          <AIAnalysisCard
            agent={aiResult?.agent || "PRODUCTION"}
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
