// Runes in the scrolling bands and the footer motto show their Latin letters while the cursor
// passes over them, then fade back to runes.
import { finePointer } from './motion';

const RADIUS = 70;
for (const band of document.querySelectorAll<HTMLElement>('.rune-band, .marquee, .footer-runes')) {
  const glyphs = [...band.querySelectorAll<HTMLElement>('.rune-glyph')];
  let frame = 0;
  let x = 0;
  const decode = () => {
    frame = 0;
    for (const glyph of glyphs) {
      const bounds = glyph.getBoundingClientRect();
      glyph.classList.toggle('decoded', Math.abs(bounds.left + bounds.width / 2 - x) < RADIUS);
    }
  };
  band.addEventListener('pointermove', (event) => {
    if (!finePointer.matches) return;
    x = event.clientX;
    if (!frame) frame = requestAnimationFrame(decode);
  });
  band.addEventListener('pointerleave', () => {
    cancelAnimationFrame(frame);
    frame = 0;
    glyphs.forEach((glyph) => glyph.classList.remove('decoded'));
  });
}
