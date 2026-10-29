const viewer = document.querySelector<HTMLDialogElement>('.shot-viewer');
const picture = viewer?.querySelector('img');
const caption = viewer?.querySelector('.theme-name');
const counter = viewer?.querySelector('.theme-count');
const shots = Array.from(document.querySelectorAll<HTMLAnchorElement>('.screenshot-link')).map(link => ({
  file: link.dataset.shot!,
  alt: link.querySelector('img')?.alt ?? '',
  caption: link.closest('figure')?.querySelector('figcaption')?.textContent ?? '',
}));
let opener: HTMLAnchorElement | null = null;
let shown = 0;

function showShot(index: number) {
  if (!picture || !caption || !counter || !shots.length) return;
  shown = (index + shots.length) % shots.length;
  picture.src = `/shots/${shots[shown].file}.webp`;
  picture.alt = shots[shown].alt;
  caption.textContent = shots[shown].caption;
  counter.textContent = `${shown + 1} / ${shots.length}`;
  for (const near of [shown - 1, shown + 1]) new Image().src = `/shots/${shots[(near + shots.length) % shots.length].file}.webp`;
}

document.querySelectorAll<HTMLAnchorElement>('.screenshot-link').forEach(link => {
  link.addEventListener('click', event => {
    if (!viewer || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    opener = link;
    showShot(shots.findIndex(shot => shot.file === link.dataset.shot));
    viewer.showModal();
  });
});
viewer?.addEventListener('close', () => opener?.focus({ preventScroll: true }));
viewer?.querySelectorAll<HTMLElement>('.theme-viewer-step').forEach(step => {
  step.addEventListener('click', () => showShot(shown + Number(step.dataset.step)));
});
viewer?.addEventListener('keydown', event => {
  if (event.key === 'ArrowLeft') { event.preventDefault(); showShot(shown - 1); }
  else if (event.key === 'ArrowRight') { event.preventDefault(); showShot(shown + 1); }
});
let swipeStart: number | null = null;
picture?.addEventListener('pointerdown', event => { if (event.pointerType !== 'mouse') swipeStart = event.clientX; });
picture?.addEventListener('pointerup', event => {
  if (swipeStart !== null && Math.abs(event.clientX - swipeStart) > 40) showShot(shown + (event.clientX < swipeStart ? 1 : -1));
  swipeStart = null;
});
viewer?.querySelector('.theme-viewer-close')?.addEventListener('click', () => viewer.close());
viewer?.addEventListener('click', event => { if (event.target === viewer) viewer.close(); });
