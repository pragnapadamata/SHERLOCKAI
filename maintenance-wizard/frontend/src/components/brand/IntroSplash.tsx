import { useEffect, useState } from 'react';

import { cn } from '@/lib/cn';

import { Motto } from './Motto';

// The transition-into-the-app intro: the "TATA" and "STEEL" wordmarks form, the motto
// rises in, then it fades out. Controlled by the shell so it plays once per login (not on
// app open) and never on in-app navigation. Click or any key skips it.
export function IntroSplash({ onDone }: { onDone: () => void }) {
  const [out, setOut] = useState(false);

  useEffect(() => {
    const toOut = setTimeout(() => setOut(true), 1600);
    const toDone = setTimeout(onDone, 2100);
    const skip = () => onDone();
    window.addEventListener('keydown', skip);
    window.addEventListener('pointerdown', skip);
    return () => {
      clearTimeout(toOut);
      clearTimeout(toDone);
      window.removeEventListener('keydown', skip);
      window.removeEventListener('pointerdown', skip);
    };
  }, [onDone]);

  return (
    <div
      aria-hidden
      className={cn(
        'fixed inset-0 z-[100] flex flex-col items-center justify-center bg-white transition-opacity duration-500',
        out ? 'opacity-0' : 'opacity-100',
      )}
    >
      <div className="flex items-baseline gap-3">
        <span className="intro-tata text-6xl font-bold tracking-tight text-brand-500">TATA</span>
        <span className="intro-steel text-6xl font-light tracking-tight text-brand-500">STEEL</span>
      </div>
      <Motto className="intro-motto mt-4 text-brand-700" />
    </div>
  );
}
