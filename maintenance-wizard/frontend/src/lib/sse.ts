import { fetchEventSource } from '@microsoft/fetch-event-source';

import { currentUserId } from '@/auth/session';

import { API_BASE } from './api';

interface SSEHandlers {
  onEvent: (event: unknown) => void;
  onClose?: () => void;
  onError?: (err: unknown) => void;
}

// POST + Server-Sent Events. Native EventSource cannot POST a JSON body, so we use
// fetch-event-source, attaching X-User-Id and parsing each data: frame as JSON.
export function streamPost(
  path: string,
  body: unknown,
  handlers: SSEHandlers,
  signal?: AbortSignal,
): void {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const uid = currentUserId();
  if (uid) headers['X-User-Id'] = uid;

  void fetchEventSource(`${API_BASE}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
    signal,
    openWhenHidden: true,
    async onopen(res) {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
    },
    onmessage(ev) {
      if (!ev.data) return;
      try {
        handlers.onEvent(JSON.parse(ev.data));
      } catch {
        // ignore keep-alive / non-JSON frames
      }
    },
    onclose() {
      handlers.onClose?.();
    },
    onerror(err) {
      throw err; // stop the library's auto-retry; surfaced via the rejected promise
    },
  }).catch((err) => {
    if (signal?.aborted) return;
    handlers.onError?.(err);
  });
}
