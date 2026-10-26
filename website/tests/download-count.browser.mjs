import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { chromium } from 'playwright-core';

const executablePath = process.env.EITR_BROWSER_EXECUTABLE || ['/opt/google/chrome/chrome', '/usr/bin/chromium', '/usr/bin/google-chrome'].find(existsSync);
const browser = await chromium.launch({ executablePath, headless: true });
try {
  for (const scenario of ['positive', 'zero', 'error', 'invalid']) {
    const page = await browser.newPage({ reducedMotion: 'reduce' });
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.href === 'https://download.eitr.info/stats.json') {
        if (scenario === 'error') return route.abort();
        return route.fulfill({
          json: { total: scenario === 'positive' ? 1234 : scenario === 'zero' ? 0 : 'bad' },
          headers: { 'Access-Control-Allow-Origin': 'https://eitr.info' },
        });
      }
      if (url.origin !== 'https://eitr.info') return route.abort();
      const path = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
      const file = new URL(`../dist/${path}`, import.meta.url);
      if (!existsSync(file)) return route.fulfill({ status: 404, body: '' });
      const contentType = path.endsWith('.html') ? 'text/html' : path.endsWith('.js') ? 'text/javascript' : path.endsWith('.css') ? 'text/css' : 'application/octet-stream';
      return route.fulfill({ body: readFileSync(file), contentType });
    });
    await page.goto('https://eitr.info/', { waitUntil: 'networkidle' });
    const label = page.locator('[data-download-count]');
    if (scenario === 'positive') {
      assert.equal(await label.innerText(), 'Downloaded 1,234 times');
      assert.equal(await label.isVisible(), true);
    } else {
      assert.equal(await label.isVisible(), false);
      assert.equal(await label.textContent(), '');
    }
    await page.close();
  }
} finally {
  await browser.close();
}
console.log('Download count browser cases passed (all requests mocked).');
