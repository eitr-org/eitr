import { message } from '../messages';
// Clicking a theme card (or Enter/Space on it) shows its wallpaper large and
// still, without the well's ripple, with the theme's name and colors. Like the
// desktop's theme picker, the neighbouring themes stand beside it as narrow
// slices; clicking one selects it. The arrows, Left/Right keys and a swipe step
// through the themes, wrapping around.
const viewer = document.querySelector<HTMLDialogElement>('.theme-viewer');
const image = viewer?.querySelector('img');
const name = viewer?.querySelector('.theme-name');
const count = viewer?.querySelector('.theme-count');
const swatches = viewer?.querySelector('.swatches');
const cards = [...document.querySelectorAll<HTMLElement>('.theme-card')];
const sides = [...(viewer?.querySelectorAll<HTMLElement>('.theme-carousel-side') ?? [])];
const SLICES = 5;
let current = 0;

function slices() {
  for (const side of sides) {
    const direction = Number(side.dataset.side);
    side.replaceChildren(...Array.from({ length: SLICES }, (_, step) => {
      const index = (current + direction * (step + 1) + cards.length * SLICES) % cards.length;
      const slice = document.createElement('button');
      slice.type = 'button';
      slice.tabIndex = -1;
      slice.className = 'theme-slice';
      slice.style.setProperty('--distance', String(step));
      slice.style.backgroundImage = `url(/art/themes/${cards[index].dataset.theme}.webp)`;
      slice.addEventListener('click', () => show(index));
      return slice;
    }));
    if (direction < 0) side.append(...[...side.children].reverse());
  }
}

function show(index: number) {
  if (!viewer || !image || !name || !count || !swatches || !cards.length) return;
  current = (index + cards.length) % cards.length;
  const card = cards[current];
  image.src = `/art/themes/${card.dataset.theme}-full.webp`;
  image.alt = message('wallpaper', {name: card.dataset.name ?? ''});
  name.textContent = card.dataset.name ?? '';
  count.textContent = `${current + 1} / ${cards.length}`;
  swatches.replaceChildren(...[...card.querySelectorAll('.swatches i')].map((swatch) => swatch.cloneNode()));
  slices();
  // Warm the neighbours so stepping feels instant.
  for (const near of [current - 1, current + 1]) {
    new Image().src = `/art/themes/${cards[(near + cards.length) % cards.length].dataset.theme}-full.webp`;
  }
}

function open(card: HTMLElement) {
  show(cards.indexOf(card));
  viewer?.showModal();
}

cards.forEach((card) => {
  card.addEventListener('click', () => open(card));
  card.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(card); }
  });
});
viewer?.querySelectorAll<HTMLElement>('.theme-viewer-step').forEach((button) => {
  button.addEventListener('click', () => show(current + Number(button.dataset.step)));
});
document.addEventListener('keydown', (event) => {
  if (!viewer?.open) return;
  if (event.key === 'ArrowLeft') { event.preventDefault(); show(current - 1); }
  else if (event.key === 'ArrowRight') { event.preventDefault(); show(current + 1); }
});
let swipeFrom: number | null = null;
image?.addEventListener('pointerdown', (event) => { if (event.pointerType !== 'mouse') swipeFrom = event.clientX; });
image?.addEventListener('pointerup', (event) => {
  if (swipeFrom !== null && Math.abs(event.clientX - swipeFrom) > 40) show(current + (event.clientX < swipeFrom ? 1 : -1));
  swipeFrom = null;
});
viewer?.querySelector('.theme-viewer-close')?.addEventListener('click', () => viewer.close());
// A click on the backdrop, outside the picture, closes it too.
viewer?.addEventListener('click', (event) => { if (event.target === viewer) viewer.close(); });
