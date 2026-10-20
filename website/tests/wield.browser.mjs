// Dragging the hero logo turns it into Mjölnir aimed at the logo's spot;
// releasing strikes there and replays the arrival impact. A click keeps the
// logo's lightning, and reduced motion leaves the logo alone.
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { chromium } from 'playwright-core';

const executablePath = process.env.EITR_BROWSER_EXECUTABLE || [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  '/usr/bin/google-chrome-stable', '/usr/bin/google-chrome',
].find(existsSync);
if (!executablePath) throw new Error('Set EITR_BROWSER_EXECUTABLE to a Chrome/Chromium executable.');
const site = process.env.EITR_SITE_URL || 'http://127.0.0.1:4321/';
const browser = await chromium.launch({ executablePath, headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on('pageerror', (error) => errors.push(String(error)));
  await page.goto(site, { waitUntil: 'networkidle' });
  // Seek the ring's entrance: it waits for the logo, then reveals clockwise.
  const sweep = await page.locator('.hero .rune-ring-art').evaluate((ring) => {
    const animation = ring.getAnimations()[0];
    animation.pause();
    const values = [2000, 3350, 4100].map((time) => {
      animation.currentTime = time;
      return parseFloat(getComputedStyle(ring).getPropertyValue('--rune-sweep'));
    });
    animation.play();
    return values;
  });
  assert.deepEqual(sweep, [0, 180, 360]);
  await page.waitForTimeout(2700);
  const box = await page.locator('.hero .emblem-depth').boundingBox();
  const center = { x: box.x + box.width / 2, y: box.y + box.height / 2 };
  await page.mouse.move(center.x, center.y);
  await page.mouse.down();
  await page.mouse.move(center.x + 260, center.y + 140, { steps: 10 });
  assert.equal(await page.locator('.wielded-hammer').count(), 1);
  assert.equal(await page.locator('.hero .emergent-logo').evaluate((logo) => getComputedStyle(logo).opacity), '0');
  // The hammer's head points at the logo's spot: the head is closer to it than the handle's end.
  const aim = await page.locator('.wielded-hammer').evaluate((hammer, target) => {
    const head = hammer.querySelector('[data-hammer-part="head"]').getBoundingClientRect();
    const handle = hammer.querySelector('[data-hammer-part="handle"]').getBoundingClientRect();
    const distance = (rect) => Math.hypot(rect.left + rect.width / 2 - target.x, rect.top + rect.height / 2 - target.y);
    return distance(head) < distance(handle);
  }, center);
  assert.equal(aim, true);
  // The wielded copy keeps its metal and leather: its gradients resolve to visible defs.
  const painted = await page.locator('.wielded-hammer [data-hammer-part="head"]').evaluate((head) => {
    const id = getComputedStyle(head).fill.match(/#([\w-]+)/)?.[1];
    const gradient = id && document.getElementById(id);
    return !!gradient && getComputedStyle(gradient.closest('svg')).display !== 'none';
  });
  assert.equal(painted, true);
  await page.evaluate(() => {
    window.groundStrikes = [];
    document.addEventListener('eitr:strike', (event) => window.groundStrikes.push(event.detail));
  });
  await page.mouse.up();
  await page.waitForFunction(() => document.querySelector('.hero .impact-stage').classList.contains('restrike'));
  assert.equal(await page.locator('.hero .rune-ring-art').evaluate((ring) =>
    getComputedStyle(ring).animationDelay), '1.6s');
  // The hammer lands with the shared ground strike, on the logo's spot.
  const strikes = await page.evaluate(() => window.groundStrikes);
  assert.equal(strikes.length, 1);
  assert.ok(Math.hypot(strikes[0].x - center.x, strikes[0].y - center.y) < 40);
  await page.waitForFunction(() => !document.querySelector('.wielded-hammer'));
  // Between replays (intro.astro drops 'playing' for two frames) the ring stays hidden.
  assert.equal(await page.locator('.hero .impact-stage').evaluate((stage) => {
    stage.classList.remove('playing');
    const sweep = getComputedStyle(stage.querySelector('.rune-ring-art')).getPropertyValue('--rune-sweep');
    stage.classList.add('playing');
    return sweep;
  }), '0deg');
  await page.mouse.click(center.x, center.y);
  assert.equal(await page.locator('.wielded-hammer').count(), 0);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  assert.equal(await page.locator('.hero .rune-ring-art').evaluate((ring) => getComputedStyle(ring).maskImage), 'none');
  assert.equal(await page.locator('.hero .rune-ring-spark').evaluate((spark) => getComputedStyle(spark).display), 'none');
  await page.mouse.move(center.x, center.y);
  await page.mouse.down();
  await page.mouse.move(center.x + 200, center.y, { steps: 6 });
  assert.equal(await page.locator('.wielded-hammer').count(), 0);
  await page.mouse.up();
  assert.deepEqual(errors, []);
  console.log('Mjölnir: drag aims at the logo, release replays the strike, click and reduced motion leave it alone.');
} finally {
  await browser.close();
}
