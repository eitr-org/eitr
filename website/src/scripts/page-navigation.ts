const menu = document.querySelector<HTMLDialogElement>('#mobile-menu');
const trigger = document.querySelector<HTMLButtonElement>('.menu-toggle');
const close = menu?.querySelector<HTMLButtonElement>('.menu-close');
const menuContent = menu?.querySelector<HTMLElement>('.mobile-menu-content');
const narrow = matchMedia('(max-width: 1200px)');
if (menu && trigger && close && menuContent) {
  const controls = Array.from(document.querySelectorAll<HTMLElement>('.header-inner nav, .header-inner .version-badge'));
  const homes = controls.map(control => ({ control, marker: document.createComment('header control') }));
  for (const { control, marker } of homes) control.before(marker);
  trigger.addEventListener('click', () => {
    for (const { control } of homes) menuContent.append(control);
    menu.showModal();
    trigger.setAttribute('aria-expanded', 'true');
    document.body.classList.add('menu-open');
    close.focus();
  });
  const dismiss = () => menu.close();
  close.addEventListener('click', dismiss);
  // Links to another page load it with the menu open; closing first would move the
  // link out of the dialog mid-click. Same-page anchors close the menu to show the target.
  menu.addEventListener('click', event => {
    const link = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>('a[href]') : null;
    if (link && link.pathname === location.pathname && link.hash) dismiss();
  });
  menu.addEventListener('close', () => {
    for (const { control, marker } of homes) marker.after(control);
    trigger.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('menu-open');
    trigger.focus({ preventScroll: true });
  });
  narrow.addEventListener('change', () => { if (!narrow.matches && menu.open) dismiss(); });
  window.addEventListener('pageshow', event => { if (event.persisted && menu.open) dismiss(); });
}

const outline = document.querySelector<HTMLElement>('.page-outline');
if (outline) {
  const links = Array.from(outline.querySelectorAll<HTMLAnchorElement>('a'));
  const headings = links.map(link => document.getElementById(decodeURIComponent(link.hash.slice(1)))).filter((heading): heading is HTMLElement => Boolean(heading));
  const update = () => {
    const current = headings.filter(heading => !heading.closest('[hidden]') && heading.getBoundingClientRect().top <= 150).at(-1) ?? headings.find(heading => !heading.closest('[hidden]'));
    for (const link of links) {
      if (link.hash === `#${current?.id}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    }
  };
  const observer = new IntersectionObserver(update, { rootMargin: '-110px 0px -60% 0px', threshold: [0, 1] });
  for (const heading of headings) observer.observe(heading);
  update();
  window.addEventListener('hashchange', update);
  let scheduled = false;
  window.addEventListener('scroll', () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => { scheduled = false; update(); });
  }, { passive: true });
}
