const headingPattern = /<(h[2-6])>([\s\S]*?)<\/\1>/g;

export function headings(html) {
  const usedIds = new Set();
  return Array.from(html.matchAll(headingPattern), ([, level, title]) => {
    const stem = title.replace(/<[^>]*>/g, '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
      .replaceAll('&amp;', 'and').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'section';
    let id = stem;
    let suffix = 2;
    while (usedIds.has(id)) id = `${stem}-${suffix++}`;
    usedIds.add(id);
    return {level, title, id};
  });
}

export function matchingHeadingStructure(english, translated) {
  const source = headings(english);
  const target = headings(translated);
  return source.length === target.length && source.every((heading, index) => heading.level === target[index].level);
}

export function anchorHeadings(html, english) {
  if (!matchingHeadingStructure(english, html)) throw new Error('Handbook heading structure differs from English');
  const source = headings(english);
  const sections = [];
  let index = 0;
  const anchored = html.replace(headingPattern, (_heading, level, title) => {
    const {id} = source[index++];
    if (level === 'h2') sections.push({id, title});
    return `<${level} id="${id}">${title}</${level}>`;
  });
  return {html: anchored, sections};
}
