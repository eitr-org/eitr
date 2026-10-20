import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('eitr_layout', ROOT / 'distro/lib/layout.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LayoutManifestTests(unittest.TestCase):
    def test_every_tracked_path_has_an_explicit_class(self):
        layout = module.Layout(ROOT)
        for path in subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines():
            rule = layout.classify(path)
            self.assertIn(rule['class'], 'CDGP', path)
            self.assertIs(type(rule['runtime']), bool)
        with self.assertRaises(ValueError):
            layout.classify('unknown-component/new-file')

    def test_runtime_stage_excludes_tests_and_reference_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            module.Layout(ROOT).stage(directory)
            paths = [str(path.relative_to(directory)) for path in Path(directory).rglob('*')]
            self.assertFalse(any('/tests/' in path or '/references/' in path or '__pycache__' in path for path in paths))
            self.assertIn('quickshell/desktop-bar/shell.qml', paths)
            self.assertIn('walker/scripts/menus/search-index.py', paths)
            self.assertFalse(any(path.startswith('config/') for path in paths))

    def test_preferences_are_not_shipped_code(self):
        layout = module.Layout(ROOT)
        for path in ['nvim/init.lua', 'hypr/local.lua', 'quickshell/desktop-bar/bar-settings.json']:
            self.assertEqual(layout.classify(path)['class'], 'P')
