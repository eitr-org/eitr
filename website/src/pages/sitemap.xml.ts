import type { APIContext } from 'astro';
import { languageCodes, localizedPath, hasLocalizedPage } from '../i18n';
import { publicPages } from '../data/site-pages';

export function GET({ site }: APIContext) {
  if (!site) throw new Error('A public site URL is required for the sitemap.');
  const entries = publicPages.flatMap(page => hasLocalizedPage(page.path) ? languageCodes.map(language => ({path: localizedPath(page.path, language)})) : [page]).map(page => `<url><loc>${new URL(page.path, site).href}</loc></url>`).join('\n');
  return new Response(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries}\n</urlset>\n`, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
}
