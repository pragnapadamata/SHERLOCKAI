import { type ReactNode } from 'react';

import { cn } from '@/lib/cn';

export function Badge({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border border-line bg-canvas px-2 py-0.5 text-xs font-medium text-ink-secondary',
        className,
      )}
    >
      {children}
    </span>
  );
}
