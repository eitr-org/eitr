// The tour's tabs: click or use the arrow, Home and End keys to switch areas.
const tour = document.querySelector<HTMLElement>('[data-tour]');
if (tour) {
  const tabs = [...tour.querySelectorAll<HTMLButtonElement>('[role="tab"]')];
  const select = (chosen: HTMLButtonElement, focus = false) => {
    for (const tab of tabs) {
      const active = tab === chosen;
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
      const panel = document.getElementById(tab.getAttribute('aria-controls') ?? '');
      if (panel) panel.hidden = !active;
    }
    if (focus) chosen.focus();
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => select(tab));
    tab.addEventListener('keydown', event => {
      const next = { ArrowRight: index + 1, ArrowLeft: index - 1, Home: 0, End: tabs.length - 1 }[event.key];
      if (next === undefined) return;
      event.preventDefault();
      select(tabs[(next + tabs.length) % tabs.length], true);
    });
  });
}

// Clicking an area's screenshot opens all of that area's screenshots large; the
// arrows, Left/Right keys and a swipe step through them, wrapping around.
const viewer = document.querySelector<HTMLDialogElement>('.shot-viewer');
const picture = viewer?.querySelector('img');
const caption = viewer?.querySelector('.theme-name');
const counter = viewer?.querySelector('.theme-count');
let shots: { file: string; caption: string }[] = [];
let area = '';
let shown = 0;

function showShot(index: number) {
  if (!picture || !caption || !counter || !shots.length) return;
  shown = (index + shots.length) % shots.length;
  picture.src = `/shots/${shots[shown].file}.webp`;
  picture.alt = shots[shown].caption;
  caption.textContent = `${area} · ${shots[shown].caption}`;
  counter.textContent = `${shown + 1} / ${shots.length}`;
  for (const near of [shown - 1, shown + 1]) new Image().src = `/shots/${shots[(near + shots.length) % shots.length].file}.webp`;
}

document.querySelectorAll<HTMLButtonElement>('.tour-shot').forEach(button => {
  button.addEventListener('click', () => {
    shots = JSON.parse(button.dataset.shots ?? '[]');
    area = button.dataset.area ?? '';
    showShot(0);
    viewer?.showModal();
  });
});
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
