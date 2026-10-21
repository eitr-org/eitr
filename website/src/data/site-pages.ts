// Public information pages, shared by metadata, navigation and the sitemap.
export const sitePages = {
  home: { path: '/', label: 'Home', title: 'Eitr Linux — An Arch-based distribution with Hyprland', description: 'Eitr Linux brings Hyprland, a custom Quickshell desktop, graphical controls, developer tools, offline installation and built-in recovery into one Arch-based distribution.' },
  about: { path: '/about/', label: 'About Eitr Linux', title: 'About Eitr Linux — An Arch-based Linux distribution', description: 'What Eitr Linux is, who it is for, how it builds on Arch Linux, and the scope of its current beta.' },
  features: { path: '/features/', label: 'Features', title: 'Eitr Linux features — Desktop, development and recovery', description: 'Explore Eitr’s native desktop panels, AI assistant collaboration, cloud account tools, themes, gaming, offline Handbook and system recovery.' },
  installation: { path: '/installation/', label: 'Installation & hardware', title: 'Install Eitr Linux — ISO, hardware and beta limitations', description: 'Download the Eitr Linux ISO, plan an x86_64 UEFI installation, and understand tested hardware, NVIDIA drivers, VM testing and current limitations.' },
  guide: { path: '/guide/', label: 'Guides & Handbook', title: 'Eitr Linux guides — Installation, VM testing and recovery', description: 'Canonical Eitr Linux installation, Linux and Mac VM testing, recovery and offline Handbook guides.' },
  privacy: { path: '/privacy/', label: 'Privacy', title: 'Eitr Linux privacy — Reports and website data', description: 'How Eitr Linux handles optional problem reports and what the Eitr website collects.' },
} as const;
