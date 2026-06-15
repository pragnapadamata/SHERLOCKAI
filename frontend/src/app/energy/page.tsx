"use client";
import { useEffect, useState, useCallback } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { AIAnalysisCard } from "@/components/dashboard/AIAnalysisCard";
import { EnergyAreaChart, SimpleBarChart, IncidentPieChart } from "@/components/charts/Charts";
import { energyAPI } from "@/lib/api";
import { Zap, Flame, Wind, TrendingDown, Leaf, DollarSign, BarChart2, Filter } from "lucide-react";

const PLANTS = ["ALL", "Plant-A", "Plant-B", "Plant-C", "Plant-D"];

function EfficiencyBar({
  label,
  value,
  target = 85,
}: {
  label: string;
  value: number;
  target?: number;
}) {
  const pct = Math.min(100, value);
  const color =
    value >= target ? "#10b981" : value >= target * 0.85 ? "#f59e0b" : "#ef4444";
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold text-white">
            {value.toFixed(1)}%
          </span>
          <span
            className={`text-xs font-medium ${
              value >= target ? "text-green-400" : "text-red-400"
            }`}
          >
            {value >= target ? "▲" : "▼"} target {target}%
          </span>
        </div>
      </div>
      <div className="relative h-2 w-full bg-surface-50 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
        {/* Target marker */}
        <div
          className="absolute top-0 w-px h-full bg-white/30"
          style={{ left: `${target}%` }}
        />
      </div>
    </div>
  );
}

function SavingsCard({
  title,
  kwh,
  inr,
  co2,
  priority,
}: {
  title: string;
  kwh: number;
  inr: number;
  co2: number;
  priority: "HIGH" | "MEDIUM" | "LOW";
}) {
  const priorityStyle = {
    HIGH:   { badge: "badge-critical", dot: "bg-red-400"   },
    MEDIUM: { badge: "badge-medium",   dot: "bg-yellow-400" },
    LOW:    { badge: "badge-low",      dot: "bg-green-400"  },
  }[priority];

  return (
    <div className="p-4 rounded-xl bg-gradient-to-br from-green-500/10 to-green-500/5 border border-green-500/20 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-white leading-tight">{title}</p>
        <span className={`${priorityStyle.badge} flex-shrink-0`}>{priority}</span>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <div>
          <div className="text-xs text-muted-foreground mb-0.5">Savings</div>
          <div className="text-sm font-semibold text-green-400 font-mono">
            {kwh.toFixed(0)} kWh
          </div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground mb-0.5">Value</div>
          <div className="text-sm font-semibold text-white font-mono">
            ₹{inr.toFixed(0)}L
          </div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground mb-0.5">CO₂ Cut</div>
          <div className="text-sm font-semibold text-cyan-400 font-mono">
            {co2.toFixed(1)}t
          </div>
        </div>
      </div>
    </div>
  );
}

