import { useEffect, useState } from 'react';

import { useProactiveState } from '@/hooks/queries';

/** A ticking wall clock; re-renders every `intervalMs`. */
export function useNow(intervalMs = 1000): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}

/**
 * Offset (ms) that anchors the synthetic timeline to the present: the dataset's latest
 * point (the proactive `end`) maps to the server's "now", so synthetic event/cursor/chart
 * times read as recent rather than weeks old. Returns 0 until the state has loaded, and is
 * applied uniformly wherever a synthetic time is displayed.
 */
export function useAnchorOffsetMs(): number {
  const { data } = useProactiveState();
  if (!data?.end) return 0;
  const end = Date.parse(data.end);
  const serverNow = data.server_now ? Date.parse(data.server_now) : Date.now();
  if (Number.isNaN(end) || Number.isNaN(serverNow)) return 0;
  return serverNow - end;
}

/** Shift a synthetic ISO timestamp into the anchored present (presentation only). */
export function anchored(iso: string | null | undefined, offsetMs: number): string | undefined {
  if (!iso) return undefined;
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return undefined;
  return new Date(t + offsetMs).toISOString();
}
