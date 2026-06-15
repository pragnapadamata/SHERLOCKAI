import {
  MessageSquareText,
} from 'lucide-react';

import { NavItem } from './NavItem';

const GROUPS = [
  {
    label: 'Intelligence',
    items: [
      { to: '/assistant', icon: MessageSquareText, label: 'Assistant' },
    ],
  },
];

export function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-hairline bg-surface md:flex">
      <nav className="scrollbar-thin flex-1 space-y-6 overflow-y-auto px-3 py-5">
        {GROUPS.map((group) => (
          <div key={group.label}>
            <p className="px-3 pb-2 text-xs font-semibold uppercase tracking-wider text-ink-subtle">
              {group.label}
            </p>
            <div className="space-y-1">
              {group.items.map((item) => (
                <NavItem
                  key={item.to}
                  {...item}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>
      <div className="border-t border-hairline px-4 py-3 text-xs text-ink-subtle">
        Hot Strip Mill · Finishing · AMDC
      </div>
    </aside>
  );
}
