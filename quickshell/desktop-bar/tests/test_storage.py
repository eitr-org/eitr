import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    'system_details', Path(__file__).parents[1] / 'scripts/system-details.py')
system_details = importlib.util.module_from_spec(spec)
spec.loader.exec_module(system_details)


class StorageTests(unittest.TestCase):
    def test_only_installation_drive_is_shown_and_shared_subvolumes_are_counted_once(self):
        devices = {'blockdevices': [
            {'name': 'zram0', 'type': 'disk'},
            {'name': 'nvme0n1', 'type': 'disk', 'size': 1000, 'rota': False, 'model': ' System SSD ',
             'children': [{'name': 'nvme0n1p2', 'mountpoints': ['/', '/home', '/var/log']} ]},
            {'name': 'sda', 'type': 'disk', 'size': 2000, 'rota': True, 'model': 'Data drive'},
        ]}
        stats = SimpleNamespace(total=100, used=40, free=60)
        with patch.object(system_details, 'query', return_value=json.dumps(devices)), \
                patch.object(system_details.shutil, 'disk_usage', return_value=stats) as usage:
            sections = system_details.storage()
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]['usage'], 40)
        self.assertEqual(sections[0]['name'], 'System SSD')
        usage.assert_called_once_with('/')
        self.assertIn(['Type / device', 'NVMe SSD · nvme0n1'], sections[0]['rows'])

    def test_encrypted_partition_reports_mounted_usage(self):
        devices = {'blockdevices': [
            {'name': 'sda', 'type': 'disk', 'rota': False, 'children': [
                {'name': 'sda2', 'children': [{'name': 'cryptroot', 'mountpoints': ['/']}]}]},
        ]}
        with patch.object(system_details, 'query', return_value=json.dumps(devices)), \
                patch.object(system_details.shutil, 'disk_usage', return_value=SimpleNamespace(total=100, used=75, free=25)):
            self.assertEqual(system_details.storage()[0]['usage'], 75)


if __name__ == '__main__':
    unittest.main()
