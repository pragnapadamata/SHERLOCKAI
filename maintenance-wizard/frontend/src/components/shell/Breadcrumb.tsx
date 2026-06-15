import { ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export interface Crumb {
  label: string;
  to?: string;
}

export function Breadcrumb({ items }: { items: Crumb[] }) {
  return (
    <nav className="flex items-center gap-1.5 text-xs text-ink-muted">
      {items.map((c, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <ChevronRight className="h-3 w-3 text-ink-subtle" />}
          {c.to ? (
            <Link to={c.to} className="transition-colors hover:text-brand-600">
              {c.label}
            </Link>
          ) : (
            <span className="text-ink-secondary">{c.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
