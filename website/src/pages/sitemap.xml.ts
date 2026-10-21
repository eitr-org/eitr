import type { APIContext } from 'astro';
import { sitePages } from '../data/site-pages';

export function GET({ site }: APIContext) {
  if (!site) throw new Error('A public site URL is required for the sitemap.');
  const entries = Object.values(sitePages).map(page => `<url><loc>${new URL(page.path, site).href}</loc></url>`).join('\n');
  return new Response(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries}\n</urlset>\n`, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
}
