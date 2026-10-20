// Shared rules for the decorative effects: nothing moves when the visitor
// prefers reduced motion, and nothing animates while the tab is hidden.
export const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
export const finePointer = matchMedia('(hover: hover) and (pointer: fine)');

export const motionAllowed = () => !reducedMotion.matches && !document.hidden;

/** Calls `listener` whenever motion becomes allowed or disallowed. */
export function onMotionChange(listener: () => void) {
  reducedMotion.addEventListener('change', listener);
  document.addEventListener('visibilitychange', listener);
}

/** Lightning anywhere on the page announces itself, so thunder can follow. */
export type StrikeDetail = { x: number; y: number; strength: number; sound?: 'close-thunder' };
export const STRIKE = 'eitr:strike';
export function announceStrike(detail: StrikeDetail) {
  document.dispatchEvent(new CustomEvent<StrikeDetail>(STRIKE, { detail }));
}

/** A jagged bolt from (x1, y1) to (x2, y2) with a few forks, as canvas segments. */
export function boltPath(x1: number, y1: number, x2: number, y2: number, roughness = 0.22) {
  const points: [number, number][] = [[x1, y1]];
  const steps = 14;
  const length = Math.hypot(x2 - x1, y2 - y1);
  for (let index = 1; index < steps; index += 1) {
    const t = index / steps;
    const sway = (Math.random() - 0.5) * length * roughness * Math.sin(Math.PI * t);
    points.push([x1 + (x2 - x1) * t + sway, y1 + (y2 - y1) * t + (Math.random() - 0.5) * 8]);
  }
  points.push([x2, y2]);
  return points;
}
