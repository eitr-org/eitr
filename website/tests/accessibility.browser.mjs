// Runs axe-core on every page, at desktop and phone widths and with reduced
// motion, and fails on serious or critical WCAG 2.2 A/AA violations. Expects
// the site served at EITR_SITE_URL (default: `npm run preview`).
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { chromium } from 'playwright-core';

const executablePath = process.env.EITR_BROWSER_EXECUTABLE || [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  '/usr/bin/google-chrome-stable', '/usr/bin/google-chrome',
].find(existsSync);
if (!executablePath) throw new Error('Set EITR_BROWSER_EXECUTABLE to a Chrome/Chromium executable.');
const axeSource = readFileSync(createRequire(import.meta.url).resolve('axe-core/axe.min.js'), 'utf8');
const site = process.env.EITR_SITE_URL || 'http://127.0.0.1:4321/';
const pages = ['/', '/guide/', '/intro/', '/privacy/'];
const views = [
  { name: 'desktop', viewport: { width: 1440, height: 900 }, reducedMotion: 'no-preference' },
  { name: 'phone', viewport: { width: 390, height: 844 }, reducedMotion: 'no-preference' },
  { name: 'reduced motion', viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' },
];

const browser = await chromium.launch({ executablePath, headless: true });
const problems = [];
try {
  for (const appearance of ['dark', 'light']) {
  for (const view of views) {
    const context = await browser.newContext({ viewport: view.viewport, reducedMotion: view.reducedMotion });
    await context.addInitScript(appearance=>localStorage.setItem('eitr-appearance',appearance),appearance);
    for (const path of pages) {
      const page = await context.newPage();
      await page.goto(new URL(path, site).href, { waitUntil: 'networkidle' });
      // Reveal every scroll-animated section so axe checks what visitors read.
      await page.evaluate(async () => {
        for (let y = 0; y < document.documentElement.scrollHeight; y += innerHeight / 2) {
          scrollTo(0, y);
          await new Promise(resolve => setTimeout(resolve, 60));
        }
        document.querySelectorAll('.reveal').forEach(element => element.classList.add('visible'));
        scrollTo(0, 0);
      });
      await page.waitForTimeout(1200);
      await page.addScriptTag({ content: axeSource });
      const results = await page.evaluate(() => window.axe.run(document, {
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] },
      }));
      for (const violation of results.violations.filter(item => ['serious', 'critical'].includes(item.impact))) {
        const targets = violation.nodes.slice(0, 3).map(node => node.target.join(' ')).join(' | ');
        problems.push(`${appearance} ${view.name} ${path}: ${violation.id} (${violation.impact}, ${violation.nodes.length}x) ${violation.help}\n    ${targets}`);
      }
      if(path==='/' && view.name==='desktop') {
        for(const theme of ['catppuccin-latte','norse']) {
          await page.locator(`[data-theme="${theme}"]`).hover();
          await page.waitForTimeout(900);
          const hovered=await page.evaluate(()=>window.axe.run(document,{
            runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']},
          }));
          for(const issue of hovered.violations.filter(violation=>['serious','critical'].includes(violation.impact))) {
            problems.push(`${appearance} hover ${theme}: ${issue.id} ${issue.nodes.map(node=>node.target.join(' ')).join(' | ')}`);
          }
        }
        await page.mouse.move(0,0);
        await page.waitForTimeout(1200);
        for(const button of await page.locator('[data-realm-open]').all()) {
          await button.click();
          const modal=await page.evaluate(()=>window.axe.run(document,{
            runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']},
          }));
          for(const issue of modal.violations.filter(violation=>['serious','critical'].includes(violation.impact))) {
            problems.push(`${appearance} realm ${await button.getAttribute('data-realm-open')}: ${issue.id}`);
          }
          await page.keyboard.press('Escape');
        }
      }
      await page.close();
    }
    await context.close();
  }
  }
} finally {
  await browser.close();
}
assert.equal(problems.length, 0, `Accessibility violations:\n${problems.join('\n')}`);
console.log(`Passed: no serious or critical WCAG 2.2 AA violations on ${pages.length} pages in both themes, desktop, phone and reduced motion.`);
