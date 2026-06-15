import { Activity, Cpu, Database, FileText, type LucideIcon } from 'lucide-react';

import { CiteChip, renderCitations } from '@/components/ui/Cite';
import { channelLabel } from '@/lib/channels';
import type { SourceRef } from '@/lib/types';

export function sourceLabel(s: SourceRef): { primary: string; secondary?: string } {
  switch (s.kind) {
    case 'document':
      return { primary: s.doc_id ?? s.source ?? 'Document', secondary: s.section ?? s.doc_type ?? undefined };
    case 'record':
      return { primary: `${s.table ?? 'record'} · ${s.id ?? ''}`.trim(), secondary: s.equipment_id ?? undefined };
    case 'sensor':
      return { primary: 'Sensor window', secondary: s.n_samples ? `${s.n_samples} samples` : undefined };
    case 'computation':
      return {
        primary: s.method ?? 'Computation',
        secondary: s.model ?? s.drivers?.map(channelLabel).join(', ') ?? undefined,
      };
    default:
      return { primary: s.kind };
  }
}

function iconFor(kind: string): LucideIcon {
  if (kind === 'document') return FileText;
  if (kind === 'record') return Database;
  if (kind === 'sensor') return Activity;
  return Cpu;
}

export function ProvenanceList({
  sources,
  title = 'Sources',
  bare = false,
}: {
  sources: SourceRef[];
  title?: string;
  bare?: boolean;
}) {
  if (!sources || sources.length === 0) return null;
  return (
    <div>
      {!bare && (
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-muted">
          {title} ({sources.length})
        </p>
      )}
      <ul className="space-y-1.5">
        {sources.map((s, i) => {
          const { primary, secondary } = sourceLabel(s);
          const Icon = iconFor(s.kind);
          return (
            <li
              key={i}
              className="flex items-start gap-2 rounded-md border border-hairline bg-canvas px-2.5 py-1.5 text-xs"
            >
              <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-subtle" />
              <span className="min-w-0">
                <span className="font-medium text-ink-secondary">{renderCitations(primary)}</span>
                {secondary && <span className="text-ink-muted"> · {renderCitations(secondary)}</span>}
                {typeof s.score === 'number' && (
                  <span className="ml-1 text-ink-subtle">({s.score.toFixed(2)})</span>
                )}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// Numbered source badge -- delegates to the shared CiteChip so numbered refs and inline
// label/number chips get identical visual treatment (one chip component, app-wide).
export function CitationChip({ index, source }: { index: number; source: SourceRef }) {
  const { primary } = sourceLabel(source);
  return <CiteChip label={String(index)} title={primary} />;
}
