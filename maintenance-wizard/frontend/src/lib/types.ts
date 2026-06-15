// TypeScript mirror of the FastAPI responses. Field names match the backend
// exactly (verified against the Phase 6 routers and models).

export type Severity = 'low' | 'medium' | 'high' | 'critical';
export type TicketStatus = 'open' | 'acknowledged' | 'in_progress' | 'resolved' | 'closed';
export type TicketKind = 'acute_alarm' | 'predictive_advisory' | 'user_request';
export type Role = 'engineer' | 'supervisor' | 'plant_manager' | 'analyst' | 'system';

export interface User {
  user_id: string;
  name: string;
  role: string;
  area: string;
}

/** Provenance citation. `kind` selects which other fields are populated. */
export interface SourceRef {
  kind: 'document' | 'record' | 'sensor' | 'computation' | string;
  doc_id?: string | null;
  doc_type?: string | null;
  source?: string | null;
  section?: string | null;
  equipment_id?: string | null;
  score?: number | null;
  table?: string | null;
  id?: string | null;
  window?: Record<string, unknown> | null;
  n_samples?: number | null;
  method?: string | null;
  detail?: string | null;
  model?: string | null;
  drivers?: string[] | null;
}

export interface Finding {
  role: string;
  summary: string;
  key_facts: Record<string, unknown>;
  provenance: SourceRef[];
  tools_used: string[];
  stop_reason: string;
  tokens_in: number;
  tokens_out: number;
}

export interface PlanStep {
  step: number;
  tool: string;
  args: Record<string, unknown>;
  ok: boolean;
}

export interface Equipment {
  equipment_id: string;
  name: string;
  area: string;
  type: string;
  manufacturer_code?: string;
  model_no?: string;
  install_date?: string;
  service_hours?: number;
  mtbf_hours?: number;
  monitored?: boolean;
  process_criticality?: string;
  typical_delay_severity_min?: number;
  spare_availability?: string;
  procurement_lead_time_weeks?: number;
  notes?: string;
  [key: string]: unknown;
}

export interface PriorityComponent {
  dimension: string;
  raw_value: string | number;
  normalized: number;
  weight: number;
  contribution: number;
}

export interface PriorityItem {
  equipment_id: string;
  name: string;
  priority_score: number;
  base_score?: number;
  rank?: number;
  vital_few?: boolean;
  components?: PriorityComponent[];
  dynamic_risk?: string;
  [key: string]: unknown;
}

export interface SensorChannel {
  unit: string;
  latest: number;
  mean: number;
  min: number;
  max: number;
  std: number;
  slope_per_day: number;
}

export interface SensorSeriesPoint {
  timestamp: string;
  [channel: string]: number | string | null;
}

export interface SensorData {
  window: { start: string; end: string; n_samples: number };
  channels: Record<string, SensorChannel>;
  regime: { current: string; counts: Record<string, number> };
  anomalies: { count: number; last_at: string | null };
  iso_thresholds_mm_s?: { alert: number; action: number; damage: number };
  series?: SensorSeriesPoint[];
}

export interface TicketUpdate {
  timestamp: string;
  note: string;
  status: string | null;
  author: string | null;
}

export interface FeedbackRecord {
  feedback_id?: string;
  created_at?: string;
  target_type?: string;
  target_id?: string | null;
  feedback_type?: string;
  rating?: number | null;
  correction?: string | null;
  author_user_id?: string;
  notes?: string | null;
}

export interface Ticket {
  ticket_id: string;
  status: string;
  severity: string;
  kind: string;
  equipment_id: string;
  title: string;
  originating_event?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  answer: string;
  findings: Finding[];
  provenance: SourceRef[];
  recommended_actions?: string;
  timeline: TicketUpdate[];
  feedback: FeedbackRecord[];
}

export interface Alert {
  alert_id: string;
  timestamp: string;
  equipment_id: string;
  severity: string;
  kind: string;
  message: string;
  headline?: string; // clean, derived display headline (preferred over message)
  subline?: string; // muted technical sub-line (score + humanized drivers)
  ticket_id: string | null;
  anomaly_score: number | null;
  contributing_channels: string[];
  analysis_summary: string;
  acknowledged: boolean;
  audience_roles: string[];
}

export interface LogbookEntry {
  entry_id: string;
  timestamp: string;
  equipment_id: string;
  author_user_id: string;
  entry_type: string;
  text: string;
  related_fault_code: string | null;
}

export interface EquipmentDetail {
  equipment: Equipment;
  sensors: SensorData | null;
  open_tickets: Ticket[];
  logbook: LogbookEntry[];
}

export interface ReportSection {
  role: string;
  summary: string;
  key_facts: Record<string, unknown>;
}

export interface Report {
  equipment_id: string;
  generated_at: string;
  title: string;
  body: string;
  sections: ReportSection[];
  provenance: SourceRef[];
  specialists_used: string[];
  tokens_in: number;
  tokens_out: number;
}

export interface ProactiveState {
  cursor: string;
  end: string;
  monitored_assets: string[];
  last_polled_at?: string | null;
  server_now?: string;
}

export interface ProactiveOutcome {
  kind: string;
  equipment_id: string;
  alert_id: string;
  ticket_id: string;
  severity: string;
  tokens_in: number;
  tokens_out: number;
}

export interface PollRequest {
  advance_to?: string;
  steps?: number;
  equipment_id?: string;
}

export interface PollResult {
  cursor: string;
  outcomes: ProactiveOutcome[];
  alerts: Alert[];
}

export interface FeedbackRequest {
  target_type: string;
  feedback_type: string;
  target_id?: string | null;
  rating?: number | null;
  correction?: string | null;
  author_user_id?: string | null;
  notes?: string | null;
}

// --- SSE events ---

/** Events shared by the chat stream and the proactive self-diagnosis stream. */
export type TraceEvent =
  | { type: 'status'; message: string; session_id?: string }
  | { type: 'tool_start'; tool: string; session_id?: string }
  | { type: 'tool_end'; tool: string; ok: boolean; summary?: string; session_id?: string }
  | { type: 'error'; message: string; session_id?: string };

export interface ChatFinal {
  type: 'final';
  answer: string;
  provenance: SourceRef[];
  specialists_used: string[];
  findings: Finding[];
  plan: PlanStep[];
  session_id: string;
  iterations: number;
  stop_reason: string;
  tokens_in: number;
  tokens_out: number;
}

export type ChatEvent = TraceEvent | ChatFinal;

export interface ProactiveFinal {
  type: 'final';
  outcomes: ProactiveOutcome[];
  alerts: Alert[];
  cursor: string;
  session_id?: string;
}

export type ProactiveStreamEvent = TraceEvent | ProactiveFinal;
