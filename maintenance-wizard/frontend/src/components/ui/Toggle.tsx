import { cn } from '@/lib/cn';

interface ToggleProps {
  checked: boolean;
  onChange: (value: boolean) => void;
  label?: string;
  className?: string;
}

// Track 36x20, knob 16, inset 2 on every side: OFF = flush left (translate 0),
// ON = slid right by 16 (left 2 -> 18, right edge 34, 2px inside the 36 track).
export function Toggle({ checked, onChange, label, className }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={cn('inline-flex items-center gap-2', className)}
    >
      <span
        className={cn(
          'relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors',
          checked ? 'bg-brand-500' : 'bg-line',
        )}
      >
        <span
          className={cn(
            'absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform duration-200',
            checked ? 'translate-x-4' : 'translate-x-0',
          )}
        />
      </span>
      {label && <span className="text-sm text-ink-secondary">{label}</span>}
    </button>
  );
}
