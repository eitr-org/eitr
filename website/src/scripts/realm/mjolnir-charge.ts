// Hold the mouse button on empty space to charge Mjölnir: sparks gather around
// the cursor. Release to strike: lightning falls on that spot and the ground
// cracks for a moment. Links, controls and text selection keep working, since
// moving before the charge starts, or pressing on anything interactive or on the
// scrollbar, does nothing. Mjölnir's landings (MjolnirScene, wield-mjolnir) use
// the same ground strike.
import { announceStrike, boltPath, finePointer, motionAllowed, type StrikeDetail } from './motion';

const INTERACTIVE = 'a, button, input, textarea, select, summary, label, pre, code, dialog, [role="button"], [contenteditable], .theme-card';
const CHARGE_DELAY = 350;
const FULL_CHARGE = 1100;

const canvas = document.createElement('canvas');
canvas.className = 'mjolnir-charge';
canvas.setAttribute('aria-hidden', 'true');
document.body.append(canvas);
const context = canvas.getContext('2d')!;

// Bolts and cracks keep page coordinates, so they stay where the lightning hit while the page scrolls.
type Crack = { points: [number, number][]; born: number };
let press: { x: number; y: number; start: number } | null = null;
let charging = false;
let cracks: Crack[] = [];
let bolt: { points: [number, number][][]; born: number; strength: number } | null = null;
// Mjölnir's strikes keep the Eitr emblem in front of their cracks: its outer
// edge (the logo's first contour, so the E's counter too) is cut out of them.
let cover: HTMLElement | null = null;
let emblem: { outline: Path2D; size: number } | null = null;
fetch('/branding/eitr-logo.svg').then((response) => response.text()).then((markup) => {
  const logo = new DOMParser().parseFromString(markup, 'image/svg+xml');
  const outline = logo.querySelector('path')?.getAttribute('d')?.match(/M[^M]+/)?.[0];
  const size = Number(logo.documentElement.getAttribute('viewBox')?.split(/\s+/)[2]);
  if (outline && size) emblem = { outline: new Path2D(outline), size };
}).catch(() => {});
let frame = 0;

function resize() {
  const ratio = Math.min(devicePixelRatio || 1, 2);
  canvas.width = innerWidth * ratio;
  canvas.height = innerHeight * ratio;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
}
resize();
addEventListener('resize', resize);

const chargeLevel = (now: number) => (press && charging ? Math.min(1, (now - press.start - CHARGE_DELAY) / FULL_CHARGE) : 0);

function drawSparks(now: number) {
  if (!press || !charging) return;
  const level = chargeLevel(now);
  const glow = context.createRadialGradient(press.x, press.y, 0, press.x, press.y, 26 + level * 30);
  glow.addColorStop(0, `rgba(220, 236, 255, ${0.35 + level * 0.4})`);
  glow.addColorStop(1, 'rgba(120, 170, 255, 0)');
  context.fillStyle = glow;
  context.beginPath();
  context.arc(press.x, press.y, 26 + level * 30, 0, Math.PI * 2);
  context.fill();
  const count = 6 + Math.round(level * 10);
  for (let index = 0; index < count; index += 1) {
    const angle = now / (260 - level * 120) + (index * Math.PI * 2) / count;
    const radius = 34 - level * 18 + Math.sin(now / 90 + index) * 4;
    const x = press.x + Math.cos(angle) * radius;
    const y = press.y + Math.sin(angle) * radius;
    context.strokeStyle = `rgba(235, 245, 255, ${0.5 + level * 0.5})`;
    context.lineWidth = 1.2 + level;
    context.beginPath();
    context.moveTo(x, y);
    context.lineTo(x + (Math.random() - 0.5) * 9, y + (Math.random() - 0.5) * 9);
    context.stroke();
  }
}

function trace(points: [number, number][]) {
  context.beginPath();
  points.forEach(([x, y], index) => (index ? context.lineTo(x - scrollX, y - scrollY) : context.moveTo(x - scrollX, y - scrollY)));
}

function strokeBolt(points: [number, number][], width: number, alpha: number) {
  trace(points);
  context.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
  context.lineWidth = width;
  context.shadowColor = 'rgba(170, 205, 255, 0.95)';
  context.shadowBlur = 18;
  context.stroke();
  context.shadowBlur = 0;
}

