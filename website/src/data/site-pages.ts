import { handbookChapters } from './handbook';

// Public information pages, shared by metadata, navigation and the sitemap.
export const sitePages = {
  home: { path: '/', label: 'Home', title: 'Eitr Linux — Keyboard-first Arch, an integrated desktop', description: 'Eitr Linux brings Hyprland, Quickshell, curated developer tools, AI coding agents, cloud and Git workflows, and system recovery into one keyboard-first Arch Linux environment.' },
  about: { path: '/about/', label: 'About Eitr Linux', title: 'About Eitr Linux — An Arch-based Linux distribution', description: 'What Eitr Linux is, who it is for, how it builds on Arch Linux, and the scope of its current beta.' },
  features: { path: '/features/', label: 'Features', title: 'Eitr Linux features — Desktop, development and recovery', description: 'Explore Eitr’s native desktop panels, AI assistant collaboration, cloud account tools, repeating reminders, organization profiles, themes, gaming, offline Handbook and system recovery.' },
  development: { path: '/development/', label: 'Development', title: 'Develop with Eitr Linux — Editors, AI, cloud and Git workflows', description: 'Explore Eitr’s included terminal environment, optional editors and toolchains, AI coding agents, explicit cloud contexts, Git identities, monitoring dashboards and Git plugins.' },
  installation: { path: '/installation/', label: 'Installation & hardware', title: 'Install Eitr Linux — ISO, hardware and beta limitations', description: 'Download the Eitr Linux ISO, plan an x86_64 UEFI or unattended installation with organization profiles, and understand tested hardware, NVIDIA drivers, VM testing and current limitations.' },
  guide: { path: '/guide/', label: 'Handbook & guides', title: 'Eitr Linux Handbook — Desktop, development and system guides', description: 'Read Eitr’s Handbook online: keyboard shortcuts, applications, development, AI agents, Git identities, cloud workflows, desktop settings and recovery.' },
  privacy: { path: '/privacy/', label: 'Privacy', title: 'Eitr Linux privacy — Reports and website data', description: 'How Eitr Linux handles optional problem reports and what the Eitr website collects.' },
} as const;

export const publicPages = [...Object.values(sitePages), ...handbookChapters.map(chapter => ({path: chapter.path, label: chapter.title, title: `${chapter.title} — Eitr Linux Handbook`, description: chapter.summary}))];
