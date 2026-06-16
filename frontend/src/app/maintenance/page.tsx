"use client";
import { useEffect, useState, useCallback } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { AIAnalysisCard } from "@/components/dashboard/AIAnalysisCard";
import { SensorLineChart, SimpleBarChart } from "@/components/charts/Charts";
import { maintenanceAPI, dashboardAPI } from "@/lib/api";
import { MaintenancePrediction, SEVERITY_COLORS } from "@/types";
import {
  Wrench, AlertTriangle, CheckCircle, Clock,
  Thermometer, Activity, Gauge, Filter, RefreshCw,
  ChevronUp, ChevronDown, DollarSign,
} from "lucide-react";

const SEV_BADGE: Record<string, string> = {
  CRITICAL: "badge-critical",
  HIGH:     "badge-high",
  MEDIUM:   "badge-medium",
  LOW:      "badge-low",
};

const PLANTS = ["ALL", "Plant-A", "Plant-B", "Plant-C", "Plant-D"];
const STATUS_FILTERS = ["ALL", "Overdue", "In Progress", "Scheduled", "Completed"];

function SensorGauge({ label, value, max, unit, color }: {
  label: string; value: number; max: number; unit: string; color: string;
}) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between items-center">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-xs font-mono font-semibold text-white">{value.toFixed(1)}{unit}</span>
      </div>
      <div className="h-2 w-full bg-surface-50 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

