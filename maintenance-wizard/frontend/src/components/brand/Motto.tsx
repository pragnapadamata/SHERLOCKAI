import { cn } from '@/lib/cn';

// The Tata Group signature line, rendered as crisp text (never a raster). Colour is set
// by the caller so it sits cleanly on either the blue brand surfaces or white.
export function Motto({ className }: { className?: string }) {
  return (
    <span className={cn('font-medium tracking-wide', className)}>#WeAlsoMakeTomorrow</span>
  );
}
