import { useCallback, useRef, useState } from 'react';

import { streamPost } from '@/lib/sse';
import type { ChatEvent, ChatFinal } from '@/lib/types';

import { applyTraceEvent, type TraceNode } from './trace';

export interface ChatTurn {
  id: number;
  query: string;
  trace: TraceNode[];
  final?: ChatFinal;
  error?: string;
  status: 'streaming' | 'done' | 'error';
}

let turnCounter = 0;

export function useChatStream(sessionId: string) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const stackRef = useRef<number[]>([]);

  const send = useCallback(
    (query: string) => {
      if (streaming || !query.trim()) return;
      const turnId = ++turnCounter;
      stackRef.current = [];
      setTurns((prev) => [...prev, { id: turnId, query, trace: [], status: 'streaming' }]);
      setStreaming(true);

      const ac = new AbortController();
      abortRef.current = ac;
      const update = (fn: (t: ChatTurn) => ChatTurn) =>
        setTurns((prev) => prev.map((t) => (t.id === turnId ? fn(t) : t)));

      streamPost(
        '/api/chat',
        { query, session_id: sessionId },
        {
          onEvent: (raw) => {
            const ev = raw as ChatEvent;
            if (ev.type === 'final') {
              update((t) => ({ ...t, final: ev, status: 'done' }));
            } else if (ev.type === 'error') {
              update((t) => ({ ...t, error: ev.message, status: 'error' }));
            } else {
              update((t) => ({ ...t, trace: applyTraceEvent(t.trace, stackRef.current, ev) }));
            }
          },
          onClose: () => {
            setStreaming(false);
            abortRef.current = null;
          },
          onError: () => {
            update((t) => ({
              ...t,
              status: t.final ? 'done' : 'error',
              error: t.final ? undefined : 'The stream was interrupted.',
            }));
            setStreaming(false);
          },
        },
        ac.signal,
      );
    },
    [sessionId, streaming],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setStreaming(false);
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setTurns([]);
    setStreaming(false);
  }, []);

  return { turns, streaming, send, stop, reset };
}
