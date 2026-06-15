import { currentUserId } from '@/auth/session';

import type {
  Alert,
  Equipment,
  EquipmentDetail,
  FeedbackRecord,
  FeedbackRequest,
  LogbookEntry,
  PollRequest,
  PollResult,
  PriorityItem,
  ProactiveState,
  Report,
  SensorData,
  Ticket,
  User,
} from './types';

/** Same origin by default (Vite proxy in dev, FastAPI static mount for the single-origin build). */
export const API_BASE = import.meta.env.VITE_API_BASE ?? '';

export class ApiError extends Error {
  status: number;
  detail?: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

export async function apiFetch<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const uid = currentUserId();
  if (uid) headers['X-User-Id'] = uid;
  Object.assign(headers, opts.headers ?? {}); // explicit override (e.g. resolving an OAuth uid)

  const res = await fetch(`${API_BASE}${path}`, {
    method: opts.method ?? 'GET',
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    signal: opts.signal,
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    let detail: unknown;
    try {
      const data = (await res.json()) as { detail?: unknown };
      detail = data?.detail ?? data;
      if (typeof detail === 'string') message = detail;
    } catch {
      // non-JSON error body; keep the generic message
    }
    throw new ApiError(res.status, message, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function query(params: Record<string, string | number | boolean | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') q.set(k, String(v));
  }
  const s = q.toString();
  return s ? `?${s}` : '';
}

export const api = {
  me: (asUserId?: string) =>
    apiFetch<User>('/api/me', asUserId ? { headers: { 'X-User-Id': asUserId } } : {}),
  users: () => apiFetch<User[]>('/api/users'),

  equipment: () => apiFetch<Equipment[]>('/api/dashboard/equipment'),
  priority: () => apiFetch<PriorityItem[]>('/api/dashboard/priority'),
  sensors: (id: string, opts?: { series?: boolean; last_n?: number }) =>
    apiFetch<SensorData>(`/api/dashboard/sensors/${id}${query({ series: opts?.series, last_n: opts?.last_n })}`),
  equipmentDetail: (id: string) => apiFetch<EquipmentDetail>(`/api/dashboard/equipment/${id}`),

  alerts: (opts?: { unacknowledged?: boolean; equipment_id?: string }) =>
    apiFetch<Alert[]>(`/api/alerts${query({ unacknowledged: opts?.unacknowledged, equipment_id: opts?.equipment_id })}`),
  ackAlert: (id: string) => apiFetch<Alert>(`/api/alerts/${id}/ack`, { method: 'POST' }),

  tickets: (opts?: { status?: string; equipment_id?: string }) =>
    apiFetch<Ticket[]>(`/api/tickets${query({ status: opts?.status, equipment_id: opts?.equipment_id })}`),
  ticket: (id: string) => apiFetch<Ticket>(`/api/tickets/${id}`),
  updateTicketStatus: (id: string, body: { status: string; note?: string }) =>
    apiFetch<Ticket>(`/api/tickets/${id}/status`, { method: 'POST', body }),
  addTimelineNote: (id: string, note: string) =>
    apiFetch<Ticket>(`/api/tickets/${id}/timeline`, { method: 'POST', body: { note } }),

  submitFeedback: (body: FeedbackRequest) =>
    apiFetch<FeedbackRecord>('/api/feedback', { method: 'POST', body }),

  generateReport: (equipment_id: string) =>
    apiFetch<Report>('/api/reports', {
      method: 'POST',
      body: { equipment_id },
      signal: AbortSignal.timeout(300_000), // a full live agentic run can take 1-3 min; allow up to 5
    }),

  logbook: (opts?: { equipment_id?: string; limit?: number }) =>
    apiFetch<LogbookEntry[]>(`/api/logbook${query({ equipment_id: opts?.equipment_id, limit: opts?.limit })}`),

  proactiveState: () => apiFetch<ProactiveState>('/api/proactive/state'),
  runPoll: (body: PollRequest) => apiFetch<PollResult>('/api/proactive/poll', { method: 'POST', body }),
  resetProactive: () => apiFetch<ProactiveState>('/api/proactive/reset', { method: 'POST' }),
};
