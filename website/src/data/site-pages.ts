import en from '../i18n/en.json';
import { handbookChapters } from './handbook';

// Public information pages, shared by metadata, navigation and the sitemap.
export const sitePages = {
  home: { path: '/', label: en.metadata.home_label, title: en.metadata.home_title, description: en.metadata.home_description },
  screenshots: { path: '/screenshots/', label: en.metadata.screenshots_label, title: en.metadata.screenshots_title, description: en.metadata.screenshots_description },
  about: { path: '/about/', label: en.metadata.about_label, title: en.metadata.about_title, description: en.metadata.about_description },
  features: { path: '/features/', label: en.metadata.features_label, title: en.metadata.features_title, description: en.metadata.features_description },
  development: { path: '/development/', label: en.metadata.development_label, title: en.metadata.development_title, description: en.metadata.development_description },
  installation: { path: '/installation/', label: en.metadata.installation_label, title: en.metadata.installation_title, description: en.metadata.installation_description },
  guide: { path: '/guide/', label: en.metadata.guide_label, title: en.metadata.guide_title, description: en.metadata.guide_description },
  privacy: { path: '/privacy/', label: en.metadata.privacy_label, title: en.metadata.privacy_title, description: en.metadata.privacy_description },
} as const;

export const publicPages = [...Object.values(sitePages), ...handbookChapters.map(chapter => ({path: chapter.path, label: chapter.title, title: `${chapter.title} — Eitr Linux Handbook`, description: chapter.summary}))];
