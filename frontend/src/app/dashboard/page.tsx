"use client";
import { useEffect, useState, useCallback, useRef } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { AlertFeed } from "@/components/dashboard/AlertFeed";
import { SensorLineChart, EnergyAreaChart } from "@/components/charts/Charts";
import { dashboardAPI, maintenanceAPI, liveAPI } from "@/lib/api";
import { DashboardKPIs, Alert } from "@/types";
import {
  ShieldAlert, Zap, Factory, Wrench, AlertTriangle,
  Activity, TrendingDown, Cloud, Gauge, Radio, ChevronUp, ChevronDown,
  Terminal, Server, Shield, Cpu, RefreshCw, AlertCircle, Clock, Database, Wifi, CheckCircle2, HelpCircle,
  Maximize2, Crosshair, Minus, Plus, Layers, X
} from "lucide-react";

const DEMO_ALERT_TYPES = [
  { id: "CRITICAL_FAILURE",  label: "⚙️ High Vibration",   plant: "Plant-D" },
  { id: "GAS_LEAK",          label: "🌡️ Temperature Rise", plant: "Plant-B" },
  { id: "ENERGY_SURGE",      label: "⚡ Motor Overload",   plant: "Plant-C" },
  { id: "PRODUCTION_HALT",   label: "🔧 Bearing Wear",     plant: "Plant-A" },
];

// Contextual diagnostics mapped to nodes in the Plant Risk Map
const PLANT_DIAGNOSTICS: Record<string, {
  name: string;
  status: "NORMAL" | "WARNING" | "CRITICAL";
  diagnosis: string;
  rootCause: string;
  confidence: number;
  evidence: string;
  actions: string[];
}> = {
  "Plant-A": {
    name: "Hot Strip Mill — Rolling Line",
    status: "WARNING",
    diagnosis: "Mill Stand #3 gearbox bearing wear progressing.",
    rootCause: "Lubrication film breakdown with micro metal shavings.",
    confidence: 0.84,
    evidence: "Vibration at 9.2 mm/s² (warning: 8.5). Bearing temp 78°C, oil film pressure down 6%. Shaft alignment drift 0.04 mm.",
    actions: [
      "Verify roll bearing lube flow and filtration",
      "Schedule bearing housing seal inspection",
      "Reduce Mill Stand #3 speed 5% temporarily"
    ]
  },
  "Plant-B": {
    name: "Coke Oven Battery",
    status: "WARNING",
    diagnosis: "Battery flue #4 temperature rise with offtake pressure drop.",
    rootCause: "Partial blockage in gas offtake reducing draft.",
    confidence: 0.81,
    evidence: "Flue temp 1340°C (limit: 1300°C). Gas offtake pressure −8% vs nominal. Quench cycle lagging.",
    actions: [
      "Inspect gas offtake main for blockage",
      "Rebalance combustion air on battery #4",
      "Increase quench tower cooling cycle"
    ]
  },
  "Plant-C": {
    name: "Power Station — Substation Grid",
    status: "WARNING",
    diagnosis: "Transformer T-2 motor overload on cooling fan bank.",
    rootCause: "Stage-2 cooling fan relay delay during peak load shift.",
    confidence: 0.88,
    evidence: "Transformer core temp 89°C (nominal: 80°C). Substation efficiency dip to 94.8%. Fan motor current +14%.",
    actions: [
      "Force-override Stage-2 fan activation",
      "Check auxiliary grid circuit backup",
      "Verify breaker status on feeder C-4"
    ]
  },
  "Plant-D": {
    name: "Blast Furnace No.2",
    status: "CRITICAL",
    diagnosis: "Hearth refractory degradation with high thrust-bearing vibration.",
    rootCause: "High-temperature erosion of refractory in the lower hearth.",
    confidence: 0.96,
    evidence: "Thermocouple TC-409 reads 1640.1°C (limit: 1550°C). Thrust bearing vibration 11.4 mm/s². Shell expansion 0.12 mm/day.",
    actions: [
      "Increase hearth spray cooling water by 12%",
      "Schedule emergency refractory grout injection",
      "Run Blast Furnace No.2 at reduced output profile"
    ]
  }
};

/* ============================================================ */
/* Plant Risk Map metadata (drives the mission-control map view) */
/* ============================================================ */
type RiskStatus = "NORMAL" | "WARNING" | "CRITICAL";
const statusHex = (s: RiskStatus) => (s === "CRITICAL" ? "#ef4444" : s === "WARNING" ? "#f59e0b" : "#10b981");

const PLANT_RISK_META: Record<string, {
  name: string;
  desc: string;
  risk: number;
  status: RiskStatus;
  chimneys: number;
  drivers: { label: string; detail: string }[];
  impact: { plant: string; level: "High" | "Medium" | "Low"; pct: number }[];
  downtime: string;
}> = {
  "Plant-A": {
    name: "Hot Strip Mill",
    desc: "Rolling & finishing line", risk: 54, status: "WARNING", chimneys: 2,
    drivers: [
      { label: "Bearing Wear", detail: "Mill Stand #3 Gearbox" },
      { label: "Lubrication Issue", detail: "Roll Bearing Oil Film" },
      { label: "Shaft Misalignment", detail: "Coupling F-2" },
    ],
    impact: [
      { plant: "Plant-B", level: "Medium", pct: 48 },
      { plant: "Plant-D", level: "Low", pct: 26 },
      { plant: "Plant-C", level: "Low", pct: 22 },
    ],
    downtime: "28h",
  },
  "Plant-B": {
    name: "Coke Oven",
    desc: "Coal carbonization battery", risk: 58, status: "WARNING", chimneys: 3,
    drivers: [
      { label: "Temperature Rise", detail: "Battery Flue #4" },
      { label: "Pressure Drop", detail: "Gas Offtake Main" },
      { label: "Cooling Efficiency Loss", detail: "Quench Tower" },
    ],
    impact: [
      { plant: "Plant-D", level: "Medium", pct: 55 },
      { plant: "Plant-A", level: "Low", pct: 24 },
      { plant: "Plant-C", level: "Low", pct: 18 },
    ],
    downtime: "41h",
  },
  "Plant-C": {
    name: "Power Station",
    desc: "Main power & substation grid", risk: 45, status: "WARNING", chimneys: 1,
    drivers: [
      { label: "Motor Overload", detail: "Transformer T-2 Fan" },
      { label: "Temperature Rise", detail: "Core 89°C / 80°C" },
      { label: "Cooling Efficiency Loss", detail: "Stage-2 Fan Bank" },
    ],
    impact: [
      { plant: "Plant-A", level: "High", pct: 84 },
      { plant: "Plant-D", level: "High", pct: 80 },
      { plant: "Plant-B", level: "Medium", pct: 57 },
    ],
    downtime: "33h",
  },
  "Plant-D": {
    name: "Blast Furnace",
    desc: "Iron smelting unit", risk: 96, status: "CRITICAL", chimneys: 4,
    drivers: [
      { label: "High Vibration", detail: "BF-2 Thrust Bearing" },
      { label: "Temperature Rise", detail: "Stove Wall #3" },
      { label: "Pressure Drop", detail: "Bustle Pipe #7" },
    ],
    impact: [
      { plant: "Plant-A", level: "High", pct: 92 },
      { plant: "Plant-B", level: "Medium", pct: 58 },
      { plant: "Plant-C", level: "High", pct: 87 },
    ],
    downtime: "80h",
  },
};

// Canvas geometry — nodes + connection anchors share one coordinate space
const MAP_W = 980;
const MAP_H = 520;
const NODE_W = 260;
const NODE_CX = 130;   // factory visual centre X within a node container
const NODE_CY = 145;   // factory visual centre Y within a node container
const MAP_NODE_POS: Record<string, { left: number; top: number }> = {
  "Plant-A": { left: 60, top: 15 },
  "Plant-B": { left: 520, top: 15 },
  "Plant-C": { left: 60, top: 260 },
  "Plant-D": { left: 520, top: 260 },
};
const anchorOf = (id: string) => ({
  x: MAP_NODE_POS[id].left + NODE_CX,
  y: MAP_NODE_POS[id].top + NODE_CY,
});

