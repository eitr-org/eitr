"""Keep the Control Center launcher first in both bar orientations."""
from pathlib import Path
import unittest

BAR = Path(__file__).resolve().parents[1]


class EitrLogoTests(unittest.TestCase):
    def test_logo_precedes_overview_and_toggles_control_center(self):
        shell = (BAR / 'shell.qml').read_text()
        for group, identifier in (('verticalWorkspaces', 'verticalControlCenterLogo'),
                                  ('workspaces', 'controlCenterLogo')):
            with self.subTest(group=group):
                contents = shell.split('id: ' + group + '\n', 1)[1].split('Repeater {', 1)[0]
                self.assertLess(contents.index('EitrLogo {'), contents.index('icon: "󰕮"'))
                self.assertIn('slotWidth: shell.workspaceItemSize', contents)
                self.assertIn('id: ' + identifier, contents)
                self.assertIn('onClicked: bar.toggleControlCenter()', contents)
        self.assertIn('target: barContents', shell)
        self.assertIn('EitrLogo EitrLogo.qml', (BAR / 'qmldir').read_text())

    def test_logo_uses_canonical_asset_and_theme_ink(self):
        self.assertEqual((BAR / 'assets/eitr-logo-white.svg').read_bytes(),
                         (BAR.parents[1] / 'branding/svg/eitr-logo-white.svg').read_bytes())
        source = (BAR / 'EitrLogo.qml').read_text()
        self.assertIn('icon.color: logo.foreground', source)
        self.assertIn('Eitr.I18n.tr("Control Center")', source)
        self.assertNotIn('Rectangle {', source)
