import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { chromium } from 'playwright-core';

const executablePath=process.env.EITR_BROWSER_EXECUTABLE || ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/usr/bin/chromium','/usr/bin/google-chrome','/opt/google/chrome/chrome'].find(existsSync);
if(!executablePath) throw new Error('Set EITR_BROWSER_EXECUTABLE to Chrome/Chromium.');
const site=process.env.EITR_SITE_URL || 'http://127.0.0.1:4321/';
const handbook=JSON.parse(readFileSync(new URL('../../quickshell/desktop-bar/handbook/catalog.json',import.meta.url),'utf8')).chapters;
const publicPaths=[...readdirSync(new URL('../src/pages/',import.meta.url))
 .filter(name=>name.endsWith('.astro') && name!=='intro.astro')
 .map(name=>name==='index.astro'?'/':`/${name.slice(0,-6)}/`), ...handbook.map(chapter=>`/guide/${chapter.id}/`)].sort();
const browser=await chromium.launch({executablePath,headless:true});
try {
 const context=await browser.newContext({javaScriptEnabled:false});
 const page=await context.newPage();
 const response=await page.request.get(new URL('/sitemap.xml',site).href);
 assert.equal(response.status(),200);
 assert.match(response.headers()['content-type'],/xml/);
 const xml=await response.text();
 // Parse XML in the browser rather than matching XML with regular expressions.
 const parser=await browser.newPage();
 const urls=await parser.evaluate(xml=>{
  const doc=new DOMParser().parseFromString(xml,'application/xml');
  if(doc.querySelector('parsererror')) throw new Error('Invalid sitemap XML');
  return [...doc.querySelectorAll('loc')].map(node=>node.textContent);
 },xml);
 assert.deepEqual(urls.map(url=>new URL(url).pathname).sort(),publicPaths);
 assert.ok(urls.every(url=>new URL(url).origin==='https://eitr.info'));
 const robots=await page.request.get(new URL('/robots.txt',site).href);
 assert.equal(robots.status(),200);
 const rules=await robots.text();
 assert.match(rules,/Sitemap: https:\/\/eitr\.info\/sitemap\.xml/);
 for(const agent of ['*','OAI-SearchBot','Claude-SearchBot','Claude-User']) {
  assert.ok(rules.includes(`User-agent: ${agent}\nAllow: /`));
 }
 let links=0;
 const documents=new Map();
 for(const path of [...publicPaths,'/intro/']) {
  const result=await page.goto(new URL(path,site).href,{waitUntil:'networkidle'});
  assert.equal(result.status(),200,path);
  const html=await result.text();
  assert.match(html,/Eitr Linux/,`${path} must identify the project in static HTML`);
  assert.match(await page.title(),/Eitr Linux/);
  assert.equal(await page.locator('h1').count(),1,`${path} needs one page heading`);
  assert.ok((await page.locator('meta[name="description"]').getAttribute('content')).length>40);
  assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'),`https://eitr.info${path}`);
  assert.equal(await page.locator('meta[property="og:title"]').getAttribute('content'),await page.title());
  const noindex=await page.locator('meta[name="robots"]').count();
  assert.equal(noindex,path==='/intro/'?1:0);
  if(noindex) assert.equal(await page.locator('meta[name="robots"]').getAttribute('content'),'noindex, follow');
  for(const route of ['/about/','/features/','/development/','/guide/','/installation/']) {
   assert.equal(await page.locator(`header nav a[href="${route}"]`).count(),1);
  }
  if(path!=='/intro/') {
   const blocks=(await page.locator('script[type="application/ld+json"]').allTextContents()).map(text=>JSON.parse(text));
   const data=blocks.find(block=>block['@graph']);
   assert.equal(data['@context'],'https://schema.org');
   assert.ok(data['@graph'].some(item=>item['@type']==='WebPage' && item.url===`https://eitr.info${path}`));
   if(path==='/') {
    const software=data['@graph'].find(item=>item['@type']==='SoftwareApplication');
    assert.ok(software.screenshot.length>=1 && software.downloadUrl.endsWith('.iso'));
    const faq=blocks.find(block=>block['@type']==='FAQPage');
    assert.ok(faq.mainEntity.some(item=>/How long does installation take/.test(item.name)));
    assert.equal(await page.locator('meta[property="og:image"]').getAttribute('content'),'https://eitr.info/og/eitr-desktop.jpg');
   }
  }
  const chapter=handbook.find(chapter=>path===`/guide/${chapter.id}/`);
  if(chapter) {
   const expected=await parser.evaluate(blocks=>{
    const document=new DOMParser().parseFromString(blocks.filter(block=>!block.startsWith('<h1>')).join('\n'),'text/html');
    return document.body.textContent.replace(/\s+/g,' ').trim();
   },chapter.blocks);
   const actual=(await page.locator('.doc-copy').textContent()).replace(/\s+/g,' ').trim();
   assert.equal(actual,expected,`${path} must preserve the complete canonical chapter`);
   assert.equal(await page.locator('a[href^="handbook:"]').count(),0);
  }
  for(const width of [390,768,1024,1440]) {
   await page.setViewportSize({width,height:900});
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${path} overflows at ${width}`);
  }
  const anchors=await page.locator('a[href]').evaluateAll(nodes=>nodes.map(node=>({href:node.href,target:node.target,rel:node.rel,download:node.hasAttribute('download')})));
  for(const anchor of anchors) {
   const url=new URL(anchor.href);
   if(!['http:','https:'].includes(url.protocol)) continue;
   if(url.origin!==new URL(site).origin) {
    if(anchor.download) continue;
    assert.equal(anchor.target,'_blank',anchor.href);
    assert.ok(anchor.rel.includes('noopener'),anchor.href);
    continue;
   }
   links++;
   if(!documents.has(url.pathname)) {
    const target=await page.request.get(url.href);
    assert.equal(target.status(),200,url.href);
    documents.set(url.pathname,await target.text());
   }
   if(url.hash) assert.ok(await parser.evaluate(({html,id})=>new DOMParser().parseFromString(html,'text/html').getElementById(id)!==null,{html:documents.get(url.pathname),id:decodeURIComponent(url.hash.slice(1))}),url.href);
  }
 }
 const llms=await page.request.get(new URL('/llms.txt',site).href);
 assert.equal(llms.status(),200);
 const text=await llms.text();
 assert.ok(text.includes('https://eitr.info/development/'));
 assert.ok(text.includes('https://eitr.info/guide/git-accounts/'));
 await context.close();
 console.log(`Passed: sitemap, crawler rules, static metadata, ${links} internal links, external-link behavior and ${publicPaths.length+1} pages without JavaScript.`);
} finally {await browser.close();}
