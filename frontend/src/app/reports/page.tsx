"use client";
import { useEffect, useState, useCallback } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { AIAnalysisCard } from "@/components/dashboard/AIAnalysisCard";
import { SimpleBarChart, IncidentPieChart } from "@/components/charts/Charts";
import { reportsAPI } from "@/lib/api";
import {
  FileText, Download, BarChart3, Shield, Zap, Wrench,
  TrendingUp, TrendingDown, CheckCircle, AlertTriangle,
  Calendar, Printer, ChevronDown, ChevronUp,
  Clock, DollarSign, Leaf, Loader2,
} from "lucide-react";

type ReportType = "executive" | "maintenance" | "safety" | "energy";

const REPORT_TABS: { key: ReportType; label: string; icon: React.ElementType; color: string }[] = [
  { key: "executive",   label: "Executive Summary", icon: BarChart3, color: "#9f1239" },
  { key: "maintenance", label: "Maintenance",        icon: Wrench,    color: "#f59e0b" },
  { key: "safety",      label: "Safety",             icon: Shield,    color: "#ef4444" },
  { key: "energy",      label: "Energy",             icon: Zap,       color: "#10b981" },
];

function ReportCard({
  icon: Icon, title, value, unit, delta, deltaPositive, sub, color,
}: {
  icon: React.ElementType; title: string; value: string; unit?: string;
  delta?: string; deltaPositive?: boolean; sub?: string; color: string;
}) {
  return (
    <div className="p-4 rounded-xl border transition-all hover:border-opacity-60"
      style={{ background: `${color}08`, borderColor: `${color}20` }}>
      <div className="flex items-center justify-between mb-3">
        <div className="p-2 rounded-lg" style={{ background: `${color}20` }}>
          <Icon size={15} style={{ color }} />
        </div>
        {delta && (
          <div className={`flex items-center gap-1 text-xs font-medium px-1.5 py-0.5 rounded-full ${
            deltaPositive
              ? "text-green-400 bg-green-500/10"
              : "text-red-400 bg-red-500/10"
          }`}>
            {deltaPositive ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
            {delta}
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-white mb-0.5">
        {value}
        {unit && <span className="text-base font-normal text-gray-400 ml-1">{unit}</span>}
      </div>
      <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide">{title}</div>
      {sub && <div className="text-xs text-gray-600 mt-1">{sub}</div>}
    </div>
  );
}

function Section({ title, children, defaultOpen = true }: {
  title: string; children: React.ReactNode; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="card-glass rounded-xl border border-card-border overflow-hidden">
      <button onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-card/30 transition-colors">
        <h3 className="font-semibold text-white text-sm">{title}</h3>
        {open ? <ChevronUp size={15} className="text-muted-foreground" /> : <ChevronDown size={15} className="text-muted-foreground" />}
      </button>
      {open && <div className="px-5 pb-5">{children}</div>}
    </div>
  );
}

function KPIRow({ label, value, status }: { label: string; value: string; status: "good" | "warning" | "critical" | "neutral" }) {
  const color = { good: "text-green-400", warning: "text-amber-400", critical: "text-red-400", neutral: "text-gray-400" }[status];
  const icon  = { good: CheckCircle, warning: AlertTriangle, critical: AlertTriangle, neutral: Clock }[status];
  const Icon  = icon;
  return (
    <div className="flex items-center justify-between py-2 border-b border-card-border/20 last:border-0">
      <div className="flex items-center gap-2">
        <Icon size={12} className={color} />
        <span className="text-sm text-gray-300">{label}</span>
      </div>
      <span className={`text-sm font-semibold font-mono ${color}`}>{value}</span>
    </div>
  );
}

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<ReportType>("executive");
  const [execData,  setExecData]  = useState<any>(null);
  const [maintData, setMaintData] = useState<any>(null);
  const [safetyData,setSafetyData]= useState<any>(null);
  const [energyData,setEnergyData]= useState<any>(null);
  const [loading,   setLoading]   = useState(true);
  const [refreshing,setRefreshing]= useState(false);
  const [pdfLoading,setPdfLoading]= useState(false);
  const [generatedAt, setGeneratedAt] = useState<string>("");

  const fetchAll = useCallback(async () => {
    try {
      const [eRes, mRes, sRes, enRes] = await Promise.all([
        reportsAPI.getExecutiveSummary(),
        reportsAPI.getMaintenanceReport(),
        reportsAPI.getSafetyReport(),
        reportsAPI.getEnergyReport(),
      ]);
      setExecData(eRes.data);
      setMaintData(mRes.data);
      setSafetyData(sRes.data);
      setEnergyData(enRes.data);
      setGeneratedAt(new Date().toLocaleString("en-IN", {
        day: "numeric", month: "short", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      }));
    } catch (e) { console.error(e); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);
  const handleRefresh = () => { setRefreshing(true); fetchAll(); };

  const handlePrint = () => window.print();

  const handlePdfExport = async () => {
    setPdfLoading(true);
    try {
      const res = await reportsAPI.getBoardPdf();
      const url = URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const a   = document.createElement("a");
      a.href = url;
      a.download = `TataSteel_Sherlock_BoardReport_${Date.now()}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("PDF export failed:", e);
    } finally {
      setPdfLoading(false);
    }
  };

  const handleExport = (type: string) => {
    const data = { executive: execData, maintenance: maintData, safety: safetyData, energy: energyData };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url; a.download = `sherlock-report-${type}-${Date.now()}.json`; a.click();
    URL.revokeObjectURL(url);
  };

  // Build chart data
  const maintStatusData = maintData
    ? Object.entries(maintData.by_status || {}).map(([name, val]) => ({ name, count: val as number }))
    : [];
  const maintTypeData = maintData
    ? Object.entries(maintData.by_type || {}).map(([name, val]) => ({ name, count: val as number }))
    : [];
  const safetySevData = safetyData
    ? Object.entries(safetyData.by_severity || {}).map(([name, value]) => ({ name, value: value as number }))
    : [];
  const safetyTypeData = safetyData
    ? Object.entries(safetyData.by_type || {}).slice(0, 6).map(([name, value]) => ({ name, value: value as number }))
    : [];
  const energyPlantData = energyData
    ? Object.entries(energyData.by_plant || {}).map(([name, val]) => ({
        name, efficiency: Number(((val as number) * 100).toFixed(1)),
      }))
    : [];

  const ekpis = execData?.kpis?.summary;

  return (
    <AppShell>
      <Header
        title="Reports & Analytics"
        subtitle="Executive summaries, operational KPIs, and trend analysis"
        onRefresh={handleRefresh}
        isRefreshing={refreshing}
      />

      <div className="p-6 space-y-6">

        {/* Top action bar */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Tabs */}
          <div className="flex items-center gap-1 bg-card border border-card-border rounded-lg p-1">
            {REPORT_TABS.map(tab => {
              const Icon = tab.icon;
              return (
                <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    activeTab === tab.key ? "bg-steel-600 text-white" : "text-muted-foreground hover:text-white"
                  }`}>
                  <Icon size={12} />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {generatedAt && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Calendar size={12} />
                {generatedAt}
              </div>
            )}
            <button onClick={handlePrint}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-card-border text-xs text-muted-foreground hover:text-white transition-all">
              <Printer size={13} />Print
            </button>
            <button
              onClick={handlePdfExport}
              disabled={pdfLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-600 disabled:opacity-60 text-xs text-white transition-all font-medium"
            >
              {pdfLoading
                ? <><Loader2 size={13} className="animate-spin" />Generating…</>
                : <><FileText size={13} />Board PDF</>
              }
            </button>
            <button onClick={() => handleExport(activeTab)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-steel-600 hover:bg-steel-500 text-xs text-white transition-all">
              <Download size={13} />Export JSON
            </button>
          </div>
        </div>

        {/* ── EXECUTIVE SUMMARY TAB ── */}
        {activeTab === "executive" && (
          <div className="space-y-5">
            {/* Headline KPIs */}
            {loading ? (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[...Array(8)].map((_, i) => <div key={i} className="h-28 bg-card rounded-xl animate-pulse" />)}
              </div>
            ) : ekpis && (
              <>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <ReportCard icon={Shield}      title="Safety Score"       value={ekpis.safety_score.toFixed(0)}              unit="/100" color="#10b981" delta="+2.1%" deltaPositive />
                  <ReportCard icon={Zap}         title="Energy Score"       value={ekpis.energy_score.toFixed(0)}              unit="/100" color="#06b6d4" delta="-0.8%" deltaPositive={false} />
                  <ReportCard icon={BarChart3}   title="Production KPI"     value={ekpis.production_kpi.toFixed(1)}            unit="%" color="#db2777" delta="+5.3%" deltaPositive />
                  <ReportCard icon={AlertTriangle} title="Downtime Risk"    value={ekpis.downtime_prediction_pct.toFixed(1)}   unit="%" color="#ef4444" />
                  <ReportCard icon={AlertTriangle} title="Active Alerts"    value={ekpis.active_alerts.toString()}             color="#f59e0b" sub={`${ekpis.critical_incidents} critical`} />
                  <ReportCard icon={Wrench}      title="Overdue Maintenance" value={ekpis.overdue_maintenance.toString()}      color="#f97316" />
                  <ReportCard icon={Leaf}        title="CO₂ Emissions"      value={(ekpis.total_co2_tonnes / 1000).toFixed(1)} unit="kt" color="#06b6d4" />
                  <ReportCard icon={DollarSign}  title="Energy Savings Opp" value={(ekpis.potential_savings_kwh / 1000).toFixed(0)} unit="MWh" color="#10b981" />
                </div>

                {/* Plant status table */}
                <Section title="Plant Status Overview">
                  <table className="w-full data-table mt-2">
                    <thead>
                      <tr className="border-b border-card-border/40">
                        <th className="text-left">Plant</th>
                        <th className="text-left">Status</th>
                        <th className="text-left">Failure Risk</th>
                        <th className="text-left">Safety Score</th>
                        <th className="text-left">Energy Eff.</th>
                        <th className="text-left">Production</th>
                        <th className="text-left">Downtime</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(execData?.kpis?.plant_summaries || []).map((p: any) => {
                        const statusColor: Record<string, string> = {
                          NORMAL: "badge-low", WARNING: "badge-medium", CRITICAL: "badge-critical",
                        };
                        return (
                          <tr key={p.plant_id}>
                            <td><span className="text-xs font-semibold text-white">{p.plant_id}</span></td>
                            <td><span className={statusColor[p.status]}>{p.status}</span></td>
                            <td>
                              <div className="flex items-center gap-1.5">
                                <div className="w-12 h-1 bg-surface-50 rounded-full overflow-hidden">
                                  <div className="h-full rounded-full" style={{
                                    width: `${p.failure_probability * 100}%`,
                                    background: p.failure_probability > 0.6 ? "#ef4444" : p.failure_probability > 0.4 ? "#f59e0b" : "#10b981",
                                  }} />
                                </div>
                                <span className="text-xs font-mono text-white">{(p.failure_probability * 100).toFixed(0)}%</span>
                              </div>
                            </td>
                            <td><span className="text-xs font-mono text-white">{p.safety_score.toFixed(1)}/100</span></td>
                            <td><span className="text-xs font-mono text-white">{p.energy_efficiency.toFixed(1)}%</span></td>
                            <td><span className="text-xs font-mono text-white">{p.production_rate.toFixed(0)} t/d</span></td>
                            <td>
                              {p.downtime_hours > 0
                                ? <span className="text-xs text-amber-400">{p.downtime_hours}h</span>
                                : <span className="text-xs text-green-400">None</span>}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </Section>
              </>
            )}

            {/* AI summary */}
            {execData?.ai_summary && (
              <Section title="AI Executive Summary">
                <AIAnalysisCard
                  agent="REPORTING"
                  response={execData.ai_summary}
                  confidence={execData.confidence || 0.93}
                  reasoning="Compiled from all four operational domains using real-time sensor and incident data."
                  impact={execData.impact || "Implementing all recommendations has estimated significant annual financial impact."}
                />
              </Section>
            )}
          </div>
        )}

        {/* ── MAINTENANCE REPORT TAB ── */}
        {activeTab === "maintenance" && (
          <div className="space-y-5">
            {loading ? (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => <div key={i} className="h-28 bg-card rounded-xl animate-pulse" />)}
              </div>
            ) : maintData && (
              <>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <ReportCard icon={FileText}   title="Total Tasks"      value={maintData.total_tasks?.toString() || "—"}                                                       color="#f59e0b" />
                  <ReportCard icon={AlertTriangle} title="Overdue Tasks" value={(maintData.by_status?.Overdue || 0).toString()}                                                 color="#ef4444" />
                  <ReportCard icon={DollarSign} title="Total Cost"       value={`$${((maintData.total_cost_usd || 0) / 1000).toFixed(0)}k`}                                    color="#9f1239" />
                  <ReportCard icon={TrendingUp} title="Avg Confidence"   value={`${((maintData.avg_confidence || 0) * 100).toFixed(0)}%`}                                      color="#10b981" />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <Section title="Tasks by Status">
                    {maintStatusData.length > 0
                      ? <SimpleBarChart data={maintStatusData} xKey="name" bars={[{ key: "count", color: "#f59e0b", label: "Tasks" }]} height={200} />
                      : <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">Loading…</div>}
                  </Section>
                  <Section title="Tasks by Type">
                    {maintTypeData.length > 0
                      ? <SimpleBarChart data={maintTypeData} xKey="name" bars={[{ key: "count", color: "#9f1239", label: "Tasks" }]} height={200} />
                      : <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">Loading…</div>}
                  </Section>
                </div>

                <Section title="Overdue Tasks — Top 10">
                  <table className="w-full data-table mt-2">
                    <thead>
                      <tr className="border-b border-card-border/40">
                        <th className="text-left">Date</th>
                        <th className="text-left">Plant / Unit</th>
                        <th className="text-left">Type</th>
                        <th className="text-left">Component</th>
                        <th className="text-left">Cost (USD)</th>
                        <th className="text-left">Confidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(maintData.overdue_tasks || []).slice(0, 10).map((t: any, i: number) => (
                        <tr key={i}>
                          <td><span className="text-xs font-mono text-muted-foreground">{String(t.date).slice(0, 10)}</span></td>
                          <td><div className="text-xs font-medium text-white">{t.plant_id}<span className="text-muted-foreground ml-1">{t.unit_id}</span></div></td>
                          <td><span className="text-xs text-gray-300">{t.maintenance_type}</span></td>
                          <td><span className="text-xs text-gray-300">{t.component}</span></td>
                          <td><span className="text-xs font-mono text-amber-400">${Number(t.cost_usd).toLocaleString()}</span></td>
                          <td>
                            <div className="flex items-center gap-1.5">
                              <div className="w-10 h-1 bg-surface-50 rounded-full overflow-hidden">
                                <div className="h-full bg-steel-500 rounded-full" style={{ width: `${Number(t.confidence_score) * 100}%` }} />
                              </div>
                              <span className="text-xs font-mono text-muted-foreground">{(Number(t.confidence_score) * 100).toFixed(0)}%</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── SAFETY REPORT TAB ── */}
        {activeTab === "safety" && (
          <div className="space-y-5">
            {loading ? (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => <div key={i} className="h-28 bg-card rounded-xl animate-pulse" />)}
              </div>
            ) : safetyData && (
              <>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <ReportCard icon={Shield}      title="Safety Score"      value={safetyData.safety_score?.toFixed(0) || "—"}           unit="/100" color="#10b981" delta="+1.4%" deltaPositive />
                  <ReportCard icon={AlertTriangle} title="Total Incidents" value={safetyData.total_incidents?.toString() || "—"}                    color="#ef4444" />
                  <ReportCard icon={CheckCircle} title="Resolution Rate"   value={`${safetyData.resolution_rate?.toFixed(1) || "—"}%`}             color="#06b6d4" />
                  <ReportCard icon={Clock}       title="Avg Response"      value={`${safetyData.avg_response_time_min?.toFixed(0) || "—"} min`}    color="#f59e0b" />
                </div>

                <Section title="KPI Summary">
                  <div className="space-y-1 mt-2">
                    <KPIRow label="Safety Score"        value={`${safetyData.safety_score?.toFixed(1)}/100`}                          status={safetyData.safety_score > 80 ? "good" : safetyData.safety_score > 60 ? "warning" : "critical"} />
                    <KPIRow label="Unresolved Incidents" value={safetyData.unresolved?.toString() || "—"}                             status={safetyData.unresolved === 0 ? "good" : safetyData.unresolved < 5 ? "warning" : "critical"} />
                    <KPIRow label="Critical Severity"    value={(safetyData.by_severity?.CRITICAL || 0).toString()}                   status={safetyData.by_severity?.CRITICAL === 0 ? "good" : "critical"} />
                    <KPIRow label="Average Risk Score"   value={`${((safetyData.avg_risk_score || 0) * 100).toFixed(1)}%`}            status={safetyData.avg_risk_score < 0.3 ? "good" : safetyData.avg_risk_score < 0.6 ? "warning" : "critical"} />
                    <KPIRow label="Resolution Rate"      value={`${safetyData.resolution_rate?.toFixed(1) || "—"}%`}                  status={safetyData.resolution_rate > 85 ? "good" : safetyData.resolution_rate > 65 ? "warning" : "critical"} />
                    <KPIRow label="Avg Response Time"    value={`${safetyData.avg_response_time_min?.toFixed(0) || "—"} min`}         status={safetyData.avg_response_time_min < 30 ? "good" : safetyData.avg_response_time_min < 90 ? "warning" : "critical"} />
                  </div>
                </Section>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <Section title="Severity Distribution">
                    {safetySevData.length > 0
                      ? <IncidentPieChart data={safetySevData} height={220} />
                      : <div className="h-52 flex items-center justify-center text-muted-foreground text-sm">Loading…</div>}
                  </Section>
                  <Section title="Incident Types">
                    {safetyTypeData.length > 0
                      ? <SimpleBarChart data={safetyTypeData} xKey="name" bars={[{ key: "value", color: "#ef4444", label: "Count" }]} height={220} />
                      : <div className="h-52 flex items-center justify-center text-muted-foreground text-sm">Loading…</div>}
                  </Section>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── ENERGY REPORT TAB ── */}
        {activeTab === "energy" && (
          <div className="space-y-5">
            {loading ? (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => <div key={i} className="h-28 bg-card rounded-xl animate-pulse" />)}
              </div>
            ) : energyData && (
              <>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <ReportCard icon={Zap}       title="Energy Score"     value={`${((energyData.avg_efficiency || 0) * 100).toFixed(0)}`}  unit="/100" color="#10b981" delta="+0.5%" deltaPositive />
                  <ReportCard icon={BarChart3} title="Total Consumption" value={`${((energyData.total_consumption_kwh || 0) / 1000).toFixed(0)}`} unit="MWh" color="#06b6d4" />
                  <ReportCard icon={Leaf}      title="CO₂ Emissions"    value={(energyData.total_co2_tonnes || 0).toFixed(0)}             unit="t"   color="#06b6d4" />
                  <ReportCard icon={DollarSign} title="Savings Value"   value={`₹${(energyData.estimated_savings_inr || 0).toFixed(0)}L`}             color="#f59e0b" sub="Identified opportunities" />
                </div>

                <Section title="KPI Summary">
                  <div className="space-y-1 mt-2">
                    <KPIRow label="Average Efficiency"     value={`${((energyData.avg_efficiency || 0) * 100).toFixed(1)}%`}               status={energyData.avg_efficiency > 0.8 ? "good" : energyData.avg_efficiency > 0.65 ? "warning" : "critical"} />
                    <KPIRow label="Total Consumption"      value={`${((energyData.total_consumption_kwh || 0) / 1000).toFixed(0)} MWh`}   status="neutral" />
                    <KPIRow label="CO₂ Emissions"          value={`${(energyData.total_co2_tonnes || 0).toFixed(1)} tonnes`}               status="neutral" />
                    <KPIRow label="Potential Savings"      value={`${((energyData.potential_savings_kwh || 0) / 1000).toFixed(0)} MWh`}   status="warning" />
                    <KPIRow label="Estimated Savings Value" value={`₹${(energyData.estimated_savings_inr || 0).toFixed(0)}L`}             status="good" />
                  </div>
                </Section>

                <Section title="Efficiency by Plant">
                  {energyPlantData.length > 0 ? (
                    <SimpleBarChart
                      data={energyPlantData}
                      xKey="name"
                      bars={[{ key: "efficiency", color: "#10b981", label: "Efficiency %" }]}
                      height={200}
                    />
                  ) : <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">Loading…</div>}
                </Section>
              </>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
