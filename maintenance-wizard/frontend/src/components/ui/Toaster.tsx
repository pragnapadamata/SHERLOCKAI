import { createContext, type ReactNode, useCallback, useContext, useState } from 'react';

import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';

import { cn } from '@/lib/cn';

type ToastKind = 'success' | 'error' | 'info';

interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

interface ToastApi {
  toast: (message: string, kind?: ToastKind) => void;
}

const ToastContext = createContext<ToastApi | null>(null);
let counter = 0;

export function ToasterProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const remove = useCallback((id: number) => {
    setToasts((current) => current.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, kind: ToastKind = 'info') => {
      const id = ++counter;
      setToasts((current) => [...current, { id, kind, message }]);
      setTimeout(() => remove(id), 4500);
    },
    [remove],
  );

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[60] flex w-80 flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              'flex items-start gap-2 rounded-md border bg-surface px-3 py-2.5 text-sm shadow-pop',
              t.kind === 'error'
                ? 'border-critical-ring'
                : t.kind === 'success'
                  ? 'border-healthy-ring'
                  : 'border-line',
            )}
          >
            {t.kind === 'error' ? (
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-critical" />
            ) : t.kind === 'success' ? (
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-healthy" />
            ) : (
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" />
            )}
            <p className="flex-1 text-ink">{t.message}</p>
            <button onClick={() => remove(t.id)} className="text-ink-subtle hover:text-ink">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToasterProvider');
  return ctx;
}
