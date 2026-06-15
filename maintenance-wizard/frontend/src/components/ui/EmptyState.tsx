import { type ReactNode } from 'react';

import { cn } from '@/lib/cn';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn('flex flex-col items-center justify-center gap-2 px-6 py-12 text-center', className)}
    >
      {icon && <div className="text-ink-subtle">{icon}</div>}
      <p className="text-sm font-medium text-ink">{title}</p>
      {description && <p className="max-w-sm text-sm text-ink-muted">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
