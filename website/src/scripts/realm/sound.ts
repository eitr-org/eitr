// Logo thunder and Fenrir's snap are synthesized; his snarl, the theme-switch
// howl and fully charged thunder use CC0 recordings. Browsers allow sound after the
// visitor has clicked or pressed a key; until then every effect stays silent.
// Thunder and Fenrir follow the music volume; the theme-switch howl is independent.
const music = document.querySelector<HTMLAudioElement>('#norse-audio');
let context: AudioContext | undefined;

// The first interaction creates (or resumes) the audio context; whatever it
// causes, such as clicking the logo, can already be heard.
function unlock() {
  context ??= new AudioContext();
  if (context.state === 'suspended') void context.resume();
  loadSnarl(context);
}
for (const type of ['pointerdown', 'keydown'] as const) addEventListener(type, unlock, { capture: true, passive: true });

function ready() {
  return context && context.state === 'running' && !document.hidden ? context : null;
}

function noise(audio: AudioContext, seconds: number, smoothing = 0) {
  const buffer = audio.createBuffer(1, Math.ceil(audio.sampleRate * seconds), audio.sampleRate);
  const samples = buffer.getChannelData(0);
  let previous = 0;
  for (let index = 0; index < samples.length; index += 1) {
    previous = smoothing ? (previous + smoothing * (Math.random() * 2 - 1)) / (1 + smoothing) : Math.random() * 2 - 1;
    samples[index] = smoothing ? previous * 3.5 : previous;
  }
  const source = audio.createBufferSource();
  source.buffer = buffer;
  return source;
}

function envelope(audio: AudioContext, points: [number, number][]) {
  const gain = audio.createGain();
  const now = audio.currentTime;
  gain.gain.setValueAtTime(0.0001, now);
  for (const [time, value] of points) gain.gain.exponentialRampToValueAtTime(Math.max(value, 0.0001), now + time);
  return gain;
}

/** A thunder rumble: brown noise sinking through a closing low-pass filter. */
export function rumble(strength: number) {
  const audio = ready();
  if (!audio) return;
  const now = audio.currentTime;
  const seconds = 2.6 + strength * 1.4;
  const source = noise(audio, seconds, 0.02);
  const lowpass = audio.createBiquadFilter();
  lowpass.type = 'lowpass';
  lowpass.frequency.setValueAtTime(900, now);
  lowpass.frequency.exponentialRampToValueAtTime(120, now + seconds);
  const peak = (music?.volume ?? 0.2) * (0.9 + strength * 0.8);
  const gain = envelope(audio, [[0.08, peak], [0.6, peak * 0.45], [seconds, 0.0001]]);
  source.connect(lowpass).connect(gain).connect(audio.destination);
  source.start(now);
}

// Fenrir's snarl (CC0, see public/audio/CREDITS.md), decoded once the visitor
// has interacted, so it is ready when Ragnarök is summoned.
let snarl: AudioBuffer | undefined;
function loadSnarl(audio: AudioContext) {
  if (snarl) return;
  fetch('/audio/fenrir-snarl.mp3')
    .then((response) => response.arrayBuffer())
    .then((data) => audio.decodeAudioData(data))
    .then((buffer) => { snarl = buffer; })
    .catch(() => {});
}

/**
 * Fenrir growls as he appears; 2.05 s in, the clip turns into an attack snarl
 * that peaks as his jaws close (Ragnarök's bite comes 2.25 s after he appears).
 */
export function fenrirSnarl() {
  const audio = ready();
  if (!audio || !snarl) return;
  const source = audio.createBufferSource();
  source.buffer = snarl;
  const gain = audio.createGain();
  gain.gain.value = (music?.volume ?? 0.2) * 3;
  source.connect(gain).connect(audio.destination);
  source.start();
}

/** The snap of Fenrir's jaws: a bright crack of teeth over a low thud. */
export function fenrirSnap() {
  const audio = ready();
  if (!audio) return;
  const now = audio.currentTime;
  const volume = music?.volume ?? 0.2;
  const crack = noise(audio, 0.09);
  const teeth = audio.createBiquadFilter();
  teeth.type = 'highpass';
  teeth.frequency.value = 1800;
  const crackGain = audio.createGain();
  crackGain.gain.setValueAtTime(0.0001, now);
  crackGain.gain.exponentialRampToValueAtTime(volume * 2.2, now + 0.004);
  crackGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.09);
  crack.connect(teeth).connect(crackGain).connect(audio.destination);
  crack.start(now);
  const jaw = audio.createOscillator();
  jaw.frequency.setValueAtTime(140, now);
  jaw.frequency.exponentialRampToValueAtTime(45, now + 0.18);
  const jawGain = audio.createGain();
  jawGain.gain.setValueAtTime(0.0001, now);
  jawGain.gain.exponentialRampToValueAtTime(volume * 2.6, now + 0.008);
  jawGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.22);
  jaw.connect(jawGain).connect(audio.destination);
  jaw.start(now);
  jaw.stop(now + 0.25);
}

// CC0 designed solo howl by NaturesTemper; see audio/CREDITS.md.
let howlBuffer: Promise<AudioBuffer> | undefined;
export async function wolfHowl(signal: AbortSignal) {
  const audio = ready();
  if (!audio || signal.aborted) return;
  try {
    howlBuffer ??= fetch('/audio/wolf-howl.mp3').then(response => {
      if (!response.ok) throw new Error('Wolf recording unavailable');
      return response.arrayBuffer();
    }).then(data => audio.decodeAudioData(data));
    const buffer = await howlBuffer;
    if (signal.aborted || document.hidden) return;
    const source = audio.createBufferSource();
    source.buffer = buffer;
    const gain = envelope(audio, [[.22, .24], [2.8, .2], [4, .0001]]);
    source.connect(gain).connect(audio.destination);
    const stop = () => source.stop();
    signal.addEventListener('abort', stop, { once: true });
    source.onended = () => {
      signal.removeEventListener('abort', stop);
      source.disconnect();gain.disconnect();
    };
    source.start(audio.currentTime, .5, 4);
  } catch { howlBuffer = undefined; }
}

// Close lightning strike recorded by TRP (CC0); see audio/CREDITS.md.
let thunderBuffer: Promise<AudioBuffer> | undefined;
export async function closeThunder(strength: number) {
  const audio = ready();
  if (!audio) return;
  try {
    thunderBuffer ??= fetch('/audio/close-thunder.mp3').then(response => {
      if (!response.ok) throw new Error('Thunder recording unavailable');
      return response.arrayBuffer();
    }).then(data => audio.decodeAudioData(data));
    const buffer = await thunderBuffer;
    if (!ready()) return;
    const seconds = 5 + Math.max(0, Math.min(1, strength)) * 3;
    const source = audio.createBufferSource();
    source.buffer = buffer;
    const peak = (music?.volume ?? 0.2) * (0.8 + strength * 0.6);
    const gain = envelope(audio, [[.01, peak], [seconds - 1, peak * .8], [seconds, .0001]]);
    source.connect(gain).connect(audio.destination);
    const stop = () => { if (document.hidden) source.stop(); };
    document.addEventListener('visibilitychange', stop);
    source.onended = () => {
      document.removeEventListener('visibilitychange', stop);
      source.disconnect();gain.disconnect();
    };
    source.start(audio.currentTime, .7, seconds);
  } catch { thunderBuffer = undefined; }
}
