import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import eitr_tailscale_migration as migration


class TailscaleMigrationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        patcher = patch.dict(os.environ, {'XDG_STATE_HOME': str(Path(directory.name) / 'state')})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.backend = Mock()
        self.backend.records.return_value = {}
        self.backend.prepare_review.return_value = {'token': 'review'}
        self.backend.confirm_review.return_value = True
        self.notify = Mock()

    def test_installs_the_pinned_official_plugin_once_and_notifies(self):
        migration.enqueue()
        with patch.object(migration.shutil, 'which', return_value='/usr/bin/tailscale'):
            self.assertTrue(migration.retry(backend=self.backend, notify=self.notify))
            self.assertFalse(migration.retry(backend=self.backend, notify=self.notify))
        self.backend.prepare_review.assert_called_once_with(migration.URL, plugin_id='tailscale', revision=migration.COMMIT)
        self.backend.confirm_review.assert_called_once_with('review')
        self.notify.assert_called_once_with()
        self.assertFalse(migration.pending().exists())

    def test_desktops_without_tailscale_or_with_the_plugin_just_finish(self):
        for which, records in ((None, {}), ('/usr/bin/tailscale', {'tailscale': {}})):
            with self.subTest(which=which):
                migration.enqueue()
                self.backend.records.return_value = records
                with patch.object(migration.shutil, 'which', return_value=which):
                    self.assertFalse(migration.retry(backend=self.backend, notify=self.notify))
                self.assertFalse(migration.pending().exists())
        self.backend.prepare_review.assert_not_called()
        self.notify.assert_not_called()

    def test_a_failed_fetch_keeps_the_queue_for_the_next_login(self):
        migration.enqueue()
        self.backend.prepare_review.side_effect = subprocess.CalledProcessError(128, 'git')
        with patch.object(migration.shutil, 'which', return_value='/usr/bin/tailscale'), \
             self.assertRaises(subprocess.SubprocessError):
            migration.retry(backend=self.backend, notify=self.notify)
        self.assertTrue(migration.pending().exists())
        self.notify.assert_not_called()

    def test_the_shipped_migration_queues_the_install(self):
        shipped = Path(__file__).resolve().parents[1] / 'migrations/20261110190000-tailscale-plugin.py'
        exec(compile(shipped.read_text(), str(shipped), 'exec'), {})
        self.assertTrue(migration.pending().exists())


if __name__ == '__main__':
    unittest.main()
