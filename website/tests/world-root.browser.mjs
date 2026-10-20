import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { chromium } from 'playwright-core';

const executablePath = process.env.EITR_BROWSER_EXECUTABLE || [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/chromium', '/usr/bin/google-chrome-stable', '/opt/google/chrome/chrome',
].find(existsSync);
if (!executablePath) throw new Error('Set EITR_BROWSER_EXECUTABLE to Chrome/Chromium.');
const browser = await chromium.launch({ executablePath, headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.goto(process.env.EITR_SITE_URL || 'http://127.0.0.1:4321/', { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.querySelector('.world-root .root-wood')?.getAttribute('d'));
  const original = await page.locator('.root-wood').getAttribute('d');
  assert.ok(original.endsWith('Z'), 'Wood is a filled silhouette');
  assert.equal(await page.locator('.world-root path').count(), 2, 'Keep all wood and grain in two static paths');
  assert.equal(await page.locator('.world-root mask, .world-root filter').count(), 0);
  assert.ok(await page.locator('.world-root').evaluate(svg => svg.querySelectorAll('*').length <= 8));
  assert.ok(await page.locator('.world-root').evaluate(svg => [...svg.querySelectorAll('*')].every(node => getComputedStyle(node).filter === 'none')));
  assert.equal(await page.locator('.world-root clipPath polygon').getAttribute('data-reached'), '0');
  assert.ok(await page.locator('.world-root').evaluate(svg => svg.getBoundingClientRect().right < document.querySelector('main .wrap').getBoundingClientRect().left));
  await page.evaluate(() => {
    for (const name of ['getTotalLength', 'getPointAtLength']) {
      const original = SVGGeometryElement.prototype[name];
      SVGGeometryElement.prototype[name] = function (...args) {
        if (this.closest('.world-root')) throw new Error('Root must not measure SVG geometry while scrolling');
        return original.apply(this, args);
      };
    }
  });
  await page.evaluate(() => scrollTo(0, 1800));
  await page.waitForFunction(() => Number(document.querySelector('.world-root clipPath polygon').getAttribute('data-reached')) > 1000);
  assert.equal(await page.locator('.root-wood').getAttribute('d'), original, 'Scrolling only updates the clip');
  assert.ok(await page.locator('.world-root clipPath polygon').evaluate(clip => {
    const points = [...clip.points];
    const lowest = Math.max(...points.map(point => point.y));
    return points.filter(point => point.y === lowest).length === 1;
  }), 'Growing root ends in one point, never a flat cut');
  const screenshot = process.env.EITR_ROOT_SCREENSHOT;
  if (screenshot) await page.screenshot({ path: screenshot });
  await page.evaluate(() => scrollTo(0, 0));
  await page.waitForFunction(() => document.querySelector('.world-root clipPath polygon').getAttribute('data-reached') === '0');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.waitForFunction(() => Number(document.querySelector('.world-root clipPath polygon').getAttribute('data-reached')) >= Number(document.querySelector('.world-root').getAttribute('height')));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForFunction(() => getComputedStyle(document.querySelector('.world-root')).display === 'none');
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.waitForFunction(() => getComputedStyle(document.querySelector('.world-root')).display !== 'none');
  assert.equal(await page.locator('.root-wood').getAttribute('d'), original, 'Resize restores the seeded root shape');
  assert.deepEqual(errors, []);
  console.log('World root: two static paths, no masks/filters/geometry queries, clip growth/reversal, reduced motion, mobile and stable resize passed.');
} finally {
  await browser.close();
}
