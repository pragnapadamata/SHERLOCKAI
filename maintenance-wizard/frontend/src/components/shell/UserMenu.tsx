import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ChevronDown, LogOut, UserCog } from 'lucide-react';

import { useAuth } from '@/auth/AuthContext';
import { titleCase } from '@/lib/format';

export function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  if (!user) return null;
  const initials = user.name
    .split(' ')
    .map((p) => p[0])
    .slice(0, 2)
    .join('');

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-md px-2 py-1.5 text-white/90 transition-colors hover:bg-white/10"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/20 text-xs font-semibold">
          {initials}
        </span>
        <span className="hidden text-left sm:block">
          <span className="block text-sm font-medium leading-tight">{user.name}</span>
          <span className="block text-xs leading-tight text-white/70">{titleCase(user.role)}</span>
        </span>
        <ChevronDown className="h-4 w-4 text-white/70" />
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-60 rounded-lg border border-hairline bg-surface py-1 shadow-pop">
          <div className="border-b border-hairline px-3 py-2.5">
            <p className="text-sm font-medium text-ink">{user.name}</p>
            <p className="text-xs text-ink-muted">
              {titleCase(user.role)} · {user.area}
            </p>
            <p className="mt-0.5 font-mono text-xs text-ink-subtle">{user.user_id}</p>
          </div>
          <button
            onClick={() => {
              setOpen(false);
              navigate('/login');
            }}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-ink-secondary hover:bg-canvas"
          >
            <UserCog className="h-4 w-4" /> Switch user
          </button>
          <button
            onClick={() => {
              logout();
              navigate('/login');
            }}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-ink-secondary hover:bg-canvas"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      )}
    </div>
  );
}
