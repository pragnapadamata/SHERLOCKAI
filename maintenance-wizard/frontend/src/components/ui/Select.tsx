import { type SelectHTMLAttributes } from 'react';

import { ChevronDown } from 'lucide-react';

import { cn } from '@/lib/cn';

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="relative inline-block">
      <select
        className={cn(
          'h-9 appearance-none rounded-md border border-line bg-surface pl-3 pr-8 text-sm text-ink',
          'focus:outline-none focus:ring-2 focus:ring-brand-300 disabled:opacity-50',
          className,
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted" />
    </div>
  );
}
