// Shared model for the live agent trace, used by both the chat stream and the
// alert-center self-diagnosis stream (same SSE event shape from the backend).
export interface TraceNode {
  id: number;
  kind: 'status' | 'tool';
  label: string;
  depth: number;
  running: boolean;
  ok?: boolean;
  summary?: string;
}

interface RawTraceEvent {
  type: string;
  message?: string;
  tool?: string;
  ok?: boolean;
  summary?: string;
}

let nodeId = 0;

// Folds one streamed event into the trace. `stack` (mutated) tracks open tool calls so
// nested specialist -> tool events render at the right depth (LIFO, as the backend emits).
export function applyTraceEvent(trace: TraceNode[], stack: number[], ev: RawTraceEvent): TraceNode[] {
  if (ev.type === 'status') {
    return [...trace, { id: ++nodeId, kind: 'status', label: ev.message ?? '', depth: 0, running: false }];
  }
  if (ev.type === 'tool_start') {
    const depth = stack.length;
    const id = ++nodeId;
    stack.push(id);
    return [...trace, { id, kind: 'tool', label: ev.tool ?? '', depth, running: true }];
  }
  if (ev.type === 'tool_end') {
    const id = stack.pop();
    return trace.map((n) =>
      n.id === id ? { ...n, running: false, ok: ev.ok, summary: ev.summary } : n,
    );
  }
  return trace;
}
