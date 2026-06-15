import { type ReactNode } from 'react';

import { AlertTriangle } from 'lucide-react';

import { cn } from '@/lib/cn';

import { Button } from './Button';

interface ErrorStateProps {
  title?: string;
  message?: ReactNode;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn('flex flex-col items-center justify-center gap-2 px-6 py-10 text-center', className)}
    >
      <AlertTriangle className="h-6 w-6 text-high" />
      <p className="text-sm font-medium text-ink">{title}</p>
      {message && <p className="max-w-md text-sm text-ink-muted">{message}</p>}
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} className="mt-1">
          Retry
        </Button>
      )}
    </div>
  );
}
