"""Public plugin exports and owner dependency boundaries."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from layout import Layout

import eitr_plugins


class PluginFacadeTests(unittest.TestCase):
    def test_original_exports_remain_available(self):
        expected = {
            'ALL_INSTALLED', 'ALREADY_INSTALLED', 'BLOCKLIST', 'COMMIT',
            'HOOK_EVENTS', 'HOOK_TIMEOUT', 'OFFICIAL_REPOSITORY', 'Plugins',
            'REPORT_URL', 'SLUG', 'SSH_SHORT', 'UI_FAILURE_LIMIT', 'add_flags',
            'binary_files', 'blocked_reason', 'blocklist', 'clone', 'command',
            'commit', 'dispatch_hooks', 'executable_files', 'git', 'identifier',
            'image_asset', 'live_flags', 'manifest', 'normalized_url',
            'object_keys', 'official', 'plugin_files', 'policy_reason',
            'printable', 'qml_files', 'repository_plugins', 'repository_url',
            'service_text', 'short_author', 'string', 'unique_object',
            'unit_content', 'update_changes', 'validate_ui',
        }
        self.assertEqual(set(expected), {name for name in vars(eitr_plugins) if not name.startswith('_')})

    def test_owner_dependencies_do_not_return_to_facade(self):
        library = Path(__file__).resolve().parents[2] / 'distro/lib'
        for owner in ('manifest', 'install', 'runtime'):
            with self.subTest(owner=owner):
                tree = ast.parse((library / f'eitr_plugin_{owner}.py').read_text())
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.update(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        imports.add(node.module)
                self.assertNotIn('eitr_plugins', imports)
                if owner == 'manifest':
                    self.assertTrue(imports.isdisjoint({
                        'eitr_plugin_install', 'eitr_plugin_runtime',
                    }))

    def test_staged_library_imports_through_bootstrap(self):
        root = Path(__file__).resolve().parents[2]
        layout = Layout(root)
        libraries = sorted(str(path.relative_to(root)) for path in (root / 'distro/lib').glob('*.py'))
        for name in ('manifest', 'install', 'runtime'):
            rule = layout.classify(f'distro/lib/eitr_plugin_{name}.py')
            self.assertEqual((rule['class'], rule['runtime']), ('C', True))
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            with patch.object(layout, 'files', return_value=libraries):
                layout.stage(destination)
            environment = dict(os.environ, PYTHONPATH=str(destination / 'lib'), PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run(
                [sys.executable, '-c',
                 'import sys; import eitr_bootstrap; import eitr_plugin_manifest; '
                 'assert "eitr_plugin_install" not in sys.modules; '
                 'assert "eitr_plugin_runtime" not in sys.modules; '
                 'import eitr_plugin_install; import eitr_plugin_runtime; '
                 'assert "eitr_plugins" not in sys.modules; '
                 'from eitr_plugins import Plugins, manifest, dispatch_hooks; '
                 'assert callable(Plugins) and callable(manifest) and callable(dispatch_hooks)'],
                cwd=directory, env=environment, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
