// Scroll reveals, symbol illumination and a light that follows the cursor
// over cards. Everything stays still when the visitor prefers reduced motion.
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const revealed = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        revealed.unobserve(entry.target);
      }
    }
  },
  { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
);
document.querySelectorAll(".reveal").forEach((element, index) => {
  (element as HTMLElement).style.setProperty("--delay", `${(index % 6) * 70}ms`);
  if (reduced) element.classList.add("visible");
  else revealed.observe(element);
});

document.querySelectorAll<HTMLElement>(".glowable").forEach((card) => {
  card.addEventListener("pointermove", (event) => {
    const bounds = card.getBoundingClientRect();
    card.style.setProperty("--x", `${event.clientX - bounds.left}px`);
    card.style.setProperty("--y", `${event.clientY - bounds.top}px`);
  });
});

const header = document.querySelector(".site-header");
const onScroll = () => header?.classList.toggle("scrolled", window.scrollY > 24);
window.addEventListener("scroll", onScroll, { passive: true });
onScroll();

const symbols = new IntersectionObserver(entries => {
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;
    if (!matchMedia('(prefers-reduced-motion: reduce)').matches) entry.target.classList.add('awakened');
    symbols.unobserve(entry.target);
  }
}, {threshold: .6});
document.querySelectorAll('.norse-symbol').forEach(symbol => symbols.observe(symbol));

// Continuous animations run only while their part of the page can be seen.
const offscreen = new IntersectionObserver(entries => {
  for (const entry of entries) (entry.target as HTMLElement).toggleAttribute('data-offscreen', !entry.isIntersecting);
}, { rootMargin: '100px 0px' });
document.querySelectorAll('.hero, .rune-band, .marquee, main .wordmark, main .bifrost-brand, .footer .wordmark, .status-dot')
  .forEach(element => offscreen.observe(element));

const ambientParticles = document.querySelector<HTMLElement>('.ambient-sparks');
const ambientReduced = matchMedia('(prefers-reduced-motion: reduce)');
const updateParticles = () => {
  if (ambientParticles) ambientParticles.dataset.ambient = String(!document.hidden && !ambientReduced.matches);
};
document.addEventListener('visibilitychange', updateParticles);
ambientReduced.addEventListener('change', updateParticles);
updateParticles();