export default function EnergyPage() {
  const [consumption, setConsumption] = useState<any[]>([]);
  const [analytics, setAnalytics]     = useState<any>(null);
  const [aiResult, setAiResult]       = useState<any>(null);
  const [loading, setLoading]         = useState(true);
  const [aiLoading, setAiLoading]     = useState(false);
  const [refreshing, setRefreshing]   = useState(false);
  const [selectedPlant, setSelectedPlant] = useState("ALL");

  const fetchData = useCallback(async () => {
    try {
      const [consRes, analyticsRes] = await Promise.all([
        energyAPI.getConsumption(selectedPlant),
        energyAPI.getAnalytics(selectedPlant),
      ]);
      setConsumption(consRes.data.consumption || []);
      setAnalytics(analyticsRes.data);
    } catch (e) {
      console.error("Energy fetch error:", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedPlant]);

  const fetchAI = useCallback(async () => {
    setAiLoading(true);
    try {
      const res = await energyAPI.analyze(selectedPlant);
      setAiResult(res.data);
    } catch (e) {
      console.error("AI energy error:", e);
    } finally {
      setAiLoading(false);
    }
  }, [selectedPlant]);

  useEffect(() => {
    setLoading(true);
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

  // Derive chart-ready data from analytics
  const plantEffData = analytics
    ? Object.entries(analytics.plant_efficiency || {}).map(([name, val]) => ({
        name,
        efficiency: Number(((val as number) * 100).toFixed(1)),
      }))
    : [];

  const plantConsData = analytics
    ? Object.entries(analytics.plant_consumption || {}).map(([name, val]) => ({
        name,
        consumption: Number(((val as number) / 1000).toFixed(1)),
      }))
    : [];

  const energyMixData = analytics
    ? [
        { name: "Electricity", value: analytics.avg_electricity_kwh || 0 },
        { name: "Gas",         value: analytics.avg_gas_m3 || 0 },
        { name: "Steam",       value: analytics.avg_steam_kg || 0 },
      ]
    : [];

  const unitEffData = analytics
    ? Object.entries(analytics.unit_efficiency || {})
        .sort(([, a], [, b]) => (a as number) - (b as number))
        .slice(0, 6)
        .map(([name, val]) => ({
          name: name.length > 14 ? name.slice(0, 14) + "…" : name,
          efficiency: Number(((val as number) * 100).toFixed(1)),
        }))
    : [];

  // Savings opportunities (derived from analytics)
  const totalSavings = analytics?.total_potential_savings_kwh ?? 0;
  const savingsOpps = [
    {
      title: "Off-peak load shifting — redistribute heavy loads to 22:00–06:00 window",
      kwh: totalSavings * 0.38,
      inr: (totalSavings * 0.38 * 0.008) / 100000,
      co2: totalSavings * 0.38 * 0.00043,
      priority: "HIGH" as const,
    },
    {
      title: "Heat recovery from BOF exhaust gases via recuperator installation",
      kwh: totalSavings * 0.25,
      inr: (totalSavings * 0.25 * 0.008) / 100000,
      co2: totalSavings * 0.25 * 0.00043,
      priority: "HIGH" as const,
    },
    {
      title: "Variable-speed drive upgrade on cooling water circulation pumps",
      kwh: totalSavings * 0.18,
      inr: (totalSavings * 0.18 * 0.008) / 100000,
      co2: totalSavings * 0.18 * 0.00043,
      priority: "MEDIUM" as const,
    },
    {
      title: "Compressed air leak detection and repair programme",
      kwh: totalSavings * 0.12,
      inr: (totalSavings * 0.12 * 0.008) / 100000,
      co2: totalSavings * 0.12 * 0.00043,
      priority: "MEDIUM" as const,
    },
    {
      title: "LED lighting retrofit across all plant floor and yard areas",
      kwh: totalSavings * 0.07,
      inr: (totalSavings * 0.07 * 0.008) / 100000,
      co2: totalSavings * 0.07 * 0.00043,
      priority: "LOW" as const,
    },
  ];

  const a = analytics;

  return (
    <AppShell>
      <Header
        title="Energy Optimisation"
        subtitle="Consumption analysis, efficiency tracking, and savings opportunities"
        onRefresh={handleRefresh}
        isRefreshing={refreshing}
      />

      <div className="p-6 space-y-6">
        {/* Plant filter */}
        <div className="flex items-center gap-1 bg-card border border-card-border rounded-lg p-1 w-fit">
          {PLANTS.map((p) => (
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

        {/* KPI row */}
        {loading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-28 bg-card rounded-xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Energy Score"
              value={a ? a.energy_score.toFixed(0) : "—"}
              unit="/100"
              icon={Zap}
              iconColor="text-green-400"
              status={
                a?.energy_score > 80
                  ? "good"
                  : a?.energy_score > 65
                  ? "warning"
                  : "critical"
              }
              subValue={`${a ? (a.avg_efficiency * 100).toFixed(1) : "—"}% avg efficiency`}
            />
            <MetricCard
              title="Total Consumption"
              value={a ? (a.total_energy_kwh / 1000).toFixed(0) : "—"}
              unit=" MWh"
              icon={BarChart2}
              iconColor="text-steel-400"
              status="neutral"
              subValue="Current period"
            />
            <MetricCard
              title="CO₂ Emissions"
              value={a ? a.total_co2_tonnes.toFixed(0) : "—"}
              unit=" t"
              icon={Leaf}
              iconColor="text-cyan-400"
              status="neutral"
              subValue="Scope 1 + Scope 2"
            />
            <MetricCard
              title="Potential Savings"
              value={a ? `₹${a.estimated_savings_inr.toFixed(0)}L` : "—"}
              icon={DollarSign}
              iconColor="text-amber-400"
              status="warning"
              subValue={`${a ? (a.total_potential_savings_kwh / 1000).toFixed(0) : "—"} MWh identified`}
            />
          </div>
        )}

        {/* Main grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

          {/* Left 2/3 */}
          <div className="xl:col-span-2 space-y-5">

            {/* Consumption area chart */}
            <div className="card-glass rounded-xl p-5 border border-card-border">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-white">Consumption Trend</h3>
                  <p className="text-xs text-muted-foreground">
                    Total kWh and efficiency ratio over time
                  </p>
                </div>
                <Zap size={15} className="text-muted-foreground" />
              </div>
              {consumption.length > 0 ? (
                <EnergyAreaChart data={consumption.slice(-80)} height={220} />
              ) : (
                <div className="h-56 flex items-center justify-center">
                  <div className="w-6 h-6 border-2 border-steel-500 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>

            {/* Plant comparison: efficiency vs consumption */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="card-glass rounded-xl p-5 border border-card-border">
                <h3 className="font-semibold text-white mb-1">Plant Efficiency</h3>
                <p className="text-xs text-muted-foreground mb-4">
                  Average efficiency ratio per plant
                </p>
                {plantEffData.length > 0 ? (
                  <SimpleBarChart
                    data={plantEffData}
                    xKey="name"
                    bars={[{ key: "efficiency", color: "#10b981", label: "Efficiency %" }]}
                    height={170}
                  />
                ) : (
                  <div className="h-44 flex items-center justify-center text-muted-foreground text-sm">
                    Loading…
                  </div>
                )}
              </div>
              <div className="card-glass rounded-xl p-5 border border-card-border">
                <h3 className="font-semibold text-white mb-1">Total Consumption</h3>
                <p className="text-xs text-muted-foreground mb-4">
                  MWh consumed per plant
                </p>
                {plantConsData.length > 0 ? (
                  <SimpleBarChart
                    data={plantConsData}
                    xKey="name"
                    bars={[{ key: "consumption", color: "#06b6d4", label: "MWh" }]}
                    height={170}
                  />
                ) : (
                  <div className="h-44 flex items-center justify-center text-muted-foreground text-sm">
                    Loading…
                  </div>
                )}
              </div>
            </div>

            {/* Worst-performing units */}
            <div className="card-glass rounded-xl p-5 border border-card-border">
              <h3 className="font-semibold text-white mb-1">Lowest-Efficiency Units</h3>
              <p className="text-xs text-muted-foreground mb-5">
                Units furthest below the 85% efficiency target
              </p>
              <div className="space-y-3">
                {loading ? (
                  [...Array(5)].map((_, i) => (
                    <div key={i} className="space-y-1">
                      <div className="h-3 bg-card rounded animate-pulse w-full" />
                      <div className="h-2 bg-card rounded animate-pulse w-3/4" />
                    </div>
                  ))
                ) : (
                  unitEffData.map((u) => (
                    <EfficiencyBar key={u.name} label={u.name} value={u.efficiency} />
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right 1/3 */}
          <div className="space-y-5">

            {/* Energy mix pie */}
            <div className="card-glass rounded-xl p-5 border border-card-border">
              <h3 className="font-semibold text-white mb-1">Energy Mix</h3>
              <p className="text-xs text-muted-foreground mb-2">
                Average consumption by source
              </p>
              {energyMixData.some((d) => d.value > 0) ? (
                <IncidentPieChart data={energyMixData} height={210} />
              ) : (
                <div className="h-52 flex items-center justify-center text-muted-foreground text-sm">
                  Loading…
                </div>
              )}
            </div>

            {/* Quick stats */}
            <div className="card-glass rounded-xl p-5 border border-card-border space-y-4">
              <h3 className="font-semibold text-white">Quick Stats</h3>
              {[
                {
                  icon: Zap,
                  label: "Avg Electricity",
                  value: a ? `${a.avg_electricity_kwh.toFixed(0)} kWh` : "—",
                  color: "text-cyan-400",
                },
                {
                  icon: Flame,
                  label: "Avg Gas",
                  value: a ? `${a.avg_gas_m3.toFixed(0)} m³` : "—",
                  color: "text-orange-400",
                },
                {
                  icon: Wind,
                  label: "Avg Steam",
                  value: a ? `${a.avg_steam_kg.toFixed(0)} kg` : "—",
                  color: "text-cyan-400",
                },
                {
                  icon: TrendingDown,
                  label: "Savings Potential",
                  value: a ? `${(a.total_potential_savings_kwh / 1000).toFixed(0)} MWh` : "—",
                  color: "text-green-400",
                },
              ].map(({ icon: Icon, label, value, color }) => (
                <div key={label} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-surface-50">
                      <Icon size={13} className={color} />
                    </div>
                    <span className="text-xs text-muted-foreground">{label}</span>
                  </div>
                  <span className="text-xs font-mono font-semibold text-white">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Savings opportunities */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                Savings Opportunities
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                AI-identified optimisation actions ranked by impact
              </p>
            </div>
            <div className="text-xs text-green-400 font-mono font-semibold">
              Total: ₹{a ? a.estimated_savings_inr.toFixed(0) : "—"}L / period
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {savingsOpps.map((opp, i) => (
              <SavingsCard key={i} {...opp} />
            ))}
          </div>
        </div>

        {/* AI analysis */}
        <div>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
            AI Energy Analysis
          </h2>
          <AIAnalysisCard
            agent={aiResult?.agent || "ENERGY"}
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
