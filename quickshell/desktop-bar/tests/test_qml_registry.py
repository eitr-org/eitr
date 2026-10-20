from pathlib import Path
import unittest


class QmlRegistryTests(unittest.TestCase):
    def test_directory_registry_includes_all_named_components(self):
        root = Path(__file__).parents[1]
        registry = (root / 'qmldir').read_text()
        registered = {line.split()[-1] for line in registry.splitlines() if line.strip()}
        components = {file.name for file in root.glob('*.qml') if file.stem[0].isupper()}
        self.assertEqual(registered, components)
        self.assertIn('singleton DesktopFonts 1.0 DesktopFonts.qml', registry)


if __name__ == '__main__':
    unittest.main()
