import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { chromium } from 'playwright-core';

const executablePath = process.env.EITR_BROWSER_EXECUTABLE || [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/chromium', '/usr/bin/google-chrome-stable', '/opt/google/chrome/chrome',
].find(existsSync);
if (!executablePath) throw new Error('Set EITR_BROWSER_EXECUTABLE to Chrome/Chromium.');
const browser = await chromium.launch({ executablePath, headless: true });
const url = process.env.EITR_SITE_URL || 'http://127.0.0.1:4321/';
const errors = [];
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.on('pageerror', error => errors.push(String(error)));
const trigger = async () => { await page.keyboard.type('ragnarok'); };
const dismiss = async () => {
  await page.keyboard.press('Escape');
  await page.waitForFunction(() => !document.querySelector('.ragnarok'));
  assert.equal(await page.locator('html').getAttribute('data-ragnarok'), null);
};
try {
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.evaluate(() => {
    const field = document.createElement('input');
    field.id = 'ragnarok-test-input';
    document.body.append(field);
    field.focus();
  });
  await trigger();
  assert.equal(await page.locator('.ragnarok').count(), 0, 'Typing in a field must stay inert');
  await page.locator('#ragnarok-test-input').evaluate(field => field.remove());
  await trigger();
  await page.waitForSelector('.ragnarok.fenrir');
  await trigger();
  assert.equal(await page.locator('.ragnarok').count(), 1, 'Repeated triggers cannot overlap');
  await page.waitForSelector('.ragnarok.roaring');
  assert.equal(await page.locator('.fenrir-face').evaluate(face => getComputedStyle(face).backgroundPosition), '100% 50%');
  await page.waitForSelector('.ragnarok.biting');
  assert.equal(await page.locator('.fenrir-jaw').count(), 2);
  await page.waitForSelector('.ragnarok.swallowed');
  // The 0.18 s fade must reach full darkness; a fixed wait raced late frames.
  await page.waitForFunction(() => getComputedStyle(document.querySelector('.fenrir-darkness')).opacity === '1', null, { timeout: 2000 });
  await page.waitForSelector('.ragnarok.rebirth');
  await page.evaluate(()=>{document.documentElement.dataset.appearance='light';});
  assert.equal(await page.locator('.ragnarok-rebirth p').evaluate(element=>getComputedStyle(element).color),'rgb(244, 234, 220)');
  await page.evaluate(()=>{document.documentElement.dataset.appearance='dark';});
  await page.waitForFunction(() => !document.querySelector('.ragnarok'));
  assert.equal(await page.locator('html').getAttribute('data-ragnarok'), null, 'Natural completion cleans state');
  await page.setViewportSize({ width: 390, height: 844 });
  await trigger();
  await page.waitForSelector('.ragnarok.fenrir');
  await page.waitForTimeout(500);
  assert.ok(await page.locator('.ragnarok-fenrir').evaluate(face => face.getBoundingClientRect().width <= innerWidth));
  await dismiss();
  await trigger();
  await page.waitForSelector('.ragnarok.fenrir');
  await page.locator('.ragnarok').click({ position: { x: 5, y: 5 } });
  await page.waitForFunction(() => !document.querySelector('.ragnarok'));
  await trigger();
  await page.waitForSelector('.ragnarok.fenrir');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.waitForFunction(() => !document.querySelector('.ragnarok'));
  await trigger();
  await page.waitForSelector('.ragnarok.rebirth');
  assert.equal(await page.locator('.ragnarok-fenrir').isVisible(), false);
  assert.equal(await page.locator('.fenrir-jaws').isVisible(), false);
  await dismiss();
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.route('**/art/fenrir-bite.webp', route => route.abort());
  await page.reload({ waitUntil: 'networkidle' });
  await trigger();
  await page.waitForSelector('.ragnarok.rebirth');
  assert.equal(await page.locator('.ragnarok.fenrir').count(), 0, 'Missing art falls back to quiet rebirth');
  await dismiss();
  assert.deepEqual(errors, []);
  console.log('Ragnarök: face frames, bite, natural cleanup, mobile, skip, motion changes and missing-art fallback passed.');
} finally {
  await browser.close();
}
