import { type FormEvent, useEffect, useRef, useState } from 'react';

import { MessageSquareText, Plus, Send } from 'lucide-react';

import { useAuth } from '@/auth/AuthContext';
import { PageHeader } from '@/components/shell/PageHeader';
import { Button, EmptyState } from '@/components/ui';
import { AgentTrace } from '@/components/domain/AgentTrace';
import { useChatStream } from '@/hooks/useChatStream';

const SUGGESTIONS = [
  'What is the status of the F2 work-roll bearing?',
  'Diagnose the F3 main drive gearbox and recommend actions.',
  'Which assets should I prioritise this week and why?',
];

export default function AssistantPage() {
  const { user } = useAuth();
  const [sessionId] = useState(() => `chat-${user?.user_id ?? 'anon'}-${Date.now()}`);
  const { turns, streaming, send, reset } = useChatStream(sessionId);
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement>(null);
  const turnRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const prevStreaming = useRef(streaming);

  // While the agent works, follow the live trace; the moment a turn completes, anchor the
  // TOP of that turn (question + collapsed "Agent reasoning" + start of the answer) at the
  // top of the chat viewport -- never scroll to the bottom (the collapsed Sources row).
  useEffect(() => {
    const last = turns[turns.length - 1];
    if (streaming && last && !last.final) {
      endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    } else if (prevStreaming.current && !streaming && last) {
      turnRefs.current.get(last.id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    prevStreaming.current = streaming;
  }, [streaming, turns]);

  function submit(e?: FormEvent) {
    e?.preventDefault();
    if (!input.trim() || streaming) return;
    send(input.trim());
    setInput('');
  }

  const initials = (user?.name ?? 'U')
    .split(' ')
    .map((p) => p[0])
    .slice(0, 2)
    .join('');

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Assistant"
        description="Ask the maintenance agent, watch it reason, then read the cited answer"
        actions={
          <Button variant="secondary" size="sm" onClick={reset} disabled={streaming}>
            <Plus className="h-4 w-4" /> New chat
          </Button>
        }
      />

      <div className="scrollbar-thin flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl space-y-6 p-6">
          {turns.length === 0 && (
            <EmptyState
              icon={<MessageSquareText className="h-8 w-8" />}
              title="Ask about any asset"
              description="The agent routes to specialists, calls tools, and answers with citations."
              action={
                <div className="flex flex-col gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => setInput(s)}
                      className="rounded-md border border-hairline bg-surface px-3 py-2 text-left text-sm text-ink-secondary transition-colors hover:border-brand-300 hover:bg-brand-50"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              }
            />
          )}

          {turns.map((t) => (
            <div
              key={t.id}
              ref={(el) => {
                if (el) turnRefs.current.set(t.id, el);
                else turnRefs.current.delete(t.id);
              }}
              className="space-y-3"
            >
              <div className="flex items-start justify-end gap-2">
                <div className="max-w-[80%] rounded-lg rounded-tr-sm bg-brand-500 px-4 py-2 text-sm text-white">
                  {t.query}
                </div>
                <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700">
                  {initials}
                </span>
              </div>
              <div className="rounded-lg border border-hairline bg-surface p-4 shadow-card">
                <AgentTrace turn={t} />
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>
      </div>

      <div className="border-t border-hairline bg-surface p-4">
        <form onSubmit={submit} className="mx-auto flex max-w-3xl items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            rows={1}
            placeholder="Ask about an asset, fault, or priority…"
            className="min-h-[40px] flex-1 resize-none rounded-md border border-line bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brand-300"
          />
          <Button type="submit" disabled={!input.trim() || streaming} loading={streaming}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
