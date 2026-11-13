"""Official design allowlists, privileged guards and non-destructive visibility."""
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'distro/lib'))
sys.path.insert(0, str(ROOT / 'distro/system'))
sys.path.insert(0, str(ROOT / 'walker/tests'))
from home_isolation import setUpModule, tearDownModule
import eitr_lockscreen_packages as catalog
import eitr_lockscreen_packages_root as privileged
import eitr_own_lockscreens as own


class LockscreenPackageTests(unittest.TestCase):
    def test_optional_allowlist(self):
        self.assertEqual(catalog.names(['clockwork/tape']), ['eitr-lockscreen-clockwork-tape'])
        for value in ([], ['eitr'], ['../nothing'], ['nothing', 'nothing'], ['--help'], [None], 'nothing'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                catalog.names(value)

    def test_root_refuses_unprivileged_and_current_removal(self):
        with patch.object(privileged.os, 'geteuid', return_value=1000), self.assertRaises(ValueError):
            privileged.dispatch('remove', io.StringIO('["nothing"]'))
        with patch.object(privileged.os, 'geteuid', return_value=0), \
                patch.object(privileged, 'in_use', return_value={'nothing'}), \
                patch.object(privileged.subprocess, 'run') as command, self.assertRaises(ValueError):
            privileged.dispatch('remove', io.StringIO('["nothing"]'))
        command.assert_not_called()

    def test_only_eitr_repositories_and_explicit_install(self):
        config = '[options]\nSigLevel = Required DatabaseOptional\n[extra]\nServer = bad\n[eitr-testing]\nServer = testing\n[eitr]\nServer = stable\n[custom]\nServer = bad\n'
        captured = []
        def run(arguments, **options):
            captured.append((arguments, Path(arguments[2]).read_text()))
        with patch.object(privileged.subprocess, 'check_output', return_value=config), \
                patch.object(privileged.subprocess, 'run', side_effect=run):
            privileged.install(['eitr-lockscreen-nothing'])
        arguments, filtered = captured[0]
        self.assertNotIn('[extra]', filtered)
        self.assertNotIn('[custom]', filtered)
        self.assertIn('[eitr-testing]', filtered)
        self.assertIn('[eitr]', filtered)
        self.assertNotIn('--asdeps', arguments)
        self.assertNotIn('-Sy', arguments)

    def test_migration_marker_is_written_only_after_success_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(privileged, 'MARKER', Path(directory) / 'marker'), \
                patch.object(privileged, 'SAVED', Path(directory) / 'saved'), \
                patch.object(privileged, 'install') as install, \
                patch.object(privileged.subprocess, 'run') as select:
            privileged.SAVED.write_text('desktop-lockscreen-clockwork-tape\n')
            install.side_effect = RuntimeError('offline')
            with self.assertRaises(RuntimeError):
                privileged.migrate()
            self.assertFalse(privileged.MARKER.exists())
            self.assertTrue(privileged.SAVED.exists())
            install.side_effect = None
            privileged.migrate()
            self.assertTrue(privileged.MARKER.exists())
            select.assert_called_once_with(['/usr/lib/eitr/desktop-login-select', 'clockwork/tape'], check=True)
            install.reset_mock()
            privileged.migrate()
            install.assert_not_called()

    def test_root_protects_login_and_own_session_base(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            login = home / 'login.conf'
            login.write_text('[Theme]\nCurrent=desktop-lockscreen-clockwork-tape\n')
            selected = home / '.config/lockscreen/selected'
            selected.parent.mkdir(parents=True)
            selected.write_text('user:my-picture')
            settings = home / '.local/share/eitr/lockscreens/my-picture/lockscreen.json'
            settings.parent.mkdir(parents=True)
            settings.write_text('{"design":"material-you"}')
            with patch.object(privileged, 'LOGIN', login), patch.object(privileged.pwd, 'getpwall', return_value=[SimpleNamespace(pw_dir=directory)]):
                self.assertEqual(privileged.in_use(), {'clockwork/tape', 'material-you'})

    def test_catalog_keeps_all_previews_but_installed_page_is_filtered(self):
        with patch.object(catalog, 'installed_designs', return_value={'eitr', 'nothing'}), \
                patch.object(catalog, 'current_designs', return_value={'nothing'}):
            rows = catalog.listing()
            self.assertEqual(len(rows), 9)
            current = next(row for row in rows if row['id'] == 'nothing')
            self.assertTrue(current['current'])
            self.assertFalse(current['removable'])
            self.assertFalse(next(row for row in rows if row['id'] == 'eitr')['removable'])
            self.assertEqual({row['id'] for row in catalog.listing(True)}, {'eitr', 'nothing'})

    def test_own_lockscreens_hidden_without_deleting(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'mine'
            folder.mkdir()
            (folder / 'picture.png').write_bytes(b'picture')
            (folder / 'lockscreen.json').write_text('{"design":"material-you", "picture":"picture.png"}')
            with patch.object(own, 'own', return_value=Path(directory)), patch.object(catalog, 'installed_designs', return_value=set()):
                self.assertEqual(own.own_lockscreens(), {})
                self.assertTrue((folder / 'picture.png').exists())
            with patch.object(own, 'own', return_value=Path(directory)), patch.object(catalog, 'installed_designs', return_value={'material-you'}):
                self.assertIn('user:mine', own.own_lockscreens())

    def test_split_stage_owns_only_one_design_and_shared_wrapper(self):
        spec = importlib.util.spec_from_file_location('single_login_stage', ROOT / 'quickshell/lockscreen/scripts/install-login.py')
        stage = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stage)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage.stage(root, 'clockwork/tape')
            theme = root / 'usr/share/sddm/themes/desktop-lockscreen-clockwork-tape'
            self.assertTrue((theme / 'Design.qml').is_file())
            self.assertEqual((theme / 'Main.qml').read_text(), (stage.LOGIN_WRAPPER / 'Main.qml').read_text())
            self.assertTrue((theme / 'LoginDisplay.js').is_file())
            self.assertEqual(len(list((root / 'usr/share/sddm/themes').iterdir())), 1)
            self.assertFalse((root / 'usr/lib/eitr/desktop-login-select').exists())
            self.assertEqual(catalog.manifests(root / 'usr/share/eitr/lockscreen-designs.d'), {'clockwork/tape': 'desktop-lockscreen-clockwork-tape'})

    def test_split_pkgbuild_stages_the_named_session_and_login_design(self):
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            source.mkdir()
            (source / 'eitr').symlink_to(ROOT, target_is_directory=True)
            target = root / 'package'
            subprocess.run(['bash', '-euc',
                            'startdir="$1"; srcdir="$2"; pkgdir="$3"; source "$startdir/PKGBUILD"; '
                            'pkgname=eitr-lockscreen-clockwork-tape; package_eitr-lockscreen-clockwork-tape',
                            'stage', str(ROOT / 'distro/pkg/eitr-lockscreens'), str(source), str(target)],
                           check=True, capture_output=True, text=True)
            themes = target / 'usr/share/eitr/quickshell/lockscreen/themes'
            self.assertEqual([str(path.relative_to(themes)) for path in themes.rglob('Main.qml')], ['clockwork/tape/Main.qml'])
            self.assertTrue((target / 'usr/share/sddm/themes/desktop-lockscreen-clockwork-tape/Design.qml').is_file())
            self.assertFalse((target / 'usr/lib/eitr/desktop-login-select').exists())
