const menu = document.querySelector<HTMLDetailsElement>('.language-menu');
menu?.addEventListener('click', event => {
  const link = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>('[data-language]') : null;
  if (!link) return;
  try { localStorage.setItem('eitr-language', link.dataset.language!); } catch {}
  const target = new URL(link.href);
  target.hash = location.hash;
  target.search = location.search;
  link.href = target.href;
});
document.addEventListener('click', event => {
  if (menu?.open && !menu.contains(event.target as Node)) menu.open = false;
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && menu?.open) {
    menu.open = false;
    menu.querySelector('summary')?.focus();
  }
});
