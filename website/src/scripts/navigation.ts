const crossing = document.querySelector<HTMLElement>('.bifrost-crossing');
if (crossing) {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let animation: Animation | undefined;
  const cancel = () => {
    animation?.cancel();
    animation = undefined;
    crossing.dataset.active = 'false';
  };
  document.addEventListener('click', event => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || reduced.matches) return;
    const link = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>('a[href]') : null;
    if (!link || link.classList.contains('skip') || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    const url = new URL(link.href, location.href);
    if (url.origin !== location.origin || url.pathname !== location.pathname || url.search !== location.search || !url.hash) return;
    let id: string;
    try { id = decodeURIComponent(url.hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target) return;
    const distance = target.getBoundingClientRect().top - parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop || '0');
    if (Math.abs(distance) < 24) return;
    cancel();
    const direction = distance > 0 ? 1 : -1;
    crossing.dataset.active = 'true';
    const current = crossing.animate([
      { opacity: 0, backgroundPosition: `${direction > 0 ? 0 : 100}% 50%` },
      { opacity: 1, offset: .2 },
      { opacity: .85, offset: .7 },
      { opacity: 0, backgroundPosition: `${direction > 0 ? 100 : 0}% 50%` },
    ], { duration: Math.min(1300, Math.max(850, Math.abs(distance) * .16)), easing: 'ease-in-out' });
    animation = current;
    current.finished.then(() => {
      if (animation === current) cancel();
    }, () => {});
  });
  reduced.addEventListener('change', () => { if (reduced.matches) cancel(); });
  document.addEventListener('visibilitychange', () => { if (document.hidden) cancel(); });
}