// Friendly asset name for an internal plant id
const assetName = (id: string) => PLANT_RISK_META[id]?.name || PLANT_DIAGNOSTICS[id]?.name || id;

/* Rising smoke puffs (pure SVG/SMIL, no images) */
function Smoke({ x, y, seed }: { x: number; y: number; seed: number }) {
  return (
    <g>
      {[0, 1, 2, 3].map((p) => (
        <circle key={p} cx={x} cy={y} r={2.4 + p * 0.7} fill="#9aa3b2" opacity="0">
          <animate attributeName="opacity" values="0;0.32;0" dur="3.4s" begin={`${seed * 0.5 + p * 0.85}s`} repeatCount="indefinite" />
          <animateTransform attributeName="transform" type="translate" values="0,0; -4,-22; -11,-50" dur="3.4s" begin={`${seed * 0.5 + p * 0.85}s`} repeatCount="indefinite" />
        </circle>
      ))}
    </g>
  );
}

/* Circular risk ring with % label */
function RiskRing({ value, color }: { value: number; color: string }) {
  const r = 22;
  const c = 2 * Math.PI * r;
  return (
    <svg width="58" height="58" viewBox="0 0 58 58" className="flex-shrink-0">
      <g transform="rotate(-90 29 29)">
        <circle cx="29" cy="29" r={r} stroke="#2a1a20" strokeWidth="4.5" fill="none" />
        <circle
          cx="29" cy="29" r={r} stroke={color} strokeWidth="4.5" fill="none"
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - value / 100)}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </g>
      <text x="29" y="30" textAnchor="middle" dominantBaseline="central" fill="#fff" style={{ fontSize: "13px", fontFamily: "JetBrains Mono, monospace", fontWeight: 700 }}>
        {value}%
      </text>
    </svg>
  );
}

/* Code-drawn isometric factory with live animation (smoke, furnace glow, beacon) */
function AnimatedFactory({ plantId, status, selected, chimneys }: { plantId: string; status: RiskStatus; selected: boolean; chimneys: number }) {
  const accent = statusHex(status);
  const fid = `fg-${plantId}`;
  const chimXs = Array.from({ length: chimneys }, (_, i) =>
    chimneys === 1 ? 124 : 96 + (i * 64) / Math.max(1, chimneys - 1)
  );
  return (
    <svg width="240" height="210" viewBox="0 0 240 210" className="overflow-visible select-none">
      <defs>
        <radialGradient id={fid} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={accent} stopOpacity="0.95" />
          <stop offset="45%" stopColor={accent} stopOpacity="0.5" />
          <stop offset="100%" stopColor={accent} stopOpacity="0" />
        </radialGradient>
        <radialGradient id={`${fid}-base`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={accent} stopOpacity="0.5" />
          <stop offset="100%" stopColor={accent} stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* status pad glow */}
      <ellipse cx="120" cy="172" rx="98" ry="22" fill={`url(#${fid}-base)`} opacity={selected ? 0.55 : 0.3}>
        <animate attributeName="opacity" values={`${selected ? 0.55 : 0.3};${selected ? 0.3 : 0.16};${selected ? 0.55 : 0.3}`} dur="3s" repeatCount="indefinite" />
      </ellipse>

      {/* gentle bob */}
      <g>
        <animateTransform attributeName="transform" type="translate" values="0,0; 0,-3; 0,0" dur="5s" repeatCount="indefinite" />

        {/* ground platform */}
        <polygon points="120,168 36,128 120,88 204,128" fill="#140a0e" stroke="#3a2630" strokeWidth="1" />
        <polygon points="120,168 36,128 120,88 204,128" fill="none" stroke={accent} strokeOpacity="0.25" strokeWidth="1" />

        {/* furnace pooled glow on platform */}
        <ellipse cx="120" cy="150" rx="42" ry="9" fill={`url(#${fid})`}>
          <animate attributeName="opacity" values="0.9;0.5;0.9" dur="2.2s" repeatCount="indefinite" />
        </ellipse>

        {/* main hall — three iso faces */}
        <polygon points="54,116 120,150 120,112 54,78" fill="#211a1f" stroke="#46343b" strokeWidth="0.8" />
        <polygon points="120,150 186,116 186,78 120,112" fill="#2c2228" stroke="#46343b" strokeWidth="0.8" />
        <polygon points="54,78 120,112 186,78 120,44" fill="#372b31" stroke="#4d3a41" strokeWidth="0.8" />

        {/* roof ridge accents */}
        <polyline points="70,72 120,98 170,72" fill="none" stroke="#5a464e" strokeWidth="1" opacity="0.7" />

        {/* furnace mouth (left face) + pulsing glow */}
        <circle cx="86" cy="132" r="20" fill={`url(#${fid})`}>
          <animate attributeName="opacity" values="1;0.55;1" dur="1.8s" repeatCount="indefinite" />
        </circle>
        <polygon points="74,126 92,135 92,148 74,139" fill="#f43f5e">
          <animate attributeName="opacity" values="1;0.6;1" dur="1.4s" repeatCount="indefinite" />
        </polygon>

        {/* windows on right face (some blink) */}
        {[0, 1, 2].map((i) => (
          <g key={i}>
            <rect x={132 + i * 16} y={96 + i * 8} width="8" height="8" fill="#fbbf24" opacity="0.85">
              {i === 1 && <animate attributeName="opacity" values="0.85;0.2;0.85" dur="2.6s" repeatCount="indefinite" />}
            </rect>
          </g>
        ))}

        {/* chimneys + smoke */}
        {chimXs.map((cx, i) => (
          <g key={i}>
            <rect x={cx - 5} y={70} width="10" height="58" rx="1.5" fill="#2c2228" stroke="#46343b" strokeWidth="0.8" />
            <rect x={cx - 5} y={70} width="4" height="58" fill="#1f181c" />
            <ellipse cx={cx} cy={70} rx="6" ry="2.4" fill="#46343b" />
            <ellipse cx={cx} cy={70} rx="3.4" ry="1.3" fill="#0c0608" />
            <rect x={cx - 6} y={92} width="12" height="3" fill={accent} opacity="0.5" />
            <Smoke x={cx} y={66} seed={i} />
          </g>
        ))}

        {/* warning beacon on roof apex */}
        <circle cx="120" cy="44" r="3.4" fill={accent}>
          <animate attributeName="opacity" values="1;0.2;1" dur="1.1s" repeatCount="indefinite" />
        </circle>
        <circle cx="120" cy="44" r="3.4" fill="none" stroke={accent} strokeWidth="1">
          <animate attributeName="r" values="3.4;10;3.4" dur="1.8s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.8;0;0.8" dur="1.8s" repeatCount="indefinite" />
        </circle>
      </g>
    </svg>
  );
}

