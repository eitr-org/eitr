"""Compatibility surface captured before splitting the plugin implementation."""
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
            'ET', 'HOOK_EVENTS', 'HOOK_TIMEOUT', 'OFFICIAL_REPOSITORY',
            'Path', 'Plugins', 'PurePosixPath', 'REPORT_URL',
            'SLUG', 'SSH_SHORT', 'UI_FAILURE_LIMIT', 'add_flags',
            'binary_files', 'blocked_reason', 'blocklist', 'clone',
            'command', 'commit', 'config', 'contextlib',
            'data', 'datetime', 'dispatch_hooks', 'eitr_policy',
            'executable_files', 'fcntl', 'git', 'hashlib',
            'identifier', 'image_asset', 'json', 'live_flags',
            'manifest', 'mark', 'normalized_url', 'object_keys',
            'official', 'os', 'plugin_files', 'policy_reason',
            'printable', 'qml_files', 're', 'repository_plugins',
            'repository_url', 'service_text', 'short_author', 'shutil',
            'signal', 'state', 'string', 'subprocess',
            'tempfile', 'tr', 'unique_object', 'unit_content',
            'update_changes', 'urlsplit', 'validate_ui',
        }
        self.assertEqual(set(expected), {name for name in vars(eitr_plugins) if not name.startswith('_')})

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
                 'import eitr_bootstrap; import eitr_plugin_manifest; '
                 'import eitr_plugin_install; import eitr_plugin_runtime; '
                 'from eitr_plugins import Plugins, manifest, dispatch_hooks; '
                 'assert callable(Plugins) and callable(manifest) and callable(dispatch_hooks)'],
                cwd=directory, env=environment, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
