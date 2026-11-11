import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'throughput-domain.py'


def load():
    specification = importlib.util.spec_from_file_location('throughput_domain', SCRIPT)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class ThroughputTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.now = 100.0

    def adapter(self, name, received, sent, device=True):
        statistics = self.root / name / 'statistics'
        statistics.mkdir(parents=True, exist_ok=True)
        (statistics / 'rx_bytes').write_text(str(received))
        (statistics / 'tx_bytes').write_text(str(sent))
        if device:
            (self.root / name / 'device').mkdir(exist_ok=True)

    def test_speed_is_the_difference_since_the_previous_read(self):
        domain = load().ThroughputDomain(self.root, clock=lambda: self.now)
        self.adapter('enp5s0', 1000, 500)
        self.adapter('lo', 0, 0, device=False)
        first = domain.read('throughput.network')
        self.assertEqual((first['download'], first['upload'], first['interfaces']), (None, None, ['enp5s0']))
        self.now += 2
        self.adapter('enp5s0', 5000, 1500)
        self.adapter('lo', 999999, 999999, device=False)
        second = domain.read('throughput.network')
        self.assertEqual((second['download'], second['upload']), (2000, 500))

    def test_a_stale_read_and_a_reset_counter_report_no_bogus_speed(self):
        domain = load().ThroughputDomain(self.root, clock=lambda: self.now)
        self.adapter('wlan0', 1000, 1000)
        domain.read('throughput.network')
        self.now += 60
        self.assertIsNone(domain.read('throughput.network')['download'])
        self.now += 1
        self.adapter('wlan0', 10, 10)
        self.assertEqual(domain.read('throughput.network')['download'], 0)


if __name__ == '__main__':
    unittest.main()
