"""Check the source catalogs and the production output without launching a browser."""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit, urljoin
import xml.etree.ElementTree as ElementTree

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ('en', 'pt-br', 'es', 'de', 'fr')
CHAPTERS = json.loads((ROOT.parent / 'quickshell/desktop-bar/handbook/chapters.json').read_text())
PAGES = ('', 'about/', 'features/', 'development/', 'installation/', 'privacy/', 'screenshots/', 'guide/', 'intro/') + tuple(f'guide/{chapter["id"]}/' for chapter in CHAPTERS)


class Document(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.ids = set()
        self.feed(path.read_text())

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        self.tags.append((tag, attributes))
        if 'id' in attributes:
            self.ids.add(attributes['id'])

    def attributes(self, tag, **matching):
        return [attributes for name, attributes in self.tags if name == tag
                and all(attributes.get(key) == value for key, value in matching.items())]


class WebsiteTranslations(unittest.TestCase):
    def test_catalogs_and_placeholders(self):
        english = json.loads((ROOT / 'src/i18n/en.json').read_text())
        placeholders = lambda text: Counter(re.findall(r'\{\w+\}', text))
        for language in LANGUAGES:
            catalog = json.loads((ROOT / f'src/i18n/{language}.json').read_text())
            self.assertEqual(catalog.keys(), english.keys(), language)
            for scope, messages in english.items():
                self.assertEqual(catalog[scope].keys(), messages.keys(), (language, scope))
                for key, source in messages.items():
                    text = catalog[scope][key]
                    self.assertTrue(text.strip(), (language, scope, key))
                    self.assertEqual(placeholders(text), placeholders(source), (language, scope, key))
                    self.assertNotIn('<script', text)

    def test_built_routes_metadata_and_links(self):
        documents = {}
        for language in LANGUAGES:
            prefix = '' if language == 'en' else f'{language}/'
            for page in PAGES:
                path = f'/{prefix}{page}'
                file = ROOT / f'dist/{prefix}{page}index.html'
                self.assertTrue(file.is_file(), path)
                document = Document(file)
                documents[path] = document
                self.assertEqual(document.attributes('html')[0]['lang'], 'pt-BR' if language == 'pt-br' else language)
                self.assertEqual(len(document.attributes('h1')), 1, path)
                self.assertEqual(document.attributes('link', rel='canonical')[0]['href'], f'https://eitr.info{path}')
                self.assertGreater(len(document.attributes('meta', name='description')[0]['content']), 40, path)
                alternates = {attributes['hreflang']: attributes['href'] for attributes in document.attributes('link', rel='alternate')}
                expected = {('pt-BR' if locale == 'pt-br' else locale): f'https://eitr.info/{"" if locale == "en" else locale + "/"}{page}' for locale in LANGUAGES}
                expected['x-default'] = f'https://eitr.info/{page}'
                self.assertEqual(alternates, expected, path)
                self.assertEqual(bool(document.attributes('meta', name='robots')), page == 'intro/', path)
                switches = [attributes for attributes in document.attributes('a') if 'data-language' in attributes]
                self.assertEqual(len(switches), 5, path)
                for switch in switches:
                    locale = switch['data-language']
                    self.assertEqual(switch['href'], f'/{"" if locale == "en" else locale + "/"}{page}')
                if language != 'en' and page.count('/') <= 1:
                    html = file.read_text()
                    for english in ['Skip to content', 'Previous screenshot', 'Previous theme', 'Main navigation', 'On this page']:
                        self.assertNotIn(english, html, (path, english))
        for path, document in documents.items():
            for anchor in document.attributes('a'):
                target = urlsplit(urljoin(f'https://eitr.info{path}', anchor.get('href', '')))
                if target.scheme not in ('http', 'https') or target.netloc != 'eitr.info':
                    continue
                pathname = unquote(target.path)
                file = ROOT / 'dist' / pathname.lstrip('/')
                if pathname.endswith('/'):
                    file /= 'index.html'
                self.assertTrue(file.is_file(), (path, anchor))
                if target.fragment and file.suffix == '.html':
                    linked = documents.get(pathname) or Document(file)
                    self.assertIn(unquote(target.fragment), linked.ids, (path, anchor))

    def test_every_localized_fragment_resolves(self):
        documents = {}
        for language in LANGUAGES[1:]:
            pages = list((ROOT / 'dist' / language).rglob('*.html'))
            self.assertTrue(pages, f'Build localized pages before testing: {language}')
            for file in pages:
                path = '/' + file.relative_to(ROOT / 'dist').as_posix()
                path = path.removesuffix('index.html')
                document = Document(file)
                for anchor in document.attributes('a'):
                    target = urlsplit(urljoin(f'https://eitr.info{path}', anchor.get('href', '')))
                    if target.netloc != 'eitr.info' or target.scheme not in ('http', 'https') or not target.fragment:
                        continue
                    target_file = ROOT / 'dist' / unquote(target.path).lstrip('/')
                    if target.path.endswith('/'):
                        target_file /= 'index.html'
                    self.assertTrue(target_file.is_file(), (path, anchor))
                    if target_file not in documents:
                        documents[target_file] = Document(target_file)
                    self.assertIn(unquote(target.fragment), documents[target_file].ids, (path, anchor))

    def test_localized_heading_ids_match_english(self):
        for chapter in CHAPTERS:
            suffix = f'guide/{chapter["id"]}/index.html'
            english = Document(ROOT / f'dist/{suffix}')
            source = [(tag, attributes.get('id')) for tag, attributes in english.tags if re.fullmatch(r'h[2-6]', tag)]
            for language in LANGUAGES[1:]:
                localized = Document(ROOT / f'dist/{language}/{suffix}')
                target = [(tag, attributes.get('id')) for tag, attributes in localized.tags if re.fullmatch(r'h[2-6]', tag)]
                self.assertEqual(target, source, (language, chapter['id']))

    def test_reviewed_chapter_content(self):
        import hashlib
        book = ROOT.parent / 'quickshell/desktop-bar/handbook'
        english = json.loads((book / 'catalog.json').read_text())['chapters']
        for language in LANGUAGES[1:]:
            desktop = 'pt_BR' if language == 'pt-br' else language
            catalog = json.loads((book / f'catalogs/{desktop}.json').read_text())['chapters']
            hashes = json.loads((book / f'content/{desktop}/source-hashes.json').read_text())
            for definition, source in zip(CHAPTERS, english):
                candidate = next(chapter for chapter in catalog if chapter['id'] == source['id'])
                fresh = 'source' not in definition or (
                    (book / f'content/{desktop}/{source["id"]}.md').is_file()
                    and hashes.get(source['id']) == hashlib.sha256((ROOT.parent / definition['source']).read_bytes()).hexdigest())
                levels = lambda chapter: re.findall(r'<(h[2-6])>', '\n'.join(chapter['blocks']))
                translated = candidate.get('sourceLocale') == desktop and fresh and levels(source) == levels(candidate)
                expected = candidate if translated else source
                output = ROOT / f'dist/{language}/guide/{source["id"]}/index.html'
                document = Document(output)
                html = output.read_text()
                self.assertIn(expected['title'], html)
                self.assertEqual('data-translation-fallback' in html, not translated)
                self.assertEqual(document.attributes('div', **{'class': 'doc-copy'})[0]['lang'], ('pt-BR' if language == 'pt-br' else language) if translated else 'en')
                class Text(HTMLParser):
                    def __init__(self, markup):
                        super().__init__()
                        self.parts = []
                        self.feed(markup)

                    def handle_data(self, text):
                        self.parts.append(text)

                self.assertIn(''.join(Text(expected['blocks'][1]).parts), ''.join(Text(html).parts))

    def test_sitemap(self):
        tree = ElementTree.parse(ROOT / 'dist/sitemap.xml')
        urls = [entry.text for entry in tree.findall('.//{*}loc')]
        self.assertEqual(len(urls), len(set(urls)))
        for language in LANGUAGES:
            prefix = '' if language == 'en' else f'{language}/'
            for page in PAGES:
                url = f'https://eitr.info/{prefix}{page}'
                self.assertEqual(url in urls, page != 'intro/', url)
        for url in urls:
            self.assertTrue(url.startswith('https://eitr.info/'), url)
            path = ROOT / 'dist' / urlsplit(url).path.lstrip('/') / 'index.html'
            self.assertTrue(path.is_file(), url)


if __name__ == '__main__':
    unittest.main()
