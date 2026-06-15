import { Check, ChevronRight, Loader2, Sparkles, X } from 'lucide-react';

import { MarkdownView } from '@/components/ui';
import type { TraceNode } from '@/hooks/trace';
import { cn } from '@/lib/cn';
import { titleCase } from '@/lib/format';
import { humanizeTrace } from '@/lib/humanizeTrace';

interface TraceListProps {
  trace: TraceNode[];
  streaming?: boolean;
  title?: string;
  // When false, render only the step list (no header/box) -- for use inside a collapsed
  // disclosure that already provides the "Agent reasoning" header. Defaults to the full box.
  header?: boolean;
}

export function TraceList({ trace, streaming, title = 'Agent reasoning', header = true }: TraceListProps) {
  if (trace.length === 0) return null;
  const steps = (
    <ul className="space-y-1">
      {trace.map((n) => (
        <li key={n.id} className="flex items-start gap-2 text-sm" style={{ paddingLeft: n.depth * 18 }}>
          <span className="mt-0.5 shrink-0">
            {n.kind === 'status' ? (
              <ChevronRight className="h-3.5 w-3.5 text-ink-subtle" />
            ) : n.running ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin text-brand-500" />
            ) : n.ok === false ? (
              <X className="h-3.5 w-3.5 text-critical" />
            ) : (
              <Check className="h-3.5 w-3.5 text-healthy" />
            )}
          </span>
          <div className="min-w-0">
            <span className={cn('font-medium', n.kind === 'status' ? 'text-ink-secondary' : 'text-ink')}>
              {n.kind === 'tool' ? titleCase(n.label) : humanizeTrace(n.label)}
            </span>
            {n.summary && (
              <MarkdownView className="text-ink-muted" compact>
                {humanizeTrace(n.summary)}
              </MarkdownView>
            )}
          </div>
        </li>
      ))}
    </ul>
  );

  if (!header) return steps;

  return (
    <div className="rounded-lg border border-hairline bg-canvas p-3">
      <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-ink-muted">
        <Sparkles className="h-3.5 w-3.5 text-brand-500" />
        {title}
        {streaming && <Loader2 className="h-3 w-3 animate-spin text-brand-500" />}
      </p>
      {steps}
    </div>
  );
}
