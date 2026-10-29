import en from './en.json';
import pt from './pt-br.json';
import es from './es.json';
import de from './de.json';
import fr from './fr.json';
export const languages = {en: 'English', 'pt-br': 'Português (Brasil)', es: 'Español', de: 'Deutsch', fr: 'Français'};
export type Language = keyof typeof languages;
export const languageCodes = Object.keys(languages) as Language[];
const catalogs: Record<Language, Record<string, Record<string, string>>> = {en, 'pt-br': pt, es, de, fr};
export function languageFor(path: string): Language {
  const prefix = path.split('/')[1];
  return Object.hasOwn(languages, prefix) ? prefix as Language : 'en';
}
export function unprefixed(path: string) {
  return path.replace(/^\/(pt-br|es|de|fr)(?=\/|$)/, '') || '/';
}
export const pagePaths = ['/', '/about/', '/features/', '/development/', '/installation/', '/privacy/', '/screenshots/', '/intro/', '/guide/'];
export function hasLocalizedPage(path: string) {
  return pagePaths.includes(path) || /^\/guide\/[a-z0-9-]+\/$/.test(path);
}
export function localizedPath(path: string, language: Language) {
  const base = unprefixed(path);
  const pathname = base.split(/[?#]/)[0];
  return language === 'en' || !hasLocalizedPage(pathname) ? base : `/${language}${base}`;
}
export function localizeLinks(html: string, language: Language) {
  return html.replace(/href="(\/[^"\s]*)"/g, (_attribute, path: string) => `href="${localizedPath(path, language)}"`);
}
export function translator(path: string, scope: string) {
  const language = languageFor(path);
  return (key: string, values: Record<string, string | number> = {}) => {
    const text = catalogs[language][scope]?.[key] ?? catalogs.en[scope]?.[key];
    if (text === undefined) throw new Error(`Unknown website message: ${scope}.${key}`);
    return text.replace(/\{(\w+)\}/g, (placeholder, name: string) => String(values[name] ?? placeholder));
  };
}
