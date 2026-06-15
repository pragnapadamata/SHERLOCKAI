import { type ReactNode } from 'react';

import { cn } from '@/lib/cn';

import { Card } from './Card';

interface StatProps {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  icon?: ReactNode;
  accent?: string;
  className?: string;
}

export function Stat({ label, value, hint, icon, accent, className }: StatProps) {
  return (
    <Card className={cn('p-4', className)}>
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-medium uppercase tracking-wide text-ink-muted">{label}</p>
        {icon && <span className="text-ink-subtle">{icon}</span>}
      </div>
      <p className={cn('mt-2 text-4xl font-bold leading-none tabular-nums text-ink-heading', accent)}>
        {value}
      </p>
      {hint && <p className="mt-2 text-xs text-ink-muted">{hint}</p>}
    </Card>
  );
}
