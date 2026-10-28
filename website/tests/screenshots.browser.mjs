import assert from 'node:assert/strict';
import { existsSync, readdirSync } from 'node:fs';
import { chromium } from 'playwright-core';

const executablePath = process.env.EITR_BROWSER_EXECUTABLE || [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/chromium', '/usr/bin/google-chrome-stable', '/opt/google/chrome/chrome',
].find(existsSync);
if (!executablePath) throw new Error('Set EITR_BROWSER_EXECUTABLE to Chrome/Chromium.');
const site = process.env.EITR_SITE_URL || 'http://127.0.0.1:4321/';
const browser = await chromium.launch({ executablePath, headless: true });
try {
  const files = readdirSync(new URL('../public/shots/', import.meta.url)).filter(file => file.endsWith('.webp')).sort();
  for (const appearance of ['dark', 'light']) {
    const context = await browser.newContext({ reducedMotion: 'reduce' });
    await context.addInitScript(appearance => localStorage.setItem('eitr-appearance', appearance), appearance);
    const page = await context.newPage();
    await page.goto(new URL('/screenshots/', site).href, { waitUntil: 'networkidle' });
    const links = page.locator('.screenshot-link');
    assert.deepEqual((await links.evaluateAll(nodes => nodes.map(node => node.getAttribute('href').split('/').pop()))).sort(), files);
    for (const width of [360, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${appearance} grid at ${width}`);
      await links.first().focus();
      await page.keyboard.press('Enter');
      const viewer = page.locator('.shot-viewer');
      assert.equal(await viewer.evaluate(dialog => dialog.open), true);
      assert.equal(await viewer.locator('.theme-count').textContent(), `1 / ${files.length}`);
      await page.keyboard.press('ArrowRight');
      assert.equal(await viewer.locator('img').getAttribute('src'), await links.nth(1).getAttribute('href'));
      await page.keyboard.press('ArrowLeft');
      await viewer.locator('[data-step="-1"]').click();
      assert.equal(await viewer.locator('.theme-count').textContent(), `${files.length} / ${files.length}`);
      await viewer.locator('[data-step="1"]').click();
      assert.equal(await viewer.locator('img').getAttribute('alt'), await links.first().locator('img').getAttribute('alt'));
      assert.equal(await viewer.locator('.theme-name').textContent(), await links.first().locator('..').locator('figcaption').textContent());
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `viewer at ${width}`);
      await page.keyboard.press('Escape');
      assert.equal(await viewer.evaluate(dialog => dialog.open), false);
      assert.equal(await links.first().evaluate(link => document.activeElement === link), true);
      await links.nth(12).click();
      assert.equal(await viewer.locator('.theme-count').textContent(), `13 / ${files.length}`);
      await viewer.locator('.theme-viewer-close').click();
      assert.equal(await links.nth(12).evaluate(link => document.activeElement === link), true);
    }
    await context.close();
  }
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(new URL('/screenshots/', site).href);
  for (const image of await page.locator('.screenshot-link img').all()) {
    assert.equal(await image.getAttribute('loading'), 'lazy');
    assert.ok(Number(await image.getAttribute('width')) > 0 && Number(await image.getAttribute('height')) > 0);
    assert.ok((await image.getAttribute('alt')).length > 0);
    const response = await page.request.get(new URL(await image.getAttribute('src'), site).href);
    assert.equal(response.status(), 200);
  }
  await page.locator('.screenshot-link').first().click();
  assert.match(page.url(), /\/shots\/desktop.webp$/);
  await context.close();
  console.log('Screenshots: complete catalog, keyboard, buttons, focus, both palettes, responsive viewer and no-JS links passed.');
} finally {
  await browser.close();
}
