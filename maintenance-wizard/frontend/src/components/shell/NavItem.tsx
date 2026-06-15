import { type LucideIcon } from 'lucide-react';
import { NavLink } from 'react-router-dom';

import { cn } from '@/lib/cn';

interface NavItemProps {
  to: string;
  icon: LucideIcon;
  label: string;
  badge?: number;
}

export function NavItem({ to, icon: Icon, label, badge }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
          isActive
            ? 'bg-brand-50 text-brand-700'
            : 'text-ink-secondary hover:bg-canvas hover:text-ink',
        )
      }
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="flex-1 truncate">{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="rounded-full bg-critical px-1.5 text-xs font-semibold text-white">{badge}</span>
      )}
    </NavLink>
  );
}
