import { type ReactNode } from 'react';
import { Link } from 'react-router-dom';

import { LogoLockup } from '@/components/brand/LogoLockup';

import { Clock } from './Clock';
import { UserMenu } from './UserMenu';

export function Topbar({ right }: { right?: ReactNode }) {
  return (
    <header className="flex h-14 shrink-0 items-center gap-4 bg-brand-500 px-4 text-white">
      <Link to="/assistant" className="flex items-center gap-3">
        <LogoLockup tone="onBlue" variant="compact" />
        <span className="hidden h-7 w-px bg-white/30 sm:block" />
        <span className="hidden text-sm font-semibold tracking-tight sm:block">Maintenance Wizard</span>
      </Link>
      <div className="flex-1" />
      <Clock />
      {right}
      <UserMenu />
    </header>
  );
}
