export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  plant: string;
}

export interface PlantStatus {
  id: string;
  name: string;
  status: "NORMAL" | "WARNING" | "CRITICAL";
  failure_probability: number;
  production_rate: number;
  units: string[];
}

export interface DashboardKPIs {
  summary: {
    downtime_prediction_pct: number;
    safety_score: number;
    energy_score: number;
    production_kpi: number;
    active_alerts: number;
    critical_incidents: number;
    overdue_maintenance: number;
    total_co2_tonnes: number;
    potential_savings_kwh: number;
  };
  plant_summaries: PlantSummary[];
  recent_alerts: Alert[];
  maintenance_status: {
    overdue: number;
    in_progress: number;
    scheduled: number;
    total_cost_usd: number;
  };
}

export interface PlantSummary {
  plant_id: string;
  failure_probability: number;
  safety_score: number;
  energy_efficiency: number;
  production_rate: number;
  downtime_hours: number;
  status: "NORMAL" | "WARNING" | "CRITICAL";
}

export interface Alert {
  id: string;
  plant: string;
  unit: string;
  type: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  risk_score: number;
  timestamp: string;
  resolved: boolean;
}

export interface MaintenancePrediction {
  timestamp: string;
  plant_id: string;
  unit_id: string;
  vibration: number;
  temperature: number;
  pressure: number;
  failure_probability: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  recommended_action: string;
  confidence: number;
}

export interface SafetyIncident {
  timestamp: string;
  plant_id: string;
  unit_id: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  incident_type: string;
  risk_score: number;
  resolved: number;
  response_time_minutes: number;
}

export interface EnergyReading {
  timestamp: string;
  plant_id: string;
  unit_id: string;
  electricity_kwh: number;
  gas_m3: number;
  steam_kg: number;
  total_energy_kwh: number;
  efficiency_ratio: number;
  co2_tonnes: number;
  potential_savings_kwh: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  confidence?: number;
  reasoning?: string;
  impact?: string;
  timestamp: Date;
}

export interface AgentResponse {
  agent: string;
  response: string;
  confidence: number;
  reasoning: string;
  impact: string;
  routing_scores: Record<string, number>;
  query: string;
}

export const SEVERITY_COLORS = {
  CRITICAL: "text-red-400",
  HIGH:     "text-amber-400",
  MEDIUM:   "text-yellow-400",
  LOW:      "text-green-400",
  NORMAL:   "text-steel-300",
};

export const STATUS_COLORS = {
  CRITICAL: "#ef4444",
  WARNING:  "#f59e0b",
  NORMAL:   "#10b981",
};

export const AGENT_COLORS: Record<string, string> = {
  MAINTENANCE: "#f59e0b",
  SAFETY:      "#ef4444",
  ENERGY:      "#10b981",
  PRODUCTION:  "#06b6d4",
  REPORTING:   "#db2777",
  SUPERVISOR:  "#9f1239",
};

export const AGENT_ICONS: Record<string, string> = {
  MAINTENANCE: "🔧",
  SAFETY:      "🛡️",
  ENERGY:      "⚡",
  PRODUCTION:  "🏭",
  REPORTING:   "📊",
  SUPERVISOR:  "🤖",
};

export const AGENT_NAMES: Record<string, string> = {
  MAINTENANCE: "Predictive Reliability Specialist",
  SAFETY:      "HSE Risk Analyst",
  ENERGY:      "Energy Systems Optimizer",
  PRODUCTION:  "Operations Flow Engineer",
  REPORTING:   "Executive Systems Reporter",
  SUPERVISOR:  "Sherlock Lead Orchestrator",
};

