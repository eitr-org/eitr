import en from './en.json';
import pt from './pt-br.json';
import es from './es.json';
import de from './de.json';
import fr from './fr.json';
import ja from './ja.json';
import zh from './zh-cn.json';
import ko from './ko.json';
export const languages = {en: 'English', 'pt-br': 'Português (Brasil)', es: 'Español', de: 'Deutsch', fr: 'Français', ja: '日本語', 'zh-cn': '简体中文', ko: '한국어'};
export type Language = keyof typeof languages;
export const languageCodes = Object.keys(languages) as Language[];
const catalogs: Record<Language, Record<string, Record<string, string>>> = {en, 'pt-br': pt, es, de, fr, ja, 'zh-cn': zh, ko};
/** The BCP 47 tag for `lang` and `hreflang`. */
export function htmlLanguage(language: Language) {
  return ({'pt-br': 'pt-BR', 'zh-cn': 'zh-CN'} as Record<string, string>)[language] ?? language;
}
/** The desktop's locale name, as in the Handbook catalogs. */
export function desktopLocale(language: Language) {
  return ({'pt-br': 'pt_BR', 'zh-cn': 'zh_CN'} as Record<string, string>)[language] ?? language;
}
/** The short code the language menu shows. */
export function languageBadge(language: Language) {
  return language.split('-')[0].toUpperCase();
}
/** Japanese, Chinese and Korean set without Latin capitals and letter-spacing. */
export function isCjk(language: Language) {
  return ['ja', 'zh-cn', 'ko'].includes(language);
}
export function languageFor(path: string): Language {
  const prefix = path.split('/')[1];
  return Object.hasOwn(languages, prefix) ? prefix as Language : 'en';
}
export function unprefixed(path: string) {
  return path.replace(/^\/(pt-br|es|de|fr|ja|zh-cn|ko)(?=\/|$)/, '') || '/';
}
export const pagePaths = ['/', '/about/', '/features/', '/whats-new/', '/development/', '/installation/', '/privacy/', '/screenshots/', '/intro/', '/guide/'];
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