export default function MaintenancePage() {
  const [predictions, setPredictions]   = useState<MaintenancePrediction[]>([]);
  const [tasks, setTasks]               = useState<any[]>([]);
  const [analytics, setAnalytics]       = useState<any>(null);
  const [timeseries, setTimeseries]     = useState<any[]>([]);
  const [aiResult, setAiResult]         = useState<any>(null);
  const [loading, setLoading]           = useState(true);
  const [aiLoading, setAiLoading]       = useState(false);
  const [refreshing, setRefreshing]     = useState(false);
  const [selectedPlant, setSelectedPlant] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [sortField, setSortField]       = useState<"failure_probability" | "vibration" | "temperature">("failure_probability");
  const [sortDir, setSortDir]           = useState<"desc" | "asc">("desc");
  const [page, setPage]                 = useState(0);
  const PAGE_SIZE = 10;

  const fetchData = useCallback(async () => {
    try {
      const [predRes, taskRes, analyticsRes, tsRes] = await Promise.all([
        maintenanceAPI.getPredictions(selectedPlant, 100),
        maintenanceAPI.getTasks(selectedPlant, statusFilter === "ALL" ? undefined : statusFilter),
        maintenanceAPI.getAnalytics(selectedPlant),
        dashboardAPI.getTimeseries(selectedPlant),
      ]);
      setPredictions(predRes.data.predictions || []);
      setTasks(taskRes.data.tasks || []);
      setAnalytics(analyticsRes.data);
      setTimeseries(tsRes.data.plant_series || []);
    } catch (e) {
      console.error("Maintenance fetch error:", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedPlant, statusFilter]);

  const fetchAI = useCallback(async () => {
    setAiLoading(true);
    try {
      const res = await maintenanceAPI.analyze(selectedPlant);
      setAiResult(res.data);
    } catch (e) {
      console.error("AI analysis error:", e);
    } finally {
      setAiLoading(false);
    }
  }, [selectedPlant]);

  useEffect(() => {
    setLoading(true);
    setPage(0);
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    fetchAI();
  }, [fetchAI]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
    fetchAI();
  };

  const handleSort = (field: typeof sortField) => {
    if (field === sortField) setSortDir(d => d === "desc" ? "asc" : "desc");
    else { setSortField(field); setSortDir("desc"); }
    setPage(0);
  };

  const sorted = [...predictions].sort((a, b) => {
    const av = a[sortField] as number;
    const bv = b[sortField] as number;
    return sortDir === "desc" ? bv - av : av - bv;
  });
  const paginated = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);

  // Build bar chart data from analytics
  const statusBarData = analytics ? Object.entries(analytics.status_counts || {}).map(([name, value]) => ({
    name, count: value as number,
  })) : [];

  const componentBarData = analytics ? Object.entries(analytics.component_failures || {}).slice(0, 6).map(([name, value]) => ({
    name: name.length > 12 ? name.slice(0, 12) + "…" : name,
    failures: value as number,
  })) : [];

  // Top-3 critical units for sensor gauges
  const criticalUnits = predictions.filter(p => p.severity === "CRITICAL" || p.severity === "HIGH").slice(0, 3);

  const SortIcon = ({ field }: { field: typeof sortField }) => (
    <span className="ml-1 opacity-60">
      {sortField === field ? (sortDir === "desc" ? "↓" : "↑") : "↕"}
    </span>
  );

  return (
    <AppShell>
      <Header
        title="Maintenance & Reliability"
        subtitle="Equipment health, failure prediction, and work order management"
        onRefresh={handleRefresh}
        isRefreshing={refreshing}
      />

      <div className="p-6 space-y-6">
        {/* Plant + status filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1 bg-card border border-card-border rounded-lg p-1">
            {PLANTS.map(p => (
              <button
                key={p}
                onClick={() => setSelectedPlant(p)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  selectedPlant === p
                    ? "bg-steel-600 text-white"
                    : "text-muted-foreground hover:text-white"
                }`}
              >
                {p}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <Filter size={13} className="text-muted-foreground" />
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="bg-card border border-card-border rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-steel-500"
            >
              {STATUS_FILTERS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        {/* KPI row */}
        {loading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => <div key={i} className="h-28 bg-card rounded-xl animate-pulse" />)}
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="High-Risk Units"
              value={predictions.filter(p => p.failure_probability > 0.6).length}
              icon={AlertTriangle}
              iconColor="text-red-400"
              status={predictions.filter(p => p.failure_probability > 0.6).length > 5 ? "critical" : "warning"}
              subValue={`of ${predictions.length} total units`}
            />
            <MetricCard
              title="Overdue Tasks"
              value={analytics?.status_counts?.Overdue ?? 0}
              icon={Clock}
              iconColor="text-amber-400"
              status={(analytics?.status_counts?.Overdue ?? 0) > 3 ? "critical" : "warning"}
              subValue={`${analytics?.status_counts?.["In Progress"] ?? 0} in progress`}
            />
            <MetricCard
              title="Avg Confidence"
              value={analytics ? (analytics.avg_confidence * 100).toFixed(0) : "—"}
              unit="%"
              icon={Gauge}
              iconColor="text-steel-400"
              status="neutral"
              subValue="AI prediction accuracy"
            />
            <MetricCard
              title="Maintenance Cost"
              value={analytics ? `$${(analytics.total_cost / 1000).toFixed(0)}k` : "—"}
              icon={DollarSign}
              iconColor="text-green-400"
              status="neutral"
              subValue="Current period total"
            />
          </div>
        )}

        {/* Main grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

          {/* Left 2/3: sensor chart + prediction table */}
          <div className="xl:col-span-2 space-y-5">

            {/* Sensor timeseries */}
            <div className="card-glass rounded-xl p-5 border border-card-border">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-white">Sensor Trend</h3>
                  <p className="text-xs text-muted-foreground">Failure probability & vibration over time</p>
                </div>
                <Activity size={15} className="text-muted-foreground" />
              </div>
              {timeseries.length > 0 ? (
                <SensorLineChart data={timeseries} height={210} />
              ) : (
                <div className="h-52 flex items-center justify-center">
                  <div className="w-6 h-6 border-2 border-steel-500 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>

            {/* Prediction table */}
            <div className="card-glass rounded-xl border border-card-border overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-card-border/40">
                <div>
                  <h3 className="font-semibold text-white">Failure Predictions</h3>
                  <p className="text-xs text-muted-foreground">{sorted.length} units · sorted by {sortField.replace("_", " ")}</p>
                </div>
                <span className="text-xs text-muted-foreground font-mono">
                  Page {page + 1}/{Math.max(totalPages, 1)}
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full data-table">
                  <thead>
                    <tr className="border-b border-card-border/40 bg-surface-50/50">
                      <th className="text-left">Plant / Unit</th>
                      <th
                        className="text-left cursor-pointer hover:text-white select-none"
                        onClick={() => handleSort("failure_probability")}
                      >
                        Failure Risk <SortIcon field="failure_probability" />
                      </th>
                      <th
                        className="text-left cursor-pointer hover:text-white select-none"
                        onClick={() => handleSort("vibration")}
                      >
                        Vibration <SortIcon field="vibration" />
                      </th>
                      <th
                        className="text-left cursor-pointer hover:text-white select-none"
                        onClick={() => handleSort("temperature")}
                      >
                        Temp <SortIcon field="temperature" />
                      </th>
                      <th className="text-left">Severity</th>
                      <th className="text-left">Recommended Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      [...Array(8)].map((_, i) => (
                        <tr key={i}>
                          {[...Array(6)].map((_, j) => (
                            <td key={j}><div className="h-3 bg-card rounded animate-pulse w-20" /></td>
                          ))}
                        </tr>
                      ))
                    ) : paginated.map((p, i) => (
                      <tr key={i} className="group">
                        <td>
                          <div className="font-medium text-white text-xs">{p.plant_id}</div>
                          <div className="text-xs text-muted-foreground">{p.unit_id}</div>
                        </td>
                        <td>
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-surface-50 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${p.failure_probability * 100}%`,
                                  background: p.failure_probability > 0.7 ? "#ef4444" : p.failure_probability > 0.5 ? "#f59e0b" : "#10b981",
                                }}
                              />
                            </div>
                            <span className={`text-xs font-mono font-semibold ${SEVERITY_COLORS[p.severity]}`}>
                              {(p.failure_probability * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                        <td>
                          <span className="text-xs font-mono text-amber-300">{p.vibration.toFixed(2)} m/s²</span>
                        </td>
                        <td>
                          <span className="text-xs font-mono text-orange-300">{p.temperature.toFixed(0)}°C</span>
                        </td>
                        <td>
                          <span className={SEV_BADGE[p.severity]}>{p.severity}</span>
                        </td>
                        <td>
                          <span className="text-xs text-gray-400 leading-tight">{p.recommended_action}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-5 py-3 border-t border-card-border/40">
                  <span className="text-xs text-muted-foreground">
                    {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, sorted.length)} of {sorted.length}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage(p => Math.max(0, p - 1))}
                      disabled={page === 0}
                      className="px-3 py-1 text-xs rounded bg-card border border-card-border text-muted-foreground hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                      disabled={page >= totalPages - 1}
                      className="px-3 py-1 text-xs rounded bg-card border border-card-border text-muted-foreground hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right 1/3: equipment status + status breakdown */}
          <div className="space-y-5">

            {/* Critical unit gauges */}
            <div className="card-glass rounded-xl p-5 border border-card-border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-white">Critical Equipment</h3>
                <span className="badge-critical">{predictions.filter(p => p.severity === "CRITICAL").length} CRITICAL</span>
              </div>
              {criticalUnits.length === 0 && !loading && (
                <div className="flex items-center gap-2 py-4">
                  <CheckCircle size={16} className="text-green-400" />
                  <span className="text-sm text-green-400">No critical units</span>
                </div>
              )}
              <div className="space-y-5">
                {criticalUnits.map((u, i) => (
                  <div key={i} className="p-3 rounded-lg bg-surface-50 border border-card-border/60">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="text-xs font-semibold text-white">{u.unit_id}</div>
                        <div className="text-xs text-muted-foreground">{u.plant_id}</div>
                      </div>
                      <span className={SEV_BADGE[u.severity]}>{u.severity}</span>
                    </div>
                    <div className="space-y-2">
                      <SensorGauge label="Vibration" value={u.vibration} max={10} unit=" m/s²" color="#f59e0b" />
                      <SensorGauge label="Temperature" value={u.temperature} max={1650} unit="°C" color="#ef4444" />
                      <SensorGauge label="Pressure" value={u.pressure} max={18.5} unit=" bar" color="#06b6d4" />
                      <SensorGauge label="Failure Risk" value={u.failure_probability * 100} max={100} unit="%" color={u.failure_probability > 0.7 ? "#ef4444" : "#f59e0b"} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Task status breakdown */}
            {statusBarData.length > 0 && (
              <div className="card-glass rounded-xl p-5 border border-card-border">
                <h3 className="font-semibold text-white mb-4">Task Status</h3>
                <SimpleBarChart
                  data={statusBarData}
                  xKey="name"
                  bars={[{ key: "count", color: "#06b6d4", label: "Tasks" }]}
                  height={160}
                />
              </div>
            )}

            {/* Component failures */}
            {componentBarData.length > 0 && (
              <div className="card-glass rounded-xl p-5 border border-card-border">
                <h3 className="font-semibold text-white mb-1">Overdue by Component</h3>
                <p className="text-xs text-muted-foreground mb-4">Top failing components</p>
                <SimpleBarChart
                  data={componentBarData}
                  xKey="name"
                  bars={[{ key: "failures", color: "#ef4444", label: "Overdue" }]}
                  height={160}
                />
              </div>
            )}
          </div>
        </div>

        {/* Work order table */}
        <div className="card-glass rounded-xl border border-card-border overflow-hidden">
          <div className="px-5 py-4 border-b border-card-border/40">
            <h3 className="font-semibold text-white">Work Orders</h3>
            <p className="text-xs text-muted-foreground">{tasks.length} tasks · {statusFilter === "ALL" ? "all statuses" : statusFilter}</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full data-table">
              <thead>
                <tr className="border-b border-card-border/40 bg-surface-50/50">
                  <th className="text-left">Date</th>
                  <th className="text-left">Plant / Unit</th>
                  <th className="text-left">Type</th>
                  <th className="text-left">Component</th>
                  <th className="text-left">Status</th>
                  <th className="text-left">Cost (USD)</th>
                  <th className="text-left">Duration</th>
                  <th className="text-left">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  [...Array(6)].map((_, i) => (
                    <tr key={i}>
                      {[...Array(8)].map((_, j) => (
                        <td key={j}><div className="h-3 bg-card rounded animate-pulse w-16" /></td>
                      ))}
                    </tr>
                  ))
                ) : tasks.slice(0, 20).map((t, i) => {
                  const statusColor: Record<string, string> = {
                    Completed: "badge-low",
                    Scheduled: "badge-normal",
                    "In Progress": "badge-medium",
                    Overdue: "badge-critical",
                  };
                  return (
                    <tr key={i}>
                      <td><span className="text-xs font-mono text-muted-foreground">{String(t.date).slice(0, 10)}</span></td>
                      <td>
                        <div className="text-xs font-medium text-white">{t.plant_id}</div>
                        <div className="text-xs text-muted-foreground">{t.unit_id}</div>
                      </td>
                      <td><span className="text-xs text-gray-300">{t.maintenance_type}</span></td>
                      <td><span className="text-xs text-gray-300">{t.component}</span></td>
                      <td><span className={statusColor[t.status] || "badge-normal"}>{t.status}</span></td>
                      <td><span className="text-xs font-mono text-green-400">${Number(t.cost_usd).toLocaleString()}</span></td>
                      <td><span className="text-xs text-gray-400">{t.duration_hours}h</span></td>
                      <td>
                        <div className="flex items-center gap-1.5">
                          <div className="w-10 h-1 bg-surface-50 rounded-full overflow-hidden">
                            <div className="h-full bg-steel-500 rounded-full" style={{ width: `${Number(t.confidence_score) * 100}%` }} />
                          </div>
                          <span className="text-xs font-mono text-muted-foreground">{(Number(t.confidence_score) * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI analysis */}
        <div>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">AI Recommendations</h2>
          <AIAnalysisCard
            agent={aiResult?.agent || "MAINTENANCE"}
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
