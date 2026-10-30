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


class IdentityCacheTests(unittest.TestCase):
    def test_cached_identity_skips_topology_and_unsupported_gpu_queries(self):
        identity = {'cpu': {'name': 'Cached processor', 'cores': '4 / 8'},
                    'storage': {'name': 'Cached SSD', 'rows': [['Capacity', '100 GiB']]},
                    'gpu': {'available': False, 'name': 'GPU telemetry unavailable'}}
        stats = SimpleNamespace(total=100, used=40, free=60)
        with patch.object(system_details, 'query', return_value='') as query, \
                patch.object(system_details, 'cpu_identity', side_effect=AssertionError('CPU rediscovery')), \
                patch.object(system_details, 'storage_identity', side_effect=AssertionError('Disk rediscovery')), \
                patch.object(system_details.time, 'sleep'), \
                patch.object(system_details.shutil, 'disk_usage', return_value=stats):
            result = system_details.snapshot(identity)
        self.assertEqual(result['identity'], identity)
        self.assertEqual(result['sections'][0]['name'], 'Cached processor')
        self.assertEqual(result['sections'][3]['name'], 'Cached SSD')
        self.assertEqual(result['sections'][3]['usage'], 40)
        query.assert_called_once_with(['sensors', '-j'])
        self.assertEqual(identity['storage']['rows'], [['Capacity', '100 GiB']])
    def test_supported_gpu_uses_cached_model_with_fresh_telemetry(self):
        identity = {'available': True, 'name': 'Cached GPU'}
        with patch.object(system_details, 'query', return_value='42, 512, 4096, 55, 20, 100') as query:
            result = system_details.gpu(identity)
        self.assertEqual(result['name'], 'Cached GPU')
        self.assertEqual(result['usage'], 42)
        self.assertNotIn('name,', query.call_args.args[0][1])


if __name__ == '__main__':
    unittest.main()


class HardwareSamplingFixtures(unittest.TestCase):
    def test_cpu_delta_uses_busy_ticks_and_iowait(self):
        files = {'/proc/cpuinfo': 'model name: Fixture CPU\ncpu MHz: 3000\n',
                 '/proc/loadavg': '1.00 2.00 3.00 1/100 42'}
        with patch.object(system_details, 'cpu_ticks', side_effect=[(1000, 700), (1100, 725)]), \
                patch.object(system_details.time, 'sleep') as sleep, \
                patch.object(system_details.Path, 'read_text', autospec=True, side_effect=lambda path: files[str(path)]), \
                patch.object(system_details, 'query', return_value=''):
            result = system_details.cpu({'name': 'Fixture CPU', 'cores': '4 / 8'})
        self.assertEqual(result['usage'], 75)
        self.assertIn(['Load · 1 / 5 / 15 min', '1.00 / 2.00 / 3.00'], result['rows'])
        sleep.assert_called_once_with(.2)

    def test_cpu_ticks_include_iowait_in_idle(self):
        with patch.object(system_details.Path, 'read_text', return_value='cpu 10 20 30 40 50 60 70 80 90 100\n'):
            self.assertEqual(system_details.cpu_ticks(), (360, 90))

    def test_missing_or_timed_out_gpu_is_cached(self):
        for error in (FileNotFoundError(), system_details.subprocess.TimeoutExpired('nvidia-smi', 2)):
            with patch.object(system_details.subprocess, 'check_output', side_effect=error) as command:
                graphics = system_details.gpu()
                identity = {'available': bool(graphics['rows']), 'name': graphics['name']}
                self.assertIsNone(system_details.gpu(identity)['usage'])
                self.assertIsNone(system_details.gpu(identity)['usage'])
                command.assert_called_once()
                self.assertEqual(command.call_args.kwargs['timeout'], 2)
