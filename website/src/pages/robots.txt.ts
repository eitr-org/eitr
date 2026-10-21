import type { APIContext } from 'astro';

export function GET({ site }: APIContext) {
  if (!site) throw new Error('A public site URL is required for robots.txt.');
  return new Response(`# Public pages are available for search. Hosting-level crawler rules also apply.
User-agent: *
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

Sitemap: ${new URL('sitemap.xml', site).href}
`, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}
