import { cn } from '@/lib/cn';

import { Motto } from './Motto';

interface LogoLockupProps {
  tone?: 'onBlue' | 'onWhite';
  variant?: 'stacked' | 'compact';
  className?: string;
}

// The Tata Steel logo with the "We Also Make Tomorrow" tagline lockup. White knockout on
// blue surfaces (topbar, login hero), full colour on white. The tagline is crisp text.
export function LogoLockup({ tone = 'onBlue', variant = 'stacked', className }: LogoLockupProps) {
  const src = tone === 'onBlue' ? '/tata-steel-logo-white.svg' : '/tata-steel-logo.svg';
  const logoH = variant === 'compact' ? 'h-6' : 'h-10';
  const mottoSize = variant === 'compact' ? 'text-[9px]' : 'text-xs';
  const mottoColor = tone === 'onBlue' ? 'text-white/85' : 'text-brand-700';

  return (
    <span
      className={cn(
        'inline-flex flex-col',
        variant === 'compact' ? 'gap-0.5' : 'gap-2',
        className,
      )}
    >
      <img src={src} alt="Tata Steel" className={cn(logoH, 'w-auto self-start')} />
      <Motto className={cn(mottoSize, 'leading-none', mottoColor)} />
    </span>
  );
}
