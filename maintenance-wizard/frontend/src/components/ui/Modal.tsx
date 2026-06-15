import { type ReactNode, useEffect } from 'react';
import { createPortal } from 'react-dom';

import { X } from 'lucide-react';

import { cn } from '@/lib/cn';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}

export function Modal({ open, onClose, title, children, footer, className }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-ink-heading/40" onClick={onClose} />
      <div
        className={cn(
          'relative z-10 w-full max-w-lg rounded-lg border border-hairline bg-surface shadow-pop',
          className,
        )}
      >
        {title && (
          <div className="flex items-center justify-between border-b border-hairline px-5 py-4">
            <h3 className="text-sm font-semibold text-ink-heading">{title}</h3>
            <button onClick={onClose} className="text-ink-muted transition-colors hover:text-ink">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}
        <div className="px-5 py-4">{children}</div>
        {footer && (
          <div className="flex justify-end gap-2 border-t border-hairline px-5 py-3">{footer}</div>
        )}
      </div>
    </div>,
    document.body,
  );
}
