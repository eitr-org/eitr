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
    def test_online_peers_are_filtered_and_sorted_without_queries(self):
        data = {'BackendState': 'Running', 'TailscaleIPs': ['100.64.0.1'],
                'Self': {'HostName': 'desktop'}, 'CurrentTailnet': {'Name': 'example'},
                'Peer': {'a': {'HostName': 'zebra', 'Online': True, 'Active': True, 'CurAddr': 'direct'},
                         'b': {'HostName': 'alpha', 'Online': True, 'Active': False, 'Relay': 'relay'},
                         'c': {'HostName': 'offline', 'Online': False}}}
        with patch.object(status.shutil, 'which', return_value='/usr/bin/tailscale'), \
                patch.object(status, 'query', return_value=subprocess.CompletedProcess([], 0, json.dumps(data))) as query:
            result = status.tailscale_status()
        query.assert_called_once_with(['tailscale', 'status', '--json'])
        self.assertEqual([peer['name'] for peer in result['peers']], ['alpha', 'zebra'])
        self.assertEqual(result['peers'][0]['connection'], 'Idle; ping to check')
        self.assertEqual(result['facts'][0]['value'], 'desktop')

    def test_unavailable_and_signed_out_are_not_connected(self):
        with patch.object(status.shutil, 'which', return_value='/usr/bin/tailscale'):
            for response, expected in ((subprocess.TimeoutExpired('tailscale', 3), 'Tailscale status unavailable.'),
                                       (subprocess.CompletedProcess([], 1, '{}'), 'Tailscale status unavailable.'),
                                       (subprocess.CompletedProcess([], 1, '{"BackendState":"Running"}'), 'Tailscale status unavailable.'),
                                       (subprocess.CompletedProcess([], 0, '{"BackendState":"NeedsLogin"}'), 'Signed out')):
                with self.subTest(expected=expected), patch.object(status, 'query') as query:
                    if isinstance(response, Exception):
                        query.side_effect = response
                    else:
                        query.return_value = response
                    result = status.tailscale_status()
                    self.assertEqual(result['status'], expected)
                    self.assertFalse(result['connected'])
                    self.assertEqual(result['signedOut'], expected == 'Signed out')

    def test_sharing_status_does_not_start_service(self):
        with patch.object(status.shutil, 'which', return_value='/usr/bin/sunshine'), \
                patch.object(status, 'query', return_value=subprocess.CompletedProcess([], 0, 'ActiveState=active\nUnitFileState=enabled\n')) as query:
            result = status.streaming_status()
        self.assertTrue(result['running'])
        self.assertTrue(result['startAtLogin'])
        self.assertEqual(query.call_args.args[0][:4], ['systemctl', '--user', 'show', 'eitr-sunshine.service'])

    def test_panel_actions_keep_setup_in_walker_and_exclude_self_links(self):
        with patch.dict(os.environ, EITR_CODE_ROOT=str(ROOT)), patch.object(status, 'table', return_value={}):
            rows = status.menu_actions('remote-away')
        titles = [row['source'] for row in rows]
        self.assertIn('Connect', titles)
        self.assertIn('Detailed Status', titles)
        self.assertIn('Sign In', titles)
        self.assertNotIn('Connection Status', titles)


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
        self.assertFalse(result['tailscale']['installed'])
        self.assertEqual(result['tailscale']['status'], 'Tailscale is not installed.')
        self.assertEqual(result['streaming']['status'], 'Sunshine is not installed.')

    def test_policy_denied_skips_clients_and_actions(self):
        with patch('eitr_policy.allowed', return_value=False), \
                patch.object(self.domain.adapter, 'query') as query, \
                patch.object(self.domain.adapter, 'menu_actions') as actions:
            self.assertEqual(self.domain.read('remote.status'), {'allowed': False, 'tailscale': {}, 'streaming': {}})
            self.assertEqual(self.domain.read('remote.availability'), {'allowed': False})
        query.assert_not_called()
        actions.assert_not_called()

    def test_service_error_preserves_translated_messages(self):
        with patch('eitr_policy.allowed', return_value=True), \
                patch.object(self.domain.adapter.shutil, 'which', return_value='/fixture/client'), \
                patch.object(self.domain.adapter, 'query', side_effect=subprocess.TimeoutExpired('fixture', 3)), \
                patch.object(self.domain.adapter, 'menu_actions', return_value=[]):
            result = self.domain.read('remote.status')
        self.assertEqual(result['tailscale']['status'], 'Tailscale status unavailable.')
        self.assertEqual(result['streaming']['status'], 'Sharing status unavailable.')

    def test_availability_does_not_read_clients(self):
        with patch('eitr_policy.allowed', return_value=True), patch.object(self.domain.adapter, 'status') as read:
            self.assertEqual(self.domain.read('remote.availability'), {'allowed': True})
        read.assert_not_called()
