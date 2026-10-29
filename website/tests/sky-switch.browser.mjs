import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { chromium } from 'playwright-core';
const executablePath=process.env.EITR_BROWSER_EXECUTABLE || ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/usr/bin/chromium','/usr/bin/chromium-browser',
  '/usr/bin/google-chrome-stable','/usr/bin/google-chrome'].find(existsSync);
if(!executablePath) throw new Error('Set EITR_BROWSER_EXECUTABLE to Chrome/Chromium.');
const site=process.env.EITR_SITE_URL || 'http://127.0.0.1:4321/';
const axe=readFileSync(createRequire(import.meta.url).resolve('axe-core/axe.min.js'),'utf8');
const browser=await chromium.launch({executablePath,headless:true});
try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',error=>errors.push(String(error)));
 await page.goto(site,{waitUntil:'networkidle'});
 const toggle=page.getByRole('switch',{name:'Light theme'});
 const assertSkyIcon=async appearance=>{
  assert.equal(await toggle.locator('.sky-icon-sun').isVisible(),appearance==='dark');
  assert.equal(await toggle.locator('.sky-icon-moon').isVisible(),appearance==='light');
 };
 assert.equal(await toggle.getAttribute('aria-checked'),'false');
 await assertSkyIcon('dark');
 assert.equal(await page.locator('[data-chase]').count(),0);
 await page.evaluate(()=>{
  window.skyHowls=0;window.skyHowlEnded=false;
  const original=AudioBufferSourceNode.prototype.start;
  AudioBufferSourceNode.prototype.start=function(...args){if(args[1]===.5) {window.skyHowls++;window.skyHowlDuration=args[2];this.addEventListener('ended',()=>{window.skyHowlEnded=true;},{once:true});}return original.apply(this,args);};
 });
 assert.equal(await page.locator('#norse-audio').evaluate(element=>element.paused),true);
 await toggle.click();
 assert.equal(await page.locator('[data-sky-change]').getAttribute('data-active'),'true');
 assert.equal(await toggle.isDisabled(),true);
 await page.waitForFunction(()=>Number.isFinite(Number(document.querySelector('.sky-flight').dataset.wolfY)));
 let previousY=-Infinity;
 for(let sample=0;sample<5;sample++) {
  const y=await page.locator('.sky-flight').evaluate(element=>Number(element.dataset.wolfY));
  assert.ok(y>=previousY,'The wolf must never move upward');
  previousY=y;
  await page.waitForTimeout(180);
 }
 const wipe=await page.evaluate(()=>document.getAnimations().map(animation=>animation.effect?.getKeyframes()).find(frames=>frames?.length>2 && frames.every(keyframe=>keyframe.clipPath?.startsWith('polygon(')))?.map(keyframe=>keyframe.clipPath));
 assert.ok(wipe && wipe.length>2 && wipe.every(path=>path.startsWith('polygon(')),'Theme reveal must follow the V, not a flat wipe');
 assert.equal(await page.locator('[data-sky-change]').evaluate(element=>getComputedStyle(element).backgroundColor),'rgba(0, 0, 0, 0)');
 assert.equal(await page.locator('.sky-caption').count(),0);
 assert.equal(await page.locator('.sky-flight').evaluate(element=>element.width>0&&element.height>0),true);
 assert.equal(await page.locator('[data-sky-change]').getAttribute('data-to'),'light');
 assert.equal(await page.locator('[data-sky-change]').evaluate(element=>element.parentElement===document.body),true);
 await toggle.dispatchEvent('click');
 await page.waitForFunction(()=>document.documentElement.dataset.appearance==='light');
 await page.waitForFunction(()=>document.querySelector('[data-sky-change]').dataset.active==='false');
 assert.equal(await toggle.getAttribute('aria-checked'),'true');
 await assertSkyIcon('light');
 assert.equal(await toggle.isEnabled(),true);
 assert.equal(await page.evaluate(()=>window.skyHowlDuration),4);
 assert.equal(await page.evaluate(()=>window.skyHowlEnded),false,'The howl must outlast the visual transition');
 await page.waitForFunction(()=>window.skyHowlEnded===true);
 assert.equal(await page.evaluate(()=>localStorage.getItem('eitr-appearance')),'light');
 assert.equal(await page.locator('body').evaluate(element=>getComputedStyle(element).backgroundColor),'rgb(242, 236, 223)');
 const ravenTip=await page.locator('.raven-tip').evaluate(element=>({background:getComputedStyle(element).backgroundColor,color:getComputedStyle(element).color}));
 assert.deepEqual(ravenTip,{background:'rgb(251, 246, 237)',color:'rgb(41, 37, 33)'});
 assert.equal(await page.evaluate(()=>window.skyHowls),1);
 assert.equal(await page.locator('#norse-audio').evaluate(element=>element.paused),true);
 for(const width of [375,768,1440]) {
  await page.setViewportSize({width,height:1000});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`Overflow at ${width}`);
  assert.equal(await toggle.isVisible(),true);
 }
 await page.setViewportSize({width:1440,height:1000});
 await page.addScriptTag({content:axe});
 const results=await page.evaluate(()=>axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}));
 const serious=results.violations.filter(violation=>['serious','critical'].includes(violation.impact));
 assert.deepEqual(serious.map(violation=>({id:violation.id,nodes:violation.nodes.map(node=>node.target)})),[]);
 await page.reload({waitUntil:'networkidle'});
 assert.equal(await toggle.getAttribute('aria-checked'),'true');
 await assertSkyIcon('light');
 await page.evaluate(()=>{
  window.skyHowls=0;
  const original=AudioBufferSourceNode.prototype.start;
  AudioBufferSourceNode.prototype.start=function(...args){if(args[1]===.5) window.skyHowls++;return original.apply(this,args);};
 });
 await page.getByRole('button',{name:/Music/}).click();
 await page.waitForFunction(()=>!document.querySelector('#norse-audio').paused);
 await toggle.click();
 await page.waitForFunction(()=>window.skyHowls===1);
 await page.waitForFunction(()=>document.querySelector('[data-sky-change]').dataset.active==='false');
 await page.getByRole('button',{name:/Music/}).click();
 await toggle.click();
 await page.waitForFunction(()=>document.querySelector('[data-sky-change]').dataset.active==='false');
 assert.equal(await page.evaluate(()=>window.skyHowls),2);
 await page.goto(new URL('/guide/',site).href,{waitUntil:'networkidle'});
 assert.equal(await toggle.getAttribute('aria-checked'),'true');
 await assertSkyIcon('light');
 await toggle.click();
 assert.equal(await page.locator('[data-sky-change]').getAttribute('data-to'),'dark');
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.waitForFunction(()=>document.querySelector('[data-sky-change]').dataset.active==='false');
 assert.equal(await toggle.getAttribute('aria-checked'),'false');
 await assertSkyIcon('dark');
 await toggle.focus();await page.keyboard.press('Space');
 assert.equal(await toggle.getAttribute('aria-checked'),'true');
 await assertSkyIcon('light');
 assert.equal(await page.locator('[data-sky-change]').getAttribute('data-active'),'false');
 assert.deepEqual(errors,[]);
 const blocked=await browser.newPage();
 await blocked.addInitScript(()=>{document.startViewTransition=undefined;Storage.prototype.getItem=()=>{throw new DOMException('Blocked','SecurityError')};Storage.prototype.setItem=()=>{throw new DOMException('Blocked','SecurityError')};});
 await blocked.emulateMedia({reducedMotion:'reduce'});
 await blocked.goto(site,{waitUntil:'networkidle'});
 await blocked.getByRole('switch',{name:'Light theme'}).click();
 assert.equal(await blocked.locator('html').getAttribute('data-appearance'),'light');
 await blocked.close();
 // Deep-scroll Retina captures must remain viewport-sized in both directions.
 const retina=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:2});
 await retina.goto(site,{waitUntil:'networkidle'});
 for(const section of ['#themes','#road']) {
 await retina.evaluate(section=>scrollTo({top:document.querySelector(section).getBoundingClientRect().top+scrollY-80,behavior:'instant'}),section);
 await retina.waitForTimeout(400);
 const savedY=await retina.evaluate(()=>scrollY);
 const sectionTop=await retina.locator(section).evaluate(element=>element.getBoundingClientRect().top);
 for(let direction=0;direction<2;direction++) {
  await retina.getByRole('switch',{name:'Light theme'}).click();
  await retina.waitForFunction(()=>document.documentElement.dataset.skyCapture==='true');
  assert.equal(await retina.locator('.site-page').evaluate(element=>element.getBoundingClientRect().height),1000);
  assert.ok(Math.abs(await retina.locator(section).evaluate(element=>element.getBoundingClientRect().top)-sectionTop)<2);
  await retina.waitForFunction(()=>document.querySelector('[data-sky-change]').dataset.active==='false');
  assert.ok(Math.abs(await retina.evaluate(()=>scrollY)-savedY)<2);
  assert.equal(await retina.locator('html').getAttribute('data-sky-capture'),null);
 }
 }
 await retina.getByRole('switch',{name:'Light theme'}).click();
 await retina.waitForFunction(()=>document.documentElement.dataset.skyCapture==='true');
 await retina.setViewportSize({width:1280,height:900});
 await retina.waitForFunction(()=>document.querySelector('[data-sky-change]').dataset.active==='false');
 assert.equal(await retina.locator('html').getAttribute('data-sky-capture'),null);
 assert.ok(await retina.getByRole('switch',{name:'Light theme'}).isEnabled());
 await retina.getByRole('switch',{name:'Light theme'}).click();
 await retina.waitForFunction(()=>document.documentElement.dataset.skyCapture==='true');
 await retina.locator('.version-badge').click();
 await retina.waitForFunction(()=>document.querySelector('[data-sky-change]').dataset.active==='false');
 assert.equal(await retina.locator('html').getAttribute('data-sky-capture'),null);
 await retina.close();
 const still=await browser.newPage({reducedMotion:'reduce'});
 await still.addInitScript(()=>localStorage.setItem('eitr-appearance','light'));
 await still.goto(site,{waitUntil:'networkidle'});
 const badges=await still.locator('.theme-tag,.tour-shot-hint').evaluateAll(items=>items.map(element=>({background:getComputedStyle(element).backgroundColor,color:getComputedStyle(element).color})));
 for(const badge of badges) assert.deepEqual(badge,{background:'rgb(251, 246, 237)',color:'rgb(41, 37, 33)'});
 await still.addScriptTag({content:axe});
 const allVisible=await still.evaluate(()=>axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}));
 assert.deepEqual(allVisible.violations.filter(violation=>['serious','critical'].includes(violation.impact)).map(violation=>({id:violation.id,nodes:violation.nodes.map(node=>node.target)})),[]);
 await still.close();
 console.log('Passed: day/night chase, persistence, navigation, keyboard, reduced motion, blocked storage, mobile widths and light-mode accessibility.');
} finally {await browser.close();}
