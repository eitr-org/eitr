"""Display broker fixtures run without a compositor or attached monitor."""
import asyncio
import importlib.util
import json
from pathlib import Path
import subprocess
import threading
import unittest
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


domain_module = load('display-domain')
primary = load('display-primary')
broker_module = load('bar-data')


class TopologyTests(unittest.TestCase):
    def test_hotplug_primary_loss_and_reserved_space(self):
        domain = domain_module.DisplayDomain()
        adapter = Mock()
        adapter.preferred_outputs.return_value = ['DP-2', 'eDP-1']
        adapter.saved_primary.return_value = 'DP-1'
        adapter.choose_primary = primary.choose_primary
        domain.adapters['display-primary'] = adapter
        laptop = dict(name='eDP-1', width=1920, height=1080, reserved=[30, 0, 0, 0])
        large = dict(name='DP-1', width=3840, height=2160, reserved=[0, 10, 0, 40])
        preferred = dict(name='DP-2', width=1280, height=720, reserved=[0, 0, 0, 0])
        live = [laptop, large]
        def run(command, **kwargs):
            self.assertLessEqual(kwargs['timeout'], 5)
            result = live if 'monitors' in command else {'css': '6 12 18 24'}
            return subprocess.CompletedProcess(command, 0, json.dumps(result))
        with patch.object(domain_module.subprocess, 'run', side_effect=run):
            snapshot = domain.read('display.topology')
            self.assertEqual(snapshot['primary'], 'DP-1')
            self.assertEqual(snapshot['monitors'][1]['reserved'], [0, 10, 0, 40])
            self.assertEqual(snapshot['windowGaps'], [6, 12, 18, 24])
            live[:] = [laptop, preferred]
            self.assertEqual(domain.read('display.topology')['primary'], 'DP-2')
            live[:] = [laptop]
            self.assertEqual(domain.read('display.topology')['primary'], 'eDP-1')
            live.clear()
            self.assertEqual(domain.read('display.topology')['primary'], '')

    def test_settings_reuses_topology_without_monitor_query(self):
        domain = domain_module.DisplayDomain()
        domain.live = [dict(name='DP-1', reserved=[0, 0, 0, 0])]
        adapter = Mock()
        adapter.list_settings.return_value = {'monitors': []}
        domain.adapters['display-settings'] = adapter
        with patch.object(domain_module.subprocess, 'run', side_effect=AssertionError('duplicate query')):
            self.assertEqual(domain.read('display.settings'), {'monitors': []})
        adapter.list_settings.assert_called_once_with(domain.live)


class BrightnessTests(unittest.IsolatedAsyncioTestCase):
    async def test_ddc_does_not_poll_and_absent_monitor_is_valid(self):
        broker = broker_module.Broker(lambda frame: None, lambda topic: {'available': False, 'kind': '', 'value': 0})
        try:
            broker.request(dict(v=1, op='subscribe', topic='display.brightness', token='panel'))
            await broker.states['display.brightness']['task']
            self.assertEqual(broker.states['display.brightness']['status'], 'ready')
            broker.states['display.brightness']['data'] = {'kind': 'ddc', 'available': True}
            self.assertFalse(broker.scheduled('display.brightness'))
            broker.request(dict(v=1, op='unsubscribe', topic='display.brightness', token='panel'))
            self.assertFalse(broker.scheduled('display.nightlight'))
        finally:
            await broker.close()

    async def test_slow_read_cannot_publish_after_slider_releases_demand(self):
        gate = threading.Event()
        frames = []
        def reader(topic):
            gate.wait(2)
            return {'available': True, 'kind': 'ddc', 'value': 20}
        broker = broker_module.Broker(frames.append, reader, timeout=.01)
        try:
            broker.request(dict(v=1, op='subscribe', topic='display.brightness', token='panel'))
            task = broker.states['display.brightness']['task']
            await asyncio.sleep(.03)
            self.assertEqual(broker.states['display.brightness']['error'], 'timeout')
            broker.request(dict(v=1, op='unsubscribe', topic='display.brightness', token='panel'))
            gate.set()
            for attempt in range(100):
                if task.done():
                    break
                await asyncio.sleep(.01)
            self.assertTrue(task.done())
            self.assertFalse(any(frame.get('status') == 'ready' for frame in frames))
            self.assertIsNone(broker.states['display.brightness']['task'])
        finally:
            gate.set()
            await broker.close()
