import { anchorHeadings, matchingHeadingStructure } from './handbook-headings.mjs';
import { createHash } from 'node:crypto';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { localizedPath, type Language } from '../i18n';
import pt from '../../../quickshell/desktop-bar/handbook/catalogs/pt_BR.json';
import es from '../../../quickshell/desktop-bar/handbook/catalogs/es.json';
import de from '../../../quickshell/desktop-bar/handbook/catalogs/de.json';
import fr from '../../../quickshell/desktop-bar/handbook/catalogs/fr.json';
import catalog from '../../../quickshell/desktop-bar/handbook/catalog.json';
import definitions from '../../../quickshell/desktop-bar/handbook/chapters.json';

const repository = 'https://github.com/eitr-org/eitr/blob/main/';
const definitionsById = new Map(definitions.map(chapter => [chapter.id, chapter]));
const chaptersById = new Map(catalog.chapters.map(chapter => [chapter.id, chapter]));

const translatedCatalogs = {'pt-br': pt, es, de, fr};
const repositoryRoot = pathToFileURL(resolve(existsSync('quickshell/desktop-bar/handbook/chapters.json') ? '.' : '..') + '/');
export function chaptersFor(language: Language = 'en') {
  const desktopLocale = language === 'pt-br' ? 'pt_BR' : language;
  const folder = new URL(`quickshell/desktop-bar/handbook/content/${desktopLocale}/`, repositoryRoot);
  const manifest = new URL('source-hashes.json', folder);
  const hashes = language !== 'en' && existsSync(manifest) ? JSON.parse(readFileSync(manifest, 'utf8')) : {};
  return catalog.chapters.map(english => {
    const candidate = language === 'en' ? undefined : translatedCatalogs[language].chapters.find(entry => entry.id === english.id);
    const definition = definitionsById.get(english.id);
    if (!definition) throw new Error(`No Handbook definition for ${english.id}`);
    const current = 'source' in definition
      ? existsSync(new URL(`${english.id}.md`, folder)) && hashes[english.id] === createHash('sha256').update(readFileSync(new URL(definition.source, repositoryRoot))).digest('hex')
      : true;
    // A changed heading hierarchy cannot safely inherit English anchors by position.
    const translated = candidate?.sourceLocale === desktopLocale && current
      && matchingHeadingStructure(english.blocks.join('\n'), candidate.blocks.join('\n'));
    const chapter = translated ? candidate : english;
    // These are the trusted, generated Handbook blocks, not visitor-supplied HTML.
    // Keep their prose, commands and tables intact; adapt only navigation for the web.
    let html = chapter.blocks.filter(block => !block.startsWith('<h1>')).join('\n');
    for (const linked of catalog.chapters) {
      html = html.replace(new RegExp(`href="handbook:${linked.id}(#[^"]*)?"`, 'g'),
        (_attribute, fragment = '') => `href="${localizedPath(`/guide/${linked.id}/`, language)}${fragment}"`);
    }
    if (html.includes('href="handbook:')) throw new Error(`Unresolved Handbook link in ${chapter.id}`);
    const anchored = anchorHeadings(html, english.blocks.join('\n'));
    html = anchored.html;
    const sections = anchored.sections;
    const source = 'source' in definition ? definition.source : 'elephant/shortcut-reference.json';
    html = html.replaceAll('href="LINUX-VM-TESTING.md"', `href="${repository}distro/LINUX-VM-TESTING.md"`);
    html = html.replaceAll('<pre>', '<pre tabindex="0">');
    html = html.replaceAll('href="https://', 'target="_blank" rel="noopener noreferrer" href="https://');
    return {
      id: chapter.id,
      path: localizedPath(`/guide/${chapter.id}/`, language),
      fallback: language !== 'en' && !translated,
      contentLanguage: translated ? (language === 'pt-br' ? 'pt-BR' : language) : 'en',
      title: chapter.title,
      summary: chapter.summary,
      html,
      source: repository + source,
      markdown: chapter.markdown,
      sections,
      generated: !('source' in definition),
    };
});
}
export const handbookChapters = chaptersFor();

// Fail the build if the website is given a partial or outdated chapter registry.
if (definitions.some(chapter => !chaptersById.has(chapter.id))) {
  throw new Error('Rebuild the Handbook before building its public reader.');
}
