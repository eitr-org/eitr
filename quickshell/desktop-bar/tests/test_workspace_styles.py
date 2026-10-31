from pathlib import Path
import re
import json
import runpy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / "quickshell/desktop-bar"
CHOICES = runpy.run_path(str(ROOT / "tools/choice-lists.py"))
STYLES = [row["id"] for row in CHOICES["load_catalog"]()["workspace_styles"]]


class WorkspaceStyleTests(unittest.TestCase):
    def test_every_style_list_offers_the_same_styles(self):
        self.assertEqual(CHOICES["synchronize"](check=True), [])

    def test_catalog_rejects_duplicate_and_unordered_choices(self):
        import tempfile
        for mutation in ('duplicate', 'order'):
            catalog = CHOICES["load_catalog"]()
            rows = catalog['workspace_styles']
            if mutation == 'duplicate':
                rows.append(rows[0])
            else:
                rows.reverse()
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'choices.json'
                path.write_text(json.dumps(catalog))
                with self.assertRaises(ValueError):
                    CHOICES['load_catalog'](path)

    def test_changed_catalog_detects_every_projection(self):
        catalog = CHOICES['load_catalog']()
        catalog['workspace_styles'].append({'id': 'Test', 'label': 'Test'})
        catalog['lockscreen_designs'].append({'id': 'test', 'label': 'Test'})
        for relative, pattern, replacement in CHOICES['projections'](catalog):
            source = (ROOT / relative).read_text()
            updated, count = re.subn(pattern, lambda match: replacement, source,
                                     flags=re.MULTILINE | re.DOTALL)
            self.assertEqual(count, 1, relative)
            self.assertNotEqual(source, updated, relative)
        self.assertTrue(CHOICES['check_documentation'](catalog))

    def test_documentation_rejects_stale_lists_and_translated_counts(self):
        import shutil
        import tempfile
        catalog = CHOICES['load_catalog']()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            documents = [Path('quickshell/desktop-bar/README.md'),
                         Path('quickshell/lockscreen/README.md')]
            content = Path('quickshell/desktop-bar/handbook/content')
            for name in ('appearance.md', 'desktop-bar.md'):
                documents.extend(path.relative_to(ROOT) for path in (ROOT / content).rglob(name))
            for relative in documents:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, destination)
            for row in catalog['lockscreen_designs']:
                main = root / 'quickshell/lockscreen/themes' / row['id'] / 'Main.qml'
                main.parent.mkdir(parents=True, exist_ok=True)
                main.touch()
            self.assertEqual(CHOICES['check_documentation'](catalog, root), [])
            mutations = [
                ('appearance.md', 'Girl Coffee,', ''),
                ('appearance.md', 'nine shipped', 'eight shipped'),
                ('de/appearance.md', 'neun Designs', 'acht Designs'),
                ('es/appearance.md', 'nueve diseños', 'ocho diseños'),
                ('fr/appearance.md', 'neuf modèles', 'huit modèles'),
                ('pt_BR/appearance.md', 'nove desenhos', 'oito desenhos'),
                ('desktop-bar.md', 'Dots, Glyph', 'Glyph, Dots'),
                ('fr/desktop-bar.md', 'Points, Glyphe', 'Points, Autre, Glyphe'),
            ]
            for relative, old, new in mutations:
                with self.subTest(document=relative, old=old):
                    path = root / content / relative
                    original = path.read_text()
                    self.assertIn(old, original)
                    path.write_text(original.replace(old, new))
                    self.assertTrue(CHOICES['check_documentation'](catalog, root))
                    path.write_text(original)

    def test_styles_are_alphabetical_and_the_menu_fits_them_all(self):
        self.assertEqual(STYLES, sorted(STYLES))
        menu = (BAR / "panels/WorkspaceStyleMenu.qml").read_text()
        self.assertIn("implicitHeight: styles.length * PanelStyle.selectionRowHeight", menu)
        self.assertIn("model: menu.styles", menu)

    def test_active_markers_use_accent_ink_without_a_filled_background(self):
        marker = (BAR / "bar/WorkspaceMarker.qml").read_text()
        self.assertIn("color: marker.active ? marker.accent : marker.foreground", marker)
        self.assertNotIn("color: marker.accent\n", marker)
        self.assertIn('marker.active ? "transparent"', marker)
        css = (ROOT / "walker/themes/current/workspace-examples.css").read_text()
        self.assertNotIn("@workspace_selected_fg_color", css)
        self.assertIn("box-shadow: none", css)

    def test_runes_cover_all_ten_workspaces_in_futhark_order(self):
        marker = (BAR / "bar/WorkspaceMarker.qml").read_text()
        runes = re.search(r'readonly property var runes: \[(.*?)\]', marker)[1]
        self.assertEqual(re.findall(r'"(.)"', runes), list("ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾ"))
        self.assertIn('"Noto Sans Runic"', marker)
        self.assertIn("noto-fonts", (ROOT / "distro/packages.txt").read_text().split())

    def test_runes_are_the_default_when_nothing_is_saved(self):
        import json
        import os
        import subprocess
        import tempfile
        defaults = json.loads((ROOT / "distro/defaults/quickshell/desktop-bar/workspace-style.json").read_text())
        self.assertEqual(defaults["style"], "Runes")
        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run([sys.executable, str(BAR / "scripts/workspace-style.py"), "current"],
                                    env={**os.environ, "HOME": home, "XDG_CONFIG_HOME": home + "/.config"},
                                    capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), "Runes")
        self.assertIn('local current = "Runes"', (ROOT / "elephant/menus/workspaces.lua").read_text())
        self.assertIn('property string workspaceStyle: "Runes"', (BAR / "shell.qml").read_text())


if __name__ == "__main__":
    unittest.main()
