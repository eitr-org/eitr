import assert from 'node:assert/strict';
import { existsSync, readFileSync, mkdirSync } from 'node:fs';
import { chromium } from 'playwright-core';

const site = process.env.EITR_SITE_URL || 'http://127.0.0.1:4321/';
const executablePath = process.env.EITR_BROWSER_EXECUTABLE || ['/opt/google/chrome/chrome', '/usr/bin/chromium', '/usr/bin/google-chrome'].find(existsSync);
if (!executablePath) throw new Error('Set EITR_BROWSER_EXECUTABLE to Chrome/Chromium.');
const packages = new Set(readFileSync(new URL('../../distro/packages.txt', import.meta.url), 'utf8').split('\n').map(line => line.trim()));
for (const dependency of ['kitty', 'zsh', 'tmux', 'neovim', 'git', 'docker', 'docker-compose', 'lazygit', 'lazydocker']) {
  assert.ok(packages.has(dependency), `${dependency} must still be included for the Development page claim`);
}
const browser = await chromium.launch({ executablePath, headless: true });
try {
  for (const appearance of ['dark', 'light']) {
    for (const width of [390, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 960 }, reducedMotion: 'reduce' });
      await context.addInitScript(appearance => localStorage.setItem('eitr-appearance', appearance), appearance);
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(site, { waitUntil: 'networkidle' });
      assert.match(await page.locator('.hero .lead').innerText(), /keyboard-first Arch Linux.*Hyprland and Quickshell/s);
      assert.match(await page.locator('.workflow-overview').innerText(), /LazyVim, tmux and Docker.*Git identities and cloud contexts/s);
      if (width < 1201) {
        await page.getByRole('button', { name: 'Menu', exact: true }).click();
        const menu = page.getByRole('dialog', { name: 'Main menu' });
        assert.ok(await menu.isVisible());
        assert.equal(await menu.locator('nav a').count(), 8);
        assert.equal(await page.evaluate(() => getComputedStyle(document.body).overflow), 'hidden');
        assert.ok(await menu.getByRole('button', { name: 'Close', exact: true }).evaluate(button => button === document.activeElement));
        assert.ok(await menu.locator('nav a').evaluateAll(links => links.every(link => link.getBoundingClientRect().height >= 44)));
        await page.keyboard.press('Escape');
        await menu.waitFor({ state: 'hidden' });
        assert.ok(await page.getByRole('button', { name: 'Menu', exact: true }).evaluate(button => button === document.activeElement));
        await page.keyboard.press('Enter');
      }
      const development = page.locator('header nav a[href="/development/"]');
      await development.focus();
      assert.ok(await development.evaluate(element => {
        const bounds = element.getBoundingClientRect();
        return bounds.left >= 0 && bounds.right <= innerWidth;
      }), 'Development must be reachable in the mobile header');
      await page.keyboard.press('Enter');
      await page.waitForURL('**/development/');
      assert.match(await page.locator('h1').innerText(), /From a keystroke/);
      assert.match(await page.locator('#environment').innerText(), /Included.*Curated optional installs.*Cursor/s);
      assert.match(await page.locator('#agents').innerText(), /off by default/);
      if (width >= 1100) {
        const outline = page.getByRole('navigation', { name: 'On this page', exact: true });
        assert.ok(await outline.isVisible());
        assert.equal(await outline.locator('a').count(), await page.locator('.inner-content h2').count());
        await outline.locator('a[href="#agents-title"]').click();
        await page.waitForFunction(() => document.querySelector('.page-outline a[aria-current="location"]')?.getAttribute('href') === '#agents-title');
      } else {
        assert.equal(await page.locator('.page-rail').isVisible(), false);
      }
      await page.goto(new URL('/guide/', site).href, { waitUntil: 'networkidle' });
      const search = page.getByLabel('Find a Handbook chapter');
      await search.fill('git');
      assert.ok(await page.locator('[data-chapter]:visible').count() > 0);
      assert.ok(await page.locator('a[href="/guide/git-accounts/"][data-chapter]').isVisible());
      await search.fill('not-a-real-chapter-12345');
      assert.equal(await page.locator('[data-chapter]:visible').count(), 0);
      assert.match(await page.locator('#chapter-count').innerText(), /^0 of /);
      await search.fill('');
      assert.ok(await page.locator('[data-chapter]:visible').count() > 20);
      await page.goto(new URL('/installation/#compatibility', site).href, { waitUntil: 'networkidle' });
      assert.match(await page.locator('main').innerText(), /beta/);
      assert.match(await page.locator('#compatibility').innerText(), /BitLocker.*remain to be validated/s);
      if (process.env.EITR_WEB_REVIEW_CAPTURES) {
        mkdirSync(process.env.EITR_WEB_REVIEW_CAPTURES, { recursive: true });
        for (const [name, path] of [['home', '/'], ['development', '/development/'], ['handbook', '/guide/'], ['chapter', '/guide/git-accounts/']]) {
          await page.goto(new URL(path, site).href, { waitUntil: 'networkidle' });
          await page.screenshot({ path: `${process.env.EITR_WEB_REVIEW_CAPTURES}/${name}-${width}-${appearance}.png` });
        }
      }
      assert.deepEqual(errors, []);
      await context.close();
    }
  }
  console.log('Passed: verified included tools, first impressions, keyboard navigation, mobile Development discovery, Handbook search and release limitations in both themes.');
} finally { await browser.close(); }
