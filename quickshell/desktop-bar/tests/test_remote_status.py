import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('remote_status', ROOT / 'quickshell/desktop-bar/scripts/remote-status.py')
status = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(status)


class RemoteStatusTests(unittest.TestCase):
    def test_moonlight_status_is_independent_of_sunshine(self):
        with patch.object(status.shutil, 'which', side_effect=lambda executable: '/usr/bin/moonlight' if executable == 'moonlight' else None), patch.object(status, 'query') as query:
            result = status.streaming_status()
        self.assertTrue(result['moonlightInstalled'])
        self.assertFalse(result['installed'])
        query.assert_not_called()

    def test_sharing_status_does_not_start_service(self):
        with patch.object(status.shutil, 'which', return_value='/usr/bin/sunshine'), \
                patch.object(status, 'query', return_value=subprocess.CompletedProcess([], 0, 'ActiveState=active\nUnitFileState=enabled\n')) as query:
            result = status.streaming_status()
        self.assertTrue(result['running'])
        self.assertTrue(result['startAtLogin'])
        self.assertEqual(query.call_args.args[0][:4], ['systemctl', '--user', 'show', 'eitr-sunshine.service'])

    def test_panel_actions_keep_setup_in_walker_and_exclude_self_links(self):
        with patch.dict(os.environ, EITR_CODE_ROOT=str(ROOT)), patch.object(status, 'table', return_value={}):
            rows = status.menu_actions('remote-access')
        titles = [row['source'] for row in rows]
        self.assertIn('Start Sharing', titles)
        self.assertIn('Set Up Sharing', titles)
        self.assertNotIn('Sharing Status', titles)

    def test_tailscale_is_left_to_its_plugin(self):
        with patch('eitr_policy.allowed', return_value=True), \
                patch.object(status, 'streaming_status', return_value={}), patch.object(status, 'menu_actions', return_value=[]):
            self.assertEqual(set(status.status()), {'allowed', 'streaming'})


class RemoteDomainTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('remote_domain', ROOT / 'quickshell/desktop-bar/scripts/remote-domain.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.domain = module.RemoteDomain()

    def test_client_missing_preserves_cli_result(self):
        with patch.object(self.domain.adapter.shutil, 'which', return_value=None), \
                patch.object(self.domain.adapter, 'menu_actions', return_value=[]), \
                patch('eitr_policy.allowed', return_value=True), \
                patch.object(self.domain.adapter, 'query') as query:
            result = self.domain.read('remote.status')
        query.assert_not_called()
        self.assertEqual(result['streaming']['status'], 'Sunshine is not installed.')

    def test_policy_denied_skips_clients_and_actions(self):
        with patch('eitr_policy.allowed', return_value=False), \
                patch.object(self.domain.adapter, 'query') as query, \
                patch.object(self.domain.adapter, 'menu_actions') as actions:
            self.assertEqual(self.domain.read('remote.status'), {'allowed': False, 'streaming': {}})
            self.assertEqual(self.domain.read('remote.availability'), {'allowed': False})
        query.assert_not_called()
        actions.assert_not_called()

    def test_service_error_preserves_translated_messages(self):
        with patch('eitr_policy.allowed', return_value=True), \
                patch.object(self.domain.adapter.shutil, 'which', return_value='/fixture/client'), \
                patch.object(self.domain.adapter, 'query', side_effect=subprocess.TimeoutExpired('fixture', 3)), \
                patch.object(self.domain.adapter, 'menu_actions', return_value=[]):
            result = self.domain.read('remote.status')
        self.assertEqual(result['streaming']['status'], 'Sharing status unavailable.')

    def test_availability_does_not_read_clients(self):
        with patch('eitr_policy.allowed', return_value=True), patch.object(self.domain.adapter, 'status') as read:
            self.assertEqual(self.domain.read('remote.availability'), {'allowed': True})
        read.assert_not_called()
