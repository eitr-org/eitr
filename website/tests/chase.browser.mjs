import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { chromium } from 'playwright-core';
const executablePath = process.env.EITR_BROWSER_EXECUTABLE || [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  '/usr/bin/google-chrome-stable', '/usr/bin/google-chrome',
].find(existsSync);
if (!executablePath) throw new Error('Set EITR_BROWSER_EXECUTABLE to a Chrome/Chromium executable.');
const browser = await chromium.launch({ executablePath, headless: true });
try {
 const page = await browser.newPage({viewport:{width:1440,height:900}});
 const errors=[];page.on('pageerror',error=>errors.push(String(error)));
 await page.goto(process.env.EITR_SITE_URL || 'http://127.0.0.1:4321/',{waitUntil:'networkidle'});
 assert.equal(await page.locator('.hero-scene .impact-stage').count(),1);
 // Jörmungandr keeps away from the opening screen.
 await page.waitForFunction(()=>document.querySelector('[data-serpent]').dataset.active==='false');
 assert.equal(await page.locator('[data-serpent]').getAttribute('data-passing'),'false');
 assert.equal(await page.locator('#norse-audio').evaluate(audio=>audio.paused && !audio.autoplay && audio.preload==='none' && !performance.getEntriesByType('resource').some(entry=>entry.name.includes('/audio/wild-west-vikings.mp3'))),true);
 await page.waitForFunction(()=>document.querySelector('.impact-stage').dataset.ambient==='true');
 assert.equal(await page.locator('.ambient-sparks i').count(),24);
 // The aurora's drawing area follows its canvas even without a window resize.
 const auroraViewport=()=>page.locator('.aurora-sky').evaluate(canvas=>{const gl=canvas.getContext('webgl');return [canvas.clientWidth,gl.getParameter(gl.VIEWPORT)[2]];});
 await page.locator('.aurora-sky').evaluate(canvas=>{canvas.style.width='120px';});
 await page.waitForTimeout(150);
 await page.locator('.aurora-sky').evaluate(canvas=>{canvas.style.width='';});
 await page.waitForTimeout(150);
 const [auroraWidth,drawnWidth]=await auroraViewport();
 assert.equal(drawnWidth,Math.round(auroraWidth/2));
 assert.equal(await page.locator('.emblem-shimmer path').evaluate(path=>getComputedStyle(path).animationPlayState),'running');
 // The logo stays put while the pointer moves over the hero.
 await page.locator('.emergent-logo').evaluate(logo=>Promise.all(logo.getAnimations().map(animation=>animation.finished)));
 const logoBefore=await page.locator('.emblem-depth').boundingBox();
 await page.locator('.hero-scene').hover({position:{x:30,y:30}});
 await page.locator('h1').hover();
 await page.waitForTimeout(150);
 assert.deepEqual(await page.locator('.emblem-depth').boundingBox(),logoBefore);
 assert.equal(await page.locator('.ambient-sparks').evaluate(element=>getComputedStyle(element).position),'fixed');
 assert.equal(await page.locator('.hero h1 em').evaluate(element=>getComputedStyle(element).color),'rgb(255, 255, 255)');
 assert.equal(await page.locator('.impact-emblem').evaluate(element=>getComputedStyle(element).backgroundColor),'rgb(255, 255, 255)');
 assert.equal(await page.locator('.hero h1 .bifrost-brand').count(),0);
 for(const selector of ['.site-header .wordmark','.footer .wordmark']) {
  const colors=await page.locator(selector).evaluate(element=>{
   const animation=element.getAnimations().find(animation=>animation.animationName==='bifrost-flow');
   if(!animation) return null;
   animation.pause();animation.currentTime=0;const before=getComputedStyle(element).backgroundPosition;
   animation.currentTime=5000;const after=getComputedStyle(element).backgroundPosition;
   animation.play();return {before,after};
  });
  assert.ok(colors && colors.before!==colors.after,`Missing cycling rainbow on ${selector}`);
 }
 await page.getByRole('button',{name:'Music off',exact:true,pressed:false}).click();
 await page.waitForFunction(()=>!document.querySelector('#norse-audio').paused && document.querySelector('#norse-audio').currentTime>0);
 assert.equal(await page.locator('.music-toggle').getAttribute('aria-pressed'),'true');
 await page.getByRole('button',{name:'Music on',exact:true,pressed:true}).click();
 assert.equal(await page.locator('#norse-audio').evaluate(audio=>audio.paused),true);
 // The credits close on a click outside them and on Escape; clicks inside keep them open.
 const credits = page.locator('.ambient-music details');
 await credits.locator('summary').click();
 assert.equal(await credits.evaluate(element=>element.open),true);
 await credits.locator('p').first().click({position:{x:2,y:2}});
 assert.equal(await credits.evaluate(element=>element.open),true);
 await page.mouse.click(10, 10);
 assert.equal(await credits.evaluate(element=>element.open),false);
 await credits.locator('summary').click();
 await page.keyboard.press('Escape');
 assert.equal(await credits.evaluate(element=>element.open),false);
 // Decorative runes keep the normal pointer instead of the text cursor.
 assert.equal(await page.locator('.rune-band .rune-glyph').first().evaluate(element=>getComputedStyle(element).cursor),'default');
 assert.equal(await page.locator('.rune-band').evaluate(element=>getComputedStyle(element).cursor),'default');

 assert.equal(await page.locator('.hero-art').count(),0);
 assert.equal(await page.locator('.hero > .hero-lightning').count(),1);
 const coverage=await page.locator('.hero-lightning').evaluate(element=>{
  const overlay=element.getBoundingClientRect(),hero=element.closest('.hero').getBoundingClientRect();
  return Math.abs(overlay.width-hero.width)<2&&Math.abs(overlay.height-hero.height)<2;
 });
 assert.equal(coverage,true);
 assert.equal(await page.locator('.hero [data-lightning-effect]').count(),7);
 assert.equal(new Set(await page.locator('.hero [data-lightning-effect] path').evaluateAll(paths=>paths.map(path=>path.getAttribute('d')))).size,7);
 await page.waitForFunction(()=>getComputedStyle(document.querySelector('.hero-scene .emergent-logo')).opacity==='1');
 const emptyArea=await page.locator('.impact-stage').evaluate(stage=>{
  const rect=stage.getBoundingClientRect();return {x:rect.left+12,y:rect.top+12};
 });
 await page.mouse.click(emptyArea.x,emptyArea.y);
 assert.equal(await page.locator('.impact-stage').getAttribute('data-last-effect'),null);
 assert.notEqual(await page.evaluate(({x,y})=>getComputedStyle(document.elementFromPoint(x,y)).cursor,emptyArea),'pointer');
 const emptyLogoCorner=await page.locator('.emblem-hit').evaluate(svg=>{
  const rect=svg.getBoundingClientRect();return {x:rect.left+3,y:rect.top+3};
 });
 await page.mouse.click(emptyLogoCorner.x,emptyLogoCorner.y);
 assert.equal(await page.locator('.impact-stage').getAttribute('data-last-effect'),null);
 let previousEffect=null;
 for(let i=0;i<7;i++) {
  await page.getByRole('button',{name:'Spark lightning from the Eitr logo'}).click();
  const effect=await page.locator('.hero-scene .impact-stage').getAttribute('data-last-effect');
  assert.ok(Number(effect)>=0&&Number(effect)<7);
  assert.notEqual(effect,previousEffect);
  const originError=await page.locator('.hero').evaluate(hero=>{
   const selected=hero.querySelector(`[data-lightning-effect="${hero.querySelector('.impact-stage').dataset.lastEffect}"]`);
   const svg=selected.ownerSVGElement;
   const point=svg.createSVGPoint();point.x=500;point.y=300;
   const origin=point.matrixTransform(selected.getScreenCTM());
   const logo=hero.querySelector('.impact-emblem').getBoundingClientRect();
   return Math.hypot(origin.x-logo.left-logo.width/2,origin.y-logo.top-logo.height/2);
  });
  assert.ok(originError<2,`Lightning misses logo origin by ${originError}px`);
  const exclusion=await page.locator('.hero-lightning').evaluate(svg=>{
   const mask=svg.querySelector('[data-logo-exclusion]');
   const d=mask.getAttribute('d');
   const boundary=mask.getBBox();
   const point=svg.createSVGPoint();point.x=boundary.x+boundary.width/2;point.y=boundary.y+boundary.height/2;
   return {contours:(d.match(/M/g)||[]).length,centerExcluded:mask.isPointInFill(point),
    white:getComputedStyle(svg).stroke,maskApplied:!!svg.querySelector('g[mask]')};
  });
  assert.deepEqual(exclusion,{contours:1,centerExcluded:true,white:'rgb(255, 255, 255)',maskApplied:true});
  previousEffect=effect;
  await page.locator('.hero-scene .impact-stage').evaluate(async stage=>{
   await Promise.all(Array.from(stage.closest('.hero').querySelectorAll('[data-lightning-effect]')).flatMap(element=>element.getAnimations().map(animation=>animation.finished)));
  });
 }
 await page.getByRole('button',{name:'Spark lightning from the Eitr logo'}).focus();
 await page.keyboard.press('Enter');
 assert.notEqual(await page.locator('.hero-scene .impact-stage').getAttribute('data-last-effect'),previousEffect);
 assert.equal(await page.locator('body').evaluate(element=>getComputedStyle(element).backgroundColor),'rgb(0, 0, 0)');
 assert.equal(await page.locator('.hero').evaluate(element=>getComputedStyle(element).backgroundColor),'rgba(0, 0, 0, 0)');
 assert.ok(await page.evaluate(()=>Number(getComputedStyle(document.querySelector('main')).zIndex)>Number(getComputedStyle(document.querySelector('.ambient-sparks')).zIndex)));
 assert.equal(await page.locator('.ambient-sparks i').first().evaluate(element=>getComputedStyle(element).width),'3px');
 assert.equal(await page.locator('.what-art img').getAttribute('src'),'/art/mimir.webp');
 assert.equal(await page.locator('.myth-gallery,.chase-demo').count(),0);
 assert.ok(await page.locator('.norse-symbol').count()>=10);
 assert.equal(await page.locator('[data-chase]').count(),0);
 assert.equal(await page.locator('[data-realm-open]').count(),9);
 assert.equal(await page.locator('.realm-dialog').count(),9);
 for(const realmButton of await page.locator('[data-realm-open]').all()) {
  const id=await realmButton.getAttribute('aria-controls');
  await realmButton.click();
  const dialog=page.locator(`#${id}`);
  assert.equal(await dialog.evaluate(element=>element.open),true);
  assert.equal(await dialog.locator('.realm-dialog-symbol').evaluate(element=>Math.round(element.getBoundingClientRect().width)),48);
  assert.equal(await dialog.evaluate(element=>element.contains(document.activeElement)),true);
  await page.keyboard.press('Tab');
  assert.equal(await dialog.evaluate(element=>element.contains(document.activeElement)),true);
  await page.keyboard.press('Escape');
  assert.equal(await dialog.evaluate(element=>element.open),false);
  assert.equal(await realmButton.evaluate(element=>document.activeElement===element),true);
 }
 await page.locator('[data-realm-open="asgard"]').click();
 await page.getByRole('button',{name:'Close Asgard',exact:true}).click();
 assert.equal(await page.locator('#realm-asgard').evaluate(element=>element.open),false);
 await page.locator('[data-realm-open="asgard"]').click();
 await page.mouse.click(10,100);
 assert.equal(await page.locator('#realm-asgard').evaluate(element=>element.open),false);
 await page.locator('[data-realm-open="alfheim"]').click();
 await page.locator('#realm-alfheim .realm-cta').click();
 assert.equal(await page.locator('#realm-alfheim').evaluate(element=>element.open),false);
 assert.equal(new URL(page.url()).hash,'#themes');
 for(const path of ['/','/guide/']) {
  await page.goto(new URL(path,page.url()).href,{waitUntil:'networkidle'});
  // Downloads (the ISO and its checksum) start in place instead of a new tab.
  for(const link of await page.locator('a[href^="https://"]:not([download])').all()) {
   assert.equal(await link.getAttribute('target'),'_blank');
   assert.match(await link.getAttribute('rel'),/noopener/);
  }
 }
 await page.goto(new URL('/',page.url()).href);
 // Only maximum-charge releases select the real thunder recording.
 await page.evaluate(()=>{
  window.thunderOffsets=[];
  const original=AudioBufferSourceNode.prototype.start;
  AudioBufferSourceNode.prototype.start=function(...args){window.thunderOffsets.push(args[1]??0);return original.apply(this,args);};
 });
 await page.locator('.emergent-logo').click();
 await page.waitForTimeout(500);
 assert.ok((await page.evaluate(()=>window.thunderOffsets)).includes(0));
 assert.ok(!(await page.evaluate(()=>window.thunderOffsets)).includes(.7));
 await page.mouse.move(30,400);await page.mouse.down();
 await page.waitForTimeout(650);await page.mouse.up();await page.waitForTimeout(500);
 assert.ok(!(await page.evaluate(()=>window.thunderOffsets)).includes(.7));
 await page.mouse.down();await page.waitForTimeout(1600);await page.mouse.up();
 await page.waitForFunction(()=>window.thunderOffsets.includes(.7));
 for(const width of [375,768,1024,1440]) {
  await page.setViewportSize({width,height:900});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`Overflow at ${width}`);
  // Phones leave out the nine realms (WorldTree.astro).
  assert.equal(await page.locator('#realms').isVisible(),width>700);
  if(width<=700) continue;
  await page.locator('[data-realm-open="asgard"]').click();
  assert.equal(await page.locator('#realm-asgard').evaluate(element=>element.getBoundingClientRect().width<=innerWidth),true);
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('[data-realm-open]').evaluateAll(buttons=>buttons.every(button=>{const box=button.getBoundingClientRect();return box.left>=0&&box.right<=innerWidth;})),true);
 }
 await page.locator('#themes .norse-symbol').scrollIntoViewIfNeeded();
 await page.waitForFunction(()=>document.querySelector('.impact-stage').dataset.ambient==='false');
 // Past the opening screen, it glides by behind the page.
 await page.waitForFunction(()=>document.querySelector('[data-serpent]').dataset.passing==='true');
 assert.ok(Number(await page.locator('[data-serpent]').getAttribute('data-location'))<5);
 assert.equal(await page.locator('[data-serpent]').evaluate(element=>getComputedStyle(element).position),'fixed');
 assert.equal(await page.locator('[data-serpent]').evaluate(element=>getComputedStyle(element).pointerEvents),'none');
 assert.ok(await page.locator('[data-serpent]').evaluate(element=>element.getBoundingClientRect().width<innerWidth*.7));
 assert.equal(await page.locator('.serpent-body').evaluate(element=>element.getAnimations().length),1);
 assert.equal(await page.locator('.emblem-shimmer path').evaluate(path=>getComputedStyle(path).animationPlayState),'paused');
 assert.equal(await page.locator('.ambient-sparks').getAttribute('data-ambient'),'true');
 assert.equal(await page.locator('.ambient-sparks i').first().evaluate(element=>getComputedStyle(element).animationPlayState),'running');
 await page.waitForFunction(()=>document.querySelector('#themes .norse-symbol').classList.contains('awakened'));
 await page.emulateMedia({reducedMotion:'reduce'});
 assert.equal(await page.locator('.ambient-sparks').isVisible(),false);
 assert.equal(await page.locator('[data-serpent]').isVisible(),false);
 assert.equal(await page.locator('.emblem-shimmer').isVisible(),false);
 await page.emulateMedia({reducedMotion:'no-preference'});
 await page.goto(new URL('/',page.url()).href,{waitUntil:'networkidle'});
 await page.getByRole('link',{name:/^Begin/}).click();
 await page.waitForFunction(()=>document.querySelector('.bifrost-crossing').dataset.active==='true');
 assert.equal(new URL(page.url()).hash,'#install');
 assert.equal(await page.locator('.bifrost-crossing').evaluate(element=>getComputedStyle(element).pointerEvents),'none');
 assert.equal(await page.locator('.bifrost-crossing').evaluate(element=>{
  const rect=element.getBoundingClientRect();
  return rect.left===0 && rect.top===0 && Math.abs(rect.width-innerWidth)<1 && Math.abs(rect.height-innerHeight)<1 && getComputedStyle(element).maskImage==='none';
 }),true);
 await page.waitForFunction(()=>document.querySelector('.bifrost-crossing').dataset.active==='false');
 assert.ok(await page.evaluate(()=>scrollY>1000));
 await page.getByRole('link',{name:'Desktop',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.bifrost-crossing').dataset.active==='true');
 assert.equal(new URL(page.url()).hash,'#what');
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.waitForFunction(()=>document.querySelector('.bifrost-crossing').dataset.active==='false');
 await page.getByRole('link',{name:'Themes',exact:true}).click();
 assert.equal(await page.locator('.bifrost-crossing').getAttribute('data-active'),'false');
 assert.equal(new URL(page.url()).hash,'#themes');
 await page.emulateMedia({reducedMotion:'no-preference'});
 await page.addInitScript(()=>{window.entranceStrikes=[];document.addEventListener('eitr:strike',event=>window.entranceStrikes.push(event.detail));});
 await page.goto(new URL('/intro/',page.url()).href,{waitUntil:'networkidle'});
 // The entrance is lightning alone: one strike on the emblem, no Mjölnir.
 await page.waitForFunction(()=>window.entranceStrikes.length===1);
 const entrance=await page.evaluate(()=>{
  const emblem=document.querySelector('.impact-emblem').getBoundingClientRect();
  const strike=window.entranceStrikes[0];
  return {hammer:getComputedStyle(document.querySelector('.hammer')).visibility,
   miss:Math.hypot(strike.x-(emblem.left+emblem.width/2),strike.y-(emblem.top+emblem.height/2))};
 });
 assert.equal(entrance.hammer,'hidden');
 assert.ok(entrance.miss<40,`Entrance lightning misses the emblem by ${entrance.miss}px`);
 await page.waitForFunction(()=>getComputedStyle(document.querySelector('.emergent-logo')).opacity==='1');
 assert.equal(await page.locator('#replay').count(),1);
 await page.getByRole('button',{name:'Replay the strike'}).click();
 await page.waitForFunction(()=>getComputedStyle(document.querySelector('.emergent-logo')).opacity==='0');
 await page.waitForFunction(()=>window.entranceStrikes.length===2);
 await page.emulateMedia({reducedMotion:'reduce'});
 assert.equal(await page.locator('.hammer').isVisible(),false);
 assert.equal(await page.locator('.emergent-logo').evaluate(element=>getComputedStyle(element).opacity),'1');
 assert.deepEqual(errors,[]);
 console.log('Passed: Bifrost navigation, ambient effects/music, hero/Mimir, symbols, external links, responsive widths, reduced motion and entrance demo.');
} finally {await browser.close();}
