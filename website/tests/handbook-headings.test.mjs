import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { anchorHeadings, matchingHeadingStructure } from '../src/data/handbook-headings.mjs';

test('translated headings inherit English IDs by position and level, including duplicate and inline headings', () => {
  const english = '<h2>AI assistants</h2><h3>Use <code>Git</code></h3><h2>AI assistants</h2>';
  const translated = '<h2>Assistentes de IA</h2><h3>Usar <code>Git</code></h3><h2>Assistentes de IA</h2>';
  const result = anchorHeadings(translated, english);
  assert.deepEqual(result.sections, [{id: 'ai-assistants', title: 'Assistentes de IA'}, {id: 'ai-assistants-2', title: 'Assistentes de IA'}]);
  assert.ok(result.html.includes('<h3 id="use-git">Usar <code>Git</code></h3>'));
});

test('missing, extra or changed heading levels require chapter fallback', () => {
  const english = '<h2>First</h2><h3>Second</h3>';
  for (const translated of ['<h2>Premier</h2>', '<h2>Premier</h2><h2>Deuxième</h2>', english + '<h2>Extra</h2>']) {
    assert.equal(matchingHeadingStructure(english, translated), false);
    assert.throws(() => anchorHeadings(translated, english), /structure differs/);
  }
});

test('reviewed catalogs retain the English heading structure', () => {
  const book = new URL('../../quickshell/desktop-bar/handbook/', import.meta.url);
  const english = JSON.parse(readFileSync(new URL('catalog.json', book))).chapters;
  for (const locale of ['pt_BR', 'es', 'de', 'fr']) {
    const translated = JSON.parse(readFileSync(new URL(`catalogs/${locale}.json`, book))).chapters;
    for (const chapter of english) {
      const target = translated.find(candidate => candidate.id === chapter.id);
      assert.ok(target, `${locale}/${chapter.id} missing`);
      assert.ok(matchingHeadingStructure(chapter.blocks.join('\n'), target.blocks.join('\n')), `${locale}/${chapter.id}: heading structure needs review`);
    }
  }
});