function drawCracks(now: number) {
  cracks = cracks.filter((crack) => now - crack.born < 1600);
  for (const crack of cracks) {
    const fade = 1 - (now - crack.born) / 1600;
    trace(crack.points);
    context.strokeStyle = `rgba(255, 196, 120, ${fade * 0.9})`;
    context.lineWidth = 1.6;
    context.shadowColor = 'rgba(255, 140, 60, 0.9)';
    context.shadowBlur = 10;
    context.stroke();
    context.shadowBlur = 0;
  }
  if (cover && cracks.length && emblem) {
    const bounds = cover.getBoundingClientRect();
    // The emblem is masked with "contain", so it is a centered square.
    const side = Math.min(bounds.width, bounds.height);
    context.save();
    context.translate(bounds.left + (bounds.width - side) / 2, bounds.top + (bounds.height - side) / 2);
    context.scale(side / emblem.size, side / emblem.size);
    // Erasing needs an opaque fill; the flash leaves a translucent one behind.
    context.globalCompositeOperation = 'destination-out';
    context.fillStyle = '#000';
    context.fill(emblem.outline);
    context.restore();
  }
  if (!cracks.length) cover = null;
}

function draw(now: number) {
  context.clearRect(0, 0, innerWidth, innerHeight);
  drawCracks(now);
  drawSparks(now);
  if (bolt) {
    const age = now - bolt.born;
    if (age > 420) bolt = null;
    else {
      // Re-roll the bolt twice so it flickers like real lightning.
      if (age > 140 && bolt.points.length === 1) bolt.points.push(boltPath(...bolt.points[0][0], ...bolt.points[0].at(-1)!));
      const alpha = 1 - age / 420;
      for (const points of bolt.points) strokeBolt(points, 2 + bolt.strength * 2.5, alpha);
      if (age < 90) {
        context.fillStyle = `rgba(255, 255, 255, ${0.18 * bolt.strength * (1 - age / 90)})`;
        context.fillRect(0, 0, innerWidth, innerHeight);
      }
    }
  }
  if (press || bolt || cracks.length) frame = requestAnimationFrame(draw);
  else frame = 0;
}

const animate = () => { if (!frame) frame = requestAnimationFrame(draw); };

/**
 * Lightning falls on a viewport point and the ground cracks around it; thunder
 * follows. An emblem passed as `front` stays in front of the cracks.
 */
export function strikeGround(viewX: number, viewY: number, strength: number, front: HTMLElement | null = null, sound?: StrikeDetail['sound']) {
  cover = front;
  const x = viewX + scrollX;
  const y = viewY + scrollY;
  const top: [number, number] = [x + (Math.random() - 0.5) * 320, scrollY - 10];
  bolt = { points: [boltPath(top[0], top[1], x, y)], born: performance.now(), strength };
  const born = performance.now();
  const branches = 4 + Math.round(strength * 4);
  for (let index = 0; index < branches; index += 1) {
    const angle = (index / branches) * Math.PI * 2 + Math.random() * 0.6;
    const length = 40 + Math.random() * 90 * strength;
    cracks.push({ points: boltPath(x, y, x + Math.cos(angle) * length, y + Math.sin(angle) * length * 0.55, 0.35), born });
  }
  announceStrike({ x: viewX, y: viewY, strength, sound });
  animate();
}

function release(event: PointerEvent) {
  if (!press) return;
  const level = chargeLevel(performance.now());
  if (charging && level > 0.15) strikeGround(event.clientX, event.clientY, level, null, level === 1 ? 'close-thunder' : undefined);
  press = null;
  charging = false;
  document.documentElement.classList.remove('charging-mjolnir');
}

document.addEventListener('pointerdown', (event) => {
  if (event.button !== 0 || event.pointerType === 'touch' || !finePointer.matches || !motionAllowed()) return;
  if ((event.target as Element).closest(INTERACTIVE) || document.documentElement.dataset.ragnarok) return;
  // The page scrollbar sits outside the document's client area.
  const page = document.documentElement;
  if (event.clientX >= page.clientWidth || event.clientY >= page.clientHeight) return;
  press = { x: event.clientX, y: event.clientY, start: performance.now() };
  const pending = press;
  setTimeout(() => {
    if (press !== pending) return;
    charging = true;
    // While charging, a drag must not start selecting text.
    getSelection()?.removeAllRanges();
    document.documentElement.classList.add('charging-mjolnir');
    animate();
  }, CHARGE_DELAY);
});
document.addEventListener('pointermove', (event) => {
  if (!press) return;
  if (!charging && Math.hypot(event.clientX - press.x, event.clientY - press.y) > 8) { press = null; return; }
  press.x = event.clientX;
  press.y = event.clientY;
});
document.addEventListener('pointerup', release);
document.addEventListener('pointercancel', () => { press = null; charging = false; document.documentElement.classList.remove('charging-mjolnir'); });
addEventListener('blur', () => { press = null; charging = false; document.documentElement.classList.remove('charging-mjolnir'); });
