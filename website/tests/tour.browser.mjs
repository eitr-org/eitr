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
  const sections = page.locator('.homepage-feature');
  assert.equal(await sections.count(), 5);
  for (const section of await sections.all()) {
    assert.equal(await section.locator('img').count(), 1);
    assert.ok((await section.locator('h2').textContent()).length);
    assert.match(await section.locator('.text-link').getAttribute('href'), /^\/screenshots\/#/);
  }
  assert.equal(await page.locator('[data-tour], .tour-tabs, .shot-viewer, .workflow-overview').count(), 0);
  assert.equal(await page.locator('a[href="/screenshots/"]').filter({ hasText: 'See all screenshots' }).count(), 1);
  assert.ok(await page.locator('#themes .theme-card').count() > 0);
  for (const width of [360, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  }
  console.log('Homepage: five single-image features, gallery CTA and responsive layout passed.');
} finally {
  await browser.close();
}
