import { useNow } from '@/lib/time';

// A live, ticking date + time in the topbar -- a "this is live" credibility cue.
export function Clock() {
  const now = useNow(1000);
  const d = new Date(now);
  const date = d.toLocaleDateString(undefined, {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
  const time = d.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  return (
    <span className="hidden items-center gap-1.5 text-xs tabular-nums text-white/85 md:flex">
      <span>{date}</span>
      <span className="text-white/40">·</span>
      <span>{time}</span>
    </span>
  );
}
