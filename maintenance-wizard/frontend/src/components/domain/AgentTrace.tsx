import { Collapsible, MarkdownView } from '@/components/ui';
import type { ChatTurn } from '@/hooks/useChatStream';
import { titleCase } from '@/lib/format';

import { ProvenanceList } from './Provenance';
import { TraceList } from './TraceList';

export function AgentTrace({ turn }: { turn: ChatTurn }) {
  const streaming = turn.status === 'streaming';
  return (
    <div className="space-y-3">
      {/* Reasoning: live + expanded while the agent works; a collapsed tap-to-expand
          disclosure (collapsed by default) once the turn is done. */}
      {streaming ? (
        <TraceList trace={turn.trace} streaming />
      ) : (
        turn.trace.length > 0 && (
          <Collapsible title="Agent reasoning">
            <TraceList trace={turn.trace} header={false} />
          </Collapsible>
        )
      )}

      {turn.final && (
        <div className="space-y-3">
          {/* The clean, cited answer is the primary content. Inline citation chips unchanged. */}
          <MarkdownView>{turn.final.answer}</MarkdownView>
          {turn.final.specialists_used?.length > 0 && (
            <p className="text-xs text-ink-muted">
              Specialists: {turn.final.specialists_used.map(titleCase).join(', ')}
            </p>
          )}
          {/* Sources collapsed into a tap-to-expand disclosure (collapsed by default). */}
          {turn.final.provenance?.length > 0 && (
            <Collapsible title="Sources" count={turn.final.provenance.length}>
              <ProvenanceList sources={turn.final.provenance} bare />
            </Collapsible>
          )}
        </div>
      )}

      {turn.error && !turn.final && <p className="text-sm text-critical-fg">{turn.error}</p>}
    </div>
  );
}
