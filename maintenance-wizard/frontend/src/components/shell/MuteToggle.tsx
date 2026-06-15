import { useState } from 'react';

import { Volume2, VolumeX } from 'lucide-react';

import { isMuted, setMuted } from '@/lib/sound';

export function MuteToggle() {
  const [muted, setLocal] = useState(isMuted());
  return (
    <button
      onClick={() => {
        const next = !muted;
        setMuted(next);
        setLocal(next);
      }}
      title={muted ? 'Unmute alerts' : 'Mute alerts'}
      className="rounded-md p-2 text-white/80 transition-colors hover:bg-white/10"
    >
      {muted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
    </button>
  );
}
