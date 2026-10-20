// Mímir's well: hovering a theme card ripples it like water, and the whole site
// briefly takes on that theme's colors. Leaving the gallery restores EITR's own.
import { finePointer, reducedMotion } from './motion';

const root = document.documentElement;
const grid = document.querySelector<HTMLElement>('.theme-grid');
const roles = ['accent', 'aurora', 'violet', 'bronze'] as const;
let restore = 0;
let worn:HTMLElement | undefined;

export const PALETTE = 'eitr:palette';
const announce = () => document.dispatchEvent(new CustomEvent(PALETTE));

function recolor(card: HTMLElement) {
  for (const role of roles) {
    const color = card.dataset[role];
    if (color) root.style.setProperty(`--${role}`, root.dataset.appearance === 'light'
      ? `color-mix(in srgb, ${color} 30%, #292521)` : color);
  }
  announce();
}
function wear(card: HTMLElement) {
  clearTimeout(restore);
  worn=card;
  root.dataset.wellTheme = card.dataset.theme ?? '';
  recolor(card);
}
document.addEventListener('eitr:appearance',()=>{if(worn) recolor(worn);});

function ripple(card: HTMLElement, event: PointerEvent) {
  if (reducedMotion.matches) return;
  const bounds = card.getBoundingClientRect();
  const ring = document.createElement('span');
  ring.className = 'well-ring';
  ring.setAttribute('aria-hidden', 'true');
  ring.style.left = `${event.clientX - bounds.left}px`;
  ring.style.top = `${event.clientY - bounds.top}px`;
  card.append(ring);
  ring.addEventListener('animationend', () => ring.remove());
}

grid?.querySelectorAll<HTMLElement>('.theme-card').forEach((card) => {
  card.addEventListener('pointerenter', (event) => {
    if (!finePointer.matches) return;
    wear(card);
    ripple(card, event);
  });
});
grid?.addEventListener('pointerleave', () => {
  restore = window.setTimeout(() => {
    for (const role of roles) root.style.removeProperty(`--${role}`);
    worn=undefined;
    delete root.dataset.wellTheme;
    announce();
  }, 350);
});
