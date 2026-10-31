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

    def test_build_inputs_are_excluded_from_exported_runtime(self):
        import shutil
        inputs = ['tools/handbook-build.py',
                  'branding/sources/logos/eitr-logo-concept.png',
                  'branding/sources/logos/eitr-logo-master.png',
                  'branding/sources/logos/eitr-wordmark-master.svg']
        layout = module.Layout(ROOT)
        for relative in inputs:
            self.assertFalse(layout.classify(relative)['runtime'], relative)
        self.assertEqual(layout.classify(inputs[0])['class'], 'C')
        with tempfile.TemporaryDirectory() as directory:
            exported = Path(directory) / 'source'
            for relative in inputs + ['distro/layout-manifest.json', 'distro/legacy-layout.json']:
                target = exported / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            staged = Path(directory) / 'stage'
            staged.mkdir()
            module.Layout(exported).stage(staged)
            for relative in inputs:
                self.assertFalse((staged / relative).exists(), relative)

    def test_preferences_are_not_shipped_code(self):
        layout = module.Layout(ROOT)
        for path in ['nvim/init.lua', 'hypr/local.lua', 'quickshell/desktop-bar/bar-settings.json']:
            self.assertEqual(layout.classify(path)['class'], 'P')

    def test_eitr_colorscheme_is_package_owned_runtime_code(self):
        layout = module.Layout(ROOT)
        for relative in ['nvim-theme/colors/eitr.lua', 'nvim-theme/lua/eitr_theme/init.lua', 'nvim-theme/lua/lualine/themes/eitr.lua']:
            self.assertEqual(layout.classify(relative)['class'], 'C')
            self.assertTrue(layout.classify(relative)['runtime'])
        with tempfile.TemporaryDirectory() as directory:
            exported = Path(directory) / 'source'
            exported.mkdir()
            import shutil
            shutil.copytree(ROOT / 'nvim-theme', exported / 'nvim-theme')
            shutil.copytree(ROOT / 'distro', exported / 'distro', ignore=shutil.ignore_patterns('__pycache__'))
            staged = Path(directory) / 'stage'
            module.Layout(exported).stage(staged)
            self.assertTrue((staged / 'nvim-theme/colors/eitr.lua').is_file())

    def test_display_service_runtime_files_stage_from_export(self):
        import shutil
        runtime_files = ['quickshell/desktop-bar/DisplayService.qml',
                         'quickshell/desktop-bar/scripts/display-domain.py']
        layout = module.Layout(ROOT)
        for relative in runtime_files:
            self.assertEqual(layout.classify(relative)['class'], 'C')
            self.assertTrue(layout.classify(relative)['runtime'])
        with tempfile.TemporaryDirectory() as directory:
            exported = Path(directory) / 'source'
            for relative in runtime_files + ['distro/layout-manifest.json', 'distro/legacy-layout.json']:
                target = exported / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            staged = Path(directory) / 'stage'
            module.Layout(exported).stage(staged)
            for relative in runtime_files:
                self.assertEqual((staged / relative).read_bytes(), (ROOT / relative).read_bytes())
