import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { test } from 'node:test';

const dist = new URL('../dist/', import.meta.url);
const policy = "default-src 'self'; script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; media-src 'self'; connect-src 'self' https://download.eitr.info https://cloudflareinsights.com; object-src 'none'; base-uri 'self'; form-action 'self'; frame-src 'none'; frame-ancestors 'none'";
const expected = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Strict-Transport-Security': 'max-age=31536000',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'Content-Security-Policy': policy,
};

function* files(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = new URL(entry.name, directory);
    if (entry.isDirectory()) yield* files(new URL(`${entry.name}/`, directory));
    else yield path;
  }
}

test('production assets carry the universal security headers', () => {
  const headers = readFileSync(new URL('_headers', dist), 'utf8');
  assert.equal(headers, readFileSync(new URL('../public/_headers', import.meta.url), 'utf8'));
  const lines = headers.trimEnd().split('\n');
  assert.equal(lines.shift(), '/*');
  const actual = {};
  for (const line of lines) {
    assert.ok(line.length <= 2000, 'Cloudflare header line limit');
    const match = line.match(/^  ([\w-]+): (.+)$/);
    assert.ok(match, line);
    actual[match[1]] = match[2];
  }
  assert.deepEqual(actual, expected);
});

test('built resources stay within the policy and keep the documented inline exceptions', () => {
  let pages = 0;
  let inlineScripts = 0;
  let structuredData = 0;
  let inlineStyles = 0;
  let fonts = 0;
  let audio = 0;
  let counter = false;
  for (const path of files(dist)) {
    if (/\.woff2?$/.test(path.pathname)) fonts++;
    if (/\.mp3$/.test(path.pathname)) audio++;
    if (/\.js$/.test(path.pathname)) {
      const script = readFileSync(path, 'utf8');
      if (script.includes('https://download.eitr.info/stats.json')) counter = true;
    }
    if (!path.pathname.endsWith('.html')) continue;
    pages++;
    const html = readFileSync(path, 'utf8');
    inlineScripts += [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>/g)].length;
    structuredData += [...html.matchAll(/<script type="application\/ld\+json"/g)].length;
    inlineStyles += [...html.matchAll(/<style\b|\sstyle=/g)].length;
    for (const match of html.matchAll(/<(script|img|audio|source|link)\b[^>]*>/g)) {
      const tag = match[0];
      if (match[1] === 'link' && !/rel="(?:stylesheet|preload|modulepreload|icon)"/.test(tag)) continue;
      const source = tag.match(/(?:src|href)="([^"]+)"/)?.[1];
      if (!source) continue;
      assert.ok(new URL(source, 'https://eitr.info/').origin === 'https://eitr.info' || source.startsWith('data:image/'), source);
    }
  }
  assert.ok(pages > 0 && inlineScripts > 0 && structuredData > 0 && inlineStyles > 0);
  assert.ok(fonts > 0 && audio > 0 && counter);
});
