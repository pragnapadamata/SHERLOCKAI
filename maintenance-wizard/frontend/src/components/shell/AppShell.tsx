import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';

import { useAuth } from '@/auth/AuthContext';
import { IntroSplash } from '@/components/brand/IntroSplash';
import { initMuted } from '@/lib/sound';

import { MuteToggle } from './MuteToggle';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export function AppShell() {
  const { splashPending, consumeSplash } = useAuth();

  useEffect(() => {
    initMuted();
  }, []);

  return (
    <div className="flex h-screen flex-col">
      {splashPending && <IntroSplash onDone={consumeSplash} />}
      <Topbar
        right={
          <div className="flex items-center gap-1">
            <MuteToggle />
          </div>
        }
      />
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main className="scrollbar-thin flex-1 overflow-y-auto bg-canvas">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
