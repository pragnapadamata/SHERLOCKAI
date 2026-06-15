// Fire-once alert tone. Browsers block autoplay until a user gesture, so we
// "prime" the element on the first click (login / proactive trigger); after that it
// can be played programmatically when a new alert arrives.
let audio: HTMLAudioElement | null = null;
let muted = false;

function el(): HTMLAudioElement {
  if (!audio) {
    audio = new Audio('/alert.wav');
    audio.preload = 'auto';
  }
  return audio;
}

export function primeAudio(): void {
  const a = el();
  a.muted = true;
  a.play()
    .then(() => {
      a.pause();
      a.currentTime = 0;
      a.muted = false;
    })
    .catch(() => {
      a.muted = false;
    });
}

export function playAlert(): void {
  if (muted) return;
  const a = el();
  a.currentTime = 0;
  a.play().catch(() => {
    // ignored: not yet unlocked, or blocked
  });
}

export function setMuted(value: boolean): void {
  muted = value;
  localStorage.setItem('mw.muted', value ? '1' : '0');
}

export function isMuted(): boolean {
  return muted;
}

export function initMuted(): void {
  muted = localStorage.getItem('mw.muted') === '1';
}
