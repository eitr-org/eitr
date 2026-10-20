// Drag the EITR logo and it becomes Mjölnir: you hold the end of the handle and
// the head always points at the spot where the logo was. Release, and the
// hammer swings into that spot with the ground strike (lightning and ember
// cracks from mjolnir-charge, plus debris) before the logo emerges again. A click without
// dragging keeps the logo's own lightning. Mouse and pen only, so touch
// scrolling over the logo keeps working; off under reduced motion.
import { strikeGround } from './mjolnir-charge';
import { reducedMotion } from './motion';

const DRAG_THRESHOLD = 8;
// The drawing is 200 × 300 units: the hand holds the handle's end at (100, 24)
// and the middle of the head is straight below, at (100, 244). Shown smaller
// than on the stage.
const SCALE = 0.62;
const WIDTH = 200 * SCALE;
const HEIGHT = 300 * SCALE;
const GRIP = 24 * SCALE;
const HEAD = 220 * SCALE;



for (const stage of document.querySelectorAll<HTMLElement>('.impact-stage')) {
  const logo = stage.querySelector<HTMLButtonElement>('.emergent-logo');
  const drawing = stage.querySelector<SVGSVGElement>('.hammer');
  if (!logo || !drawing) continue;

  let press: { id: number; x: number; y: number } | null = null;
  let hammer: SVGSVGElement | null = null;
  let anchor = { x: 0, y: 0 };
  let dragged = false;

  const aim = (x: number, y: number) => {
    // Point the handle, and the head beyond it, at the anchor.
    const angle = Math.atan2(anchor.y - y, anchor.x - x) - Math.PI / 2;
    return `translate(${x - WIDTH / 2}px, ${y - GRIP}px) rotate(${angle}rad)`;
  };

  const take = (x: number, y: number) => {
    const bounds = logo.querySelector('.impact-emblem')?.getBoundingClientRect() ?? logo.getBoundingClientRect();
    anchor = { x: bounds.left + bounds.width / 2, y: bounds.top + bounds.height / 2 };
    // The Mjölnir drawn in MjolnirScene.astro, which appears only here.
    hammer = drawing.cloneNode(true) as SVGSVGElement;
    hammer.removeAttribute('class');
    hammer.classList.add('wielded-hammer');
    hammer.setAttribute('width', String(WIDTH));
    hammer.setAttribute('height', String(HEIGHT));
    // Turn around the hand on the handle, not the drawing's corner.
    hammer.style.transformOrigin = `${WIDTH / 2}px ${GRIP}px`;
    hammer.style.transform = aim(x, y);
    document.body.append(hammer);
    // While it is held, the impact's animations are off, so the strike restarts them.
    stage.classList.remove('restrike');
    stage.classList.add('wielding');
    document.documentElement.classList.add('wielding-mjolnir');
  };

  const strike = async (x: number, y: number) => {
    const held = hammer;
    if (!held) return;
    // Drive the head straight into the anchor the moment it is released.
    const dx = anchor.x - x;
    const dy = anchor.y - y;
    const distance = Math.hypot(dx, dy) || 1;
    const reach = distance - HEAD;
    const hit = { x: x + (dx / distance) * reach, y: y + (dy / distance) * reach };
    await held.animate([{ transform: aim(x, y) }, { transform: aim(hit.x, hit.y) }],
      { duration: Math.min(170, 70 + distance * 0.18), easing: 'cubic-bezier(.25,.7,.6,1)', fill: 'forwards' }).finished;
    // The ground strike, with the logo emerging from it again.
    stage.classList.add('restrike');
    stage.classList.remove('wielding');
    strikeGround(anchor.x, anchor.y, 1, logo.querySelector<HTMLElement>('.impact-emblem'));
    await held.animate([{ opacity: 1 }, { opacity: 0, transform: aim(hit.x, hit.y - 24) }],
      { duration: 380, easing: 'ease-out', fill: 'forwards' }).finished;
    held.remove();
  };

  const release = () => {
    document.documentElement.classList.remove('wielding-mjolnir');
    press = null;
    hammer = null;
  };

  logo.addEventListener('pointerdown', (event) => {
    if (event.button !== 0 || event.pointerType === 'touch' || reducedMotion.matches || hammer) return;
    press = { id: event.pointerId, x: event.clientX, y: event.clientY };
    dragged = false;
    logo.setPointerCapture(event.pointerId);
  });
  logo.addEventListener('pointermove', (event) => {
    if (!press || event.pointerId !== press.id) return;
    if (!hammer) {
      if (Math.hypot(event.clientX - press.x, event.clientY - press.y) < DRAG_THRESHOLD) return;
      dragged = true;
      take(event.clientX, event.clientY);
    }
    if (hammer) hammer.style.transform = aim(event.clientX, event.clientY);
  });
  logo.addEventListener('pointerup', (event) => {
    if (!press || event.pointerId !== press.id) return;
    if (hammer) void strike(event.clientX, event.clientY).finally(release);
    else release();
  });
  logo.addEventListener('pointercancel', () => {
    hammer?.remove();
    stage.classList.remove('wielding');
    release();
  });
  // A drag ends in a click on the logo; keep that from also firing its lightning.
  logo.addEventListener('click', (event) => {
    if (!dragged) return;
    dragged = false;
    event.stopImmediatePropagation();
  }, { capture: true });
}
