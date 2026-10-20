import json
from pathlib import Path
import re
import tomllib
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


class LauncherLayoutTests(unittest.TestCase):
    def test_apps_and_main_share_configured_width(self):
        wrapper = (ROOT / 'walker/bin/walker').read_text()
        self.assertNotIn('apps_width', wrapper)
        self.assertNotIn('--width', wrapper)
        self.assertIn('exec /usr/bin/walker --minheight 1 --maxheight 520 "$@"', wrapper)

    def test_apps_actions_only_open_uninstall_and_back(self):
        config = tomllib.loads((ROOT / 'walker/config.toml').read_text())
        actions = config['providers']['actions']['menus:apps']
        self.assertEqual({action['action'] for action in actions},
                         {'open', 'app_uninstall', 'menus:parent'})
        self.assertEqual(next(action for action in actions if action['action'] == 'open')['bind'], 'Return')

    def test_main_search_keeps_empty_navigation_and_searches_all_menus(self):
        config = tomllib.loads((ROOT / 'walker/config.toml').read_text())
        providers = config['providers']
        # Main itself searches every menu, so it also works after Shift+Backspace.
        self.assertNotIn('sets', providers)
        self.assertEqual(providers['default'], ['menus:apps'])
        main = (ROOT / 'elephant/menus/main.lua').read_text()
        self.assertIn('dofile(paths.code("elephant/scoped-menu.lua"))("main")', main)
        scoped = (ROOT / 'elephant/scoped-menu.lua').read_text()
        self.assertIn('if query and query ~= "" then', scoped)
        self.assertIn('search(name)', scoped)
        self.assertIn('if scope == "main" then return true end', (ROOT / 'elephant/search-index-entries.lua').read_text())
        self.assertIn('elephant/search-index-entries.lua', (ROOT / 'elephant/menus/search-index.lua').read_text())
        entries = json.loads((ROOT / 'elephant/menu-rows/main.json').read_text())
        self.assertTrue(all(entry['subtext'] == '>' and entry['submenu'] for entry in entries))
        wrapper = (ROOT / 'walker/bin/walker').read_text()
        self.assertIn('search-index.py" prepare', wrapper)
        self.assertNotIn('--set', wrapper)
        self.assertIn('--minheight 1 --maxheight 520', wrapper)

    def test_search_and_results_share_the_menu_surface(self):
        layout = ET.parse(ROOT / 'walker/themes/current/layout.xml')
        box = layout.find('.//object[@id="Box"]')
        children = [child.find('object').get('id') for child in box.findall('child')]
        self.assertEqual(children, ['SearchContainer', 'ResultsBox'])
        self.assertIsNotNone(layout.find('.//object[@id="ResultsBox"]//object[@id="List"]'))
        scroll = layout.find('.//object[@id="Scroll"]')
        self.assertEqual(scroll.find('property[@name="propagate-natural-height"]').text, 'true')
        self.assertEqual(scroll.find('property[@name="vexpand"]').text, 'false')
        script = (ROOT / 'walker/scripts/themes/walker.sh').read_text()
        wrapper = script.split('.box-wrapper {', 1)[1].split('}', 1)[0]
        self.assertIn('background: @window_bg_color;', wrapper)
        self.assertIn('border: 1px solid', wrapper)
        surfaces = script.split('.search-container,\n.results-box {', 1)[1].split('}', 1)[0]
        self.assertIn('background: transparent;', surfaces)

    def test_appearance_generator_tracks_bar(self):
        script = (ROOT / 'walker/scripts/themes/walker.sh').read_text()
        self.assertIn('bar-settings.py" get appearance', script)
        self.assertIn('window_alpha="1"', script)
        self.assertIn('.results-box', script)
        surfaces = script.split('.search-container,\n.results-box {', 1)[1].split('}', 1)[0]
        self.assertIn('border: none;', surfaces)

    def test_every_workspace_style_has_its_own_preview(self):
        menu = (ROOT / 'elephant/menus/workspaces.lua').read_text()
        styles = re.search(r'local choices = \{(.*?)\}', menu).group(1)
        names = [name.lower() for name in re.findall(r'"(\w+)"', styles)]
        layout = ET.parse(ROOT / 'walker/themes/current/item_menus-workspaces.xml')
        examples = {style.get('name') for style in layout.iter('class') if style.get('name', '').startswith('example-')}
        css = (ROOT / 'walker/themes/current/workspace-examples.css').read_text()
        for name in names:
            self.assertIn(f'example-{name}', examples, name)
            self.assertIn(f'.workspace-{name} .example-{name}', css, name)

    def test_generated_style_installs_the_stylesheets_it_imports(self):
        script = (ROOT / 'walker/scripts/themes/walker.sh').read_text()
        for imported in re.findall(r'@import url\("([^"/]+)"\)', script):
            self.assertIn(f'walker/themes/current/{imported}" "$WALKER_THEME_DIR/{imported}"', script, imported)


if __name__ == '__main__':
    unittest.main()
