"use client";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  PieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

const CHART_COLORS = ["#9f1239","#10b981","#f59e0b","#ef4444","#06b6d4","#db2777","#f43f5e"];

// Custom Tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-50 border border-card-border rounded-lg p-3 text-sm shadow-xl">
      {label && <div className="text-muted-foreground text-xs mb-2 font-medium">{label}</div>}
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2 py-0.5">
          <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-gray-300">{p.name}:</span>
          <span className="text-white font-mono font-medium">{typeof p.value === "number" ? p.value.toFixed(2) : p.value}</span>
        </div>
      ))}
    </div>
  );
};

interface BaseChartProps {
  data: any[];
  height?: number;
}

// Line Chart
export function SensorLineChart({ data, height = 250 }: BaseChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#3a1b24" />
        <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} stroke="#4b5563"
          tickFormatter={(v) => v ? new Date(v).toLocaleDateString("en-IN", { month: "short", day: "numeric" }) : ""}
          interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 10 }} stroke="#4b5563" />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
        <Line type="monotone" dataKey="failure_probability" stroke="#ef4444" strokeWidth={2} dot={false} name="Failure Prob" />
        <Line type="monotone" dataKey="vibration" stroke="#f59e0b" strokeWidth={2} dot={false} name="Vibration" />
      </LineChart>
    </ResponsiveContainer>
  );
}

// Area Chart for Energy
export function EnergyAreaChart({ data, height = 250 }: BaseChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <defs>
          <linearGradient id="elecGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="effGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#3a1b24" />
        <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} stroke="#4b5563"
          tickFormatter={(v) => v ? new Date(v).toLocaleDateString("en-IN", { month: "short", day: "numeric" }) : ""}
          interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 10 }} stroke="#4b5563" />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: "11px" }} />
        <Area type="monotone" dataKey="total_energy_kwh" stroke="#06b6d4" fill="url(#elecGrad)" strokeWidth={2} name="Energy (kWh)" />
        <Area type="monotone" dataKey="efficiency_ratio" stroke="#10b981" fill="url(#effGrad)" strokeWidth={2} name="Efficiency" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// Bar Chart for production
export function ProductionBarChart({ data, height = 250 }: BaseChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#3a1b24" />
        <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="#4b5563" />
        <YAxis tick={{ fontSize: 10 }} stroke="#4b5563" />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: "11px" }} />
        <Bar dataKey="actual" fill="#9f1239" name="Actual" radius={[4, 4, 0, 0]} />
        <Bar dataKey="target" fill="#374151" name="Target" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// Pie Chart for incident types
export function IncidentPieChart({ data, height = 220 }: { data: { name: string; value: number }[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie data={data} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
          paddingAngle={3} dataKey="value">
          {data.map((_, i) => (
            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: "11px" }} iconType="circle" />
      </PieChart>
    </ResponsiveContainer>
  );
}

// Radar chart for plant health
export function PlantHealthRadar({ data, height = 280 }: { data: any[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data}>
        <PolarGrid stroke="#3a1b24" />
        <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: "#9ca3af" }} />
        <Radar name="Score" dataKey="value" stroke="#9f1239" fill="#9f1239" fillOpacity={0.2} strokeWidth={2} />
        <Tooltip content={<CustomTooltip />} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

// Generic bar chart
export function SimpleBarChart({ data, xKey, bars, height = 250 }: {
  data: any[]; xKey: string; bars: { key: string; color: string; label: string }[]; height?: number
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#3a1b24" />
        <XAxis dataKey={xKey} tick={{ fontSize: 10 }} stroke="#4b5563" />
        <YAxis tick={{ fontSize: 10 }} stroke="#4b5563" />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: "11px" }} />
        {bars.map(b => (
          <Bar key={b.key} dataKey={b.key} fill={b.color} name={b.label} radius={[3, 3, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
