// Typing "ragnarok" summons Fenrir's jaws, then the world takes shape again.
// Click/Escape dismiss; reduced motion shows only the quiet rebirth.
import { message } from '../messages';
import { reducedMotion } from './motion';
import { fenrirSnap, fenrirSnarl } from './sound';

const WORD = 'ragnarok';
const FACE = '/art/fenrir-bite.webp';
const root = document.documentElement;
let typed = '';

function scene() {
  const overlay = document.createElement('div');
  overlay.className = 'ragnarok';
  overlay.setAttribute('aria-hidden', 'true');
  overlay.innerHTML = `
    <div class="ragnarok-fenrir"><div class="fenrir-face"></div></div>
    <div class="fenrir-jaws"><div class="fenrir-jaw fenrir-jaw-upper"></div><div class="fenrir-jaw fenrir-jaw-lower"></div></div>
    <div class="fenrir-darkness"></div>
    <div class="ragnarok-rebirth"><span class="wordmark"></span><p></p></div>`;
  overlay.querySelector('p')!.textContent = message('motto');
  document.body.append(overlay);
  return overlay;
}

function announce(text: string) {
  const status = document.createElement('p');
  status.className = 'visually-hidden';
  status.setAttribute('role', 'status');
  document.body.append(status);
  requestAnimationFrame(() => { status.textContent = text; });
  setTimeout(() => status.remove(), 8000);
}

function ragnarok() {
  if (root.dataset.ragnarok || document.hidden) return;
  const quiet = reducedMotion.matches;
  root.dataset.ragnarok = quiet ? 'quiet' : 'summoning';
  const overlay = scene();
  announce(message('ragnarok'));
  const timers: number[] = [];
  let finished = false;
  const at = (seconds: number, action: () => void) => timers.push(window.setTimeout(action, seconds * 1000));
  const finish = (immediate = false) => {
    if (finished) return;
    finished = true;
    timers.forEach(clearTimeout);
    removeEventListener('keydown', skip);
    document.removeEventListener('visibilitychange', visibility);
    reducedMotion.removeEventListener('change', motion);
    overlay.removeEventListener('click', click);
    const remove = () => { overlay.remove(); delete root.dataset.ragnarok; };
    if (immediate || reducedMotion.matches) remove();
    else { overlay.classList.add('ending'); window.setTimeout(remove, 600); }
  };
  const skip = (event: KeyboardEvent) => { if (event.key === 'Escape') finish(); };
  const click = () => finish();
  const visibility = () => { if (document.hidden) finish(true); };
  const motion = () => finish(true);
  addEventListener('keydown', skip);
  overlay.addEventListener('click', click);
  document.addEventListener('visibilitychange', visibility);
  reducedMotion.addEventListener('change', motion);
  const rebirth = () => { overlay.classList.add('rebirth'); root.dataset.ragnarok = 'reborn'; };
  if (quiet) {
    rebirth();
    at(4, () => finish());
    return;
  }

  // Start the choreography only after both jaw frames are ready. A failed
  // image keeps the quiet ending instead of leaving an invisible attack.
  const image = new Image();
  image.src = FACE;
  let started = false;
  const begin = (hasFace: boolean) => {
    if (finished || started) return;
    started = true;
    if (!hasFace) { rebirth(); at(4, () => finish()); return; }
    overlay.classList.add('fenrir');
    fenrirSnarl();
    at(0.65, () => overlay.classList.add('roaring'));
    at(1.05, () => overlay.classList.remove('roaring'));
    at(1.35, () => overlay.classList.add('roaring'));
    at(1.75, () => overlay.classList.add('lunging'));
    at(2.25, () => {
      overlay.classList.add('biting');
      fenrirSnap();
      root.dataset.ragnarok = 'biting';
    });
    at(2.7, () => { overlay.classList.add('swallowed'); root.dataset.ragnarok = 'swallowed'; });
    at(3.8, rebirth);
    at(7.2, () => finish());
  };
  image.decode().then(() => begin(true), () => begin(false));
  at(4, () => begin(false));
}

addEventListener('keydown', (event) => {
  const target = event.target;
  if (event.ctrlKey || event.metaKey || event.altKey || event.isComposing || !(target instanceof Element)
      || target.closest('input, textarea, select, [contenteditable], [role="textbox"]')) return;
  if (event.key.length !== 1) return;
  typed = (typed + event.key.toLowerCase()).slice(-WORD.length);
  if (typed === WORD) { typed = ''; ragnarok(); }
});
