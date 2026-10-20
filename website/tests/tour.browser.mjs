import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { chromium } from 'playwright-core';

const executablePath = process.env.EITR_BROWSER_EXECUTABLE || [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/chromium', '/usr/bin/google-chrome-stable', '/opt/google/chrome/chrome',
].find(existsSync);
if (!executablePath) throw new Error('Set EITR_BROWSER_EXECUTABLE to Chrome/Chromium.');
const site = process.env.EITR_SITE_URL || 'http://127.0.0.1:4321/';
const browser = await chromium.launch({ executablePath, headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(site, { waitUntil: 'load' });
  const tabs = page.locator('#tour [role="tab"]');
  const visible = () => page.locator('#tour [role="tabpanel"]:not([hidden])').getAttribute('id');
  assert.equal(await visible(), 'tour-desktop', 'the first area shows first');
  await tabs.nth(2).click();
  assert.equal(await visible(), 'tour-install', 'a click switches the area');
  assert.equal(await tabs.nth(2).getAttribute('aria-selected'), 'true');
  await page.keyboard.press('ArrowRight');
  assert.equal(await visible(), 'tour-safety', 'the arrow keys move between areas');
  await page.keyboard.press('End');
  await page.keyboard.press('ArrowRight');
  assert.equal(await visible(), 'tour-desktop', 'moving past the last area wraps to the first');
  await page.locator('#tour-desktop .tour-shot').click();
  const viewer = page.locator('.shot-viewer');
  assert.equal(await viewer.evaluate(dialog => dialog.open), true, 'a click opens the screenshots');
  const total = JSON.parse(await page.locator('#tour-desktop .tour-shot').getAttribute('data-shots')).length;
  assert.equal(await viewer.locator('.theme-count').textContent(), `1 / ${total}`);
  await page.keyboard.press('ArrowRight');
  assert.equal(await viewer.locator('.theme-count').textContent(), `2 / ${total}`, 'Right shows the next screenshot');
  await page.keyboard.press('ArrowLeft');
  await page.keyboard.press('ArrowLeft');
  assert.equal(await viewer.locator('.theme-count').textContent(), `${total} / ${total}`, 'Left from the first wraps');
  await viewer.locator('.theme-viewer-close').click();
  assert.equal(await viewer.evaluate(dialog => dialog.open), false);
  const files = (await page.locator('#tour .tour-shot').evaluateAll(buttons =>
    buttons.flatMap(button => JSON.parse(button.dataset.shots).map(shot => `/shots/${shot.file}.webp`))));
  for (const source of files) {
    const response = await page.request.get(new URL(source, site).href);
    assert.equal(response.status(), 200, `${source} is published`);
  }
  for (const image of await page.locator('#tour img').all()) {
    const source = await image.getAttribute('src');
    const response = await page.request.get(new URL(source, site).href);
    assert.equal(response.status(), 200, `${source} is published`);
  }
  console.log('tour ok');
} finally {
  await browser.close();
}
