import { type ReactNode, useState } from 'react';

import { ChevronRight } from 'lucide-react';

import { cn } from '@/lib/cn';

interface CollapsibleProps {
  title: string;
  count?: number;
  defaultOpen?: boolean;
  children: ReactNode;
}

// A simple disclosure: a header row that toggles its content. Collapsed by default so the
// clean synthesized report leads; supporting detail expands on demand.
export function Collapsible({ title, count, defaultOpen = false, children }: CollapsibleProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-lg border border-hairline bg-surface">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm font-semibold text-ink-heading"
      >
        <ChevronRight
          className={cn('h-4 w-4 shrink-0 text-ink-muted transition-transform', open && 'rotate-90')}
        />
        <span>{title}</span>
        {typeof count === 'number' && <span className="text-xs font-normal text-ink-muted">({count})</span>}
      </button>
      {open && <div className="border-t border-hairline p-4">{children}</div>}
    </div>
  );
}
