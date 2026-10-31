"""Provider coverage and byte parity for generated Walker row layouts."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('walker_xml', ROOT / 'tools/walker-xml.py')
walker_xml = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(walker_xml)


class WalkerXmlTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / 'elephant/menus', self.root / 'elephant/menus')
        self.directory = self.root / 'walker/themes/current'
        shutil.copytree(ROOT / 'walker/themes/current', self.directory)

    def test_repository_is_current(self):
        self.assertEqual(walker_xml.generate(ROOT, check=True), [])

    def test_check_detects_drift_missing_and_unexpected_without_writing(self):
        target = self.directory / 'item_menus-settings.xml'
        target.write_bytes(b'drift')
        (self.directory / 'item_websearch.xml').unlink()
        (self.directory / 'item_menus-orphan.xml').write_bytes(b'orphan')
        errors = walker_xml.generate(self.root, check=True)
        self.assertEqual(len(errors), 3)
        self.assertEqual(target.read_bytes(), b'drift')
        self.assertFalse((self.directory / 'item_websearch.xml').exists())

    def test_new_provider_is_discovered_and_generation_is_idempotent(self):
        (self.root / 'elephant/menus/new-menu.lua').write_text('Name = "new-menu"\n')
        self.assertTrue(any('item_menus-new-menu.xml' in error
                            for error in walker_xml.generate(self.root, check=True)))
        self.assertEqual(walker_xml.generate(self.root), [])
        self.assertEqual((self.directory / 'item_menus-new-menu.xml').read_bytes(),
                         (self.directory / 'item_menus-main.xml').read_bytes())
        before = {path.name: path.read_bytes() for path in self.directory.glob('*.xml')}
        self.assertEqual(walker_xml.generate(self.root), [])
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.directory.glob('*.xml')})

    def test_both_templates_propagate_and_custom_layout_is_preserved(self):
        custom = (self.directory / 'item_menus-workspaces.xml').read_bytes()
        for template in ('item.xml', 'item_menus-main.xml'):
            path = self.directory / template
            path.write_bytes(path.read_bytes() + b'\n')
        self.assertEqual(walker_xml.generate(self.root), [])
        for name, template in walker_xml.layouts(self.root).items():
            self.assertEqual((self.directory / name).read_bytes(), (self.directory / template).read_bytes())
        self.assertEqual((self.directory / 'item_menus-workspaces.xml').read_bytes(), custom)

    def test_description_and_submenu_widgets_remain_in_canonical_menu_row(self):
        tree = ET.parse(self.directory / 'item_menus-main.xml')
        identifiers = {element.get('id') for element in tree.iter('object')}
        self.assertTrue({'ItemText', 'ItemSubtext', 'SubmenuMarker'} <= identifiers)
        marker = tree.find(".//object[@id='SubmenuMarker']/property[@name='label']")
        self.assertEqual(marker.text, '>')
        (self.directory / 'item_menus-workspaces.xml').unlink()
        self.assertIn('item_menus-workspaces.xml: missing custom workspace layout',
                      walker_xml.generate(self.root, check=True))
