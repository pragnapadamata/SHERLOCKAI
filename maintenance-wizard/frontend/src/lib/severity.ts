import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Circle,
  Info,
  type LucideIcon,
} from 'lucide-react';

/**
 * The single source of truth for how severity, priority, and health render.
 * Class strings are written as literals so Tailwind's content scanner keeps them.
 * One semantic ramp: critical=red -> high=orange -> medium=amber -> low/healthy=green,
 * with slate for neutral/unknown. Categorical chips (criticality, spares, logbook entry
 * types) reuse this same scale via `toneClasses`, so a colour means the same thing
 * everywhere it appears.
 */
export type Tone = 'critical' | 'high' | 'medium' | 'low' | 'neutral';

interface ToneClasses {
  chip: string; // light bg + text + hairline border -- a subtle categorical chip
  text: string; // foreground colour only (e.g. the priority number)
  dot: string; // solid fill for a leading dot / accent
}

// The canonical scale: text-600 / bg-50 (slate-100 for neutral) / border-200.
const SCALE: Record<Tone, ToneClasses> = {
  critical: { chip: 'bg-red-50 text-red-600 border border-red-200', text: 'text-red-600', dot: 'bg-red-500' },
  high: { chip: 'bg-orange-50 text-orange-600 border border-orange-200', text: 'text-orange-600', dot: 'bg-orange-500' },
  medium: { chip: 'bg-amber-50 text-amber-600 border border-amber-200', text: 'text-amber-600', dot: 'bg-amber-500' },
  low: { chip: 'bg-green-50 text-green-600 border border-green-200', text: 'text-green-600', dot: 'bg-green-500' },
  neutral: { chip: 'bg-slate-100 text-slate-600 border border-slate-200', text: 'text-slate-600', dot: 'bg-slate-400' },
};

/** Chip colour classes for a categorical value on the shared scale (case-insensitive). */
export function toneClasses(tone: string): ToneClasses {
  return SCALE[String(tone).toLowerCase() as Tone] ?? SCALE.neutral;
}

// Hex of each tone (matches the SCALE text-600 shades) for SVG charts, which need a raw
// colour rather than a Tailwind class. Keep in step with SCALE above.
const TONE_HEX: Record<Tone, string> = {
  critical: '#DC2626', // red-600
  high: '#EA580C', // orange-600
  medium: '#D97706', // amber-600
  low: '#16A34A', // green-600
  neutral: '#64748B', // slate-500
};

/** Hex colour for a tone, for use in recharts/SVG (case-insensitive). */
export function toneHex(tone: string): string {
  return TONE_HEX[String(tone).toLowerCase() as Tone] ?? TONE_HEX.neutral;
}

export type Severity = 'critical' | 'high' | 'medium' | 'low';

interface SeverityStyle {
  label: string;
  badge: string; // soft background + foreground text + hairline ring
  dot: string; // solid colour for the leading dot / accent bar
  solid: string; // solid text colour
  icon: LucideIcon;
}

function fromScale(tone: Tone, label: string, icon: LucideIcon): SeverityStyle {
  const s = SCALE[tone];
  return { label, badge: s.chip, dot: s.dot, solid: s.text, icon };
}

const SEVERITY: Record<Severity, SeverityStyle> = {
  critical: fromScale('critical', 'Critical', AlertOctagon),
  high: fromScale('high', 'High', AlertTriangle),
  medium: fromScale('medium', 'Medium', Info),
  low: fromScale('low', 'Healthy', CheckCircle2),
};

const IDLE: SeverityStyle = fromScale('neutral', 'Unknown', Circle);

export function severityStyle(severity: string): SeverityStyle {
  return SEVERITY[severity as Severity] ?? { ...IDLE, label: severity || 'Unknown' };
}

/** Bucket a 0..100 priority score (or anomaly-derived score) into a severity. */
export function scoreToSeverity(score: number): Severity {
  if (score >= 85) return 'critical';
  if (score >= 70) return 'high';
  if (score >= 50) return 'medium';
  return 'low';
}

/** Spares-availability chip: in stock = green, on order = amber, else neutral. */
export function spareChip(availability: string): string {
  const v = String(availability).toLowerCase();
  if (v === 'in_stock') return 'bg-green-50 text-green-700 border border-green-200';
  if (v === 'on_order') return 'bg-amber-50 text-amber-700 border border-amber-200';
  return SCALE.neutral.chip;
}

/** Logbook entry-type chip, mapped onto the shared scale (observation stays slate). */
const ENTRY_TONE: Record<string, Tone> = {
  alert: 'critical',
  confirmation: 'low',
  action: 'medium',
  observation: 'neutral',
};
export function entryTypeChip(entryType: string): string {
  return toneClasses(ENTRY_TONE[String(entryType).toLowerCase()] ?? 'neutral').chip;
}

/** Ticket lifecycle status reuses the same token families for visual consistency. */
export type TicketStatus = 'open' | 'acknowledged' | 'in_progress' | 'resolved' | 'closed';

interface StatusStyle {
  label: string;
  badge: string;
  dot: string;
}

const STATUS: Record<TicketStatus, StatusStyle> = {
  open: { label: 'Open', badge: 'bg-medium-soft text-medium-fg border border-medium-ring', dot: 'bg-medium' },
  acknowledged: {
    label: 'Acknowledged',
    badge: 'bg-idle-soft text-idle-fg border border-idle-ring',
    dot: 'bg-idle',
  },
  in_progress: {
    label: 'In progress',
    badge: 'bg-high-soft text-high-fg border border-high-ring',
    dot: 'bg-high',
  },
  resolved: {
    label: 'Resolved',
    badge: 'bg-healthy-soft text-healthy-fg border border-healthy-ring',
    dot: 'bg-healthy',
  },
  closed: { label: 'Closed', badge: 'bg-idle-soft text-idle-fg border border-idle-ring', dot: 'bg-idle' },
};

export function statusStyle(status: string): StatusStyle {
  return (
    STATUS[status as TicketStatus] ?? {
      label: status,
      badge: 'bg-idle-soft text-idle-fg border border-idle-ring',
      dot: 'bg-idle',
    }
  );
}

/** Valid forward transitions for the ticket lifecycle (mirrors the backend service). */
export const STATUS_TRANSITIONS: Record<TicketStatus, TicketStatus[]> = {
  open: ['acknowledged', 'in_progress', 'closed'],
  acknowledged: ['in_progress', 'resolved', 'closed'],
  in_progress: ['resolved', 'closed'],
  resolved: ['closed', 'in_progress'],
  closed: [],
};
