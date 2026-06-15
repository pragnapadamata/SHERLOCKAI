import { type ButtonHTMLAttributes, forwardRef } from 'react';

import { Loader2 } from 'lucide-react';

import { cn } from '@/lib/cn';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'link';
type Size = 'sm' | 'md';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-brand-500 text-white border border-transparent hover:bg-brand-600 active:bg-brand-700',
  secondary: 'bg-surface text-ink-secondary border border-line hover:bg-canvas hover:text-ink',
  ghost: 'bg-transparent text-ink-secondary border border-transparent hover:bg-canvas hover:text-ink',
  danger: 'bg-critical text-white border border-transparent hover:brightness-95 active:brightness-90',
  link: 'bg-transparent text-brand-600 hover:text-brand-700 hover:underline',
};

const SIZES: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs gap-1.5',
  md: 'h-9 px-4 text-sm gap-2',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', loading, className, children, disabled, ...props },
  ref,
) {
  const isLink = variant === 'link';
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center rounded-md font-medium transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300',
        'disabled:pointer-events-none disabled:opacity-50',
        VARIANTS[variant],
        !isLink && SIZES[size],
        className,
      )}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
});
