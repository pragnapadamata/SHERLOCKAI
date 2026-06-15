import { cn } from '@/lib/cn';
import { statusStyle } from '@/lib/severity';

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const s = statusStyle(status);
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium',
        s.badge,
        className,
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', s.dot)} />
      {s.label}
    </span>
  );
}
