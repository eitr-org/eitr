import catalog from '../../../quickshell/desktop-bar/handbook/catalog.json';
import definitions from '../../../quickshell/desktop-bar/handbook/chapters.json';

const repository = 'https://github.com/eitr-org/eitr/blob/main/';
const definitionsById = new Map(definitions.map(chapter => [chapter.id, chapter]));
const chaptersById = new Map(catalog.chapters.map(chapter => [chapter.id, chapter]));

export const handbookChapters = catalog.chapters.map(chapter => {
  const definition = definitionsById.get(chapter.id);
  if (!definition) throw new Error(`No Handbook definition for ${chapter.id}`);
  // These are the trusted, generated Handbook blocks, not visitor-supplied HTML.
  // Keep their prose, commands and tables intact; adapt only navigation for the web.
  let html = chapter.blocks.filter(block => !block.startsWith('<h1>')).join('\n');
  for (const linked of catalog.chapters) {
    html = html.replaceAll(`href="handbook:${linked.id}"`, `href="/guide/${linked.id}/"`);
  }
  if (html.includes('href="handbook:')) throw new Error(`Unresolved Handbook link in ${chapter.id}`);
  const sections: {id: string; title: string}[] = [];
  const usedIds = new Set<string>();
  html = html.replace(/<(h[2-6])>([^<]+)<\/\1>/g, (_heading, level: string, title: string) => {
    const stem = title.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
      .replaceAll('&amp;', 'and').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'section';
    let id = stem;
    let suffix = 2;
    while (usedIds.has(id)) id = `${stem}-${suffix++}`;
    usedIds.add(id);
    if (level === 'h2') sections.push({id, title});
    return `<${level} id="${id}">${title}</${level}>`;
  });
  const source = 'source' in definition ? definition.source : 'walker/scripts/menus/shortcuts.sh';
  html = html.replaceAll('href="LINUX-VM-TESTING.md"', `href="${repository}distro/LINUX-VM-TESTING.md"`);
  html = html.replaceAll('<pre>', '<pre tabindex="0">');
  html = html.replaceAll('href="https://', 'target="_blank" rel="noopener noreferrer" href="https://');
  return {
    id: chapter.id,
    path: `/guide/${chapter.id}/`,
    title: chapter.title,
    summary: chapter.summary,
    html,
    source: repository + source,
    markdown: chapter.markdown,
    sections,
    generated: !('source' in definition),
  };
});

// Fail the build if the website is given a partial or outdated chapter registry.
if (definitions.some(chapter => !chaptersById.has(chapter.id))) {
  throw new Error('Rebuild the Handbook before building its public reader.');
}
