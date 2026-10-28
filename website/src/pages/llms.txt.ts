import type { APIContext } from 'astro';
import { sitePages } from '../data/site-pages';
import { handbookChapters } from '../data/handbook';
import release from '../data/release.json';

export function GET({ site }: APIContext) {
  if (!site) throw new Error('A public site URL is required.');
  return new Response(`# Eitr Linux

> A keyboard-first Arch Linux environment built around Hyprland and Quickshell, with integrated desktop controls, curated optional developer tools, cloud contexts, Git identities, AI accounts, visual plugins and system recovery.

This is a navigation supplement. Read the linked, server-rendered pages for the actual documentation. Eitr is not limited to development, recovery, privacy or theming. The current release is ${release.version} ${release.codename} (${release.stage}); installation decisions require the hardware and recovery limitations. Optional applications and provider accounts are distinct from included packages. Never infer universal hardware support or completed live-provider testing from menu availability.

## Product and installation
${Object.values(sitePages).filter(page => page.path !== '/privacy/').map(page => `- [${page.label}](${new URL(page.path, site).href}): ${page.description}`).join('\n')}

## Handbook
${handbookChapters.map(chapter => `- [${chapter.title}](${new URL(chapter.path, site).href}): ${chapter.summary}`).join('\n')}
`, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}