export default function DashboardPage() {
  const [kpis, setKpis]              = useState<DashboardKPIs | null>(null);
  const [timeseries, setTimeseries]  = useState<any>({ plant_series: [], energy_series: [] });
  const [aiAnalysis, setAiAnalysis]  = useState<any>(null);
  const [loading, setLoading]        = useState(true);
  const [aiLoading, setAiLoading]    = useState(false);
  const [refreshing, setRefreshing]  = useState(false);
  const [liveEvents, setLiveEvents]  = useState<any[]>([]);
  const [kpiDeltas, setKpiDeltas]    = useState<Record<string, any>>({});
  const [demoLoading, setDemoLoading]= useState(false);
  const [demoMsg, setDemoMsg]        = useState("");

  // Interactive console states
  const [selectedPlantId, setSelectedPlantId] = useState<string>("Plant-D");
  const [activeThirdRowTab, setActiveThirdRowTab] = useState<"timeline" | "queue" | "procurement">("timeline");

  // Risk map view controls
  const [mapZoom, setMapZoom] = useState(100);
  const [showPanel, setShowPanel] = useState(true);
  const selectPlant = (id: string) => { setSelectedPlantId(id); setShowPanel(true); };

  // Live command-center clock
  const [clock, setClock] = useState("--:--:-- --");
  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleTimeString("en-IN", { hour12: true }));
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, []);

  // Real-time scrolling logs console
  const [logs, setLogs] = useState<Array<{ id: number; time: string; system: string; message: string; type: "info" | "warn" | "error" | "success" }>>([
    { id: 1, time: "04:01:12", system: "SHERLOCK", message: "Monitor online. Asset models synced.", type: "success" },
    { id: 2, time: "04:01:15", system: "DATASERVICE", message: "Connected to Blast Furnace telemetry core.", type: "info" },
    { id: 3, time: "04:01:22", system: "RELIABILITY", message: "High vibration on Hot Strip Mill: 9.2 mm/s².", type: "warn" },
    { id: 4, time: "04:01:28", system: "SAFETY", message: "Coke Oven gas perimeter checks: SECURE.", type: "success" },
    { id: 5, time: "04:01:34", system: "ENERGY", message: "Off-peak load shifting active on Pump House units.", type: "info" },
  ]);

  const liveTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [kpiRes, tsRes] = await Promise.all([
        dashboardAPI.getKPIs(),
        dashboardAPI.getTimeseries(),
      ]);
      setKpis(kpiRes.data);
      setTimeseries(tsRes.data);
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const fetchAI = useCallback(async () => {
    setAiLoading(true);
    try {
      const res = await maintenanceAPI.analyze("ALL");
      setAiAnalysis(res.data);
    } catch (e) {
      console.error("AI analysis error:", e);
    } finally {
      setAiLoading(false);
    }
  }, []);

  const fetchLive = useCallback(async () => {
    try {
      const res = await liveAPI.getDashboard();
      setLiveEvents(res.data.events || []);
      setKpiDeltas(res.data.kpi_deltas || {});
    } catch { /* live feed non-critical */ }
  }, []);

  // Poll live data and animate ticker logs
  useEffect(() => {
    fetchData();
    fetchAI();
    fetchLive();

    liveTimer.current = setInterval(fetchLive, 10000);
    return () => { if (liveTimer.current) clearInterval(liveTimer.current); };
  }, [fetchData, fetchAI, fetchLive]);

  // Rolling log updates simulation
  useEffect(() => {
    const systems = ["SHERLOCK", "SAFETY", "ENERGY", "PRODUCTION", "RELIABILITY", "DATASERVICE"];
    const messages = [
      { msg: "Blast Furnace hearth holding at 1640.1 °C.", type: "info" as const },
      { msg: "Variable speed drive adjusted on Cooling System pump #4.", type: "info" as const },
      { msg: "Gas sensors: CO bounds normal at Coke Oven battery.", type: "success" as const },
      { msg: "Active alarm queue re-sorted by risk severity.", type: "info" as const },
      { msg: "Bearing wear anomaly detected on Hot Strip Mill stand #3.", type: "warn" as const },
      { msg: "Production gap to 2,500 t/day target closed by 3.2%.", type: "success" as const },
      { msg: "Failure risk recalculated: 96% on Blast Furnace No.2.", type: "warn" as const },
    ];

    const logTimer = setInterval(() => {
      const sys = systems[Math.floor(Math.random() * systems.length)];
      const item = messages[Math.floor(Math.random() * messages.length)];
      const timeStr = new Date().toLocaleTimeString("en-IN", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });

      setLogs(prev => {
        const nextId = prev.length ? prev[prev.length - 1].id + 1 : 1;
        const newLog = { id: nextId, time: timeStr, system: sys, message: item.msg, type: item.type };
        return [...prev.slice(1), newLog];
      });
    }, 5000);

    return () => clearInterval(logTimer);
  }, []);

  const handleRefresh = () => { setRefreshing(true); fetchData(); fetchLive(); };

  const handleDemoAlert = async (alertType: string, plant: string) => {
    setDemoLoading(true);
    setDemoMsg("");
    try {
      const res = await liveAPI.injectAlert(plant, alertType);
      setDemoMsg(`🚨 ${res.data.event?.severity} alert injected into ${plant}`);
      setTimeout(() => fetchLive(), 500);
      setTimeout(() => setDemoMsg(""), 6000);
    } catch {
      setDemoMsg("Failed to inject alert — is backend running?");
    } finally {
      setDemoLoading(false);
    }
  };

  const s = kpis?.summary;
  const staticAlerts: Alert[] = kpis?.recent_alerts || [];
  const liveAlerts: Alert[]   = liveEvents.map((e, i) => ({
    id:        e.id || `live-${i}`,
    plant:     e.plant || "Unknown",
    unit:      e.unit  || "Unknown",
    type:      e.incident_type || e.type || "Live Alert",
    severity:  e.severity as any,
    risk_score: e.value || 0.75,
    timestamp: e.timestamp,
    resolved:  false,
  }));
  const allAlerts = [...liveAlerts, ...staticAlerts].slice(0, 8);

  // Derive dynamic statuses from live summaries if available
  const getPlantStatus = (plantId: string) => {
    const summary = kpis?.plant_summaries.find(p => p.plant_id === plantId);
    return summary ? summary.status : PLANT_DIAGNOSTICS[plantId].status;
  };

  const getPlantHealth = (plantId: string) => {
    const summary = kpis?.plant_summaries.find(p => p.plant_id === plantId);
    return summary ? Math.round((1 - summary.failure_probability) * 100) : 80;
  };

  // Plant display metadata
  const PLANT_NODES: Record<string, { x: number; y: number; size: number; name: string }> = {
    "Plant-A": { x: 140, y: 70,  size: 24, name: "BOF Steelmaking" },
    "Plant-B": { x: 460, y: 70,  size: 20, name: "Rolling Mill" },
    "Plant-C": { x: 140, y: 220, size: 16, name: "Power Grid Substation" },
    "Plant-D": { x: 460, y: 220, size: 28, name: "Blast Furnace / Coke Ovens" }
  };

  // Overall circular gauge calculation
  const overallHealth = s
    ? Math.round(
        (s.safety_score + s.energy_score + (100 - s.downtime_prediction_pct) + s.production_kpi) / 4
      )
    : 78;

  const activeDiagnosis = PLANT_DIAGNOSTICS[selectedPlantId] || PLANT_DIAGNOSTICS["Plant-D"];

  // Command-center header stat (matches the Digital Twin header)
  const HeaderStat = ({ k, v, vClass = "text-white" }: { k: string; v: string; vClass?: string }) => (
    <div className="flex flex-col border-l border-white/15 pl-3">
      <span className="font-mono text-[8.5px] tracking-[0.15em] text-slate-400 uppercase whitespace-nowrap">{k}</span>
      <span className={`font-bold text-[15px] leading-tight mt-0.5 ${vClass}`}>{v}</span>
    </div>
  );

  // Reusable section divider to create a clear, premium top-to-bottom flow
  const SectionLabel = ({ index, title, sub, dotClass = "bg-steel-500" }: { index: string; title: string; sub?: string; dotClass?: string }) => (
    <div className="flex items-center gap-3 pt-1">
      <span className={`w-1.5 h-1.5 rounded-full ${dotClass}`} />
      <span className="font-mono text-[11px] font-black text-slate-600 tracking-widest">{index}</span>
      <h2 className="font-mono text-[11px] font-bold uppercase tracking-[0.22em] text-slate-200 whitespace-nowrap">{title}</h2>
      {sub && <span className="font-mono text-[10px] text-slate-500 whitespace-nowrap hidden md:inline">· {sub}</span>}
      <div className="flex-1 h-px bg-gradient-to-r from-white/[0.10] via-white/[0.04] to-transparent" />
    </div>
  );

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-screen bg-transparent">
          <div className="text-center space-y-4">
            <div className="w-12 h-12 border-2 border-steel-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-slate-400 font-mono text-sm">SYNCING INDUSTRIAL CORE TELEMETRY…</p>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="bg-transparent min-h-screen text-slate-100 flex flex-col font-sans">

        {/* Command Center Header (shared style with the Live Digital Twin) */}
        <div className="px-6 pt-4 pb-2 flex-shrink-0 z-20 sticky top-0">
          <div className="max-w-[1600px] mx-auto w-full rounded-2xl border border-white/50 bg-white/[0.06] backdrop-blur-xl shadow-[0_0_0_1px_rgba(255,255,255,0.05),0_10px_36px_rgba(0,0,0,0.45)] px-5 py-3 flex flex-wrap items-center gap-x-4 gap-y-3">

            {/* Brand */}
            <div className="flex items-center gap-3 pr-1">
              <div className="w-9 h-9 rounded-lg grid place-items-center bg-gradient-to-br from-cyan-400/25 to-steel-500/10 border border-cyan-400/40">
                <svg viewBox="0 0 24 24" fill="none" stroke="#22d3ee" strokeWidth="2.5" className="w-5 h-5">
                  <circle cx="12" cy="12" r="9" />
                  <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4" />
                </svg>
              </div>
              <div className="leading-tight">
                <div className="font-bold tracking-[0.16em] text-white text-[15px]">SHERLOCK AI</div>
                <div className="font-mono text-[8px] tracking-[0.28em] text-slate-400">COMMAND CENTER</div>
              </div>
            </div>

            {/* Executive stats */}
            <HeaderStat k="Plant Health" v={`${overallHealth}%`} vClass="text-cyan-300" />
            <HeaderStat k="Monitored Assets" v="124" />
            <HeaderStat k="Critical Alerts" v={`${s?.active_alerts || 6}`} vClass="text-red-400 animate-pulse" />
            <HeaderStat k="Predicted Failures" v="3" vClass="text-amber-400" />
            <HeaderStat k="Risk Exposure" v="₹42.6 L" vClass="text-cyan-300" />

            <div className="flex-1 min-w-[8px]" />

            {/* Clock */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.05] border border-white/30 font-mono text-[11px] text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>CLOCK</span>
              <b className="text-white font-mono">{clock}</b>
            </div>

            {/* Data source / refresh */}
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              title="Refresh data"
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.05] border border-white/30 font-mono text-[11px] text-slate-300 hover:text-white hover:border-white/50 transition-all"
            >
              <RefreshCw size={12} className={refreshing ? "animate-spin" : ""} /> DATA <b className="text-amber-400">DEMO</b>
            </button>
          </div>
        </div>

        {/* Outer container ensuring perfect grid spacing & layout */}
        <div className="px-6 py-6 space-y-5 flex-1 overflow-auto max-w-[1600px] mx-auto w-full">

          {/* ============================================================ */}
          {/* 01 — HEALTH OVERVIEW (Command Header / Primary Focal Point)  */}
          {/* ============================================================ */}
          <SectionLabel index="01" title="Operational Health" sub="Live Asset Health Index" dotClass="bg-emerald-500 animate-pulse" />

          <div className="card-glass overflow-hidden">
            <div className="grid grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-white/[0.06]">

              {/* FOCAL POINT: Overall Plant Health Gauge */}
              <div className="col-span-12 lg:col-span-3 p-6 flex flex-col items-center justify-center text-center relative">
                <div className="w-full flex justify-between items-center mb-4">
                  <span className="text-[10px] font-mono font-bold tracking-wider uppercase text-slate-400 flex items-center gap-1.5">
                    <Gauge size={12} className="text-steel-400" /> ASSET HEALTH INDEX
                  </span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                </div>
                <div className="relative flex items-center justify-center my-2">
                  <svg className="w-40 h-40 transform -rotate-90">
                    <circle cx="80" cy="80" r="64" stroke="#2a1620" strokeWidth="10" fill="transparent" />
                    <circle
                      cx="80"
                      cy="80"
                      r="64"
                      stroke={overallHealth > 75 ? "#10b981" : overallHealth > 50 ? "#f59e0b" : "#ef4444"}
                      strokeWidth="10"
                      fill="transparent"
                      strokeLinecap="round"
                      strokeDasharray={2 * Math.PI * 64}
                      strokeDashoffset={2 * Math.PI * 64 * (1 - overallHealth / 100)}
                      className="transition-all duration-1000 ease-out"
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center justify-center">
                    <span className="text-4xl font-mono font-black text-white tracking-tight">{overallHealth}%</span>
                    <span className="text-[9px] font-mono text-slate-400 tracking-[0.3em] uppercase mt-0.5">HEALTH</span>
                  </div>
                </div>
                <div className="mt-4 w-full grid grid-cols-2 gap-2 text-[11px] font-mono">
                  <div className="bg-white/[0.06] border-white/25 rounded-lg py-2">
                    <p className="text-[9px] text-slate-500 tracking-wider">RATING</p>
                    <p className="text-emerald-400 font-bold mt-0.5">OPTIMAL</p>
                  </div>
                  <div className="bg-white/[0.06] border-white/25 rounded-lg py-2">
                    <p className="text-[9px] text-slate-500 tracking-wider">FAIL RISK</p>
                    <p className="text-slate-200 font-bold mt-0.5">LOW</p>
                  </div>
                </div>
              </div>

              {/* Critical KPI strip */}
              <div className="col-span-12 lg:col-span-5 p-6 flex flex-col">
                <div className="w-full flex justify-between items-center mb-4">
                  <span className="text-[10px] font-mono font-bold tracking-wider uppercase text-slate-400 flex items-center gap-1.5">
                    <Wrench size={12} className="text-steel-400" /> RELIABILITY METRICS
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-steel-500 animate-pulse" /> LIVE FEED
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 flex-1">
                  {/* KPI 1: Critical Alerts */}
                  <div className="bg-white/[0.06] border-white/25 rounded-xl p-4 flex flex-col justify-between hover:border-red-500/35 transition-colors">
                    <span className="text-[10px] font-mono text-slate-400 tracking-wider">CRITICAL ALERTS</span>
                    <div className="flex items-baseline gap-2 mt-2">
                      <span className="text-3xl font-mono font-bold text-red-500">{s?.active_alerts || 3}</span>
                      <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
                    </div>
                  </div>

                  {/* KPI 2: Downtime Risk */}
                  <div className="bg-white/[0.06] border-white/25 rounded-xl p-4 flex flex-col justify-between hover:border-[#9f1239]/40 transition-colors">
                    <span className="text-[10px] font-mono text-slate-400 tracking-wider">DOWNTIME RISK</span>
                    <div className="flex items-baseline gap-1 mt-2">
                      <span className="text-3xl font-mono font-bold text-amber-500">₹42L</span>
                      <span className="text-[10px] font-mono text-slate-400">EST</span>
                    </div>
                  </div>

                  {/* KPI 3: Predicted Failure Count */}
                  <div className="bg-white/[0.06] border-white/25 rounded-xl p-4 flex flex-col justify-between hover:border-slate-500/30 transition-colors">
                    <span className="text-[10px] font-mono text-slate-400 tracking-wider">PREDICTED FAILURES</span>
                    <div className="flex items-baseline gap-1 mt-2">
                      <span className="text-3xl font-mono font-bold text-white">3</span>
                      <span className="text-[9px] font-mono text-slate-400">ASSETS</span>
                    </div>
                  </div>

                  {/* KPI 4: RUL Forecast */}
                  <div className="bg-white/[0.06] border-white/25 rounded-xl p-4 flex flex-col justify-between hover:border-steel-500/35 transition-colors">
                    <span className="text-[10px] font-mono text-slate-400 tracking-wider">RUL FORECAST</span>
                    <div className="flex items-baseline gap-1 mt-2">
                      <span className="text-3xl font-mono font-bold text-steel-400">14.2</span>
                      <span className="text-[10px] font-mono text-slate-400">DAYS AVG</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Executive Summary */}
              <div className="col-span-12 lg:col-span-4 p-6 flex flex-col">
                <div className="w-full flex justify-between items-center mb-4">
                  <span className="text-[10px] font-mono font-bold tracking-wider uppercase text-slate-400 flex items-center gap-1.5">
                    <Cpu size={12} className="text-steel-400" /> ASSET INTELLIGENCE SUMMARY
                  </span>
                  <span className="text-[9px] font-mono bg-steel-500/10 text-steel-400 border border-steel-500/20 px-1.5 py-0.5 rounded">AUTO</span>
                </div>
                <div className="flex-1 flex flex-col justify-center bg-white/[0.05] border-white/20 p-4 rounded-lg font-mono text-xs leading-relaxed text-slate-300">
                  <p className="mb-2.5">
                    &gt; <span className="text-emerald-400 font-bold">Asset fleet operating at {overallHealth}% health.</span>
                  </p>
                  <p className="mb-2.5">
                    &gt; <span className="text-red-400 font-bold">Blast Furnace flagged critical</span> — thrust-bearing vibration trending up; act within 48h.
                  </p>
                  <p>
                    &gt; Estimated downtime exposure of <span className="text-amber-500 font-bold">₹42L</span> over the next 14 operating days.
                  </p>
                </div>
                <div className="mt-3 flex items-center gap-1.5 text-[10px] font-mono text-slate-500">
                  <Terminal size={11} />
                  <span>SHERLOCK AI · CONDITION MONITORING ACTIVE</span>
                </div>
              </div>

            </div>
          </div>

          {/* ============================================================ */}
          {/* 02 — RISKS & ALERTS                                          */}
          {/* ============================================================ */}
          <SectionLabel index="02" title="Risk Dependency Map" sub="Asset Health Network" dotClass="bg-red-500 animate-pulse" />

          <div className="grid grid-cols-12 gap-5">

            {/* Full-width mission-control risk map */}
            <div className="col-span-12 card-glass overflow-hidden relative">

              {/* Header bar */}
              <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.06] bg-white/[0.05]">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-steel-500/10 border border-steel-500/20 flex items-center justify-center">
                    <Activity size={15} className="text-steel-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider text-white leading-tight">
                      Asset Health Network
                    </h3>
                    <p className="text-[10px] font-mono text-slate-500">Real-time risk propagation across connected assets</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="hidden md:inline text-[10px] font-mono text-slate-500 tracking-wider">VIEW MODE</span>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/30 text-[11px] font-mono font-bold text-slate-200">
                    <Layers size={12} className="text-steel-400" /> RISK PROPAGATION <ChevronDown size={12} className="text-slate-500" />
                  </div>
                  <button className="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/30 flex items-center justify-center text-slate-400 hover:text-white hover:border-white/20 transition-colors">
                    <Maximize2 size={13} />
                  </button>
                </div>
              </div>

              {/* Map canvas */}
              <div className="relative h-[600px] overflow-hidden bg-[#0b1322]">

                {/* ambient grid + glow fields */}
                <div className="absolute inset-0 pointer-events-none" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.022) 1px, transparent 1px)", backgroundSize: "40px 40px" }} />
                <div className="absolute -top-24 left-1/4 w-[28rem] h-[28rem] rounded-full bg-steel-600/10 blur-3xl pointer-events-none" />
                <div className="absolute -bottom-24 right-1/4 w-[28rem] h-[28rem] rounded-full bg-red-600/10 blur-3xl pointer-events-none" />

                {/* Scalable plant + dependency layer */}
                <div
                  className="absolute left-1/2 top-1/2"
                  style={{ width: MAP_W, height: MAP_H, transform: `translate(-50%,-50%) scale(${mapZoom / 100})`, transformOrigin: "center" }}
                >
                  {/* Dependency connections + flowing particles */}
                  {(() => {
                    const A = anchorOf("Plant-A"), B = anchorOf("Plant-B"), C = anchorOf("Plant-C"), D = anchorOf("Plant-D");
                    const mid = { x: (A.x + D.x) / 2, y: (A.y + D.y) / 2 };
                    return (
                      <svg className="absolute inset-0" width={MAP_W} height={MAP_H} viewBox={`0 0 ${MAP_W} ${MAP_H}`}>
                        {/* faint structural links */}
                        <line x1={A.x} y1={A.y} x2={C.x} y2={C.y} stroke="#2a1a22" strokeWidth="2" strokeDasharray="4 9" />
                        <line x1={B.x} y1={B.y} x2={D.x} y2={D.y} stroke="#2a1a22" strokeWidth="2" strokeDasharray="4 9" />

                        {/* active amber dependencies (marching ants) */}
                        <line x1={A.x} y1={A.y} x2={B.x} y2={B.y} stroke="#f59e0b" strokeOpacity="0.6" strokeWidth="2.5" strokeDasharray="9 8">
                          <animate attributeName="stroke-dashoffset" values="0;-34" dur="1.1s" repeatCount="indefinite" />
                        </line>
                        <line x1={C.x} y1={C.y} x2={D.x} y2={D.y} stroke="#f59e0b" strokeOpacity="0.6" strokeWidth="2.5" strokeDasharray="9 8">
                          <animate attributeName="stroke-dashoffset" values="0;-34" dur="1.1s" repeatCount="indefinite" />
                        </line>

                        {/* critical propagation A -> D (red, glowing) */}
                        <line x1={A.x} y1={A.y} x2={D.x} y2={D.y} stroke="#ef4444" strokeWidth="3" strokeDasharray="10 7" style={{ filter: "drop-shadow(0 0 6px rgba(239,68,68,0.7))" }}>
                          <animate attributeName="stroke-dashoffset" values="0;-34" dur="0.9s" repeatCount="indefinite" />
                        </line>

                        {/* midpoint pulse */}
                        <circle cx={mid.x} cy={mid.y} r="6" fill="#ef4444">
                          <animate attributeName="r" values="5;9;5" dur="1.4s" repeatCount="indefinite" />
                          <animate attributeName="opacity" values="1;0.5;1" dur="1.4s" repeatCount="indefinite" />
                        </circle>
                        <circle cx={mid.x} cy={mid.y} r="6" fill="none" stroke="#ef4444" strokeWidth="1.5">
                          <animate attributeName="r" values="6;20;6" dur="1.9s" repeatCount="indefinite" />
                          <animate attributeName="opacity" values="0.8;0;0.8" dur="1.9s" repeatCount="indefinite" />
                        </circle>

                        {/* flowing particles */}
                        <circle r="4" fill="#fbbf24">
                          <animateMotion dur="3s" repeatCount="indefinite" path={`M ${A.x},${A.y} L ${B.x},${B.y}`} />
                        </circle>
                        <circle r="4" fill="#fbbf24">
                          <animateMotion dur="3.4s" repeatCount="indefinite" path={`M ${C.x},${C.y} L ${D.x},${D.y}`} />
                        </circle>
                        <circle r="5" fill="#ef4444" style={{ filter: "drop-shadow(0 0 6px rgba(239,68,68,0.9))" }}>
                          <animateMotion dur="2.4s" repeatCount="indefinite" path={`M ${A.x},${A.y} L ${D.x},${D.y}`} />
                        </circle>
                        <circle r="3" fill="#ef4444" opacity="0.7">
                          <animateMotion dur="2.4s" begin="1.2s" repeatCount="indefinite" path={`M ${A.x},${A.y} L ${D.x},${D.y}`} />
                        </circle>
                      </svg>
                    );
                  })()}

                  {/* Plant nodes */}
                  {Object.keys(MAP_NODE_POS).map((id) => {
                    const meta = PLANT_RISK_META[id];
                    const color = statusHex(meta.status);
                    const isSel = selectedPlantId === id;
                    const pos = MAP_NODE_POS[id];
                    return (
                      <div
                        key={id}
                        className="absolute cursor-pointer group"
                        style={{ left: pos.left, top: pos.top, width: NODE_W }}
                        onClick={() => selectPlant(id)}
                      >
                        {/* Label row */}
                        <div className="flex items-center gap-3 relative z-10">
                          <RiskRing value={meta.risk} color={color} />
                          <div className="min-w-0">
                            <h4 className={`text-base font-extrabold tracking-wide ${isSel ? "text-white" : "text-slate-200"}`}>{meta.name}</h4>
                            <p className="text-[11px] text-slate-400 leading-tight">{meta.desc}</p>
                            <span
                              className="inline-block mt-1 text-[9px] font-mono font-bold px-1.5 py-0.5 rounded tracking-wider"
                              style={{ color, backgroundColor: `${color}1a`, border: `1px solid ${color}40` }}
                            >
                              {meta.status}
                            </span>
                          </div>
                        </div>

                        {/* Animated factory */}
                        <div className={`-mt-1 flex justify-center transition-transform duration-300 ${isSel ? "scale-[1.06]" : "group-hover:scale-105"}`}>
                          <AnimatedFactory plantId={id} status={meta.status} selected={isSel} chimneys={meta.chimneys} />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Legend overlay */}
                <div className="absolute top-4 left-4 bg-white/[0.07] backdrop-blur border border-white/30 rounded-xl p-3 w-44 z-20">
                  <p className="text-[10px] font-mono font-bold tracking-[0.2em] text-slate-400 mb-2.5">RISK INDEX</p>
                  <div className="space-y-2">
                    {[{ r: "0 – 30", l: "Normal", c: "#10b981" }, { r: "31 – 60", l: "Warning", c: "#f59e0b" }, { r: "61 – 100", l: "Critical", c: "#ef4444" }].map((row) => (
                      <div key={row.l} className="flex items-center justify-between text-[11px] font-mono">
                        <span className="flex items-center gap-2 text-slate-300">
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: row.c }} /> {row.r}
                        </span>
                        <span style={{ color: row.c }}>{row.l}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Selected Target panel */}
                {showPanel && (() => {
                  const sel = PLANT_RISK_META[selectedPlantId];
                  const selColor = statusHex(sel.status);
                  return (
                    <div className="absolute top-4 right-4 w-72 bg-white/[0.08] backdrop-blur border border-white/40 rounded-xl p-4 z-20 shadow-2xl">
                      <div className="flex items-center justify-between border-b border-white/[0.06] pb-2 mb-3">
                        <span className="text-[10px] font-mono font-bold tracking-[0.2em]" style={{ color: selColor }}>SELECTED ASSET</span>
                        <button onClick={(e) => { e.stopPropagation(); setShowPanel(false); }} className="text-slate-500 hover:text-white transition-colors">
                          <X size={13} />
                        </button>
                      </div>
                      <h4 className="text-lg font-bold text-white">{sel.name}</h4>
                      <p className="text-[11px] text-slate-400 mb-3">{sel.desc}</p>

                      <p className="text-[10px] font-mono text-slate-500 tracking-wider">RISK INDEX</p>
                      <div className="flex items-baseline gap-2 mb-3">
                        <span className="text-3xl font-mono font-black" style={{ color: selColor }}>{sel.risk}%</span>
                        <span className="text-[11px] font-mono font-bold" style={{ color: selColor }}>{sel.status}</span>
                      </div>

                      <p className="text-[10px] font-mono text-slate-500 tracking-wider mb-1.5">KEY DRIVERS</p>
                      <ul className="space-y-1 mb-3">
                        {sel.drivers.map((d) => (
                          <li key={d.label} className="text-[11px] flex items-start gap-1.5">
                            <span className="text-slate-500 mt-1">•</span>
                            <span className="text-slate-200 font-semibold">{d.label}:</span>
                            <span className="text-slate-400">{d.detail}</span>
                          </li>
                        ))}
                      </ul>

                      <p className="text-[10px] font-mono text-slate-500 tracking-wider mb-1.5">DEPENDENCY IMPACT</p>
                      <ul className="space-y-1.5 mb-3">
                        {sel.impact.map((im) => {
                          const c = im.pct >= 80 ? "#ef4444" : im.pct >= 50 ? "#f59e0b" : "#10b981";
                          return (
                            <li key={im.plant} className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-300">{assetName(im.plant)}: <span className="text-slate-400">{im.level}</span></span>
                              <span className="font-mono font-bold px-1.5 py-0.5 rounded text-[10px]" style={{ color: c, backgroundColor: `${c}1a`, border: `1px solid ${c}40` }}>{im.pct}%</span>
                            </li>
                          );
                        })}
                      </ul>

                      <div className="flex items-center justify-between border-t border-white/[0.06] pt-2.5">
                        <span className="text-[10px] font-mono text-slate-500 tracking-wider">EST. DOWNTIME RISK</span>
                        <span className="text-xl font-mono font-black" style={{ color: selColor }}>{sel.downtime}</span>
                      </div>
                    </div>
                  );
                })()}

                {/* System status (bottom-left) */}
                <div className="absolute bottom-4 left-4 flex items-center gap-3 bg-white/[0.07] backdrop-blur border border-white/40 rounded-lg px-3 py-2 text-[11px] font-mono z-20">
                  <span className="flex items-center gap-1.5 text-slate-200 font-bold"><Server size={12} className="text-steel-400" /> SYSTEM STATUS</span>
                  <span className="flex items-center gap-1.5 text-emerald-400"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> All systems monitored</span>
                  <span className="text-slate-500 hidden sm:inline">| Last Updated: 10:24:35 AM</span>
                </div>

                {/* Zoom controls (bottom-right) */}
                <div className="absolute bottom-4 right-4 flex items-center gap-2 z-20">
                  <button onClick={() => setMapZoom(100)} title="Re-center" className="w-9 h-9 rounded-lg bg-white/[0.07] border border-white/40 flex items-center justify-center text-slate-300 hover:text-white hover:border-white/20 transition-colors">
                    <Crosshair size={14} />
                  </button>
                  <div className="flex items-center bg-white/[0.07] border border-white/40 rounded-lg overflow-hidden">
                    <button onClick={() => setMapZoom((z) => Math.max(60, z - 10))} className="px-2.5 py-2 text-slate-300 hover:text-white hover:bg-white/[0.05] transition-colors">
                      <Minus size={14} />
                    </button>
                    <span className="px-1 w-12 text-center text-[11px] font-mono text-slate-300">{mapZoom}%</span>
                    <button onClick={() => setMapZoom((z) => Math.min(140, z + 10))} className="px-2.5 py-2 text-slate-300 hover:text-white hover:bg-white/[0.05] transition-colors">
                      <Plus size={14} />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Critical Alerts Feed (full width) */}
            <div className="col-span-12 card-glass p-5 flex flex-col">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <AlertCircle size={14} className="text-red-400" />
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                    Active Alarm Feed
                  </h3>
                </div>
                <span className="text-[9px] font-mono bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-full font-bold">
                  {allAlerts.length} ACTIVE
                </span>
              </div>

              <div className="flex-1 overflow-y-auto max-h-[300px] pr-1 space-y-2">
                <AlertFeed alerts={allAlerts} />
              </div>
            </div>

          </div>

          {/* ============================================================ */}
          {/* 03 — AI INSIGHTS (AI Agent Command Board)                    */}
          {/* ============================================================ */}
          <SectionLabel index="03" title="Maintenance Insights" sub="Sherlock AI Root-Cause Engine" dotClass="bg-cyan-500 animate-pulse" />

          <div className="card-glass p-5 border border-steel-400/40 relative overflow-hidden">
            {/* Decorative grid indicator */}
            <div className="absolute top-0 right-0 p-1 font-mono text-[8px] text-slate-600 select-none">
              SHERLOCK_AI_RELIABILITY_v3.5
            </div>

            <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 mb-4">
              <div className="flex items-center gap-2">
                <Cpu size={15} className="text-steel-500 animate-pulse" />
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                  Asset Intelligence · Root-Cause Diagnosis
                </h3>
              </div>
              <div className="flex items-center gap-2 font-mono text-[10px]">
                <span className="text-slate-400">SELECTED ASSET:</span>
                <span className="text-steel-400 font-bold bg-steel-500/10 border border-steel-500/20 px-2 py-0.5 rounded">
                  {assetName(selectedPlantId)}
                </span>
              </div>
            </div>

            {/* Console grid layout */}
            <div className="grid grid-cols-12 gap-5">

              {/* Left 4 cols: Diagnostics Summary & Confidence */}
              <div className="col-span-12 md:col-span-4 space-y-4 font-mono">
                <div className="bg-white/[0.05] p-4 rounded-xl border border-white/25">
                  <span className="text-[10px] text-slate-400 uppercase tracking-widest block mb-1">Diagnosis Target</span>
                  <h4 className="text-sm font-bold text-white">{activeDiagnosis.name}</h4>
                  <p className="text-xs text-slate-300 mt-2 leading-relaxed">{activeDiagnosis.diagnosis}</p>
                </div>

                <div className="bg-white/[0.05] p-4 rounded-xl border border-white/25">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] text-slate-400 uppercase tracking-widest">Sherlock Confidence</span>
                    <span className="text-xs font-bold text-steel-400">{Math.round(activeDiagnosis.confidence * 100)}%</span>
                  </div>
                  <div className="h-2.5 bg-white/[0.07] rounded-full overflow-hidden border border-white/25">
                    <div
                      className="h-full bg-gradient-to-r from-steel-600 to-steel-400 rounded-full transition-all duration-700"
                      style={{ width: `${activeDiagnosis.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-[9px] text-slate-500 block mt-1.5">BASED ON MULTI-SENSOR WEIBULL ESTIMATION</span>
                </div>
              </div>

              {/* Center 4 cols: Root Cause & Telemetry Evidence */}
              <div className="col-span-12 md:col-span-4 space-y-4 font-mono">
                <div className="bg-white/[0.05] p-4 rounded-xl border border-white/25 flex-1">
                  <span className="text-[10px] text-slate-400 uppercase tracking-widest block mb-1">Root Cause Classification</span>
                  <p className="text-xs text-amber-400 font-bold mb-2">&gt; MECHANICAL ANOMALY IDENTIFIED</p>
                  <p className="text-xs text-slate-300 leading-relaxed">{activeDiagnosis.rootCause}</p>
                </div>

                <div className="bg-white/[0.05] p-4 rounded-xl border border-white/25 flex-1">
                  <span className="text-[10px] text-slate-400 uppercase tracking-widest block mb-1.5">Sensor Evidence Log</span>
                  <div className="text-[11px] text-slate-300 bg-white/[0.04] p-2.5 rounded border border-white/25 font-mono leading-relaxed max-h-[85px] overflow-y-auto">
                    {activeDiagnosis.evidence}
                  </div>
                </div>
              </div>

              {/* Right 4 cols: Action Plan */}
              <div className="col-span-12 md:col-span-4 font-mono">
                <div className="bg-white/[0.05] p-4 rounded-xl border border-white/25 h-full flex flex-col justify-between font-mono">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase tracking-widest block mb-2">Recommended Corrective Actions</span>
                    <div className="space-y-2">
                      {activeDiagnosis.actions.map((action, index) => (
                        <div key={index} className="flex items-start gap-2 text-xs">
                          <span className="text-steel-500 font-bold mt-0.5">{index + 1}.</span>
                          <span className="text-slate-300 leading-relaxed">{action}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-white/[0.05] flex items-center justify-between text-[9px] text-slate-500">
                    <span>VERIFIED BY SHERLOCK AI v3.5</span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle2 size={10} /> APPROVED
                    </span>
                  </div>
                </div>
              </div>

            </div>
          </div>

          {/* ============================================================ */}
          {/* 04 — PREDICTIONS (Forecast / Maintenance Queue / Spares)     */}
          {/* ============================================================ */}
          <SectionLabel index="04" title="Failure Prediction" sub="30-Day Failure Forecast" dotClass="bg-amber-500 animate-pulse" />

          <div className="card-glass p-5 flex flex-col">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-white/[0.06] pb-3 mb-4 gap-3">
              <div className="flex items-center gap-2">
                <TrendingDown size={14} className="text-steel-400" />
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                  Failure Prediction & Spares Readiness
                </h3>
              </div>

              {/* Console Tab Selector */}
              <div className="flex bg-white/[0.04] p-0.5 rounded-lg border border-white/20">
                <button
                  onClick={() => setActiveThirdRowTab("timeline")}
                  className={`px-3 py-1 text-[10px] font-mono font-bold rounded-md transition-all ${
                    activeThirdRowTab === "timeline" ? "bg-white/15 text-white border border-white/40" : "text-slate-400 hover:text-white"
                  }`}
                >
                  FAILURE FORECAST (30D)
                </button>
                <button
                  onClick={() => setActiveThirdRowTab("queue")}
                  className={`px-3 py-1 text-[10px] font-mono font-bold rounded-md transition-all ${
                    activeThirdRowTab === "queue" ? "bg-white/15 text-white border border-white/40" : "text-slate-400 hover:text-white"
                  }`}
                >
                  MAINTENANCE QUEUE
                </button>
                <button
                  onClick={() => setActiveThirdRowTab("procurement")}
                  className={`px-3 py-1 text-[10px] font-mono font-bold rounded-md transition-all ${
                    activeThirdRowTab === "procurement" ? "bg-white/15 text-white border border-white/40" : "text-slate-400 hover:text-white"
                  }`}
                >
                  SPARE PARTS RISK
                </button>
              </div>
            </div>

            {/* Dynamic Panel Renderer with Consistent Heights (min-h-[160px]) */}
            <div className="min-h-[160px] flex flex-col justify-center">

              {activeThirdRowTab === "timeline" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white/[0.05] border-white/20 rounded-xl p-3 flex flex-col justify-between font-mono">
                    <div className="flex justify-between items-center text-[10px] text-slate-400 border-b border-white/[0.05] pb-1.5 mb-2">
                      <span>DAY +4 OUTLOOK</span>
                      <span className="text-red-400 font-bold">CRITICAL RISK</span>
                    </div>
                    <p className="text-xs font-bold text-white">Blast Furnace No.2 Hearth</p>
                    <p className="text-[10px] text-slate-400 mt-1 leading-normal">Refractory erosion with rising thrust-bearing vibration. Repair checklist pending operator trigger.</p>
                    <div className="flex justify-between items-center mt-3 text-[10px] pt-1.5 border-t border-white/[0.05]">
                      <span className="text-slate-500">PROBABILITY:</span>
                      <span className="text-red-400 font-bold">96%</span>
                    </div>
                  </div>

                  <div className="bg-white/[0.05] border-white/20 rounded-xl p-3 flex flex-col justify-between font-mono">
                    <div className="flex justify-between items-center text-[10px] text-slate-400 border-b border-white/[0.05] pb-1.5 mb-2">
                      <span>DAY +12 OUTLOOK</span>
                      <span className="text-amber-500 font-bold">MEDIUM RISK</span>
                    </div>
                    <p className="text-xs font-bold text-white">Hot Strip Mill Stand #3</p>
                    <p className="text-[10px] text-slate-400 mt-1 leading-normal">Gearbox bearing wear; lubrication film degrading. Vibration tracked continuously.</p>
                    <div className="flex justify-between items-center mt-3 text-[10px] pt-1.5 border-t border-white/[0.05]">
                      <span className="text-slate-500">PROBABILITY:</span>
                      <span className="text-amber-500 font-bold">74%</span>
                    </div>
                  </div>

                  <div className="bg-white/[0.05] border-white/20 rounded-xl p-3 flex flex-col justify-between font-mono">
                    <div className="flex justify-between items-center text-[10px] text-slate-400 border-b border-white/[0.05] pb-1.5 mb-2">
                      <span>DAY +22 OUTLOOK</span>
                      <span className="text-emerald-400 font-bold">LOW RISK</span>
                    </div>
                    <p className="text-xs font-bold text-white">Cooling System Pump #4</p>
                    <p className="text-[10px] text-slate-400 mt-1 leading-normal">Motor winding resistance drift detected. Winding insulation check recommended.</p>
                    <div className="flex justify-between items-center mt-3 text-[10px] pt-1.5 border-t border-white/[0.05]">
                      <span className="text-slate-500">PROBABILITY:</span>
                      <span className="text-emerald-400 font-bold">56%</span>
                    </div>
                  </div>
                </div>
              )}

              {activeThirdRowTab === "queue" && (
                <div className="overflow-x-auto w-full">
                  <table className="w-full text-left border-collapse font-mono text-xs">
                    <thead>
                      <tr className="border-b border-white/[0.06] text-slate-400 text-[10px]">
                        <th className="pb-2 font-semibold">RANK</th>
                        <th className="pb-2 font-semibold">TARGET ASSET</th>
                        <th className="pb-2 font-semibold">DIAGNOSTIC FAULT</th>
                        <th className="pb-2 font-semibold">SEVERITY</th>
                        <th className="pb-2 font-semibold">URGENCY SCORE</th>
                        <th className="pb-2 font-semibold">ACTION WINDOW</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-white/[0.03] hover:bg-white/[0.01]">
                        <td className="py-2.5 font-bold text-red-500">#1</td>
                        <td className="py-2.5 text-white font-bold">Blast Furnace No.2 Hearth</td>
                        <td className="py-2.5 text-slate-300">High Vibration</td>
                        <td className="py-2.5"><span className="text-red-400 bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20 text-[9px] font-bold">CRITICAL</span></td>
                        <td className="py-2.5 text-white font-bold">98/100</td>
                        <td className="py-2.5 text-red-400 font-bold">Within 48h</td>
                      </tr>
                      <tr className="border-b border-white/[0.03] hover:bg-white/[0.01]">
                        <td className="py-2.5 font-bold text-amber-500">#2</td>
                        <td className="py-2.5 text-white font-bold">Hot Strip Mill Stand #3</td>
                        <td className="py-2.5 text-slate-300">Bearing Wear</td>
                        <td className="py-2.5"><span className="text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20 text-[9px] font-bold">HIGH</span></td>
                        <td className="py-2.5 text-white font-bold">84/100</td>
                        <td className="py-2.5 text-amber-400 font-bold">5 Days</td>
                      </tr>
                      <tr className="hover:bg-white/[0.01]">
                        <td className="py-2.5 font-bold text-slate-400">#3</td>
                        <td className="py-2.5 text-white font-bold">Power Station Transformer T-2</td>
                        <td className="py-2.5 text-slate-300">Motor Overload</td>
                        <td className="py-2.5"><span className="text-yellow-400 bg-yellow-500/10 px-1.5 py-0.5 rounded border border-yellow-500/20 text-[9px] font-bold">MEDIUM</span></td>
                        <td className="py-2.5 text-white font-bold">62/100</td>
                        <td className="py-2.5 text-slate-400">Next Scheduled Downtime</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {activeThirdRowTab === "procurement" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
                  <div className="bg-white/[0.05] border-white/20 rounded-xl p-3 flex flex-col justify-between">
                    <div>
                      <p className="text-[10px] text-slate-400">ITEM ID: #BF-REF-GR12</p>
                      <p className="text-xs font-bold text-white mt-0.5">Specialist Hearth Refractory Grout</p>
                    </div>
                    <div className="space-y-1 mt-2 text-[10px]">
                      <div className="flex justify-between"><span className="text-slate-400">LEAD TIME:</span><span className="text-red-400 font-bold">14 Days</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">IN STOCK:</span><span className="text-red-400 font-bold">2 Units (Critical Low)</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">PRODUCTION IMPACT:</span><span className="text-white font-bold">HIGH</span></div>
                    </div>
                  </div>

                  <div className="bg-white/[0.05] border-white/20 rounded-xl p-3 flex flex-col justify-between">
                    <div>
                      <p className="text-[10px] text-slate-400">ITEM ID: #HSM-BRG-88X</p>
                      <p className="text-xs font-bold text-white mt-0.5">Mill Stand #3 Gearbox Roller Bearing</p>
                    </div>
                    <div className="space-y-1 mt-2 text-[10px]">
                      <div className="flex justify-between"><span className="text-slate-400">LEAD TIME:</span><span className="text-amber-500 font-bold">3 Days</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">IN STOCK:</span><span className="text-amber-500 font-bold">1 Unit (Low)</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">PRODUCTION IMPACT:</span><span className="text-white font-bold">MEDIUM</span></div>
                    </div>
                  </div>

                  <div className="bg-white/[0.05] border-white/20 rounded-xl p-3 flex flex-col justify-between">
                    <div>
                      <p className="text-[10px] text-slate-400">ITEM ID: #PWR-REL-108</p>
                      <p className="text-xs font-bold text-white mt-0.5">Transformer Stage-2 Fan Relay Unit</p>
                    </div>
                    <div className="space-y-1 mt-2 text-[10px]">
                      <div className="flex justify-between"><span className="text-slate-400">LEAD TIME:</span><span className="text-emerald-400 font-bold">1 Day</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">IN STOCK:</span><span className="text-emerald-400 font-bold">12 Units (Secure)</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">PRODUCTION IMPACT:</span><span className="text-white font-bold">HIGH</span></div>
                    </div>
                  </div>
                </div>
              )}

            </div>
          </div>

          {/* ============================================================ */}
          {/* 05 — OPERATIONAL METRICS (Telemetry Stream + Injection Suite)*/}
          {/* ============================================================ */}
          <SectionLabel index="05" title="Reliability Analysis" sub="Telemetry & Condition Monitoring" dotClass="bg-steel-500" />

          <div className="grid grid-cols-12 gap-5">

            {/* Telemetry stream for selected plant */}
            <div className="col-span-12 lg:col-span-8 card-glass p-5 flex flex-col">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <Activity size={14} className="text-steel-400" />
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                    Telemetry Stream · {assetName(selectedPlantId)}
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-slate-500">REALTIME SAMPLE RATE: 10HZ</span>
              </div>
              <div className="bg-white/[0.03] border border-white/20 p-3 rounded-xl flex-1 flex items-center">
                <div className="w-full">
                  {selectedPlantId === "Plant-C" ? (
                    <EnergyAreaChart data={timeseries.energy_series} height={200} />
                  ) : (
                    <SensorLineChart data={timeseries.plant_series} height={200} />
                  )}
                </div>
              </div>
            </div>

            {/* Live Telemetry Injection Suite (utility) */}
            <div className="col-span-12 lg:col-span-4 card-glass p-5 flex flex-col font-mono">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 mb-4">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Radio size={12} className="text-steel-400 animate-pulse" /> Condition Test Suite
                </h4>
              </div>
              <p className="text-[10px] text-slate-400 leading-relaxed mb-4">
                Inject simulated fault signatures to verify Sherlock AI&apos;s real-time anomaly detection and diagnosis.
              </p>
              <div className="grid grid-cols-1 gap-2.5 mt-auto">
                {DEMO_ALERT_TYPES.map(a => (
                  <button
                    key={a.id}
                    onClick={() => handleDemoAlert(a.id, a.plant)}
                    disabled={demoLoading}
                    className="px-3 py-2 rounded-lg bg-white/[0.04] border border-white/25 text-[10px] font-bold text-slate-300 hover:text-white hover:border-red-500/40 hover:bg-red-950/20 transition-all disabled:opacity-40 flex items-center justify-between"
                  >
                    <span>{a.label}</span>
                    <span className="text-slate-500">{assetName(a.plant)}</span>
                  </button>
                ))}
              </div>
            </div>

          </div>

          {demoMsg && (
            <div className="fixed bottom-6 right-6 p-4 bg-white/[0.07] border border-red-500/30 rounded-xl font-mono text-xs text-amber-400 shadow-2xl animate-bounce z-50 flex items-center gap-2">
              <ShieldAlert size={14} className="text-red-500" />
              <span>{demoMsg}</span>
            </div>
          )}

        </div>
      </div>
    </AppShell>
  );
}
