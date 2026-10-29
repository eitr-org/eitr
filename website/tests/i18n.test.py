"""Check the source catalogs and the production output without launching a browser."""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ElementTree

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ('en', 'pt-br', 'es', 'de', 'fr')
PAGES = ('', 'about/', 'features/', 'development/', 'installation/', 'privacy/', 'screenshots/', 'guide/', 'intro/')


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
                if language != 'en':
                    html = file.read_text()
                    for english in ['Skip to content', 'Previous screenshot', 'Previous theme', 'Main navigation', 'On this page']:
                        self.assertNotIn(english, html, (path, english))
        for path, document in documents.items():
            for anchor in document.attributes('a'):
                target = urlsplit(anchor.get('href', ''))
                if target.scheme or target.netloc:
                    continue
                pathname = target.path or path
                if not pathname.startswith('/'):
                    continue
                file = ROOT / 'dist' / pathname.lstrip('/')
                if pathname.endswith('/'):
                    file /= 'index.html'
                self.assertTrue(file.is_file(), (path, anchor))
                if target.fragment and file.suffix == '.html':
                    linked = documents.get(pathname) or Document(file)
                    self.assertIn(unquote(target.fragment), linked.ids, (path, anchor))

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
