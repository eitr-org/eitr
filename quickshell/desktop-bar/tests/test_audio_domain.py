import importlib.util
import json
from pathlib import Path
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'audio-domain.py'


def load():
    specification = importlib.util.spec_from_file_location('audio_domain', SCRIPT)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def port(profiles, availability='available', **properties):
    return dict(description='Port', availability=availability, profiles=profiles, properties=properties)


# The shapes `pactl -f json list cards` prints: a graphics card with two monitors (one profile
# per HDMI port), onboard audio on optical with unplugged jacks, a USB headset listing an
# optical output it does not have, and a Bluetooth headset.
CARDS = [
    dict(name='alsa_card.pci-gpu', active_profile='output:hdmi-stereo-extra1',
         properties={'device.description': 'GA104 High Definition Audio Controller', 'device.bus': 'pci'},
         profiles={'output:hdmi-stereo': dict(priority=5900, available=True),
                   'output:hdmi-stereo-extra1': dict(priority=5700, available=True),
                   'output:hdmi-stereo-extra2': dict(priority=5700, available=False)},
         ports={'hdmi-output-0': port(['output:hdmi-stereo'], **{'device.product.name': 'ARZOPA', 'port.type': 'hdmi'}),
                'hdmi-output-1': port(['output:hdmi-stereo-extra1'], **{'device.product.name': '34GL750', 'port.type': 'hdmi'}),
                'hdmi-output-2': port(['output:hdmi-stereo-extra2'], 'not available')}),
    dict(name='alsa_card.pci-onboard', active_profile='output:iec958-stereo+input:analog-stereo',
         properties={'device.description': 'Built-in Audio', 'device.bus': 'pci'},
         profiles={'output:analog-stereo': dict(priority=6500, available=True),
                   'output:analog-stereo+input:analog-stereo': dict(priority=6565, available=True),
                   'output:iec958-stereo': dict(priority=5500, available=True),
                   'output:iec958-stereo+input:analog-stereo': dict(priority=5565, available=True),
                   'input:analog-stereo': dict(priority=65, available=True)},
         ports={'analog-output-lineout': port(['output:analog-stereo', 'output:analog-stereo+input:analog-stereo'],
                                              **{'port.type': 'line'}),
                'analog-input-front-mic': port(['input:analog-stereo', 'output:analog-stereo+input:analog-stereo',
                                                'output:iec958-stereo+input:analog-stereo'], 'not available'),
                'iec958-stereo-output': port(['output:iec958-stereo', 'output:iec958-stereo+input:analog-stereo'],
                                             'availability unknown')}),
    dict(name='alsa_card.usb-headset', active_profile='output:analog-stereo+input:mono-fallback',
         properties={'device.description': 'G522', 'device.bus': 'usb'},
         profiles={'output:analog-stereo+input:mono-fallback': dict(priority=6501, available=True),
                   'output:iec958-stereo+input:mono-fallback': dict(priority=5501, available=True),
                   'output:iec958-stereo': dict(priority=5500, available=True)},
         ports={'iec958-stereo-output': port(['output:iec958-stereo', 'output:iec958-stereo+input:mono-fallback'],
                                             'availability unknown')}),
    dict(name='bluez_card.headset', active_profile='a2dp-sink', properties={}, profiles={},
         ports={'headset-output': port(['a2dp-sink', 'headset-head-unit'])}),
]


class AudioPortsTests(unittest.TestCase):
    def test_lists_the_ports_no_current_profile_uses(self):
        found = {(entry['card'], entry['port']): entry for entry in load().ports(CARDS)}
        self.assertEqual(set(found), {('alsa_card.pci-gpu', 'hdmi-output-0'), ('alsa_card.pci-onboard', 'analog-output-lineout')})
        monitor = found['alsa_card.pci-gpu', 'hdmi-output-0']
        self.assertEqual((monitor['profile'], monitor['direction'], monitor['monitor'], monitor['node']),
                         ('output:hdmi-stereo', 'output', 'ARZOPA', 'alsa_output.pci-gpu.hdmi-stereo'))

    def test_switching_output_keeps_the_cards_input(self):
        found = {entry['port']: entry for entry in load().ports(CARDS)}
        self.assertEqual(found['analog-output-lineout']['profile'], 'output:analog-stereo+input:analog-stereo')
        self.assertEqual(found['analog-output-lineout']['node'], 'alsa_output.pci-onboard.analog-stereo')

    def test_input_ports_are_offered_as_inputs(self):
        cards = json.loads(json.dumps(CARDS[1:2]))
        cards[0]['ports']['analog-input-front-mic']['availability'] = 'available'
        cards[0]['ports']['analog-output-lineout']['availability'] = 'not available'
        self.assertEqual(load().ports(cards), [])  # the current profile already has that input
        cards[0]['active_profile'] = 'output:iec958-stereo'
        (entry,) = load().ports(cards)
        self.assertEqual((entry['direction'], entry['profile'], entry['node']),
                         ('input', 'output:iec958-stereo+input:analog-stereo', 'alsa_input.pci-onboard.analog-stereo'))

    def test_unexpected_shapes_give_no_ports(self):
        self.assertEqual(load().ports(None), [])
        self.assertEqual(load().ports([dict(name='alsa_card.x', ports=None)]), [])

    def test_select_switches_only_to_an_offered_port(self):
        module = load()
        calls = []

        class Domain(module.AudioDomain):
            def pactl(self, arguments, deadline):
                calls.append(arguments)
                return json.dumps(CARDS) if arguments[:1] == ['-f'] else ''

        deadline = time.monotonic() + 5
        with self.assertRaises(ValueError):
            Domain().query('select', dict(card='alsa_card.pci-gpu', profile='output:hdmi-stereo-extra2'), deadline)
        self.assertEqual(Domain().query('select', dict(card='alsa_card.pci-gpu', profile='output:hdmi-stereo'), deadline),
                         dict(done=True))
        self.assertEqual(calls[-1], ['set-card-profile', 'alsa_card.pci-gpu', 'output:hdmi-stereo'])


if __name__ == '__main__':
    unittest.main()
