import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { ChevronRight } from 'lucide-react';

import { useAuth } from '@/auth/AuthContext';
import { LogoLockup } from '@/components/brand/LogoLockup';
import { Spinner } from '@/components/ui';
import { useUsers } from '@/hooks/queries';
import { api } from '@/lib/api';
import { cn } from '@/lib/cn';
import { primeAudio } from '@/lib/sound';
import type { User } from '@/lib/types';

// Warm, muted, professional role tint -- a left-edge accent bar + a matching role tag,
// in the beige, taupe, brown, and gray family, keeping each role distinct.
// Full literal class strings so Tailwind's content scanner keeps them.
const ROLE_ACCENT: Record<string, { bar: string; tag: string }> = {
  analyst: { bar: 'bg-[#8C8174]', tag: 'bg-[#ECE8E1] text-[#5E564B] border-[#8C8174]' },
  engineer: { bar: 'bg-[#5A4632]', tag: 'bg-[#EBE3D8] text-[#4A3826] border-[#5A4632]' },
  plant_manager: { bar: 'bg-[#A8742F]', tag: 'bg-[#F1E7D3] text-[#7E4F14] border-[#A8742F]' },
  supervisor: { bar: 'bg-[#A99685]', tag: 'bg-[#ECE4DC] text-[#6B5343] border-[#A99685]' },
};
const NEUTRAL_ACCENT = { bar: 'bg-slate-300', tag: 'bg-slate-100 text-slate-600 border-slate-200' };

function MicrosoftMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 21 21" className={className} aria-hidden role="img">
      <rect x="1" y="1" width="9" height="9" fill="#F25022" />
      <rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
      <rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
      <rect x="11" y="11" width="9" height="9" fill="#FFB900" />
    </svg>
  );
}

export default function LoginPage() {
  const [params] = useSearchParams();
  const uid = params.get('uid');
  const autherror = params.get('autherror');
  const { login } = useAuth();
  const navigate = useNavigate();
  const { data: users, isLoading, error } = useUsers();

  // A completed Microsoft sign-in (or the unconfigured fallback) is handed back as
  // ?uid=...; resolve that user and log in through the same path as a persona pick.
  useEffect(() => {
    if (!uid) return;
    let cancelled = false;
    primeAudio();
    api
      .me(uid)
      .then((user) => {
        if (!cancelled) {
          login(user);
          navigate('/assistant', { replace: true });
        }
      })
      .catch(() => {
        if (!cancelled) navigate('/login?autherror=1', { replace: true });
      });
    return () => {
      cancelled = true;
    };
  }, [uid, login, navigate]);

  function choosePersona(user: User) {
    primeAudio();
    login(user);
    navigate('/assistant', { replace: true });
  }

  if (uid) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas">
        <div className="flex items-center gap-2 text-sm text-ink-muted">
          <Spinner /> Completing sign-in…
        </div>
      </div>
    );
  }

  const accounts = (users ?? []).filter((u) => u.role !== 'system');

  return (
    <div className="flex min-h-screen">
      {/* Left: brand hero -- brand-blue vertical gradient for depth */}
      <div className="hidden w-1/2 flex-col bg-gradient-to-b from-brand-500 to-brand-700 p-12 text-white lg:flex">
        {/* Logo + headline + tagline grouped as one vertically-centred block. */}
        <div className="flex flex-1 flex-col justify-center">
          <LogoLockup tone="onBlue" variant="stacked" />
          <h1 className="mt-8 text-[2.5rem] font-bold leading-[1.1] tracking-tight">
            Maintenance Wizard
          </h1>
          <p className="mt-3 max-w-md text-white/85">
            Agentic maintenance decision support for the Hot Strip Mill. Every recommendation
            traces back to its source.
          </p>
        </div>
        <p className="text-sm text-white/70">Hot Strip Mill · AMDC</p>
      </div>

      {/* Right: sign in */}
      <div className="flex w-full items-center justify-center bg-canvas p-6 lg:w-1/2">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <LogoLockup tone="onWhite" variant="stacked" />
          </div>

          <h2 className="text-xl font-semibold text-ink-heading">Sign in</h2>
          <p className="mt-1 text-sm text-ink-muted">
            Select an identity to continue, or sign in with your Microsoft account.
          </p>

          {autherror && (
            <p className="mt-4 rounded-md border border-critical-ring bg-critical-soft px-3 py-2 text-sm text-critical-fg">
              Microsoft sign-in did not complete. Try again, or select an identity below.
            </p>
          )}

          <p className="mt-6 text-xs font-semibold uppercase tracking-wider text-ink-subtle">
            Select identity
          </p>
          <div className="mt-2 space-y-2">
            {isLoading && (
              <div className="flex items-center gap-2 py-4 text-sm text-ink-muted">
                <Spinner /> Loading identities…
              </div>
            )}
            {error && (
              <p className="py-2 text-sm text-critical-fg">
                Could not load identities. Make sure the backend is running, then reload.
              </p>
            )}
            {accounts.map((u) => {
              const accent = ROLE_ACCENT[u.role] ?? NEUTRAL_ACCENT;
              return (
                <button
                  key={u.user_id}
                  onClick={() => choosePersona(u)}
                  className="group flex w-full cursor-pointer items-stretch overflow-hidden rounded-md border border-hairline bg-surface text-left transition-colors hover:border-brand-300 hover:bg-brand-50"
                >
                  <span className={cn('w-1 shrink-0', accent.bar)} aria-hidden />
                  <span className="flex flex-1 items-center gap-3 px-4 py-3">
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-semibold text-ink">{u.name}</span>
                      <span className="block truncate font-mono text-xs text-ink-muted">{u.user_id}</span>
                    </span>
                    <span
                      className={cn(
                        'shrink-0 rounded border px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wider',
                        accent.tag,
                      )}
                    >
                      {u.role.replace('_', ' ')}
                    </span>
                    <ChevronRight className="h-4 w-4 shrink-0 text-ink-subtle transition-colors group-hover:text-brand-500" />
                  </span>
                </button>
              );
            })}
          </div>

          <div className="my-6 flex items-center gap-3">
            <span className="h-px flex-1 bg-hairline" />
            <span className="text-xs font-medium text-ink-subtle">OR</span>
            <span className="h-px flex-1 bg-hairline" />
          </div>

          <a
            href="/api/auth/login"
            className="flex w-full items-center justify-center gap-2 rounded-md border border-line bg-surface px-4 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-canvas"
          >
            <MicrosoftMark className="h-4 w-4" />
            Sign in with Microsoft
          </a>
          <p className="mt-3 text-center text-xs text-ink-muted">
            Real Microsoft Entra ID single sign-on.
          </p>
        </div>
      </div>
    </div>
  );
}
