"""About's hardware lines: installed RAM, every connected drive and the display controllers."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'system_details', Path(__file__).parents[1] / 'scripts/system-details.py')
system_details = importlib.util.module_from_spec(spec)
spec.loader.exec_module(system_details)


class AboutInventoryTests(unittest.TestCase):
    def test_installed_memory_counts_online_blocks_and_falls_back_to_usable_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = Path(directory) / 'memory'
            memory.mkdir()
            (memory / 'block_size_bytes').write_text('8000000\n')
            for index, state in enumerate(['online'] * 256 + ['offline']):
                (memory / f'memory{index}').mkdir()
                (memory / f'memory{index}' / 'state').write_text(state + '\n')
            meminfo = Path(directory) / 'meminfo'
            meminfo.write_text('MemTotal:       32740820 kB\n')
            self.assertEqual(system_details.installed_memory(memory, meminfo), 32)
            self.assertAlmostEqual(system_details.installed_memory(Path(directory) / 'missing', meminfo), 31.2, places=1)

    def test_every_drive_is_listed_with_its_printed_capacity(self):
        devices = [{'name': 'zram0', 'type': 'disk', 'size': 4 * 2 ** 30},
                   {'name': 'loop0', 'type': 'loop', 'size': 1},
                   {'name': 'sr0', 'type': 'rom', 'size': 1},
                   {'name': 'nvme0n1', 'type': 'disk', 'size': 1000204886016, 'rota': False, 'model': 'WD Green SN350 1TB', 'tran': 'nvme'},
                   {'name': 'sda', 'type': 'disk', 'size': 500107862016, 'rota': False, 'model': ' Samsung SSD ', 'tran': 'sata'},
                   {'name': 'sdb', 'type': 'disk', 'size': 4000787030016, 'rota': True, 'model': None, 'tran': 'usb'}]
        self.assertEqual([line['name'] for line in system_details.disks(devices)],
                         ['WD Green SN350 1TB · NVMe SSD · 1.0 TB', 'Samsung SSD · SSD · 500 GB', 'sdb · USB drive · 4.0 TB'])

    def test_graphics_names_come_from_the_bracketed_product(self):
        listing = ('00:02.0 "VGA compatible controller" "Intel Corporation" "Alder Lake-P GT2 [Iris Xe Graphics]" -r0c "Vendor" "Device"\n'
                   '01:00.0 "VGA compatible controller" "NVIDIA Corporation" "GA104 [GeForce RTX 3070 Lite Hash Rate]" -ra1 -p00 "MSI" "Device 3908"\n'
                   '00:1f.3 "Audio device" "Intel Corporation" "Sound" "Vendor" "Device"\n')
        self.assertEqual(system_details.graphics_names(listing),
                         ['Intel Iris Xe Graphics', 'NVIDIA GeForce RTX 3070 Lite Hash Rate'])


if __name__ == '__main__':
    unittest.main()
