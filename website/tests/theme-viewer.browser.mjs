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
  const names = await page.locator('.theme-card').evaluateAll(cards => cards.map(card => card.dataset.name));
  const shown = () => page.locator('.theme-viewer .theme-name').textContent();
  const count = () => page.locator('.theme-viewer .theme-count').textContent();
  await page.locator('.theme-card').nth(0).click();
  assert.equal(await shown(), names[0]);
  assert.equal(await count(), `1 / ${names.length}`);
  await page.keyboard.press('ArrowRight');
  assert.equal(await shown(), names[1], 'Right shows the next theme');
  await page.keyboard.press('ArrowLeft');
  await page.keyboard.press('ArrowLeft');
  assert.equal(await shown(), names.at(-1), 'Left from the first wraps to the last');
  await page.locator('.theme-viewer .theme-viewer-step[data-step="1"]').click();
  assert.equal(await shown(), names[0], 'The next arrow wraps back to the first');
  assert.match(await page.locator('.theme-viewer img').getAttribute('src'), new RegExp(`/art/themes/.+-full\\.webp$`));
  await page.locator('.theme-viewer .theme-viewer-close').click();
  assert.equal(await page.locator('.theme-viewer').evaluate(dialog => dialog.open), false);

  const phone = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  await phone.goto(site, { waitUntil: 'load' });
  assert.equal(await phone.locator('#realms').isVisible(), false, 'Phones leave out the nine realms');
  assert.equal(await page.locator('#realms').isVisible(), true, 'Wider screens keep them');
  console.log('Passed: theme viewer arrows, keys and wrapping; realms hidden on phones only.');
} finally {
  await browser.close();
}
